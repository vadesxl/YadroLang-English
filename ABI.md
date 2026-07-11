# Native ABI v1

Yadro Guard emits C-compatible, collision-resistant symbols:

- user functions: `yadro_fn_<readable>_<sha256-prefix>`
- policy/runtime functions: `yadro_abi_v1_<readable>_<sha256-prefix>`
- native process entry remains `main`

The readable segment is diagnostic only; the 16-hex SHA-256 prefix binds the complete UTF-8 source name. Parameters and returns use inferred LLVM scalar types. Policy sources, sinks and sanitizers currently return signed i64. Boolean values stay i1 internally and follow inferred signatures.

Each external source name has exactly one signature per module. A mismatch fails code generation. Native smoke tests compile Yadro source, emit an object, link C runtime stubs, execute the binary, and verify output on Ubuntu, Windows and macOS.

## Windows toolchain contract

Windows native object generation requires a supported `clang` LLVM toolchain in `PATH`. Yadro passes verified LLVM IR to clang with the host target triple, enforces a finite 30-second object-emission timeout, and rejects output without AMD64 COFF machine magic (`0x8664`). The C linker and native smoke executable also have finite timeouts. Missing compilers are hard failures, never skipped tests.

The installed clang must accept the LLVM IR emitted by the installed llvmlite version. A version mismatch or timeout is reported as a controlled compilation error.

Runtime stubs are test fixtures, not a trusted sanitizer implementation. Declassification remains a compile-time policy decision.
