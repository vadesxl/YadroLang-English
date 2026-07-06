# -*- coding: utf-8 -*-
"""AST i parser YadroLang (recursive descent + Pratt for_ expressions)."""
from dataclasses import dataclass, field
from src.lexer import Kind, Token


@dataclass
class Node:
    string: int = 0


@dataclass
class NumberLit(Node):
    value: int = 0


@dataclass
class StringLit(Node):
    value: str = ""


@dataclass
class Ident(Node):
    name: str = ""


@dataclass
class Binary(Node):
    op: str = ""; left: Node = None; right: Node = None


@dataclass
class Call(Node):
    name: str = ""; arguments: list = field(default_factory=list)


@dataclass
class Let(Node):
    name: str = ""; value: Node = None


@dataclass
class Assign(Node):
    name: str = ""; value: Node = None


@dataclass
class Return(Node):
    value: Node = None


@dataclass
class If(Node):
    condition: Node = None
    then_branch: list = field(default_factory=list)
    else_branch: list = field(default_factory=list)


@dataclass
class While(Node):
    condition: Node = None
    body: list = field(default_factory=list)


@dataclass
class Function(Node):
    name: str = ""
    parameters: list = field(default_factory=list)
    body: list = field(default_factory=list)
    mandates: list = field(default_factory=list)


@dataclass
class Program(Node):
    functions: list = field(default_factory=list)


class ParserError(Exception):
    ...


PRECEDENCE = {
    Kind.EQ: 1, Kind.GT: 1, Kind.LT: 1,
    Kind.PLUS: 2, Kind.MINUS: 2,
    Kind.STAR: 3, Kind.SLASH: 3,
}
OP_TEXT = {Kind.PLUS: "+", Kind.MINUS: "-", Kind.STAR: "*", Kind.SLASH: "/",
            Kind.GT: ">", Kind.LT: "<", Kind.EQ: "=="}


class Parser:
    def __init__(self, tokens):
        self.t = tokens; self.i = 0

    def _current(self):
        return self.t[self.i]

    def _eat(self, kind=None):
        tok = self.t[self.i]
        if kind and tok.kind != kind:
            raise ParserError(f"Expected {kind}, received '{tok.text}' on {tok.string}")
        self.i += 1
        return tok

    def parse(self):
        prog = Program()
        while self._current().kind != Kind.EOF:
            prog.functions.append(self._function())
        return prog

    def _function(self):
        line = self._eat(Kind.FN).string
        name = self._eat(Kind.NAME).text
        self._eat(Kind.LPAREN)
        parameters = []
        while self._current().kind != Kind.RPAREN:
            parameters.append(self._eat(Kind.NAME).text)
            if self._current().kind == Kind.COMMA:
                self._eat()
        self._eat(Kind.RPAREN)
        mandates = []
        if self._current().kind == Kind.NAME and self._current().text == "requires":
            self._eat()
            self._eat(Kind.LBRACKET)
            while self._current().kind != Kind.RBRACKET:
                mandates.append(self._eat(Kind.NAME).text)
                if self._current().kind == Kind.COMMA:
                    self._eat()
            self._eat(Kind.RBRACKET)
        body = self._block()
        return Function(line, name, parameters, body, mandates)

    def _block(self):
        self._eat(Kind.LBRACE)
        stmt = []
        while self._current().kind != Kind.RBRACE:
            stmt.append(self._statement())
        self._eat(Kind.RBRACE)
        return stmt

    def _statement(self):
        v = self._current().kind
        if v == Kind.RETURN:
            line = self._eat().string
            return Return(line, self._expression())
        if v == Kind.LET:
            line = self._eat().string
            name = self._eat(Kind.NAME).text
            self._eat(Kind.ASSIGN)
            return Let(line, name, self._expression())
        if v == Kind.IF:
            return self._if_branch()
        if v == Kind.WHILE:
            line = self._eat().string
            cond = self._expression()
            return While(line, cond, self._block())
        if v == Kind.NAME and self.t[self.i + 1].kind == Kind.ASSIGN:
            line = self._current().string
            name = self._eat().text
            self._eat(Kind.ASSIGN)
            return Assign(line, name, self._expression())
        return self._expression()

    def _if_branch(self):
        line = self._eat(Kind.IF).string
        cond = self._expression()
        then_branch = self._block()
        else_branch = []
        if self._current().kind == Kind.ELSE:
            self._eat()
            else_branch = self._block()
        return If(line, cond, then_branch, else_branch)

    def _expression(self, min=0):
        left = self._primary()
        while True:
            v = self._current().kind
            prev = PRECEDENCE.get(v)
            if prev is None or prev < min:
                break
            op = self._eat()
            right = self._expression(prev + 1)
            left = Binary(op.string, OP_TEXT[v], left, right)
        return left

    def _primary(self):
        tok = self._current()
        if tok.kind == Kind.NUMBER:
            self._eat(); return NumberLit(tok.string, int(tok.text))
        if tok.kind == Kind.STRING:
            self._eat(); return StringLit(tok.string, tok.text)
        if tok.kind == Kind.LPAREN:
            self._eat(); inner = self._expression(); self._eat(Kind.RPAREN); return inner
        if tok.kind == Kind.NAME:
            self._eat()
            if self._current().kind == Kind.LPAREN:
                self._eat()
                arg = []
                while self._current().kind != Kind.RPAREN:
                    arg.append(self._expression())
                    if self._current().kind == Kind.COMMA:
                        self._eat()
                self._eat(Kind.RPAREN)
                return Call(tok.string, tok.text, arg)
            return Ident(tok.string, tok.text)
        raise ParserError(f"Unexpected token '{tok.text}' on {tok.string}")
