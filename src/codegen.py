# -*- coding: utf-8 -*-
"""Verified LLVM IR generator for YadroLang ABI v1."""
from llvmlite import ir, binding as llvm
from src.syntax import (Program, Function, Return, Let, Assign, If, While,
                        NumberLit, StringLit, Ident, Binary, Call)

INT=ir.IntType(64); BOOL=ir.IntType(1); BYTE=ir.IntType(8); PTR=BYTE.as_pointer(); I32=ir.IntType(32)

class CodegenError(Exception): pass

class Codegen:
 def __init__(self):
  self.module=ir.Module(name="kernel"); self.module.triple=llvm.get_default_triple()
  self.functions={}; self.builder=None; self.scope={}; self._count=0; self.externs={}
  self.printf=ir.Function(self.module,ir.FunctionType(I32,[PTR],var_arg=True),name="printf")
 def _abi_symbol(self,name): return "yadro_ext_v1_"+name.replace(".","_")
 def _outer(self,name,arg_count):
  symbol=self._abi_symbol(name); signature=ir.FunctionType(INT,[INT]*arg_count)
  existing=self.externs.get(symbol)
  if existing and str(existing.function_type)!=str(signature): raise CodegenError(f"extern ABI mismatch for '{name}'")
  if not existing: existing=ir.Function(self.module,signature,name=symbol); self.externs[symbol]=existing
  return existing
 def _global_string(self,text):
  data=bytearray(text.encode("utf-8")+b"\0"); ty=ir.ArrayType(BYTE,len(data)); g=ir.GlobalVariable(self.module,ty,name=f".str.{self._count}"); self._count+=1; g.linkage="internal"; g.global_constant=True; g.initializer=ir.Constant(ty,data); return g
 def _ptr(self,b,g): z=ir.Constant(I32,0); return b.gep(g,[z,z],inbounds=True)
 def _i64(self,value): return self.builder.zext(value,INT) if value.type==BOOL else value
 def generate(self,program:Program):
  self._fmt_number=self._global_string("%lld\n"); self._fmt_result=self._global_string("Result main(): %lld\n"); self._fmt_string=self._global_string("%s\n")
  for f in program.functions:
   symbol="yadro_main" if f.name=="main" else "yadro_fn_"+f.name
   self.functions[f.name]=ir.Function(self.module,ir.FunctionType(INT,[INT]*len(f.parameters)),name=symbol)
  for f in program.functions:self._function(f)
  self._main_cli(); text=str(self.module)
  try: mod=llvm.parse_assembly(text); mod.verify()
  except Exception as error: raise CodegenError(f"LLVM verification failed: {error}") from error
  return text
 def _main_cli(self):
  fn=ir.Function(self.module,ir.FunctionType(I32,[]),name="main"); b=ir.IRBuilder(fn.append_basic_block("entry")); result=b.call(self.functions["main"],[]); b.call(self.printf,[self._ptr(b,self._fmt_result),result]); b.ret(I32(0))
 def _function(self,f):
  fn=self.functions[f.name]; self.builder=ir.IRBuilder(fn.append_basic_block("entry")); self.scope={}
  for arg,name in zip(fn.args,f.parameters): cell=self.builder.alloca(INT,name=name); self.builder.store(arg,cell); self.scope[name]=cell
  for statement in f.body:
   if self.builder.block.is_terminated: break
   self._statement(statement)
  if not self.builder.block.is_terminated:self.builder.ret(INT(0))
 def _statement(self,node):
  if isinstance(node,Return): self.builder.ret(self._i64(self._expression(node.value)))
  elif isinstance(node,Let): cell=self.builder.alloca(INT,name=node.name); self.builder.store(self._i64(self._expression(node.value)),cell); self.scope[node.name]=cell
  elif isinstance(node,Assign):
   if node.name not in self.scope: raise CodegenError(f"unknown variable '{node.name}'")
   self.builder.store(self._i64(self._expression(node.value)),self.scope[node.name])
  elif isinstance(node,If): self._if(node)
  elif isinstance(node,While): self._while(node)
  else:self._expression(node)
 def _if(self,node):
  cond=self._to_bool(self._expression(node.condition)); fn=self.builder.function
  then=fn.append_basic_block("then"); other=fn.append_basic_block("else") if node.else_branch else None; end=fn.append_basic_block("if.end")
  self.builder.cbranch(cond,then,other or end); self.builder.position_at_end(then)
  for statement in node.then_branch:
   if self.builder.block.is_terminated: break
   self._statement(statement)
  if not self.builder.block.is_terminated:self.builder.branch(end)
  if other:
   self.builder.position_at_end(other)
   for statement in node.else_branch:
    if self.builder.block.is_terminated: break
    self._statement(statement)
   if not self.builder.block.is_terminated:self.builder.branch(end)
  self.builder.position_at_end(end)
 def _while(self,node):
  fn=self.builder.function; cond=fn.append_basic_block("loop.cond"); body=fn.append_basic_block("loop.body"); end=fn.append_basic_block("loop.end")
  self.builder.branch(cond); self.builder.position_at_end(cond); self.builder.cbranch(self._to_bool(self._expression(node.condition)),body,end); self.builder.position_at_end(body)
  for statement in node.body:
   if self.builder.block.is_terminated: break
   self._statement(statement)
  if not self.builder.block.is_terminated:self.builder.branch(cond)
  self.builder.position_at_end(end)
 def _expression(self,node):
  if isinstance(node,NumberLit):return INT(node.value)
  if isinstance(node,Ident):return self.builder.load(self.scope[node.name],name=node.name)
  if isinstance(node,Binary):
   left=self._expression(node.left); right=self._expression(node.right)
   return {"+":lambda:self.builder.add(left,right),"-":lambda:self.builder.sub(left,right),"*":lambda:self.builder.mul(left,right),"/":lambda:self.builder.sdiv(left,right),">":lambda:self.builder.icmp_signed(">",left,right),"<":lambda:self.builder.icmp_signed("<",left,right),"==":lambda:self.builder.icmp_signed("==",left,right)}[node.op]()
  if isinstance(node,Call):
   if node.name=="print":
    item=node.arguments[0]
    if isinstance(item,StringLit): g=self._global_string(item.value); self.builder.call(self.printf,[self._ptr(self.builder,self._fmt_string),self._ptr(self.builder,g)])
    else:self.builder.call(self.printf,[self._ptr(self.builder,self._fmt_number),self._i64(self._expression(item))])
    return INT(0)
   args=[self._i64(self._expression(arg)) for arg in node.arguments]
   return self.builder.call(self.functions[node.name],args) if node.name in self.functions else self.builder.call(self._outer(node.name,len(args)),args)
  raise CodegenError(f"cannot lower {type(node).__name__}")
 def _to_bool(self,value):return value if value.type==BOOL else self.builder.icmp_signed("!=",value,INT(0))
