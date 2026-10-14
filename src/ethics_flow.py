# -*- coding: utf-8 -*-
"""Sound control-flow joins for Ethical Analyzer v2.1.

PATCH 1-6 (issue #47) - control-flow context (pc_labels). Numbering follows
compiler_fix_queue.md / issue #47; see docs/patches/patch_4_6_spec.md.
  PATCH 1: print is an output sink (by label flow, not by mandate).
  PATCH 2: assignment under a sensitive condition inherits pc_labels.
  PATCH 3: return under a sensitive condition inherits pc_labels.
  PATCH 4: branch merge joins only the branch exits (sanitizer in both branches).
  PATCH 5: pc-aware summaries - value and effect of a helper inherit caller pc.
  PATCH 6: loop fixpoint folds condition labels into pc + transitive caller PC.
"""
from src.ethics_v21 import (EthicalAnalyzer, AuditEntry, EthicalError,
                            SINKS)
from src.syntax import (Let, Assign, Return, If, While,
                        Call, Binary)

# Output sinks: take part in the label flow, but do NOT require a mandate (PATCH 1).
PROGRAM_OUTPUT = frozenset({"print"})


class SoundEthicalAnalyzer(EthicalAnalyzer):
    def _is_sink(self, name):
        # print is a sink for the label flow, but requires no mandate (PATCH 1).
        return name in SINKS or name in PROGRAM_OUTPUT

    def _flow_body(self, body, incoming, pc_labels=None):
        if pc_labels is None:
            pc_labels = set()

        pc_labels = set(pc_labels)
        env = self._copy_env(incoming)
        for statement in body:
            if isinstance(statement, (Let, Assign)):
                # PATCH 2: the control context of a branch carries labels into the variable.
                env[statement.name] = self._labels(statement.value, env) | pc_labels
            elif isinstance(statement, If):
                child_pc = pc_labels | self._labels(statement.condition, env)
                left = self._flow_body(statement.then_branch, env, child_pc)
                right = self._flow_body(statement.else_branch, env, child_pc)
                # PATCH 4: join only on the branch exits (empty else == copy of the entry).
                env = self._join_env(left, right)
            elif isinstance(statement, While):
                # PATCH 6: returns (env, pc); code after the loop is not under the condition.
                env, _ = self._flow_loop(statement.body, statement.condition,
                                         env, pc_labels)
        return env

    def _flow_loop(self, body, condition, incoming, pc_labels=None):
        if pc_labels is None:
            pc_labels = set()

        pc_labels = set(pc_labels)
        env = self._copy_env(incoming)
        # PATCH 6: fold the condition labels into pc; the condition may have become sensitive.
        pc = pc_labels | self._labels(condition, env)
        for _ in range(self.MAX_FIXPOINT_ROUNDS):
            body_env = self._flow_body(body, env, pc)
            joined = self._join_env(incoming, env, body_env)
            pc_new = pc | self._labels(condition, joined)
            if joined == env and pc_new == pc:
                return env, pc

            env, pc = joined, pc_new
        raise RuntimeError("loop flow fixpoint did not converge")

    def _return_labels(self, body, incoming, pc_labels=None):
        if pc_labels is None:
            pc_labels = set()

        pc_labels = set(pc_labels)
        env = self._copy_env(incoming)
        returned = set()
        for statement in body:
            if isinstance(statement, (Let, Assign)):
                # PATCH 2: the condition context carries labels into the assigned variable.
                env[statement.name] = self._labels(statement.value, env) | pc_labels
            elif isinstance(statement, Return):
                # PATCH 3: the condition context carries labels into the returned value.
                returned |= (self._labels(statement.value, env) | pc_labels)
            elif isinstance(statement, If):
                child_pc = pc_labels | self._labels(statement.condition, env)
                returned |= self._return_labels(statement.then_branch, env, child_pc)
                returned |= self._return_labels(statement.else_branch, env, child_pc)
                # PATCH 4: join only on the branch exits.
                env = self._join_env(
                    self._flow_body(statement.then_branch, env, child_pc),
                    self._flow_body(statement.else_branch, env, child_pc))
            elif isinstance(statement, While):
                loop_env, loop_pc = self._flow_loop(
                    statement.body, statement.condition, env, pc_labels)
                returned |= self._return_labels(statement.body, loop_env, loop_pc)
                env = loop_env
        return returned

    def _compute_summaries(self):
        # PATCH 5: initialize the pc component first (all False), then the base summaries.
        # The order matters: super() calls our _body_leaks -> _expression_leaks, which
        # reads self.pc_summary (otherwise AttributeError). All-False is the correct base
        # context: no pc effect. After super() the {False, True} lattice reaches a fixpoint.
        self.pc_summary = {name: False for name in self.functions}
        super()._compute_summaries()
        for _ in range(self.MAX_FIXPOINT_ROUNDS):
            changed = False
            for name, function in self.functions.items():
                effect = self._body_leaks(function.body, {}, {"__PC__"})
                if effect != self.pc_summary[name]:
                    self.pc_summary[name] = effect
                    changed = True
            if not changed:
                return

        raise EthicalError("Ethical analysis did not reach a fixpoint.",
                           "YADRO-E2901")

    def _body_leaks(self, body, incoming, pc_labels):
        pc_labels = set(pc_labels)
        env = self._copy_env(incoming)
        for statement in body:
            expression = getattr(statement, "value", statement)
            if isinstance(statement, (Let, Assign)):
                if self._expression_leaks(statement.value, env, pc_labels):
                    return True

                env[statement.name] = self._labels(statement.value, env) | pc_labels
            elif isinstance(statement, Return):
                if self._expression_leaks(statement.value, env, pc_labels):
                    return True
            elif isinstance(statement, If):
                if self._expression_leaks(statement.condition, env, pc_labels):
                    return True

                child_pc = pc_labels | self._labels(statement.condition, env)
                if self._body_leaks(statement.then_branch, self._copy_env(env), child_pc):
                    return True

                if self._body_leaks(statement.else_branch, self._copy_env(env), child_pc):
                    return True
            elif isinstance(statement, While):
                loop_env, loop_pc = self._flow_loop(
                    statement.body, statement.condition, env, pc_labels)
                if self._body_leaks(statement.body, loop_env, loop_pc):
                    return True

                env = loop_env
            elif self._expression_leaks(expression, env, pc_labels):
                return True
        return False

    def _scan_body(self, body, incoming, pc_labels):
        pc_labels = set(pc_labels)
        env = self._copy_env(incoming)
        for statement in body:
            if isinstance(statement, (Let, Assign)):
                self._scan_expression(statement.value, env, pc_labels)
                env[statement.name] = self._labels(statement.value, env, audit=True) | pc_labels
            elif isinstance(statement, Return):
                self._scan_expression(statement.value, env, pc_labels)
            elif isinstance(statement, If):
                self._scan_expression(statement.condition, env, pc_labels)
                child_pc = pc_labels | self._labels(statement.condition, env)
                self._scan_body(statement.then_branch, env, child_pc)
                self._scan_body(statement.else_branch, env, child_pc)
                # PATCH 4: join only on the branch exits.
                env = self._join_env(
                    self._flow_body(statement.then_branch, env, child_pc),
                    self._flow_body(statement.else_branch, env, child_pc))
            elif isinstance(statement, While):
                self._scan_expression(statement.condition, env, pc_labels)
                # PATCH 6: scan the body with the pc fixpoint (condition may have become sensitive).
                loop_env, loop_pc = self._flow_loop(
                    statement.body, statement.condition, env, pc_labels)
                self._scan_body(statement.body, loop_env, loop_pc)
                env = loop_env
            else:
                self._scan_expression(statement, env, pc_labels)
        return env

    def _expression_leaks(self, expression, env, pc_labels):
        if expression is None:
            return False

        if isinstance(expression, Binary):
            return (self._expression_leaks(expression.left, env, pc_labels)
                    or self._expression_leaks(expression.right, env, pc_labels))
        if isinstance(expression, Call):
            if self._is_sink(expression.name):
                return bool(pc_labels) or any(self._labels(arg, env) for arg in expression.arguments)
            # PATCH 5: a helper call reaching a sink under a non-empty pc = implicit flow.
            if pc_labels and self.pc_summary.get(expression.name):
                return True

            leaks = self.leak_summary.get(expression.name, set())
            for index, argument in enumerate(expression.arguments):
                for label in self._labels(argument, env):
                    if (index, label) in leaks:
                        return True

            return any(self._expression_leaks(arg, env, pc_labels) for arg in expression.arguments)
        return False

    def _scan_expression(self, expression, env, pc_labels):
        if expression is None:
            return

        if isinstance(expression, Binary):
            self._scan_expression(expression.left, env, pc_labels)
            self._scan_expression(expression.right, env, pc_labels)
            return
        if not isinstance(expression, Call):
            return

        if self._is_sink(expression.name):
            if pc_labels:
                labels = ", ".join(sorted(pc_labels))
                self.audit_trail.append(AuditEntry("implicit-condition", labels, [],
                                                   expression.name, expression.string,
                                                   "IMPLICIT_FLOW"))
                raise EthicalError(
                    f"Implicit information flow (line {expression.string}): sink '{expression.name}' is controlled by sensitive data ({labels}).",
                    "YADRO-E2302")
            leaked = set().union(*(self._labels(arg, env) for arg in expression.arguments)) if expression.arguments else set()
            if leaked:
                labels = ", ".join(sorted(leaked))
                self.audit_trail.append(AuditEntry("direct", labels, [], expression.name,
                                                   expression.string, "BLOCKED"))
                raise EthicalError(
                    f"Data leak (line {expression.string}): {labels} data reaches sink '{expression.name}' without an allowed sanitizer.",
                    "YADRO-E2301")
        # PATCH 5: a helper call with a sink under a non-empty caller pc = implicit flow.
        if pc_labels and self.pc_summary.get(expression.name):
            labels = ", ".join(sorted(pc_labels))
            self.audit_trail.append(AuditEntry("implicit-condition", labels, [],
                                               expression.name, expression.string,
                                               "IMPLICIT_FLOW"))
            raise EthicalError(
                f"Implicit information flow (line {expression.string}): call '{expression.name}' is controlled by sensitive data ({labels}) and reaches a sink.",
                "YADRO-E2302")
        target_leaks = self.leak_summary.get(expression.name, set())
        for index, argument in enumerate(expression.arguments):
            for label in self._labels(argument, env):
                if (index, label) in target_leaks:
                    raise EthicalError(
                        f"Data leak (line {expression.string}): {label} data leaks through parameter {index + 1} of '{expression.name}'.",
                        "YADRO-E2303")
        for argument in expression.arguments:
            self._scan_expression(argument, env, pc_labels)
