# YadroLang security and production audit

## Executive verdict

YadroLang is a credible research prototype, not yet a production systems language. Its strongest commercial asset is the compile-time policy engine: capabilities, explicit data-flow tracking, and implicit-flow rejection before LLVM code generation.

## Fixed in this hardening branch

- Duplicate function declarations are rejected before symbol-table collapse.
- Built-in source, sink, sanitizer, and `print` arity is validated.
- Constant-expression division by zero and `INT64_MIN / -1` are rejected.
- Code generation and filesystem failures produce controlled compiler diagnostics.
- Regression tests assert the exact security failure class, so a Python crash can no longer masquerade as a successful security block.
- Tests run on Linux, Windows, and macOS.

## High-priority remaining risks

1. `COMPLIANCE` is declared but sanitizers currently declassify every label. Declassification must become label-specific.
2. Return summaries retain only tainted/clean state and lose the concrete label.
3. The type system is effectively i64-only; strings are special-cased and memory ownership is unspecified.
4. External system APIs are declarations without a versioned runtime ABI.
5. The shell-heavy legacy CI should migrate to structured unit and integration tests.
6. Russian and English frontends are duplicated and can drift.

## Commercial recommendation

Sell **Yadro Guard**, not another general-purpose language: a compile-time policy compiler for AI agents and MCP tools that emits native code plus signed JSON/SARIF evidence. Keep YadroLang as the reference policy language and LLVM-backed execution core.
