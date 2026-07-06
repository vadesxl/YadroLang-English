# -*- coding: utf-8 -*-
"""Lexer YadroLang. Turns source text v stream tokens s positions."""
from enum import Enum, auto
from dataclasses import dataclass


class Kind(Enum):
    NUMBER = auto(); STRING = auto(); NAME = auto()
    FN = auto(); RETURN = auto(); LET = auto()
    IF = auto(); ELSE = auto(); WHILE = auto()
    TRUE = auto(); FALSE = auto()
    LPAREN = auto(); RPAREN = auto(); LBRACE = auto(); RBRACE = auto()
    LBRACKET = auto(); RBRACKET = auto()
    COMMA = auto(); SEMI = auto()
    PLUS = auto(); MINUS = auto(); STAR = auto(); SLASH = auto()
    ASSIGN = auto(); EQ = auto(); GT = auto(); LT = auto()
    EOF = auto()


KEYWORDS = {
    "fn": Kind.FN, "return": Kind.RETURN, "let": Kind.LET,
    "if": Kind.IF, "else": Kind.ELSE, "while": Kind.WHILE,
    "true": Kind.TRUE, "false": Kind.FALSE,
}


@dataclass
class Token:
    kind: Kind
    text: str
    string: int
    column: int


class LexerError(Exception):
    ...


class Lexer:
    def __init__(self, source: str):
        self.s = source
        self.i = 0
        self.string = 1
        self.column = 1

    def _step(self) -> str:
        ch = self.s[self.i]; self.i += 1
        if ch == "\n":
            self.string += 1; self.column = 1
        else:
            self.column += 1
        return ch

    def _peek(self, off=0) -> str:
        j = self.i + off
        return self.s[j] if j < len(self.s) else ""

    def tokens(self):
        output = []
        while self.i < len(self.s):
            ch = self._peek()
            if ch in " \t\r\n":
                self._step(); continue
            if ch == "#":
                while self.i < len(self.s) and self._peek() != "\n":
                    self._step()
                continue
            line, col = self.string, self.column
            if ch.isdigit():
                output.append(self._number(line, col))
            elif ch.isalpha() or ch == "_":
                output.append(self._name(line, col))
            elif ch == '"':
                output.append(self._string(line, col))
            else:
                output.append(self._character(line, col))
        output.append(Token(Kind.EOF, "", self.string, self.column))
        return output

    def _number(self, line, col):
        start = self.i
        while self._peek().isdigit():
            self._step()
        return Token(Kind.NUMBER, self.s[start:self.i], line, col)

    def _name(self, line, col):
        start = self.i
        while self._peek().isalnum() or self._peek() in ("_", "."):
            self._step()
        text = self.s[start:self.i]
        return Token(KEYWORDS.get(text, Kind.NAME), text, line, col)

    def _string(self, line, col):
        self._step()
        start = self.i
        while self._peek() != '"':
            if self.i >= len(self.s):
                raise LexerError(f"Unclosed string on {line}:{col}")
            self._step()
        text = self.s[start:self.i]
        self._step()
        return Token(Kind.STRING, text, line, col)

    _SINGLE_CHARS = {
        "(": Kind.LPAREN, ")": Kind.RPAREN, "{": Kind.LBRACE, "}": Kind.RBRACE,
        "[": Kind.LBRACKET, "]": Kind.RBRACKET,
        ",": Kind.COMMA, ";": Kind.SEMI, "+": Kind.PLUS, "-": Kind.MINUS,
        "*": Kind.STAR, "/": Kind.SLASH, ">": Kind.GT, "<": Kind.LT,
    }

    def _character(self, line, col):
        ch = self._step()
        if ch == "=" and self._peek() == "=":
            self._step(); return Token(Kind.EQ, "==", line, col)
        if ch == "=":
            return Token(Kind.ASSIGN, "=", line, col)
        if ch in self._SINGLE_CHARS:
            return Token(self._SINGLE_CHARS[ch], ch, line, col)
        raise LexerError(f"Unknown character '{ch}' on {line}:{col}")
