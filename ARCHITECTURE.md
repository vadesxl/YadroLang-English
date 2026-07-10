# Architecture

`source -> Lexer -> Parser/AST -> semantic checks -> type inference -> Ethical Analyzer -> LLVM CodeGen -> verified IR -> native object`

Yadro Guard adds two product surfaces:

- `src.guard`: source scan/compile/audit, custom JSON policy, JSON and SARIF diagnostics.
- `src.mcp_guard`: static analysis of the versioned Yadro MCP tool-graph schema.

The Ethical Analyzer uses a finite sensitivity lattice, label-preserving return/parameter summaries, PC labels for implicit flow, and bounded fixpoints. LLVM ABI v1 normalizes booleans to i64 across storage/call/return boundaries and mangles user/extern symbols deterministically.
