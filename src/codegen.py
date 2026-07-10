# -*- coding: utf-8 -*-
"""Typed verified LLVM backend facade."""
from src.codegen_verified import Codegen as _Codegen, CodegenError
from src.typesound import SoundTypeChecker
from src.ethics import SOURCES,SINKS,SANITIZERS
class Codegen(_Codegen):
 def generate(self,program):
  SoundTypeChecker(set(SOURCES)|set(SINKS)|set(SANITIZERS)|{"print"}).check(program)
  return super().generate(program)
