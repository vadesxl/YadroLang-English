# Yadro Guard threat model

## Assets
Sensitive labels, policy files, agent/MCP capability graphs, compiler integrity, LLVM output, and audit evidence.

## Trust boundaries
Untrusted YadroLang source and MCP-schema JSON enter the trusted compiler/analyzer process. Custom policy files extend built-ins but never replace validation. LLVM and the native linker are downstream trusted components.

## Attacker capabilities
An attacker may craft source, identifiers, deep expressions, recursive calls, malformed manifests, cyclic tool graphs, policy collisions, aliases, branch/loop side channels, and sanitizer spoofing.

## In scope
Explicit and control-flow leaks, confused deputy paths, excessive agency, malformed input, policy tampering through unsupported symbols, compiler crashes, deterministic termination, and cross-platform behavior.

## Out of scope
Microarchitectural side channels, malicious LLVM/toolchains, runtime compromise after compilation, semantic correctness of external sanitizer implementations, and general import of arbitrary vendor MCP formats.

## Controls
Finite label lattice, capability mandates, strict declassification, bounded fixpoints, reserved symbols, strict inferred types, verified LLVM IR, schema validation, deterministic diagnostics, and CI across three operating systems.

## Residual risks
External ABI implementations are not shipped yet; sanitizer semantics require organizational assurance; i64 arithmetic is not checked for every dynamic overflow; MCP support uses the documented Yadro schema, not every MCP dialect.
