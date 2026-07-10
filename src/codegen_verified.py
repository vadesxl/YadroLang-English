# -*- coding: utf-8 -*-
"""Verified LLVM IR backend with typed storage and stable ABI v1 symbols."""
import hashlib
from llvmlite import ir,binding as llvm
from src.syntax import Return,Let,Assign,If,While,NumberLit,StringLit,BoolLit,Ident,Binary,Call
INT,BOOL,BYTE,I32=ir.IntType(64),ir.IntType(1),ir.IntType(8),ir.IntType(32);PTR=BYTE.as_pointer()
class CodegenError(Exception):pass
def llvm_type(name):return {"i64":INT,"bool":BOOL,"string":PTR}[name]
def symbol(prefix,name):return f"yadro.{prefix}.{hashlib.sha256(name.encode()).hexdigest()[:16]}"
class Codegen:
 def __init__(self):self.module=ir.Module(name="yadro");self.module.triple=llvm.get_default_triple();self.functions={};self.externs={};self.scope={};self.builder=None;self.count=0;self.printf=ir.Function(self.module,ir.FunctionType(I32,[PTR],var_arg=True),name="printf")
 def generate(self,program):
  self.fi=self._global("%lld\n");self.fs=self._global("%s\n");self.fr=self._global("Result main(): %lld\n")
  for f in program.functions:self.functions[f.name]=ir.Function(self.module,ir.FunctionType(llvm_type(f.inferred_return_type),[llvm_type(x) for x in f.inferred_param_types]),name=symbol("fn",f.name))
  for f in program.functions:self._function(f)
  self._entry();text=str(self.module)
  try:module=llvm.parse_assembly(text);module.verify()
  except Exception as error:raise CodegenError(f"LLVM verification failed: {error}") from error
  return text
 def _entry(self):
  if "main" not in self.functions:return
  fn=ir.Function(self.module,ir.FunctionType(I32,[]),name="main");b=ir.IRBuilder(fn.append_basic_block("entry"));result=b.call(self.functions["main"],[])
  if result.type==BOOL:result=b.zext(result,INT)
  if result.type==INT:b.call(self.printf,[self._ptr(b,self.fr),result])
  b.ret(I32(0))
 def _function(self,ast):
  fn=self.functions[ast.name];self.builder=ir.IRBuilder(fn.append_basic_block("entry"));self.scope={}
  for arg,name,t in zip(fn.args,ast.parameters,ast.inferred_param_types):cell=self.builder.alloca(llvm_type(t),name=f"var.{name}");self.builder.store(arg,cell);self.scope[name]=(cell,t)
  self._body(ast.body)
  if not self.builder.block.is_terminated:self.builder.ret({"i64":INT(0),"bool":BOOL(0),"string":ir.Constant(PTR,None)}[ast.inferred_return_type])
 def _body(self,body):
  for statement in body:
   if self.builder.block.is_terminated:break
   self._statement(statement)
 def _statement(self,node):
  if isinstance(node,Return):self.builder.ret(self._expr(node.value))
  elif isinstance(node,Let):value=self._expr(node.value);cell=self.builder.alloca(value.type,name=f"var.{node.name}");self.builder.store(value,cell);self.scope[node.name]=(cell,node.inferred_type)
  elif isinstance(node,Assign):self.builder.store(self._expr(node.value),self.scope[node.name][0])
  elif isinstance(node,If):self._if(node)
  elif isinstance(node,While):self._while(node)
  else:self._expr(node)
 def _if(self,node):
  condition=self._bool(self._expr(node.condition));fn=self.builder.function;then=fn.append_basic_block("if.then");other=fn.append_basic_block("if.else") if node.else_branch else None;end=fn.append_basic_block("if.end");self.builder.cbranch(condition,then,other or end);self.builder.position_at_end(then);self._body(node.then_branch)
  if not self.builder.block.is_terminated:self.builder.branch(end)
  if other:
   self.builder.position_at_end(other);self._body(node.else_branch)
   if not self.builder.block.is_terminated:self.builder.branch(end)
  self.builder.position_at_end(end)
 def _while(self,node):
  fn=self.builder.function;cond=fn.append_basic_block("while.cond");body=fn.append_basic_block("while.body");end=fn.append_basic_block("while.end");self.builder.branch(cond);self.builder.position_at_end(cond);self.builder.cbranch(self._bool(self._expr(node.condition)),body,end);self.builder.position_at_end(body);self._body(node.body)
  if not self.builder.block.is_terminated:self.builder.branch(cond)
  self.builder.position_at_end(end)
 def _expr(self,node):
  if isinstance(node,NumberLit):return INT(node.value)
  if isinstance(node,BoolLit):return BOOL(1 if node.value else 0)
  if isinstance(node,StringLit):return self._ptr(self.builder,self._global(node.value))
  if isinstance(node,Ident):return self.builder.load(self.scope[node.name][0],name=f"load.{node.name}")
  if isinstance(node,Binary):
   left,right=self._expr(node.left),self._expr(node.right);ops={"+":self.builder.add,"-":self.builder.sub,"*":self.builder.mul,"/":self.builder.sdiv}
   return ops[node.op](left,right) if node.op in ops else self.builder.icmp_signed(node.op,left,right)
  if isinstance(node,Call):
   if node.name=="print":
    value=self._expr(node.arguments[0])
    if value.type==PTR:self.builder.call(self.printf,[self._ptr(self.builder,self.fs),value])
    else:
     if value.type==BOOL:value=self.builder.zext(value,INT)
     self.builder.call(self.printf,[self._ptr(self.builder,self.fi),value])
    return INT(0)
   args=[self._expr(arg) for arg in node.arguments]
   if node.name in self.functions:return self.builder.call(self.functions[node.name],args)
   signature=tuple(arg.type for arg in args);previous=self.externs.get(node.name)
   if previous and previous[0]!=signature:raise CodegenError(f"extern ABI mismatch for '{node.name}'")
   if not previous:self.externs[node.name]=(signature,ir.Function(self.module,ir.FunctionType(INT,list(signature)),name=symbol("abi.v1",node.name)))
   return self.builder.call(self.externs[node.name][1],args)
  raise CodegenError(f"unsupported node {type(node).__name__}")
 def _global(self,text):
  data=bytearray(text.encode()+b"\0");array=ir.ArrayType(BYTE,len(data));value=ir.GlobalVariable(self.module,array,name=f".str.{self.count}");self.count+=1;value.linkage="internal";value.global_constant=True;value.initializer=ir.Constant(array,data);return value
 @staticmethod
 def _ptr(builder,value):return builder.gep(value,[I32(0),I32(0)],inbounds=True)
 def _bool(self,value):return value if value.type==BOOL else self.builder.icmp_signed("!=",value,INT(0))
