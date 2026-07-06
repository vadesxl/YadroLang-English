# -*- coding: utf-8 -*-
"""Compiler YadroLang v1.1 - native compilation through LLVM.

    python -m src.main file.yad          # build native object_file kernel.o
    python -m src.main file.yad --ir     # output LLVM IR
"""
import sys
from llvmlite import binding as llvm
from src.lexer import Lexer, LexerError
from src.syntax import Parser, ParserError, Call, NumberLit, Binary
from src.ethics import EthicalAnalyzer, EthicalError, SINKS, SOURCES, SANITIZERS
from src.codegen import Codegen


class EntryPointError(Exception):
    """Program not_ has correct point entry 'main'."""


def _check_entry_point(ast):
    entry_points = [f for f in ast.functions if f.name == "main"]
    if not entry_points:
        raise EntryPointError(
            "No point entry: program must declare function 'main'.")
    if len(entry_points) > 1:
        raise EntryPointError(
            "Point entry 'main' declared several time - must be one.")
    if entry_points[0].parameters:
        raise EntryPointError(
            "Point entry 'main' not_ must accept parameters.")


SYSTEM_API = set(SINKS) | set(SOURCES) | set(SANITIZERS) | {"print"}


class SemanticError(Exception):
    """Call unknown functions or_ invalid number arguments."""


def _collect_calls(node, out):
    if isinstance(node, Call):
        out.append(node)
    dict = getattr(node, "__dict__", None)
    if not dict:
        return
    for value in dict.values():
        if isinstance(value, list):
            for e in value:
                _collect_calls(e, out)
        elif hasattr(value, "__dict__"):
            _collect_calls(value, out)


def _check_calls(ast):
    arity = {f.name: len(f.parameters) for f in ast.functions}
    for f in ast.functions:
        calls = []
        for stmt in f.body:
            _collect_calls(stmt, calls)
        for v in calls:
            if v.name in arity:
                if len(v.arguments) != arity[v.name]:
                    raise SemanticError(
                        f"Function '{v.name}' expects {arity[v.name]} arg., "
                        f"got {len(v.arguments)}.")
            elif v.name not in SYSTEM_API:
                raise SemanticError(f"Unknown function '{v.name}'.")



I64_MIN = -(2 ** 63)
I64_MAX = 2 ** 63 - 1


def _collect_nodes(node, type, out):
    if isinstance(node, type):
        out.append(node)
    dict = getattr(node, "__dict__", None)
    if not dict:
        return
    for value in dict.values():
        if isinstance(value, list):
            for e in value:
                _collect_nodes(e, type, out)
        elif hasattr(value, "__dict__"):
            _collect_nodes(value, type, out)


def _check_expressions(ast):
    for f in ast.functions:
        number, binary = [], []
        for stmt in f.body:
            _collect_nodes(stmt, NumberLit, number)
            _collect_nodes(stmt, Binary, binary)
        for ch in number:
            if not (I64_MIN <= ch.value <= I64_MAX):
                raise SemanticError(
                    f"Numeric literal {ch.value} outside range i64.")
        for b in binary:
            if b.op == "/" and isinstance(b.right, NumberLit) and b.right.value == 0:
                raise SemanticError("Division on zero.")


def compile(source: str, emit_ir=False) -> str:
    tokens = Lexer(source).tokens()
    ast = Parser(tokens).parse()
    _check_entry_point(ast)            # correct point entry to code
    _check_calls(ast)                 # all calls defined i s correct arity
    _check_expressions(ast)              # division on zero, range i64
    EthicalAnalyzer().check(ast)   # law to code
    ir_code = Codegen().generate(ast)
    if emit_ir:
        print(ir_code)
    return ir_code


def build_native(ir_code: str, exit="kernel.o"):
    # Initialization LLVM. V new versions llvmlite part calls is_deprecated
    # i throws exception - wrap each separately.
    for _init in (
        getattr(llvm, "initialize", None),
        getattr(llvm, "initialize_native_target", None),
        getattr(llvm, "initialize_native_asmprinter", None),
    ):
        if _init is not None:
            try:
                _init()
            except Exception:
                pass  # already initialized / call is_deprecated
    module = llvm.parse_assembly(ir_code)
    module.verify()
    # Optimization. API manager passes differs between versions llvmlite -
    # try old, then new, else_branch collect without optimizations.
    try:
        pmb = llvm.create_pass_manager_builder(); pmb.opt_level = 2
        pm = llvm.create_module_pass_manager(); pmb.populate(pm); pm.run(module)
    except AttributeError:
        try:
            pb = llvm.create_pass_builder(
                llvm.Target.from_default_triple().create_target_machine(),
                llvm.PipelineTuningOptions(speed_level=2))
            pb.getModulePassManager().run(module, pb)
        except Exception:
            pass  # without optimizations - correctness not_ suffers
    target = llvm.Target.from_default_triple().create_target_machine()
    with open(exit, "wb") as f:
        f.write(target.emit_object(module))
    print(f"[Kernel] Native object_file: {exit}")


def main_cli():
    if len(sys.argv) < 2:
        print("Usage: python -m src.main file.yad [--ir]")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        source = f.read()
    try:
        ir_code = compile(source, emit_ir="--ir" in sys.argv)
    except (EntryPointError, SemanticError, EthicalError, ParserError, LexerError) as e:
        print(f"[Kernel] Error compilation: {e}")
        sys.exit(1)
    if "--ir" not in sys.argv:
        build_native(ir_code)
    print("[Kernel] Compilation complete. Code - this law.")


if __name__ == "__main__":
    main_cli()