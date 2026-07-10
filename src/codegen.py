# -*- coding: utf-8 -*-
"""Compatibility facade for typed, verified LLVM generation."""
from src.codegen_verified import Codegen as _VerifiedCodegen, CodegenError
from src.typesys import TypeChecker
from src.ethics import SOURCES, SINKS, SANITIZERS

class Codegen(_VerifiedCodegen):
    def generate(self, program):
        TypeChecker(set(SOURCES) | set(SINKS) | set(SANITIZERS) | {"print"}).check(program)
        return super().generate(program)
