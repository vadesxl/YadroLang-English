# -*- coding: utf-8 -*-
"""Minimal strict type system for YadroLang.

The source-level types are i64, bool, and string. The stable native ABI lowers
bool to i64. String values are currently restricted to direct print arguments.
"""
from src.syntax import (Function, Return, Let, Assign, If, While, NumberLit,
                        StringLit, Ident, Binary, Call)

I64, BOOL, STRING = "i64", "bool", "string"


class TypeCheckError(Exception):
    def __init__(self, code, message, line=0):
        self.code = code
        self.line = line
        super().__init__(f"[{code}] line {line}: {message}")


class TypeChecker:
    def __init__(self, program, system_names):
        self.program = program
        self.functions = {f.name: f for f in program.functions}
        self.system_names = set(system_names)
        self.returns = {name: I64 for name in self.functions}
        self.parameter_types = {name: [I64] * len(f.parameters) for name, f in self.functions.items()}

    def check(self):
        self._check_symbols()
        for _ in range(32):
            changed = False
            for function in self.program.functions:
                result = self._infer_function(function, validate=False)
                if result and result != self.returns[function.name]:
                    self.returns[function.name] = result; changed = True
            if not changed: break
        else:
            raise TypeCheckError("YADRO-T2901", "return-type inference did not converge")
        for function in self.program.functions:
            self._infer_function(function, validate=True)
        return self

    def _check_symbols(self):
        for function in self.program.functions:
            if function.name in {"printf", "yadro_main"} or function.name.startswith("ext."):
                raise TypeCheckError("YADRO-T2101", f"reserved runtime symbol '{function.name}'", function.string)

    def _infer_function(self, function, validate):
        env = {name: I64 for name in function.parameters}
        return_types, terminates = self._block(function.body, env, validate)
        if validate and not terminates:
            raise TypeCheckError("YADRO-T2204", f"function '{function.name}' does not return on every path", function.string)
        if not return_types: return I64
        result = next(iter(return_types))
        if len(return_types) != 1:
            raise TypeCheckError("YADRO-T2203", f"mixed return types in '{function.name}': {sorted(return_types)}", function.string)
        if result == STRING:
            raise TypeCheckError("YADRO-T2205", "string return ABI is not supported yet", function.string)
        return result

    def _block(self, body, env, validate):
        returns, terminated = set(), False
        for statement in body:
            if terminated:
                if validate: raise TypeCheckError("YADRO-T2202", "unreachable statement", statement.string)
                break
            if isinstance(statement, Let):
                value_type = self._expr(statement.value, env)
                if value_type == STRING:
                    raise TypeCheckError("YADRO-T2305", "string variables are not supported; print the literal directly", statement.string)
                env[statement.name] = value_type
            elif isinstance(statement, Assign):
                if statement.name not in env:
                    raise TypeCheckError("YADRO-T2102", f"unknown variable '{statement.name}'", statement.string)
                value_type = self._expr(statement.value, env)
                if value_type != env[statement.name]:
                    raise TypeCheckError("YADRO-T2302", f"cannot assign {value_type} to {env[statement.name]} variable '{statement.name}'", statement.string)
            elif isinstance(statement, Return):
                returns.add(self._expr(statement.value, env)); terminated = True
            elif isinstance(statement, If):
                condition = self._expr(statement.condition, env)
                if condition not in {BOOL, I64}:
                    raise TypeCheckError("YADRO-T2303", f"if condition must be bool or i64 truthy, got {condition}", statement.string)
                left_env, right_env = dict(env), dict(env)
                left_returns, left_term = self._block(statement.then_branch, left_env, validate)
                right_returns, right_term = self._block(statement.else_branch, right_env, validate)
                returns |= left_returns | right_returns
                for name in set(left_env) | set(right_env):
                    lt, rt = left_env.get(name), right_env.get(name)
                    if lt and rt and lt != rt:
                        raise TypeCheckError("YADRO-T2304", f"branch type conflict for '{name}': {lt} vs {rt}", statement.string)
                    if lt == rt and lt: env[name] = lt
                terminated = bool(statement.else_branch) and left_term and right_term
            elif isinstance(statement, While):
                condition = self._expr(statement.condition, env)
                if condition not in {BOOL, I64}:
                    raise TypeCheckError("YADRO-T2303", f"while condition must be bool or i64 truthy, got {condition}", statement.string)
                loop_returns, _ = self._block(statement.body, dict(env), validate)
                returns |= loop_returns
            else:
                self._expr(statement, env)
        return returns, terminated

    def _expr(self, node, env):
        if isinstance(node, NumberLit): return I64
        if isinstance(node, StringLit): return STRING
        if isinstance(node, Ident):
            if node.name not in env: raise TypeCheckError("YADRO-T2102", f"unknown variable '{node.name}'", node.string)
            return env[node.name]
        if isinstance(node, Binary):
            left, right = self._expr(node.left, env), self._expr(node.right, env)
            if left != I64 or right != I64:
                raise TypeCheckError("YADRO-T2301", f"operator '{node.op}' requires i64 operands, got {left} and {right}", node.string)
            return BOOL if node.op in {">", "<", "=="} else I64
        if isinstance(node, Call):
            args = [self._expr(arg, env) for arg in node.arguments]
            if node.name == "print":
                if len(args) != 1: raise TypeCheckError("YADRO-T2401", "print expects one argument", node.string)
                return I64
            if node.name in self.functions:
                expected = self.parameter_types[node.name]
                for index, (actual, wanted) in enumerate(zip(args, expected), 1):
                    if actual != wanted: raise TypeCheckError("YADRO-T2402", f"argument {index} of '{node.name}' expects {wanted}, got {actual}", node.string)
                return self.returns[node.name]
            for actual in args:
                if actual != I64: raise TypeCheckError("YADRO-T2403", f"system API '{node.name}' accepts i64, got {actual}", node.string)
            return I64
        raise TypeCheckError("YADRO-T2999", f"cannot infer type of {type(node).__name__}", getattr(node, "string", 0))
