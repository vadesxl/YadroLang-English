# -*- coding: utf-8 -*-
"""Typed verified LLVM backend facade."""
from src.codegen_verified import Codegen as _Codegen, CodegenError
from src.typesys import TypeChecker
from src.ethics import SOURCES,SINKS,SANITIZERS
class Codegen(_Codegen):
 def generate(self,program):
  TypeChecker(set(SOURCES)|set(SINKS)|set(SANITIZERS)|{"print"}).check(program)
  return super().generate(program)
