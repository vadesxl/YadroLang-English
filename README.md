# YadroLang English 2.1.0

[![CI](https://github.com/vadesxl/YadroLang-English/actions/workflows/run.yml/badge.svg)](https://github.com/vadesxl/YadroLang-English/actions/workflows/run.yml)
[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](pyproject.toml)
[![License](https://img.shields.io/badge/license-GPL--3.0--only-green.svg)](LICENSE)

> "Code is law. Good is a choice."

YadroLang English is the experimental English-language implementation lane of YadroLang for policy-checked AI agents and MCP tool graphs. It compiles through LLVM to native object code, with no VM, interpreter, or garbage collector at runtime.

**Status:** research prototype. Version 2.1.0 is not a production-readiness, formal-completeness, or invulnerability claim.

## Implemented in 2.1.0

- functions, variables, recursion, `if/else`, `while`, and `return`;
- inference for i64, bool, and limited string values;
- verified LLVM IR and native object files for Linux, macOS, and Windows;
- compile-time capability mandates for sensitive system APIs;
- interprocedural multi-label taint analysis, implicit-flow/PC labels, and strict declassification;
- `scan`, `audit`, and `compile` CLI commands with JSON, SARIF, and versioned custom policies;
- bounded Yadro MCP tool-graph analysis;
- external ABI v1 with stable hashed symbols;
- cross-platform unit, native, wheel, build, and benchmark CI.

This repository shares architecture with the Russian implementation but is an independent development lane. Features and security fixes may land at different commits. Do not assume byte-for-byte or release parity.

## Pipeline

```text
.yad -> Lexer -> Parser/AST -> semantics/types -> Ethical Checker -> LLVM IR verify -> native object
```

## Example

```yadro
fn double(value) {
    return value * 2
}

fn main() {
    print(double(21))
    return 0
}
```

## Quick start

Requirements: Python 3.11+, `llvmlite==0.43.0`; Windows native object generation requires a supported LLVM/Clang toolchain.

```bash
git clone https://github.com/vadesxl/YadroLang-English.git
cd YadroLang-English
python -m pip install -e .

python -m src.guard version
python -m src.guard scan examples/safe.yad
python -m src.guard audit examples/safe.yad
python -m src.guard compile examples/test.yad --ir
python -m src.guard compile examples/test.yad -o kernel.o
```

See [CLI.md](CLI.md) for the command contract and exit codes, [FEATURE_STATUS.md](FEATURE_STATUS.md) for feature status, and [ABI.md](ABI.md) for the native boundary.

## Ethical Checker model

Sensitive sinks require declared capabilities. Data labels propagate through values, calls, returns, and control flow. A sanitizer removes only its explicitly allowed labels. Unknown or unproved transitions must fail closed.

This is a static, versioned policy model, not a universal proof of ethical behavior. It does not cover arbitrary native/FFI behavior, a malicious compiler, supply-chain compromise, runtime memory corruption, microarchitectural side channels, or mistakes in the policy itself.

## Honest limitations

- current string lowering is a transitional pointer-only `%s` implementation, not a complete memory-safe string model;
- no GC, VM, full ownership system, dynamic policy, or arbitrary vendor MCP manifest import;
- no claim of whole-program formal proof or complete attack coverage;
- the Russian Proof Seal implementation is not yet an English feature;
- protection is defense in depth, not an absolute boundary;
- new security claims require reproducible adversarial tests.

Return-path soundness is being reviewed separately and must not be treated as merged until its exact PR head is accepted. Checked arithmetic and the string memory model also require separate implementation and review lanes.

## Testing

Security and native checks must not turn green through `skip`; a missing mandatory toolchain is a failure.

```bash
python -m unittest discover -s tests -v
python -m benchmarks.run
```

## Security

A bypass is a defect, not "incorrect usage." A useful report includes a minimal reproducible input, expected and actual behavior, version/commit, platform, and threat model. Never put real credentials or personal data in an issue.

Priority audit surfaces include parser/AST direct construction, Unicode and canonicalization, integer boundaries, FFI assumptions, LLVM poison/ABI mismatches, evidence omission, resource exhaustion, malformed object formats, and cross-platform semantic drift.

## License

GPL-3.0-only. See [LICENSE](LICENSE).
