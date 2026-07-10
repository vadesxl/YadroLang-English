# -*- coding: utf-8 -*-
"""Verified LLVM IR generator for YadroLang ABI v1."""
import hashlib,re
from llvmlite import ir,binding as llvm
from src.syntax import (Program,Function,Return,Let,Assign,If,While,NumberLit,
                        BoolLit,StringLit,Ident,Binary,Call)
INT=ir.IntType(64); BOOL=ir.IntType(1); BYTE=ir.IntType(8); PTR=BYTE.as_pointer(); I32=ir.IntType(32)
class CodegenError(Exception): pass

def _symbol(prefix,name):
    readable=re.sub(r"[^A-Za-z0-9_]","_",name)[:40]
    digest=hashlib.sha256(name.encode("utf-8")).hexdigest()[:12]
    return f"yadro_{prefix}_v1_{readable}_{digest}"

class Codegen:
    def __init__(self):
        self.module=ir.Module(name="yadro"); self.module.triple=llvm.get_default_triple()
        self.functions={}; self.builder=None; self.scope={}; self.outer={}; self._count=0
        self.printf=ir.Function(self.module,ir.FunctionType(I32,[PTR],var_arg=True),name="printf")
    def _outer(self,name,arg_count):
        if name in self.outer:
            function,known=self.outer[name]
            if known!=arg_count: raise CodegenError(f"Extern ABI mismatch for '{name}': {known} versus {arg_count}")
            return function
        function=ir.Function(self.module,ir.FunctionType(INT,[INT]*arg_count),name=_symbol("ext",name))
        self.outer[name]=(function,arg_count); return function
    def _global_string(self,text):
        data=bytearray(text.encode("utf-8")+b"\0"); typ=ir.ArrayType(BYTE,len(data))
        value=ir.GlobalVariable(self.module,typ,name=f".str.{self._count}"); self._count+=1
        value.linkage="internal"; value.global_constant=True; value.initializer=ir.Constant(typ,data); return value
    def _ptr(self,builder,value):
        zero=ir.Constant(I32,0); return builder.gep(value,[zero,zero],inbounds=True)
    def _i64(self,value): return self.builder.zext(value,INT) if value.type==BOOL else value
    def generate(self,program:Program):
        self._fmt_number=self._global_string("%lld\n"); self._fmt_result=self._global_string("Result main(): %lld\n"); self._fmt_string=self._global_string("%s\n")
        for function in program.functions:
            symbol=_symbol("entry",function.name) if function.name=="main" else _symbol("fn",function.name)
            self.functions[function.name]=ir.Function(self.module,ir.FunctionType(INT,[INT]*len(function.parameters)),name=symbol)
        for function in program.functions: self._function(function)
        self._main_cli(); text=str(self.module)
        try: parsed=llvm.parse_assembly(text); parsed.verify()
        except Exception as error: raise CodegenError(f"LLVM verification failed: {error}") from error
        return text
    def _main_cli(self):
        function=ir.Function(self.module,ir.FunctionType(I32,[]),name="main"); builder=ir.IRBuilder(function.append_basic_block("entry"))
        result=builder.call(self.functions["main"],[]); builder.call(self.printf,[self._ptr(builder,self._fmt_result),result]); builder.ret(I32(0))
    def _function(self,node):
        function=self.functions[node.name]; self.builder=ir.IRBuilder(function.append_basic_block("entry")); self.scope={}
        for argument,name in zip(function.args,node.parameters):
            argument.name=name; cell=self.builder.alloca(INT,name=name); self.builder.store(argument,cell); self.scope[name]=cell
        self._body(node.body)
        if not self.builder.block.is_terminated: self.builder.ret(INT(0))
    def _body(self,statements):
        for statement in statements:
            if self.builder.block.is_terminated: break
            self._statement(statement)
    def _statement(self,node):
        if isinstance(node,Return): self.builder.ret(self._i64(self._expression(node.value)))
        elif isinstance(node,Let):
            cell=self.builder.alloca(INT,name=node.name); self.builder.store(self._i64(self._expression(node.value)),cell); self.scope[node.name]=cell
        elif isinstance(node,Assign):
            if node.name not in self.scope: raise CodegenError(f"Unknown variable '{node.name}' (line {node.string})")
            self.builder.store(self._i64(self._expression(node.value)),self.scope[node.name])
        elif isinstance(node,If): self._if(node)
        elif isinstance(node,While): self._while(node)
        else: self._expression(node)
    def _if(self,node):
        condition=self._to_bool(self._expression(node.condition)); function=self.builder.function
        then_block=function.append_basic_block("if.then"); else_block=function.append_basic_block("if.else") if node.else_branch else None; end_block=function.append_basic_block("if.end")
        self.builder.cbranch(condition,then_block,else_block or end_block)
        self.builder.position_at_end(then_block); self._body(node.then_branch)
        if not self.builder.block.is_terminated: self.builder.branch(end_block)
        if else_block:
            self.builder.position_at_end(else_block); self._body(node.else_branch)
            if not self.builder.block.is_terminated: self.builder.branch(end_block)
        self.builder.position_at_end(end_block)
    def _while(self,node):
        function=self.builder.function; condition_block=function.append_basic_block("loop.cond"); body_block=function.append_basic_block("loop.body"); exit_block=function.append_basic_block("loop.exit")
        self.builder.branch(condition_block); self.builder.position_at_end(condition_block); self.builder.cbranch(self._to_bool(self._expression(node.condition)),body_block,exit_block)
        self.builder.position_at_end(body_block); self._body(node.body)
        if not self.builder.block.is_terminated: self.builder.branch(condition_block)
        self.builder.position_at_end(exit_block)
    def _expression(self,node):
        if isinstance(node,NumberLit): return INT(node.value)
        if isinstance(node,BoolLit): return BOOL(1 if node.value else 0)
        if isinstance(node,StringLit): raise CodegenError("String values are only valid as print literals")
        if isinstance(node,Ident):
            if node.name not in self.scope: raise CodegenError(f"Unknown variable '{node.name}' (line {node.string})")
            return self.builder.load(self.scope[node.name],name=node.name)
        if isinstance(node,Binary):
            left=self._i64(self._expression(node.left)); right=self._i64(self._expression(node.right))
            operations={"+":self.builder.add,"-":self.builder.sub,"*":self.builder.mul,"/":self.builder.sdiv}
            if node.op in operations: return operations[node.op](left,right)
            return self.builder.icmp_signed(node.op,left,right)
        if isinstance(node,Call):
            if node.name=="print":
                value=node.arguments[0]
                if isinstance(value,StringLit):
                    text=self._global_string(value.value); self.builder.call(self.printf,[self._ptr(self.builder,self._fmt_string),self._ptr(self.builder,text)])
                else: self.builder.call(self.printf,[self._ptr(self.builder,self._fmt_number),self._i64(self._expression(value))])
                return INT(0)
            arguments=[self._i64(self._expression(arg)) for arg in node.arguments]
            target=self.functions.get(node.name) or self._outer(node.name,len(arguments)); return self.builder.call(target,arguments)
        raise CodegenError(f"Unsupported AST node {type(node).__name__}")
    def _to_bool(self,value): return value if value.type==BOOL else self.builder.icmp_signed("!=",value,INT(0))
