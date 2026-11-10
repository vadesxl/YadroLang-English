# YadroLang (Kernel) 2.1.0

[![CI](https://github.com/vadesxl/YadroLang-English/actions/workflows/run.yml/badge.svg)](https://github.com/vadesxl/YadroLang-English/actions/workflows/run.yml)
![Version](https://img.shields.io/badge/version-2.1.0-blue)
![Status](https://img.shields.io/badge/status-experimental-orange)

> “Code is law. Good is a choice.”

YadroLang-English is the experimental English-language facade of YadroLang for building verifiable AI components. It emits LLVM IR and native object files without a VM, interpreter, or garbage collector at runtime.

## What 2.1.0 actually includes

- functions, variables, recursion, `if`/`else`, `while`, and `return`;
- i64/bool type inference and deliberately limited string support;
- a native LLVM backend with final module verification;
- capability mandates for sensitive system operations;
- interprocedural multi-label taint analysis, including implicit control flow;
- strict declassification through known sanitizers;
- JSON/SARIF CLI, custom JSON policies, and Yadro MCP tool-graph analysis;
- cross-platform Linux, macOS, and Windows CI with mandatory native tests.

The English facade follows the Russian project’s architecture, but parity is measured feature by feature. It must not be assumed merely because APIs or documents have similar names.

## Security boundaries

YadroLang rejects formalized violations within its supported semantics. It does not prove that an AI is “ethical,” provide a whole-program formal proof, or guarantee that no vulnerability exists.

The current string backend uses transitional pointer-only `%s` lowering. It is not a complete memory-safe string model: embedded NUL, ownership, and arbitrary string storage/return remain unsupported.

Proof Seal is currently implemented and reviewed in the Russian repository, not in this English facade. Signed provenance, complete evidence coverage, full compiler integration, and microarchitectural side-channel proof are not claimed.

## Pipeline

```text
.yad -> Lexer -> Parser/AST -> Semantics and types -> Ethical Analyzer
     -> LLVM CodeGen -> parse/verify -> native object
```

Compilation fails on syntax, type, policy, or LLVM errors. Unknown sensitive operations should fail closed within the supported policy model.

## Example

```yadrolang
fn double(value) {
    return value * 2
}

fn main() {
    print(double(21))
    return 0
}
```

## Install and run

Requirements: Python 3.11+, `llvmlite==0.43.0`; native linking requires a system C/LLVM toolchain.

```bash
git clone https://github.com/vadesxl/YadroLang-English.git
cd YadroLang-English
python -m pip install -e .

# Verify and print LLVM IR
python -m src.main examples/test.yad --ir

# Emit a native object file
python -m src.main examples/test.yad

# Policy CLI
yadro-guard scan examples/safe.yad --format json
yadro-guard audit examples/safe.yad
yadro-guard-mcp scan path/to/tool-graph.json
```

## Ethical Analyzer

A sensitive API requires an explicit capability mandate checked transitively through the call graph. Sensitive values carry labels such as PII, Financial, Health, Credentials, and Location and cannot reach a prohibited sink without an allowed transformation.

```yadrolang
fn export(data) requires [NetworkAccess] {
    let safe = anonymize(data)
    return network.send(safe)
}
```

This is compile-time enforcement of a specific versioned policy, not a universal moral classifier.

## Documentation

- [Feature status](FEATURE_STATUS.md)
- [Architecture](ARCHITECTURE.md)
- [Threat model](THREAT_MODEL.md)
- [CLI](CLI.md)
- [ABI](ABI.md)
- [Security reporting](SECURITY.md)
- [Roadmap](ROADMAP.md)
- [Semantic parity](SEMANTIC_PARITY.md)

## Project status

**Code and package version: 2.1.0. Status: experimental.** Not claimed: production readiness, complete ownership/string runtime, signed provenance, complete Ethical Analyzer coverage, or protection against every side channel.

License: GPL-3.0-only.
