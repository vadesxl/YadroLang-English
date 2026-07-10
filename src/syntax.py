# -*- coding: utf-8 -*-
"""YadroLang AST and bounded Pratt parser."""
from dataclasses import dataclass, field
from src.lexer import Kind
@dataclass
class Node: string:int=0
@dataclass
class NumberLit(Node): value:int=0
@dataclass
class StringLit(Node): value:str=""
@dataclass
class BoolLit(Node): value:bool=False
@dataclass
class Ident(Node): name:str=""
@dataclass
class Binary(Node): op:str=""; left:Node=None; right:Node=None
@dataclass
class Call(Node): name:str=""; arguments:list=field(default_factory=list)
@dataclass
class Let(Node): name:str=""; value:Node=None
@dataclass
class Assign(Node): name:str=""; value:Node=None
@dataclass
class Return(Node): value:Node=None
@dataclass
class If(Node): condition:Node=None; then_branch:list=field(default_factory=list); else_branch:list=field(default_factory=list)
@dataclass
class While(Node): condition:Node=None; body:list=field(default_factory=list)
@dataclass
class Function(Node): name:str=""; parameters:list=field(default_factory=list); body:list=field(default_factory=list); mandates:list=field(default_factory=list)
@dataclass
class Program(Node): functions:list=field(default_factory=list)
class ParserError(Exception): pass
PRECEDENCE={Kind.EQ:1,Kind.GT:1,Kind.LT:1,Kind.PLUS:2,Kind.MINUS:2,Kind.STAR:3,Kind.SLASH:3}
OP_TEXT={Kind.PLUS:"+",Kind.MINUS:"-",Kind.STAR:"*",Kind.SLASH:"/",Kind.GT:">",Kind.LT:"<",Kind.EQ:"=="}
class Parser:
 MAX_DEPTH=512
 def __init__(self,tokens):self.t=tokens;self.i=0;self.depth=0
 def _current(self):return self.t[self.i]
 def _eat(self,kind=None):
  token=self.t[self.i]
  if kind and token.kind!=kind:raise ParserError(f"Expected {kind}, received '{token.text}' on {token.string}")
  self.i+=1;return token
 def parse(self):
  program=Program()
  while self._current().kind!=Kind.EOF:
   before=self.i;program.functions.append(self._function())
   if self.i<=before:raise ParserError("parser made no progress")
  return program
 def _function(self):
  line=self._eat(Kind.FN).string;name=self._eat(Kind.NAME).text;self._eat(Kind.LPAREN);params=[]
  while self._current().kind!=Kind.RPAREN:
   params.append(self._eat(Kind.NAME).text)
   if self._current().kind==Kind.COMMA:self._eat()
  self._eat(Kind.RPAREN);mandates=[]
  if self._current().kind==Kind.NAME and self._current().text=="requires":
   self._eat();self._eat(Kind.LBRACKET)
   while self._current().kind!=Kind.RBRACKET:
    mandates.append(self._eat(Kind.NAME).text)
    if self._current().kind==Kind.COMMA:self._eat()
   self._eat(Kind.RBRACKET)
  return Function(line,name,params,self._block(),mandates)
 def _block(self):
  self._eat(Kind.LBRACE);body=[]
  while self._current().kind!=Kind.RBRACE:
   if self._current().kind==Kind.EOF:raise ParserError("Unclosed block")
   before=self.i;body.append(self._statement())
   if self.i<=before:raise ParserError("parser made no progress")
  self._eat(Kind.RBRACE);return body
 def _statement(self):
  kind=self._current().kind
  if kind==Kind.RETURN:line=self._eat().string;return Return(line,self._expression())
  if kind==Kind.LET:line=self._eat().string;name=self._eat(Kind.NAME).text;self._eat(Kind.ASSIGN);return Let(line,name,self._expression())
  if kind==Kind.IF:return self._if()
  if kind==Kind.WHILE:line=self._eat().string;condition=self._expression();return While(line,condition,self._block())
  if kind==Kind.NAME and self.i+1<len(self.t) and self.t[self.i+1].kind==Kind.ASSIGN:line=self._current().string;name=self._eat().text;self._eat();return Assign(line,name,self._expression())
  return self._expression()
 def _if(self):
  line=self._eat(Kind.IF).string;condition=self._expression();then=self._block();other=[]
  if self._current().kind==Kind.ELSE:self._eat();other=self._block()
  return If(line,condition,then,other)
 def _expression(self,minimum=0):
  self.depth+=1
  if self.depth>self.MAX_DEPTH:raise ParserError("expression nesting limit exceeded")
  try:
   left=self._primary()
   while True:
    kind=self._current().kind;precedence=PRECEDENCE.get(kind)
    if precedence is None or precedence<minimum:break
    operator=self._eat();left=Binary(operator.string,OP_TEXT[kind],left,self._expression(precedence+1))
   return left
  finally:self.depth-=1
 def _primary(self):
  token=self._current()
  if token.kind==Kind.NUMBER:self._eat();return NumberLit(token.string,int(token.text))
  if token.kind==Kind.STRING:self._eat();return StringLit(token.string,token.text)
  if token.kind in (Kind.TRUE,Kind.FALSE):self._eat();return BoolLit(token.string,token.kind==Kind.TRUE)
  if token.kind==Kind.LPAREN:self._eat();value=self._expression();self._eat(Kind.RPAREN);return value
  if token.kind==Kind.NAME:
   self._eat()
   if self._current().kind==Kind.LPAREN:
    self._eat();args=[]
    while self._current().kind!=Kind.RPAREN:
     args.append(self._expression())
     if self._current().kind==Kind.COMMA:self._eat()
    self._eat(Kind.RPAREN);return Call(token.string,token.text,args)
   return Ident(token.string,token.text)
  raise ParserError(f"Unexpected token '{token.text}' on {token.string}")
