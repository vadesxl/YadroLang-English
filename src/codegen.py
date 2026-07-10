# -*- coding: utf-8 -*-
"""Typed verified LLVM backend facade using native ABI v1 symbols."""
from src import codegen_verified as _backend
from src.abi import symbol
from src.typesys import TypeChecker
from src.ethics import SOURCES,SINKS,SANITIZERS
_backend.symbol=symbol
CodegenError=_backend.CodegenError
class Codegen(_backend.Codegen):
 def generate(self,program):
  TypeChecker(set(SOURCES)|set(SINKS)|set(SANITIZERS)|{"print"}).check(program)
  return super().generate(program)
