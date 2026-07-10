# -*- coding: utf-8 -*-
"""Minimal strict type inference: i64, bool and string."""
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
   for f in program.functions:self._function(f,True)
   if repr(self.signatures)==before:break
  else:raise TypeCheckError("type inference did not converge",0,"YADRO-T2099")
  for s in self.signatures.values():s["params"]=[I64 if x==UNKNOWN else x for x in s["params"]];s["return"]=I64 if s["return"]==UNKNOWN else s["return"]
  for f in program.functions:self._function(f,False);f.inferred_param_types=list(self.signatures[f.name]["params"]);f.inferred_return_type=self.signatures[f.name]["return"]
  return self.signatures
 def _merge(self,a,b,line,ctx):
  if b==UNKNOWN:return a
  if a==UNKNOWN:return b
  if a!=b:raise TypeCheckError(f"{ctx}: expected {a}, got {b}",line,"YADRO-T2002")
  return a
 def _function(self,f,infer):
  s=self.signatures[f.name];env=dict(zip(f.parameters,s["params"]));returns=[];self._body(f.body,env,returns,infer)
  for value,line in returns:s["return"]=self._merge(s["return"],value,line,f"return type of '{f.name}'")
 def _body(self,body,env,returns,infer):
  terminated=False
  for st in body:
   if terminated:raise TypeCheckError("unreachable statement after return",st.string,"YADRO-T2006")
   if isinstance(st,Let):value=self._expr(st.value,env,infer);env[st.name]=value;st.inferred_type=value
   elif isinstance(st,Assign):
    if st.name not in env:raise TypeCheckError(f"unknown variable '{st.name}'",st.string,"YADRO-T2008")
    env[st.name]=self._merge(env[st.name],self._expr(st.value,env,infer),st.string,f"assignment to '{st.name}'")
   elif isinstance(st,Return):returns.append((self._expr(st.value,env,infer),st.string));terminated=True
   elif isinstance(st,If):
    t=self._expr(st.condition,env,infer)
    if t not in (BOOL,I64,UNKNOWN):raise TypeCheckError("if condition must be bool or legacy i64 truthiness",st.string,"YADRO-T2003")
    left,right=dict(env),dict(env);lr,rr=[],[];lt=self._body(st.then_branch,left,lr,infer);rt=self._body(st.else_branch,right,rr,infer) if st.else_branch else False;returns.extend(lr+rr)
    for name in env:env[name]=self._merge(left.get(name,env[name]),right.get(name,env[name]),st.string,f"branch value '{name}'")
    terminated=bool(st.else_branch) and lt and rt
   elif isinstance(st,While):
    t=self._expr(st.condition,env,infer)
    if t not in (BOOL,I64,UNKNOWN):raise TypeCheckError("while condition must be bool or legacy i64 truthiness",st.string,"YADRO-T2003")
    loop=dict(env);r=[];self._body(st.body,loop,r,infer);returns.extend(r)
    for name in env:env[name]=self._merge(env[name],loop.get(name,env[name]),st.string,f"loop value '{name}'")
   else:self._expr(st,env,infer)
  return terminated
 def _expr(self,n,env,infer):
  if isinstance(n,NumberLit):r=I64
  elif isinstance(n,StringLit):r=STRING
  elif isinstance(n,BoolLit):r=BOOL
  elif isinstance(n,Ident):
   if n.name not in env:raise TypeCheckError(f"unknown variable '{n.name}'",n.string,"YADRO-T2008")
   r=env[n.name]
  elif isinstance(n,Binary):
   a,b=self._expr(n.left,env,infer),self._expr(n.right,env,infer)
   if n.op in ("+","-","*","/",">","<"):
    if a not in (I64,UNKNOWN) or b not in (I64,UNKNOWN):raise TypeCheckError(f"operator '{n.op}' requires i64 operands",n.string,"YADRO-T2001")
    r=BOOL if n.op in (">","<") else I64
   elif n.op=="==":self._merge(a,b,n.string,"equality operands");r=BOOL
   else:raise TypeCheckError(f"unknown operator '{n.op}'",n.string)
  elif isinstance(n,Call):
   args=[self._expr(x,env,infer) for x in n.arguments]
   if n.name=="print":r=I64
   elif n.name in self.signatures:
    s=self.signatures[n.name]
    for i,t in enumerate(args):s["params"][i]=self._merge(s["params"][i],t,n.string,f"argument {i+1} of '{n.name}'")
    r=s["return"]
   elif n.name in self.api:
    if any(t not in (I64,UNKNOWN) for t in args):raise TypeCheckError(f"system API '{n.name}' accepts i64 values only",n.string,"YADRO-T2004")
    r=I64
   else:raise TypeCheckError(f"unknown function '{n.name}'",n.string,"YADRO-T2009")
  else:raise TypeCheckError(f"unsupported expression {type(n).__name__}",getattr(n,"string",0))
  n.inferred_type=r;return r
