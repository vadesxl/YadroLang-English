# -*- coding: utf-8 -*-
"""Typed verified LLVM backend facade using native ABI v1 symbols."""
from src import codegen_verified as _backend
from src.abi import symbol
from src.typesound import SoundTypeChecker
from src.ethics import SOURCES,SINKS,SANITIZERS
CodegenError=_backend.CodegenError
class Codegen(_backend.Codegen):
 def __init__(self):super().__init__(symbol_mangler=symbol)
 def generate(self,program):
  SoundTypeChecker(set(SOURCES)|set(SINKS)|set(SANITIZERS)|{"print"}).check(program)
  return super().generate(program)
