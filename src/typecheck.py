# -*- coding: utf-8 -*-
"""Minimal strict inferred type system for YadroLang."""
from src.syntax import (NumberLit,BoolLit,StringLit,Ident,Binary,Call,Let,Assign,
                        Return,If,While)
I64="i64"; BOOL="bool"; STRING="string"; UNKNOWN="unknown"

class TypeCheckError(Exception):
    def __init__(self,message,code="YADRO-T1000"):
        self.code=code; super().__init__(f"[{code}] {message}")

class TypeChecker:
    def __init__(self,sources,sinks,sanitizers):
        self.sources=set(sources); self.sinks=set(sinks); self.sanitizers=set(sanitizers)
        self.functions={}; self.params={}; self.returns={}
    def check(self,program):
        self.functions={f.name:f for f in program.functions}
        self.params={f.name:[UNKNOWN]*len(f.parameters) for f in program.functions}
        self.returns={f.name:UNKNOWN for f in program.functions}
        for _ in range(64):
            before=(repr(self.params),repr(self.returns))
            for function in program.functions: self._function(function)
            if before==(repr(self.params),repr(self.returns)): break
        else: raise TypeCheckError("Type inference did not converge","YADRO-T1099")
        for function in program.functions: self._function(function,final=True)
        return self
    def _error(self,node,message,code): raise TypeCheckError(f"{message} (line {node.string}).",code)
    def _merge(self,a,b,node,final=False):
        if a==UNKNOWN: return b
        if b==UNKNOWN: return a
        if a!=b: self._error(node,f"Type mismatch: {a} versus {b}","YADRO-T1001")
        return a
    def _function(self,function,final=False):
        env=dict(zip(function.parameters,self.params[function.name])); returns=[]
        terminated=self._body(function.body,env,returns,final)
        result=UNKNOWN
        for value,node in returns: result=self._merge(result,value,node,final)
        if result==STRING: self._error(function,"Functions cannot return string values","YADRO-T1005")
        if result==UNKNOWN: result=I64
        self.returns[function.name]=self._merge(self.returns[function.name],result,function,final)
        self.params[function.name]=[env.get(name,UNKNOWN) for name in function.parameters]
        return terminated
    def _body(self,body,env,returns,final=False):
        terminated=False
        for statement in body:
            if terminated: self._error(statement,"Unreachable statement after unconditional return","YADRO-T1008")
            if isinstance(statement,Let):
                value=self._expr(statement.value,env,final)
                if value==STRING: self._error(statement,"String values may only be used as print literals","YADRO-T1005")
                env[statement.name]=value
            elif isinstance(statement,Assign):
                if statement.name not in env: self._error(statement,f"Unknown variable '{statement.name}'","YADRO-T1006")
                env[statement.name]=self._merge(env[statement.name],self._expr(statement.value,env,final),statement,final)
            elif isinstance(statement,Return):
                returns.append((self._expr(statement.value,env,final),statement)); terminated=True
            elif isinstance(statement,If):
                condition=self._expr(statement.condition,env,final)
                if condition not in (BOOL,I64,UNKNOWN): self._error(statement,"if condition must be bool or i64 truthiness","YADRO-T1003")
                left=dict(env); right=dict(env); lr=[]; rr=[]
                lt=self._body(statement.then_branch,left,lr,final); rt=self._body(statement.else_branch,right,rr,final) if statement.else_branch else False
                for name in set(left)|set(right): env[name]=self._merge(left.get(name,env.get(name,UNKNOWN)),right.get(name,env.get(name,UNKNOWN)),statement,final)
                returns.extend(lr); returns.extend(rr); terminated=bool(statement.else_branch) and lt and rt
            elif isinstance(statement,While):
                condition=self._expr(statement.condition,env,final)
                if condition not in (BOOL,I64,UNKNOWN): self._error(statement,"while condition must be bool or i64 truthiness","YADRO-T1003")
                loop=dict(env); loop_returns=[]; self._body(statement.body,loop,loop_returns,final)
                for name in set(env)|set(loop): env[name]=self._merge(env.get(name,UNKNOWN),loop.get(name,UNKNOWN),statement,final)
                returns.extend(loop_returns)
            else: self._expr(statement,env,final)
        return terminated
    def _force_ident(self,node,env,expected):
        if isinstance(node,Ident): env[node.name]=self._merge(env.get(node.name,UNKNOWN),expected,node)
    def _expr(self,node,env,final=False):
        if isinstance(node,NumberLit): return I64
        if isinstance(node,BoolLit): return BOOL
        if isinstance(node,StringLit): return STRING
        if isinstance(node,Ident):
            if node.name not in env: self._error(node,f"Unknown variable '{node.name}'","YADRO-T1006")
            return env[node.name]
        if isinstance(node,Binary):
            left=self._expr(node.left,env,final); right=self._expr(node.right,env,final)
            if node.op in ("+","-","*","/",">","<"):
                self._force_ident(node.left,env,I64); self._force_ident(node.right,env,I64)
                left=self._merge(left,I64,node); right=self._merge(right,I64,node)
                return BOOL if node.op in (">","<") else I64
            if node.op=="==":
                common=self._merge(left,right,node)
                if common==STRING: self._error(node,"String comparison is not supported","YADRO-T1005")
                return BOOL
        if isinstance(node,Call):
            args=[self._expr(arg,env,final) for arg in node.arguments]
            if node.name=="print":
                if len(args)!=1: self._error(node,"print expects one argument","YADRO-T1007")
                return I64
            if node.name in self.sources: return I64
            if node.name in self.sinks or node.name in self.sanitizers:
                if args and args[0]==STRING: self._error(node,"System APIs do not accept string values","YADRO-T1004")
                return I64
            if node.name in self.functions:
                expected=self.params[node.name]
                for index,value in enumerate(args):
                    merged=self._merge(expected[index],value,node,final); expected[index]=merged
                    if isinstance(node.arguments[index],Ident): env[node.arguments[index].name]=merged
                return self.returns[node.name]
            return I64
        self._error(node,"Cannot infer expression type","YADRO-T1000")
