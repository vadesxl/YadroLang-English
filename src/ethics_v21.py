# -*- coding: utf-8 -*-
"""YadroLang Ethical Analyzer v2.1.

Finite-lattice, label-preserving interprocedural information-flow analysis.
There is no runtime monitor: policy is enforced before LLVM code generation.
"""
from dataclasses import dataclass, field
from src.syntax import (Program, Function, Return, Let, Assign, If, While,
                        NumberLit, StringLit, Ident, Binary, Call)


class TaintLabel:
    PII = "PII"
    FINANCIAL = "Financial"
    HEALTH = "Health"
    CREDENTIALS = "Credentials"
    LOCATION = "Location"


ALL_LABELS = frozenset({TaintLabel.PII, TaintLabel.FINANCIAL,
                        TaintLabel.HEALTH, TaintLabel.CREDENTIALS,
                        TaintLabel.LOCATION})

SINKS = {
    "net.send": "NetworkAccess", "net.request": "NetworkAccess",
    "net.post": "NetworkAccess", "http.redirect": "NetworkAccess",
    "ws.send": "NetworkAccess", "file.write": "DiskWrite",
    "file.delete": "DiskWrite", "file.append": "DiskWrite",
    "db.write": "DatabaseWrite", "db.insert": "DatabaseWrite",
    "db.update": "DatabaseWrite", "db.delete": "DatabaseWrite",
    "db.query": "DatabaseRead", "log.info": "LogAccess",
    "log.debug": "LogAccess", "log.error": "LogAccess",
    "console.log": "LogAccess", "api.call": "NetworkAccess",
    "email.send": "NetworkAccess", "sms.send": "NetworkAccess",
}

SOURCES = {
    "user.data": TaintLabel.PII, "user.name": TaintLabel.PII,
    "user.email": TaintLabel.PII, "user.phone": TaintLabel.PII,
    "user.address": TaintLabel.PII, "user.id": TaintLabel.PII,
    "personal.read": TaintLabel.PII, "request.body": TaintLabel.PII,
    "request.params": TaintLabel.PII, "cookie.get": TaintLabel.PII,
    "session.get": TaintLabel.PII, "payment.card": TaintLabel.FINANCIAL,
    "account.balance": TaintLabel.FINANCIAL,
    "transaction.get": TaintLabel.FINANCIAL,
    "bank.account": TaintLabel.FINANCIAL,
    "patient.record": TaintLabel.HEALTH,
    "medical.history": TaintLabel.HEALTH,
    "diagnosis.get": TaintLabel.HEALTH,
    "env.secret": TaintLabel.CREDENTIALS,
    "vault.read": TaintLabel.CREDENTIALS,
    "key.private": TaintLabel.CREDENTIALS,
    "geo.location": TaintLabel.LOCATION,
    "gps.coordinates": TaintLabel.LOCATION,
    "file.read": TaintLabel.PII, "net.accept": TaintLabel.PII,
    "db.read": TaintLabel.PII,
}

SANITIZERS = {"anonymize", "check_consent", "hash", "encrypt", "mask",
              "redact", "tokenize", "pseudonymize", "aggregate"}

COMPLIANCE = {
    TaintLabel.PII: {"anonymize", "hash", "pseudonymize", "redact", "mask", "check_consent"},
    TaintLabel.FINANCIAL: {"encrypt", "tokenize", "mask", "hash"},
    TaintLabel.HEALTH: {"anonymize", "redact", "pseudonymize", "encrypt"},
    TaintLabel.CREDENTIALS: {"encrypt", "hash", "tokenize"},
    TaintLabel.LOCATION: {"anonymize", "aggregate", "redact"},
}


class EthicalError(Exception):
    def __init__(self, message, code="YADRO-E2999"):
        self.code = code
        super().__init__(f"[{code}] {message}")


@dataclass
class AuditEntry:
    source: str
    label: str
    path: list
    sink: str
    line: int
    status: str
    detail: str = ""

    def __repr__(self):
        path = " -> ".join(self.path)
        return f"[{self.status}] {self.label}: {self.source} -> {path} -> {self.sink} (line {self.line})"


@dataclass
class ReturnSummary:
    fixed: set = field(default_factory=set)
    flows: dict = field(default_factory=dict)  # (parameter index, input label) -> output labels


class EthicalAnalyzer:
    MAX_FIXPOINT_ROUNDS = 128

    def __init__(self):
        self.functions = {}
        self.return_summary = {}
        self.leak_summary = {}
        self.audit_trail = []

    def check(self, program: Program):
        self.functions = {f.name: f for f in program.functions}
        self.audit_trail = []
        self._reject_reserved_definitions(program)
        self._compute_summaries()
        for function in program.functions:
            self._check_mandates(function)
            self._scan_body(function.body, {}, set())
        return self.audit_trail

    def _reject_reserved_definitions(self, program):
        reserved = set(SOURCES) | set(SINKS) | set(SANITIZERS) | {"print"}
        for function in program.functions:
            if function.name in reserved:
                raise EthicalError(
                    f"Reserved policy symbol '{function.name}' cannot be redefined (line {function.string}).",
                    "YADRO-E2101")

    def _compute_summaries(self):
        self.return_summary = {name: ReturnSummary() for name in self.functions}
        self.leak_summary = {name: set() for name in self.functions}
        for _ in range(self.MAX_FIXPOINT_ROUNDS):
            changed = False
            for name, function in self.functions.items():
                summary = self._summarize_returns(function)
                leaks = self._summarize_leaks(function)
                if summary != self.return_summary[name]:
                    self.return_summary[name] = summary
                    changed = True
                if leaks != self.leak_summary[name]:
                    self.leak_summary[name] = leaks
                    changed = True
            if not changed:
                return
        raise EthicalError("Ethical analysis did not reach a fixpoint.", "YADRO-E2901")

    def _summarize_returns(self, function):
        fixed = self._return_labels(function.body, {})
        flows = {}
        for index, parameter in enumerate(function.parameters):
            for label in ALL_LABELS:
                output = self._return_labels(function.body, {parameter: {label}})
                delta = output - fixed
                if delta:
                    flows[(index, label)] = delta
        return ReturnSummary(fixed, flows)

    def _summarize_leaks(self, function):
        leaking = set()
        for index, parameter in enumerate(function.parameters):
            for label in ALL_LABELS:
                if self._body_leaks(function.body, {parameter: {label}}, set()):
                    leaking.add((index, label))
        return leaking

    def _return_labels(self, body, incoming):
        env = {key: set(value) for key, value in incoming.items()}
        returned = set()
        for statement in body:
            if isinstance(statement, (Let, Assign)):
                env[statement.name] = self._labels(statement.value, env)
            elif isinstance(statement, Return):
                returned |= self._labels(statement.value, env)
            elif isinstance(statement, If):
                left_env, right_env = self._copy_env(env), self._copy_env(env)
                returned |= self._return_labels(statement.then_branch, left_env)
                returned |= self._return_labels(statement.else_branch, right_env)
                env = self._join_env(env, left_env, right_env)
            elif isinstance(statement, While):
                env, loop_returns = self._loop_fixpoint(statement.body, env)
                returned |= loop_returns
        return returned

    def _loop_fixpoint(self, body, incoming):
        env = self._copy_env(incoming)
        returned = set()
        for _ in range(self.MAX_FIXPOINT_ROUNDS):
            body_env = self._copy_env(env)
            returned |= self._return_labels(body, body_env)
            joined = self._join_env(incoming, env, body_env)
            if joined == env:
                return env, returned
            env = joined
        raise EthicalError("Loop analysis did not reach a fixpoint.", "YADRO-E2902")

    def _labels(self, expression, env, audit=False):
        if expression is None or isinstance(expression, (NumberLit, StringLit)):
            return set()
        if isinstance(expression, Ident):
            return set(env.get(expression.name, set()))
        if isinstance(expression, Binary):
            return self._labels(expression.left, env, audit) | self._labels(expression.right, env, audit)
        if isinstance(expression, Call):
            argument_labels = [self._labels(arg, env, audit) for arg in expression.arguments]
            if expression.name in SANITIZERS and expression.name not in self.functions:
                labels = set().union(*argument_labels) if argument_labels else set()
                removed = {label for label in labels if expression.name in COMPLIANCE.get(label, set())}
                remaining = labels - removed
                if audit:
                    for label in sorted(removed):
                        self.audit_trail.append(AuditEntry(expression.name, label, [], "declassified",
                                                           expression.string, "SANITIZED",
                                                           "Label-specific declassification"))
                return remaining
            if expression.name in SOURCES and expression.name not in self.functions:
                return {SOURCES[expression.name]}
            target = self.return_summary.get(expression.name)
            if target:
                result = set(target.fixed)
                for index, labels in enumerate(argument_labels):
                    for label in labels:
                        result |= target.flows.get((index, label), set())
                return result
            return set().union(*argument_labels) if argument_labels else set()
        return set()

    def _body_leaks(self, body, incoming, pc_labels):
        env = self._copy_env(incoming)
        for statement in body:
            expression = getattr(statement, "value", statement)
            if isinstance(statement, (Let, Assign)):
                if self._expression_leaks(statement.value, env, pc_labels):
                    return True
                env[statement.name] = self._labels(statement.value, env)
            elif isinstance(statement, Return):
                if self._expression_leaks(statement.value, env, pc_labels):
                    return True
            elif isinstance(statement, If):
                if self._expression_leaks(statement.condition, env, pc_labels):
                    return True
                child_pc = set(pc_labels) | self._labels(statement.condition, env)
                if self._body_leaks(statement.then_branch, self._copy_env(env), child_pc):
                    return True
                if self._body_leaks(statement.else_branch, self._copy_env(env), child_pc):
                    return True
            elif isinstance(statement, While):
                child_pc = set(pc_labels) | self._labels(statement.condition, env)
                if self._body_leaks(statement.body, self._copy_env(env), child_pc):
                    return True
            elif self._expression_leaks(expression, env, pc_labels):
                return True
        return False

    def _expression_leaks(self, expression, env, pc_labels):
        if expression is None:
            return False
        if isinstance(expression, Binary):
            return self._expression_leaks(expression.left, env, pc_labels) or self._expression_leaks(expression.right, env, pc_labels)
        if isinstance(expression, Call):
            if expression.name in SINKS:
                return bool(pc_labels) or any(self._labels(arg, env) for arg in expression.arguments)
            target_leaks = self.leak_summary.get(expression.name, set())
            for index, argument in enumerate(expression.arguments):
                for label in self._labels(argument, env):
                    if (index, label) in target_leaks:
                        return True
            return any(self._expression_leaks(arg, env, pc_labels) for arg in expression.arguments)
        return False

    def _scan_body(self, body, incoming, pc_labels):
        env = self._copy_env(incoming)
        for statement in body:
            if isinstance(statement, (Let, Assign)):
                self._scan_expression(statement.value, env, pc_labels)
                env[statement.name] = self._labels(statement.value, env, audit=True)
            elif isinstance(statement, Return):
                self._scan_expression(statement.value, env, pc_labels)
            elif isinstance(statement, If):
                self._scan_expression(statement.condition, env, pc_labels)
                condition_labels = self._labels(statement.condition, env)
                child_pc = set(pc_labels) | condition_labels
                left, right = self._copy_env(env), self._copy_env(env)
                self._scan_body(statement.then_branch, left, child_pc)
                self._scan_body(statement.else_branch, right, child_pc)
                env = self._join_env(env, left, right)
            elif isinstance(statement, While):
                self._scan_expression(statement.condition, env, pc_labels)
                child_pc = set(pc_labels) | self._labels(statement.condition, env)
                self._scan_body(statement.body, self._copy_env(env), child_pc)
            else:
                self._scan_expression(statement, env, pc_labels)

    def _scan_expression(self, expression, env, pc_labels):
        if expression is None:
            return
        if isinstance(expression, Binary):
            self._scan_expression(expression.left, env, pc_labels)
            self._scan_expression(expression.right, env, pc_labels)
            return
        if not isinstance(expression, Call):
            return
        if expression.name in SINKS:
            if pc_labels:
                labels = ", ".join(sorted(pc_labels))
                self.audit_trail.append(AuditEntry("implicit-condition", labels, [], expression.name,
                                                   expression.string, "IMPLICIT_FLOW"))
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
        target_leaks = self.leak_summary.get(expression.name, set())
        for index, argument in enumerate(expression.arguments):
            for label in self._labels(argument, env):
                if (index, label) in target_leaks:
                    raise EthicalError(
                        f"Data leak (line {expression.string}): {label} data leaks through parameter {index + 1} of '{expression.name}'.",
                        "YADRO-E2303")
        for argument in expression.arguments:
            self._scan_expression(argument, env, pc_labels)

    def _check_mandates(self, function: Function):
        for call in self._all_calls(function.body):
            needed = SINKS.get(call.name)
            if needed and needed not in function.mandates:
                raise EthicalError(
                    f"Function '{function.name}' (line {call.string}) calls '{call.name}' requiring mandate [{needed}].",
                    "YADRO-E2201")
            target = self.functions.get(call.name)
            if target:
                for mandate in target.mandates:
                    if mandate not in function.mandates:
                        raise EthicalError(
                            f"Function '{function.name}' (line {call.string}) calls '{target.name}' requiring [{mandate}], but does not declare it.",
                            "YADRO-E2202")

    def _all_calls(self, body):
        calls = []
        def expression(node):
            if isinstance(node, Call):
                calls.append(node)
                for arg in node.arguments:
                    expression(arg)
            elif isinstance(node, Binary):
                expression(node.left); expression(node.right)
        def statement(node):
            if isinstance(node, (Let, Assign, Return)):
                expression(node.value)
            elif isinstance(node, If):
                expression(node.condition)
                for item in node.then_branch + node.else_branch:
                    statement(item)
            elif isinstance(node, While):
                expression(node.condition)
                for item in node.body:
                    statement(item)
            else:
                expression(node)
        for item in body:
            statement(item)
        return calls

    @staticmethod
    def _copy_env(env):
        return {key: set(value) for key, value in env.items()}

    @staticmethod
    def _join_env(*environments):
        result = {}
        for env in environments:
            for key, labels in env.items():
                result.setdefault(key, set()).update(labels)
        return result

    def generate_audit_report(self):
        lines = ["=" * 60, "YADROLANG ETHICAL ANALYZER v2.1 - AUDIT REPORT", "=" * 60]
        lines.extend(str(entry) for entry in self.audit_trail)
        lines.append(f"Findings: {len(self.audit_trail)}")
        return "\n".join(lines)
