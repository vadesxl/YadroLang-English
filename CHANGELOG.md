# Changelog

## [2.1.0] - 2026-07-10

### Ethical Analyzer v2.1
- Label-preserving interprocedural return and parameter summaries.
- Multi-label propagation, PC-label implicit-flow tracking, and bounded fixpoints.
- Label-specific declassification with SANITIZED audit records.
- Reserved source/sink/sanitizer spoof protection and stable diagnostic codes.
- Sound branch joins and zero-iteration loop-carried labels.

### Compiler and LLVM
- Inferred `i64`, `bool`, and restricted `string` semantics.
- Bool literals, mixed-type rejection, unreachable statement detection, and recursive inference fixpoint.
- LLVM ABI v1 symbol mangling, extern arity validation, terminator-safe blocks, bool normalization, and verification on every successful compile.

### Product
- Installable `yadro-guard` and `yadro-guard-mcp` console commands.
- Source scan/compile/audit/policy/version commands with isolated custom policies.
- Text, JSON, and SARIF 2.1.0 with stable exit codes.
- Yadro MCP tool-graph schema scanner for sensitive flows and excessive agency.
- Threat model, policy/MCP/ABI/diagnostic specs, feature matrix, bounded fuzz corpus, and measured benchmarks.

### Benchmarks
GitHub-hosted Ubuntu medians: compile to verified IR 1.4378 ms, Ethical Analyzer 0.1742 ms, MCP scan 0.4222 ms.

## [2.0.0] - 2026-07-10
Compiler hardening, reason-specific security regression tests, cross-platform CI, production audit, and commercial roadmap.
