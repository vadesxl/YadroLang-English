# -*- coding: utf-8 -*-
"""YadroLang compiler entry point and semantic validation."""
import sys
from llvmlite import binding as llvm
from src.lexer import Lexer, LexerError
from src.syntax import Parser, ParserError, Call, NumberLit, Binary
from src.ethics import EthicalAnalyzer, EthicalError, SINKS, SOURCES, SANITIZERS
from src.codegen import Codegen, CodegenError


class EntryPointError(Exception):
    """The program has no valid `main` entry point."""


class SemanticError(Exception):
    """The program is syntactically valid but semantically invalid."""


def _check_entry_point(ast):
    entry_points = [f for f in ast.functions if f.name == "main"]
    if not entry_points:
        raise EntryPointError("No entry point: program must declare function 'main'.")
    if len(entry_points) > 1:
        raise EntryPointError("Entry point 'main' must be declared exactly once.")
    if entry_points[0].parameters:
        raise EntryPointError("Entry point 'main' must not accept parameters.")


def _check_unique_functions(ast):
    seen = set()
    for function in ast.functions:
        if function.name in seen:
            raise SemanticError(
                f"Function '{function.name}' is declared more than once "
                f"(line {function.string}).")
        seen.add(function.name)


SYSTEM_API_ARITY = {
    **{name: 0 for name in SOURCES},
    **{name: 1 for name in SANITIZERS},
    **{name: 1 for name in SINKS},
    "print": 1,
}
SYSTEM_API = set(SYSTEM_API_ARITY)


def _collect_calls(node, output):
    if isinstance(node, Call):
        output.append(node)
    values = getattr(node, "__dict__", None)
    if not values:
        return
    for value in values.values():
        if isinstance(value, list):
            for element in value:
                _collect_calls(element, output)
        elif hasattr(value, "__dict__"):
            _collect_calls(value, output)


def _check_calls(ast):
    arity = {f.name: len(f.parameters) for f in ast.functions}
    for function in ast.functions:
        calls = []
        for statement in function.body:
            _collect_calls(statement, calls)
        for call in calls:
            expected = arity.get(call.name, SYSTEM_API_ARITY.get(call.name))
            if expected is None:
                raise SemanticError(
                    f"Unknown function '{call.name}' (line {call.string}).")
            if len(call.arguments) != expected:
                raise SemanticError(
                    f"Function '{call.name}' expects {expected} argument(s), "
                    f"got {len(call.arguments)} (line {call.string}).")


I64_MIN = -(2 ** 63)
I64_MAX = 2 ** 63 - 1


def _collect_nodes(node, node_type, output):
    if isinstance(node, node_type):
        output.append(node)
    values = getattr(node, "__dict__", None)
    if not values:
        return
    for value in values.values():
        if isinstance(value, list):
            for element in value:
                _collect_nodes(element, node_type, output)
        elif hasattr(value, "__dict__"):
            _collect_nodes(value, node_type, output)


def _constant_int(node):
    """Evaluate a side-effect-free integer expression when possible."""
    if isinstance(node, NumberLit):
        return node.value
    if not isinstance(node, Binary):
        return None
    left = _constant_int(node.left)
    right = _constant_int(node.right)
    if left is None or right is None:
        return None
    if node.op == "+":
        return left + right
    if node.op == "-":
        return left - right
    if node.op == "*":
        return left * right
    if node.op == "/" and right != 0:
        return abs(left) // abs(right) * (-1 if (left < 0) != (right < 0) else 1)
    return None


def _check_expressions(ast):
    for function in ast.functions:
        numbers, binaries = [], []
        for statement in function.body:
            _collect_nodes(statement, NumberLit, numbers)
            _collect_nodes(statement, Binary, binaries)
        for number in numbers:
            if not (I64_MIN <= number.value <= I64_MAX):
                raise SemanticError(
                    f"Numeric literal {number.value} is outside the i64 range "
                    f"(line {number.string}).")
        for binary in binaries:
            if binary.op != "/":
                continue
            divisor = _constant_int(binary.right)
            dividend = _constant_int(binary.left)
            if divisor == 0:
                raise SemanticError(f"Division by zero (line {binary.string}).")
            if dividend == I64_MIN and divisor == -1:
                raise SemanticError(f"Signed i64 division overflow (line {binary.string}).")


def compile(source: str, emit_ir=False) -> str:
    tokens = Lexer(source).tokens()
    ast = Parser(tokens).parse()
    _check_unique_functions(ast)
    _check_entry_point(ast)
    _check_calls(ast)
    _check_expressions(ast)
    EthicalAnalyzer().check(ast)
    ir_code = Codegen().generate(ast)
    if emit_ir:
        print(ir_code)
    return ir_code


def build_native(ir_code: str, output="kernel.o"):
    for initializer in (
        getattr(llvm, "initialize", None),
        getattr(llvm, "initialize_native_target", None),
        getattr(llvm, "initialize_native_asmprinter", None),
    ):
        if initializer is not None:
            try:
                initializer()
            except Exception:
                pass
    module = llvm.parse_assembly(ir_code)
    module.verify()
    try:
        pmb = llvm.create_pass_manager_builder()
        pmb.opt_level = 2
        pm = llvm.create_module_pass_manager()
        pmb.populate(pm)
        pm.run(module)
    except AttributeError:
        try:
            target_machine = llvm.Target.from_default_triple().create_target_machine()
            pb = llvm.create_pass_builder(target_machine, llvm.PipelineTuningOptions(speed_level=2))
            pb.getModulePassManager().run(module, pb)
        except Exception:
            pass
    target = llvm.Target.from_default_triple().create_target_machine()
    with open(output, "wb") as object_file:
        object_file.write(target.emit_object(module))
    print(f"[YADRO] Native object: {output}")


def main_cli():
    if len(sys.argv) < 2:
        print("Usage: python -m src.main file.yad [--ir]")
        sys.exit(1)
    try:
        with open(sys.argv[1], encoding="utf-8") as source_file:
            source = source_file.read()
        ir_code = compile(source, emit_ir="--ir" in sys.argv)
        if "--ir" not in sys.argv:
            build_native(ir_code)
    except (OSError, EntryPointError, SemanticError, EthicalError,
            ParserError, LexerError, CodegenError, RuntimeError) as error:
        print(f"[YADRO] Compilation error: {error}")
        sys.exit(1)
    print("[YADRO] Compilation complete. Code is law.")


if __name__ == "__main__":
    main_cli()
