# -*- coding: utf-8 -*-
"""YadroLang AST and recursive-descent/Pratt parser."""
from dataclasses import dataclass, field
from src.lexer import Kind

@dataclass
class Node: string: int = 0
@dataclass
class NumberLit(Node): value: int = 0
@dataclass
class BoolLit(Node): value: bool = False
@dataclass
class StringLit(Node): value: str = ""
@dataclass
class Ident(Node): name: str = ""
@dataclass
class Binary(Node): op: str = ""; left: Node = None; right: Node = None
@dataclass
class Call(Node): name: str = ""; arguments: list = field(default_factory=list)
@dataclass
class Let(Node): name: str = ""; value: Node = None
@dataclass
class Assign(Node): name: str = ""; value: Node = None
@dataclass
class Return(Node): value: Node = None
@dataclass
class If(Node):
    condition: Node = None
    then_branch: list = field(default_factory=list)
    else_branch: list = field(default_factory=list)
@dataclass
class While(Node): condition: Node = None; body: list = field(default_factory=list)
@dataclass
class Function(Node):
    name: str = ""
    parameters: list = field(default_factory=list)
    body: list = field(default_factory=list)
    mandates: list = field(default_factory=list)
@dataclass
class Program(Node): functions: list = field(default_factory=list)

class ParserError(Exception): pass

PRECEDENCE = {Kind.EQ:1, Kind.GT:1, Kind.LT:1, Kind.PLUS:2, Kind.MINUS:2,
              Kind.STAR:3, Kind.SLASH:3}
OP_TEXT = {Kind.PLUS:"+", Kind.MINUS:"-", Kind.STAR:"*", Kind.SLASH:"/",
           Kind.GT:">", Kind.LT:"<", Kind.EQ:"=="}

class Parser:
    def __init__(self, tokens): self.t=tokens; self.i=0
    def _current(self): return self.t[self.i]
    def _eat(self, kind=None):
        tok=self._current()
        if kind and tok.kind != kind:
            raise ParserError(f"Expected {kind}, received '{tok.text}' on {tok.string}")
        self.i += 1; return tok
    def parse(self):
        program=Program()
        while self._current().kind != Kind.EOF: program.functions.append(self._function())
        return program
    def _function(self):
        line=self._eat(Kind.FN).string; name=self._eat(Kind.NAME).text; self._eat(Kind.LPAREN)
        parameters=[]
        while self._current().kind != Kind.RPAREN:
            parameters.append(self._eat(Kind.NAME).text)
            if self._current().kind == Kind.COMMA: self._eat()
        self._eat(Kind.RPAREN); mandates=[]
        if self._current().kind == Kind.NAME and self._current().text == "requires":
            self._eat(); self._eat(Kind.LBRACKET)
            while self._current().kind != Kind.RBRACKET:
                mandates.append(self._eat(Kind.NAME).text)
                if self._current().kind == Kind.COMMA: self._eat()
            self._eat(Kind.RBRACKET)
        return Function(line,name,parameters,self._block(),mandates)
    def _block(self):
        self._eat(Kind.LBRACE); statements=[]
        while self._current().kind != Kind.RBRACE:
            if self._current().kind == Kind.EOF: raise ParserError("Unclosed block at end of file")
            before=self.i; statements.append(self._statement())
            if self.i <= before: raise ParserError("Parser made no progress")
        self._eat(Kind.RBRACE); return statements
    def _statement(self):
        kind=self._current().kind
        if kind == Kind.RETURN: return Return(self._eat().string,self._expression())
        if kind == Kind.LET:
            line=self._eat().string; name=self._eat(Kind.NAME).text; self._eat(Kind.ASSIGN)
            return Let(line,name,self._expression())
        if kind == Kind.IF: return self._if_branch()
        if kind == Kind.WHILE:
            line=self._eat().string; condition=self._expression(); return While(line,condition,self._block())
        if kind == Kind.NAME and self.i+1 < len(self.t) and self.t[self.i+1].kind == Kind.ASSIGN:
            line=self._current().string; name=self._eat().text; self._eat(Kind.ASSIGN)
            return Assign(line,name,self._expression())
        return self._expression()
    def _if_branch(self):
        line=self._eat(Kind.IF).string; condition=self._expression(); then=self._block(); otherwise=[]
        if self._current().kind == Kind.ELSE: self._eat(); otherwise=self._block()
        return If(line,condition,then,otherwise)
    def _expression(self, minimum=0):
        left=self._primary()
        while True:
            kind=self._current().kind; precedence=PRECEDENCE.get(kind)
            if precedence is None or precedence < minimum: break
            op=self._eat(); right=self._expression(precedence+1)
            left=Binary(op.string,OP_TEXT[kind],left,right)
        return left
    def _primary(self):
        tok=self._current()
        if tok.kind == Kind.NUMBER: self._eat(); return NumberLit(tok.string,int(tok.text))
        if tok.kind in (Kind.TRUE,Kind.FALSE): self._eat(); return BoolLit(tok.string,tok.kind==Kind.TRUE)
        if tok.kind == Kind.STRING: self._eat(); return StringLit(tok.string,tok.text)
        if tok.kind == Kind.LPAREN:
            self._eat(); inner=self._expression(); self._eat(Kind.RPAREN); return inner
        if tok.kind == Kind.NAME:
            self._eat()
            if self._current().kind == Kind.LPAREN:
                self._eat(); arguments=[]
                while self._current().kind != Kind.RPAREN:
                    arguments.append(self._expression())
                    if self._current().kind == Kind.COMMA: self._eat()
                self._eat(Kind.RPAREN); return Call(tok.string,tok.text,arguments)
            return Ident(tok.string,tok.text)
        raise ParserError(f"Unexpected token '{tok.text}' on {tok.string}")
