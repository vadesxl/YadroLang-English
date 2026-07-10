# -*- coding: utf-8 -*-
"""Verified LLVM IR generator with typed storage and ABI v1 symbols."""
import hashlib
from llvmlite import ir, binding as llvm
from src.syntax import (Return, Let, Assign, If, While, NumberLit, StringLit,
                        BoolLit, Ident, Binary, Call)

INT, BOOL, BYTE, I32 = ir.IntType(64), ir.IntType(1), ir.IntType(8), ir.IntType(32)
PTR = BYTE.as_pointer()


class CodegenError(Exception): pass


def llvm_type(name):
    return {"i64": INT, "bool": BOOL, "string": PTR}[name]


def symbol(prefix, name):
    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()[:16]
    return f"yadro.{prefix}.{digest}"


class Codegen:
    def __init__(self):
        self.module = ir.Module(name="yadro")
        self.module.triple = llvm.get_default_triple()
        self.functions, self.externs, self.scope = {}, {}, {}
        self.builder = None; self._count = 0
        self.printf = ir.Function(self.module, ir.FunctionType(I32, [PTR], var_arg=True), name="printf")

    def generate(self, program):
        self._fmt_i64 = self._global("%lld\n"); self._fmt_str = self._global("%s\n")
        self._fmt_result = self._global("Result main(): %lld\n")
        for function in program.functions:
            result = llvm_type(function.inferred_return_type)
            params = [llvm_type(value) for value in function.inferred_param_types]
            self.functions[function.name] = ir.Function(self.module, ir.FunctionType(result, params),
                                                        name=symbol("fn", function.name))
        for function in program.functions: self._function(function)
        self._entry(program)
        text = str(self.module)
        try:
            module = llvm.parse_assembly(text); module.verify()
        except Exception as error:
            raise CodegenError(f"LLVM verification failed: {error}") from error
        return text

    def _entry(self, program):
        if "main" not in self.functions: return
        fn = ir.Function(self.module, ir.FunctionType(I32, []), name="main")
        builder = ir.IRBuilder(fn.append_basic_block("entry"))
        result = builder.call(self.functions["main"], [])
        if result.type == BOOL: result = builder.zext(result, INT)
        if result.type == INT: builder.call(self.printf, [self._ptr(builder, self._fmt_result), result])
        builder.ret(I32(0))

    def _function(self, ast):
        fn = self.functions[ast.name]; self.builder = ir.IRBuilder(fn.append_basic_block("entry")); self.scope = {}
        for argument, name, type_name in zip(fn.args, ast.parameters, ast.inferred_param_types):
            cell = self.builder.alloca(llvm_type(type_name), name=f"var.{name}")
            self.builder.store(argument, cell); self.scope[name] = (cell, type_name)
        self._body(ast.body)
        if not self.builder.block.is_terminated:
            default = {"i64": INT(0), "bool": BOOL(0), "string": ir.Constant(PTR, None)}[ast.inferred_return_type]
            self.builder.ret(default)

    def _body(self, body):
        for statement in body:
            if self.builder.block.is_terminated: break
            self._statement(statement)

    def _statement(self, node):
        if isinstance(node, Return): self.builder.ret(self._expr(node.value))
        elif isinstance(node, Let):
            value = self._expr(node.value); cell = self.builder.alloca(value.type, name=f"var.{node.name}")
            self.builder.store(value, cell); self.scope[node.name] = (cell, node.inferred_type)
        elif isinstance(node, Assign): self.builder.store(self._expr(node.value), self.scope[node.name][0])
        elif isinstance(node, If): self._if(node)
        elif isinstance(node, While): self._while(node)
        else: self._expr(node)

    def _if(self, node):
        condition = self._bool(self._expr(node.condition)); function = self.builder.function
        then = function.append_basic_block("if.then"); other = function.append_basic_block("if.else") if node.else_branch else None
        end = function.append_basic_block("if.end")
        self.builder.cbranch(condition, then, other or end)
        self.builder.position_at_end(then); self._body(node.then_branch)
        if not self.builder.block.is_terminated: self.builder.branch(end)
        if other:
            self.builder.position_at_end(other); self._body(node.else_branch)
            if not self.builder.block.is_terminated: self.builder.branch(end)
        self.builder.position_at_end(end)

    def _while(self, node):
        function = self.builder.function; cond = function.append_basic_block("while.cond")
        body = function.append_basic_block("while.body"); end = function.append_basic_block("while.end")
        self.builder.branch(cond); self.builder.position_at_end(cond)
        self.builder.cbranch(self._bool(self._expr(node.condition)), body, end)
        self.builder.position_at_end(body); self._body(node.body)
        if not self.builder.block.is_terminated: self.builder.branch(cond)
        self.builder.position_at_end(end)

    def _expr(self, node):
        if isinstance(node, NumberLit): return INT(node.value)
        if isinstance(node, BoolLit): return BOOL(1 if node.value else 0)
        if isinstance(node, StringLit): return self._ptr(self.builder, self._global(node.value))
        if isinstance(node, Ident): return self.builder.load(self.scope[node.name][0], name=f"load.{node.name}")
        if isinstance(node, Binary):
            left, right = self._expr(node.left), self._expr(node.right)
            operations = {"+":self.builder.add, "-":self.builder.sub, "*":self.builder.mul,
                          "/":self.builder.sdiv}
            if node.op in operations: return operations[node.op](left, right)
            return self.builder.icmp_signed(node.op, left, right)
        if isinstance(node, Call):
            if node.name == "print":
                value = self._expr(node.arguments[0])
                if value.type == PTR: self.builder.call(self.printf, [self._ptr(self.builder, self._fmt_str), value])
                else:
                    if value.type == BOOL: value = self.builder.zext(value, INT)
                    self.builder.call(self.printf, [self._ptr(self.builder, self._fmt_i64), value])
                return INT(0)
            args = [self._expr(arg) for arg in node.arguments]
            if node.name in self.functions: return self.builder.call(self.functions[node.name], args)
            signature = tuple(arg.type for arg in args)
            previous = self.externs.get(node.name)
            if previous and previous[0] != signature:
                raise CodegenError(f"extern ABI mismatch for '{node.name}'")
            if not previous:
                fn = ir.Function(self.module, ir.FunctionType(INT, list(signature)), name=symbol("abi.v1", node.name))
                self.externs[node.name] = (signature, fn)
            return self.builder.call(self.externs[node.name][1], args)
        raise CodegenError(f"unsupported node {type(node).__name__}")

    def _global(self, text):
        data = bytearray(text.encode("utf-8") + b"\0"); array = ir.ArrayType(BYTE, len(data))
        value = ir.GlobalVariable(self.module, array, name=f".str.{self._count}"); self._count += 1
        value.linkage = "internal"; value.global_constant = True; value.initializer = ir.Constant(array, data)
        return value

    @staticmethod
    def _ptr(builder, value): return builder.gep(value, [I32(0), I32(0)], inbounds=True)
    @staticmethod
    def _bool(value): return value if value.type == BOOL else ir.IRBuilder  # replaced below


Codegen._bool = lambda self, value: value if value.type == BOOL else self.builder.icmp_signed("!=", value, INT(0))
