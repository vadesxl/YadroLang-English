# -*- coding: utf-8 -*-
"""Minimal strict type inference for YadroLang: i64, bool and string."""
from src.syntax import (NumberLit, StringLit, BoolLit, Ident, Binary, Call,
                        Let, Assign, Return, If, While)

I64, BOOL, STRING, UNKNOWN = "i64", "bool", "string", "unknown"


class TypeCheckError(Exception):
    def __init__(self, message, line=0, code="YADRO-T2000"):
        self.code = code
        super().__init__(f"[{code}] {message} (line {line})")


class TypeChecker:
    MAX_ROUNDS = 64

    def __init__(self, system_api):
        self.system_api = set(system_api)
        self.signatures = {}

    def check(self, program):
        self.signatures = {f.name: {"params": [UNKNOWN] * len(f.parameters), "return": UNKNOWN}
                           for f in program.functions}
        for _ in range(self.MAX_ROUNDS):
            before = repr(self.signatures)
            for function in program.functions:
                self._function(function, infer=True)
            if repr(self.signatures) == before:
                break
        else:
            raise TypeCheckError("type inference did not converge", 0, "YADRO-T2099")
        for signature in self.signatures.values():
            signature["params"] = [I64 if value == UNKNOWN else value for value in signature["params"]]
            if signature["return"] == UNKNOWN:
                signature["return"] = I64
        for function in program.functions:
            self._function(function, infer=False)
            function.inferred_param_types = list(self.signatures[function.name]["params"])
            function.inferred_return_type = self.signatures[function.name]["return"]
        return self.signatures

    def _merge(self, old, new, line, context):
        if new == UNKNOWN: return old
        if old == UNKNOWN: return new
        if old != new:
            raise TypeCheckError(f"{context}: expected {old}, got {new}", line, "YADRO-T2002")
        return old

    def _function(self, function, infer):
        signature = self.signatures[function.name]
        env = dict(zip(function.parameters, signature["params"]))
        returns = []
        self._body(function.body, env, returns, infer)
        for value, line in returns:
            signature["return"] = self._merge(signature["return"], value, line,
                                                f"return type of '{function.name}'")
        if signature["return"] == UNKNOWN and not infer:
            signature["return"] = I64

    def _body(self, body, env, returns, infer):
        terminated = False
        for statement in body:
            if terminated:
                raise TypeCheckError("unreachable statement after return", statement.string,
                                     "YADRO-T2006")
            if isinstance(statement, Let):
                value = self._expr(statement.value, env, infer)
                if statement.name in env:
                    raise TypeCheckError(f"variable '{statement.name}' already declared", statement.string,
                                         "YADRO-T2007")
                env[statement.name] = value
                statement.inferred_type = value
            elif isinstance(statement, Assign):
                if statement.name not in env:
                    raise TypeCheckError(f"unknown variable '{statement.name}'", statement.string,
                                         "YADRO-T2008")
                value = self._expr(statement.value, env, infer)
                env[statement.name] = self._merge(env[statement.name], value, statement.string,
                                                  f"assignment to '{statement.name}'")
            elif isinstance(statement, Return):
                returns.append((self._expr(statement.value, env, infer), statement.string))
                terminated = True
            elif isinstance(statement, If):
                condition = self._expr(statement.condition, env, infer)
                if condition not in (BOOL, I64, UNKNOWN):
                    raise TypeCheckError("if condition must be bool or legacy i64 truthiness",
                                         statement.string, "YADRO-T2003")
                left, right = dict(env), dict(env)
                left_returns, right_returns = [], []
                left_term = self._body(statement.then_branch, left, left_returns, infer)
                right_term = self._body(statement.else_branch, right, right_returns, infer) if statement.else_branch else False
                returns.extend(left_returns); returns.extend(right_returns)
                for name in set(left) | set(right):
                    if name in env:
                        env[name] = self._merge(left.get(name, env[name]), right.get(name, env[name]),
                                                statement.string, f"branch value '{name}'")
                terminated = bool(statement.else_branch) and left_term and right_term
            elif isinstance(statement, While):
                condition = self._expr(statement.condition, env, infer)
                if condition not in (BOOL, I64, UNKNOWN):
                    raise TypeCheckError("while condition must be bool or legacy i64 truthiness",
                                         statement.string, "YADRO-T2003")
                loop_env, loop_returns = dict(env), []
                self._body(statement.body, loop_env, loop_returns, infer)
                returns.extend(loop_returns)
                for name in env:
                    env[name] = self._merge(env[name], loop_env.get(name, env[name]),
                                            statement.string, f"loop value '{name}'")
            else:
                self._expr(statement, env, infer)
        return terminated

    def _expr(self, node, env, infer):
        if isinstance(node, NumberLit): result = I64
        elif isinstance(node, StringLit): result = STRING
        elif isinstance(node, BoolLit): result = BOOL
        elif isinstance(node, Ident):
            if node.name not in env:
                raise TypeCheckError(f"unknown variable '{node.name}'", node.string, "YADRO-T2008")
            result = env[node.name]
        elif isinstance(node, Binary):
            left, right = self._expr(node.left, env, infer), self._expr(node.right, env, infer)
            if node.op in ("+", "-", "*", "/"):
                if left not in (I64, UNKNOWN) or right not in (I64, UNKNOWN):
                    raise TypeCheckError(f"operator '{node.op}' requires i64 operands", node.string,
                                         "YADRO-T2001")
                result = I64
            elif node.op in (">", "<"):
                if left not in (I64, UNKNOWN) or right not in (I64, UNKNOWN):
                    raise TypeCheckError(f"operator '{node.op}' requires i64 operands", node.string,
                                         "YADRO-T2001")
                result = BOOL
            elif node.op == "==":
                self._merge(left, right, node.string, "equality operands")
                if left == STRING or right == STRING:
                    raise TypeCheckError("string equality is not implemented", node.string, "YADRO-T2005")
                result = BOOL
            else: raise TypeCheckError(f"unknown operator '{node.op}'", node.string)
        elif isinstance(node, Call):
            args = [self._expr(arg, env, infer) for arg in node.arguments]
            if node.name == "print":
                result = I64
            elif node.name in self.signatures:
                signature = self.signatures[node.name]
                for index, value in enumerate(args):
                    signature["params"][index] = self._merge(signature["params"][index], value,
                                                              node.string, f"argument {index + 1} of '{node.name}'")
                result = signature["return"]
            elif node.name in self.system_api:
                if any(value not in (I64, UNKNOWN) for value in args):
                    raise TypeCheckError(f"system API '{node.name}' accepts i64 values only",
                                         node.string, "YADRO-T2004")
                result = I64
            else:
                raise TypeCheckError(f"unknown function '{node.name}'", node.string, "YADRO-T2009")
        else:
            raise TypeCheckError(f"unsupported expression {type(node).__name__}", getattr(node, "string", 0))
        node.inferred_type = result
        return result
