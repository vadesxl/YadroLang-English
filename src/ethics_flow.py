# -*- coding: utf-8 -*-
"""Sound control-flow joins for Ethical Analyzer v2.1."""
from src.ethics_v21 import EthicalAnalyzer
from src.syntax import Let, Assign, Return, If, While


class SoundEthicalAnalyzer(EthicalAnalyzer):
    def _flow_body(self, body, incoming):
        env = self._copy_env(incoming)
        for statement in body:
            if isinstance(statement, (Let, Assign)):
                env[statement.name] = self._labels(statement.value, env)
            elif isinstance(statement, If):
                left = self._flow_body(statement.then_branch, env)
                right = self._flow_body(statement.else_branch, env)
                env = self._join_env(env, left, right)
            elif isinstance(statement, While):
                env = self._flow_loop(statement.body, env)
        return env

    def _flow_loop(self, body, incoming):
        env = self._copy_env(incoming)
        for _ in range(self.MAX_FIXPOINT_ROUNDS):
            body_env = self._flow_body(body, env)
            joined = self._join_env(incoming, env, body_env)
            if joined == env:
                return env
            env = joined
        raise RuntimeError("loop flow fixpoint did not converge")

    def _return_labels(self, body, incoming):
        env = self._copy_env(incoming)
        returned = set()
        for statement in body:
            if isinstance(statement, (Let, Assign)):
                env[statement.name] = self._labels(statement.value, env)
            elif isinstance(statement, Return):
                returned |= self._labels(statement.value, env)
            elif isinstance(statement, If):
                returned |= self._return_labels(statement.then_branch, env)
                returned |= self._return_labels(statement.else_branch, env)
                env = self._join_env(env,
                                     self._flow_body(statement.then_branch, env),
                                     self._flow_body(statement.else_branch, env))
            elif isinstance(statement, While):
                loop_env = self._flow_loop(statement.body, env)
                returned |= self._return_labels(statement.body, loop_env)
                env = loop_env
        return returned

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
                if self._body_leaks(statement.then_branch, env, child_pc):
                    return True
                if self._body_leaks(statement.else_branch, env, child_pc):
                    return True
                env = self._join_env(env,
                                     self._flow_body(statement.then_branch, env),
                                     self._flow_body(statement.else_branch, env))
            elif isinstance(statement, While):
                child_pc = set(pc_labels) | self._labels(statement.condition, env)
                loop_env = self._flow_loop(statement.body, env)
                if self._body_leaks(statement.body, loop_env, child_pc):
                    return True
                env = loop_env
            elif self._expression_leaks(expression, env, pc_labels):
                return True
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
                child_pc = set(pc_labels) | self._labels(statement.condition, env)
                self._scan_body(statement.then_branch, env, child_pc)
                self._scan_body(statement.else_branch, env, child_pc)
                env = self._join_env(env,
                                     self._flow_body(statement.then_branch, env),
                                     self._flow_body(statement.else_branch, env))
            elif isinstance(statement, While):
                self._scan_expression(statement.condition, env, pc_labels)
                child_pc = set(pc_labels) | self._labels(statement.condition, env)
                loop_env = self._flow_loop(statement.body, env)
                self._scan_body(statement.body, loop_env, child_pc)
                env = loop_env
            else:
                self._scan_expression(statement, env, pc_labels)
        return env
