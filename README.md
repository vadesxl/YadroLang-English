# YadroLang (Kernel)

[![CI](https://github.com/vadesxl/YadroLang-English/actions/workflows/run.yml/badge.svg)](https://github.com/vadesxl/YadroLang-English/actions/workflows/run.yml)
[![Release](https://img.shields.io/github/v/release/vadesxl/YadroLang-English)](https://github.com/vadesxl/YadroLang-English/releases/latest)

> "Code is law. Good is a choice."

An experimental systems programming language, English-facade prototype, for building safe and ethical AI. Compiles to native code via LLVM.

This is a translated mirror of [vadesxl/YadroLang](https://github.com/vadesxl/YadroLang) — same architecture and logic, English keywords/identifiers/messages.

## Philosophy (Immutable laws)

- **Sovereignty** — native compilation via LLVM. No VM, no GC, no interpreter at runtime.
- **Safety** — a built-in Ethical Analyzer rejects unethical AI patterns at compile time.
- **Clarity** — strict, concise syntax.

## Compiler pipeline

```
.yad -> Lexer -> Parser (AST) -> Ethical Analyzer -> CodeGen -> LLVM IR -> native binary
```

## Features (v1.2)

- Functions, variables, if/else, while, recursion
- Built-in `print` via printf (real stdout output)
- Native entry-point autogeneration: the program compiles into an ELF binary and runs
- String printing: `print("Hello, world")` via %s/printf
- Ethical Analyzer: capability mandates `requires [...]` + interprocedural flow-based taint analysis
- Sources of personal data, sanitizers, and sinks — a formal leak model

## Example

```
fn main() {
    print(double(21))
    return factorial(5)
}
```

## Build & run

Requirements: Python 3.11+ and llvmlite.

```bash
pip install -r requirements.txt
git clone https://github.com/vadesxl/YadroLang-English.git
cd YadroLang-English

# Build native object file
python -m src.main examples/test.yad

# Print LLVM IR
python -m src.main examples/test.yad --ir
```

## Ethical mandates

Dangerous system APIs are only reachable from a function whose signature explicitly declares the matching mandate, checked transitively up to the entry point:

```
fn export(data) requires [DiskWrite] {
    check_safety(data)
    return file.write(data)
}
```

No mandate → compile error. No data sanitization → compile error (taint error).

## Three demonstrations of the analyzer

- `examples/no_mandate.yad` — missing `[NetworkAccess]` mandate → mandate error
- `examples/leak.yad` — mandate present, but personal data leaves without sanitization → taint error
- `examples/safe.yad` — mandate + sanitizer `anonymize(...)` → compiles

Sources of personal data (`user.data()`, `file.read()`, ...) taint values. Taint propagates through assignments and operations. A tainted value can only reach a sink (network/disk) after passing through a sanitizer (`anonymize(...)`, `check_consent(...)`, ...). Otherwise — compile error.

## Release

Mirrors upstream **v1.4.0 — Codegen hardening**:

- 11 fixes (5 security + 6 correctness)
- ~33 CI checks
- Ethical Analyzer: capability mandates + personal-data taint analysis

## License

GPL-3.0 (same as the upstream Russian-language project).
