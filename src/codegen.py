# -*- coding: utf-8 -*-
"""Generator LLVM IR for_ YadroLang (through llvmlite).

Support: functions, if/while, recursion, built_in 'print' (printf),
autogeneration native point entry main for_ running as_ ELF-binary.
"""
from llvmlite import ir, binding as llvm
from src.syntax import (Program, Function, Return, Let, Assign,
                           If, While, NumberLit, StringLit, Ident, Binary, Call)

INT = ir.IntType(64)
BOOL = ir.IntType(1)
BYTE = ir.IntType(8)
PTR = BYTE.as_pointer()
I32 = ir.IntType(32)


class CodegenError(Exception):
    ...


class Codegen:
    def __init__(self):
        self.module = ir.Module(name="kernel")
        self.module.triple = llvm.get_default_triple()
        self.functions = {}
        self.builder = None
        self.scope = {}
        self._count = 0
        printf_ty = ir.FunctionType(I32, [PTR], var_arg=True)
        self.printf = ir.Function(self.module, printf_ty, name="printf")
        self.outer = {}   # system API (net.*, file.*, user.* i t.p.)

    def _outer(self, name, arg_count):
        """Declares (or_ returns) outer system function.

        System API (sources/sinks/sanitizers) are_implemented outside language,
        as_ libc. Codegen declares their as_ extern s signature i64(i64...).
        Ethics their usage already checked analyzer to codegen.
        """
        key = (name, arg_count)
        if key not in self.outer:
            type = ir.FunctionType(INT, [INT] * arg_count)
            safe = "ext." + name.replace(".", "_")
            self.outer[key] = ir.Function(self.module, type, name=safe)
        return self.outer[key]

    def _global_string(self, text):
        data = bytearray(text.encode("utf-8") + b"\x00")
        type = ir.ArrayType(BYTE, len(data))
        g = ir.GlobalVariable(self.module, type, name=f".str.{self._count}")
        self._count += 1
        g.linkage = "internal"
        g.global_constant = True
        g.initializer = ir.Constant(type, data)
        return g

    def _ptr(self, b, g):
        zero = ir.Constant(I32, 0)
        return b.gep(g, [zero, zero], inbounds=True)

    def generate(self, prog: Program) -> str:
        self._fmt_number = self._global_string("%lld\n")
        self._fmt_result = self._global_string("Result main(): %lld\n")
        self._fmt_string = self._global_string("%s\n")
        for f in prog.functions:
            type = ir.FunctionType(INT, [INT] * len(f.parameters))
            symbol = "yadro_main" if f.name == "main" else f.name
            self.functions[f.name] = ir.Function(self.module, type, name=symbol)
        for f in prog.functions:
            self._function(f)
        if "main" in self.functions:
            self._main_cli()
        return str(self.module)

    def _main_cli(self):
        fn = ir.Function(self.module, ir.FunctionType(I32, []), name="main")
        b = ir.IRBuilder(fn.append_basic_block("entry"))
        result = b.call(self.functions["main"], [])
        b.call(self.printf, [self._ptr(b, self._fmt_result), result])
        b.ret(ir.Constant(I32, 0))

    def _function(self, f: Function):
        fn = self.functions[f.name]
        block = fn.append_basic_block("entry")
        self.builder = ir.IRBuilder(block)
        self.scope = {}
        for arg, name in zip(fn.args, f.parameters):
            arg.name = name
            cell = self.builder.alloca(INT, name=name)
            self.builder.store(arg, cell)
            self.scope[name] = cell
        for stmt in f.body:
            self._statement(stmt)
        if not self.builder.block.is_terminated:
            self.builder.ret(INT(0))

    def _statement(self, u):
        if isinstance(u, Return):
            self.builder.ret(self._expression(u.value))
        elif isinstance(u, Let):
            cell = self.builder.alloca(INT, name=u.name)
            self.builder.store(self._expression(u.value), cell)
            self.scope[u.name] = cell
        elif isinstance(u, Assign):
            if u.name not in self.scope:
                raise CodegenError(f"Variable '{u.name}' not_ declared (string {u.string})")
            self.builder.store(self._expression(u.value), self.scope[u.name])
        elif isinstance(u, If):
            self._if_branch(u)
        elif isinstance(u, While):
            self._while_loop(u)
        else:
            self._expression(u)

    def _if_branch(self, u: If):
        cond = self._to_bool(self._expression(u.condition))
        has_else = bool(u.else_branch)
        bb_then_branch = self.builder.append_basic_block("then_branch")
        bb_else_branch = self.builder.append_basic_block("else_branch") if has_else else None
        bb_end = self.builder.append_basic_block("end_if")
        self.builder.cbranch(cond, bb_then_branch, bb_else_branch or bb_end)
        self.builder.position_at_end(bb_then_branch)
        for s in u.then_branch:
            self._statement(s)
        if not self.builder.block.is_terminated:
            self.builder.branch(bb_end)
        if has_else:
            self.builder.position_at_end(bb_else_branch)
            for s in u.else_branch:
                self._statement(s)
            if not self.builder.block.is_terminated:
                self.builder.branch(bb_end)
        self.builder.position_at_end(bb_end)

    def _while_loop(self, u: While):
        bb_cond = self.builder.append_basic_block("loop_cond")
        bb_body = self.builder.append_basic_block("loop_body")
        bb_exit = self.builder.append_basic_block("loop_exit")
        self.builder.branch(bb_cond)
        self.builder.position_at_end(bb_cond)
        self.builder.cbranch(self._to_bool(self._expression(u.condition)), bb_body, bb_exit)
        self.builder.position_at_end(bb_body)
        for s in u.body:
            self._statement(s)
        if not self.builder.block.is_terminated:
            self.builder.branch(bb_cond)
        self.builder.position_at_end(bb_exit)

    def _expression(self, v):
        if isinstance(v, NumberLit):
            return INT(v.value)
        if isinstance(v, Ident):
            if v.name not in self.scope:
                raise CodegenError(f"Unknown variable '{v.name}' (string {v.string})")
            return self.builder.load(self.scope[v.name], name=v.name)
        if isinstance(v, Binary):
            l = self._expression(v.left); p = self._expression(v.right)
            return {
                "+": lambda: self.builder.add(l, p),
                "-": lambda: self.builder.sub(l, p),
                "*": lambda: self.builder.mul(l, p),
                "/": lambda: self.builder.sdiv(l, p),
                ">": lambda: self.builder.icmp_signed(">", l, p),
                "<": lambda: self.builder.icmp_signed("<", l, p),
                "==": lambda: self.builder.icmp_signed("==", l, p),
            }[v.op]()
        if isinstance(v, Call):
            if v.name == "print":
                node = v.arguments[0]
                if isinstance(node, StringLit):
                    g = self._global_string(node.value)
                    self.builder.call(self.printf,
                        [self._ptr(self.builder, self._fmt_string),
                         self._ptr(self.builder, g)])
                else:
                    arg = self._expression(node)
                    if arg.type == BOOL:                       # i1 -> i64
                        arg = self.builder.zext(arg, INT)
                    self.builder.call(self.printf,
                        [self._ptr(self.builder, self._fmt_number), arg])
                return INT(0)
            arg = [self._expression(a) for a in v.arguments]
            if v.name in self.functions:
                return self.builder.call(self.functions[v.name], arg)
            # system API: declare as_ outer function (libc-like)
            outer = self._outer(v.name, len(arg))
            return self.builder.call(outer, arg)
        raise CodegenError(f"Not_ can generate node {type(v).__name__}")

    def _to_bool(self, val):
        if val.type == BOOL:
            return val
        return self.builder.icmp_signed("!=", val, INT(0))
