# -*- coding: utf-8 -*-
"""Strict inferred i64/bool/string type system."""
from src.syntax import NumberLit,StringLit,BoolLit,Ident,Binary,Call,Let,Assign,Return,If,While
I64,BOOL,STRING,UNKNOWN="i64","bool","string","unknown"
class TypeCheckError(RuntimeError):
 def __init__(self,message,line=0,code="YADRO-T2000"):self.code=code;super().__init__(f"[{code}] {message} (line {line})")
class TypeChecker:
 MAX_ROUNDS=64
 def __init__(self,api):self.api=set(api);self.signatures={}
 def check(self,program):
  self.signatures={f.name:{"params":[UNKNOWN]*len(f.parameters),"return":UNKNOWN} for f in program.functions}
  for _ in range(self.MAX_ROUNDS):
   before=repr(self.signatures)
   for function in program.functions:self._function(function)
   if repr(self.signatures)==before:break
  else:raise TypeCheckError("type inference did not converge",0,"YADRO-T2099")
  for signature in self.signatures.values():signature["params"]=[I64 if x==UNKNOWN else x for x in signature["params"]];signature["return"]=I64 if signature["return"]==UNKNOWN else signature["return"]
  for function in program.functions:self._function(function);function.inferred_param_types=list(self.signatures[function.name]["params"]);function.inferred_return_type=self.signatures[function.name]["return"]
  return self.signatures
 def _merge(self,a,b,line,context):
  if b==UNKNOWN:return a
  if a==UNKNOWN:return b
  if a!=b:raise TypeCheckError(f"{context}: expected {a}, got {b}",line,"YADRO-T2002")
  return a
 def _function(self,function):
  signature=self.signatures[function.name];env=dict(zip(function.parameters,signature["params"]));returns=[];self._body(function.body,env,returns)
  for value,line in returns:signature["return"]=self._merge(signature["return"],value,line,f"return type of '{function.name}'")
 def _body(self,body,env,returns):
  terminated=False
  for statement in body:
   if terminated:raise TypeCheckError("unreachable statement after return",statement.string,"YADRO-T2006")
   if isinstance(statement,Let):
    value=self._expr(statement.value,env)
    if statement.name in env:raise TypeCheckError(f"variable '{statement.name}' already declared",statement.string,"YADRO-T2007")
    env[statement.name]=value;statement.inferred_type=value
   elif isinstance(statement,Assign):
    if statement.name not in env:raise TypeCheckError(f"unknown variable '{statement.name}'",statement.string,"YADRO-T2008")
    env[statement.name]=self._merge(env[statement.name],self._expr(statement.value,env),statement.string,f"assignment to '{statement.name}'")
   elif isinstance(statement,Return):returns.append((self._expr(statement.value,env),statement.string));terminated=True
   elif isinstance(statement,If):
    condition=self._expr(statement.condition,env)
    if condition not in (BOOL,I64,UNKNOWN):raise TypeCheckError("if condition must be bool or legacy i64 truthiness",statement.string,"YADRO-T2003")
    left,right=dict(env),dict(env);lr,rr=[],[];lt=self._body(statement.then_branch,left,lr);rt=self._body(statement.else_branch,right,rr) if statement.else_branch else False;returns.extend(lr+rr)
    for name in env:env[name]=self._merge(left.get(name,env[name]),right.get(name,env[name]),statement.string,f"branch value '{name}'")
    terminated=bool(statement.else_branch) and lt and rt
   elif isinstance(statement,While):
    condition=self._expr(statement.condition,env)
    if condition not in (BOOL,I64,UNKNOWN):raise TypeCheckError("while condition must be bool or legacy i64 truthiness",statement.string,"YADRO-T2003")
    loop=dict(env);nested=[];self._body(statement.body,loop,nested);returns.extend(nested)
    for name in env:env[name]=self._merge(env[name],loop.get(name,env[name]),statement.string,f"loop value '{name}'")
   else:self._expr(statement,env)
  return terminated
 def _expr(self,node,env):
  if isinstance(node,NumberLit):result=I64
  elif isinstance(node,StringLit):result=STRING
  elif isinstance(node,BoolLit):result=BOOL
  elif isinstance(node,Ident):
   if node.name not in env:raise TypeCheckError(f"unknown variable '{node.name}'",node.string,"YADRO-T2008")
   result=env[node.name]
  elif isinstance(node,Binary):
   left,right=self._expr(node.left,env),self._expr(node.right,env)
   if node.op in ("+","-","*","/",">","<"):
    if left not in (I64,UNKNOWN) or right not in (I64,UNKNOWN):raise TypeCheckError(f"operator '{node.op}' requires i64 operands",node.string,"YADRO-T2001")
    result=BOOL if node.op in (">","<") else I64
   elif node.op=="==":self._merge(left,right,node.string,"equality operands");result=BOOL
   else:raise TypeCheckError(f"unknown operator '{node.op}'",node.string)
  elif isinstance(node,Call):
   args=[self._expr(arg,env) for arg in node.arguments]
   if node.name=="print":result=I64
   elif node.name in self.signatures:
    signature=self.signatures[node.name]
    for index,value in enumerate(args):signature["params"][index]=self._merge(signature["params"][index],value,node.string,f"argument {index+1} of '{node.name}'")
    result=signature["return"]
   elif node.name in self.api:
    if any(value not in (I64,UNKNOWN) for value in args):raise TypeCheckError(f"system API '{node.name}' accepts i64 values only",node.string,"YADRO-T2004")
    result=I64
   else:raise TypeCheckError(f"unknown function '{node.name}'",node.string,"YADRO-T2009")
  else:raise TypeCheckError(f"unsupported expression {type(node).__name__}",getattr(node,"string",0))
  node.inferred_type=result;return result
