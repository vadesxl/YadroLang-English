# Native ABI v1

Yadro Guard emits C-compatible, collision-resistant symbols:

- user functions: `yadro_fn_<readable>_<sha256-prefix>`
- policy/runtime functions: `yadro_abi_v1_<readable>_<sha256-prefix>`
- native process entry remains `main`

The readable segment is diagnostic only; the 16-hex SHA-256 prefix binds the complete UTF-8 source name. Parameters and returns use inferred LLVM scalar types. Policy sources, sinks and sanitizers currently return signed i64. Boolean values stay i1 internally and follow inferred signatures.

Each external source name has exactly one signature per module. A mismatch fails code generation. Native smoke tests compile Yadro source, emit an object, link C runtime stubs, execute the binary, and verify output on Ubuntu, Windows and macOS.

Runtime stubs are test fixtures, not a trusted sanitizer implementation. Declassification remains a compile-time policy decision.
