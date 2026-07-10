# YadroLang inferred type system

YadroLang infers `i64`, `bool`, and `string` before LLVM generation. Arithmetic requires `i64`; comparisons return `bool`; assignment cannot change a variable's type. `if` and `while` accept `bool` plus documented legacy `i64` truthiness. Functions infer parameter and return types across calls and recursion. Mixed returns and unreachable statements are rejected with stable `YADRO-T2xxx` diagnostics.

LLVM ABI v1 uses typed storage, stable hashed user/extern symbols, terminator-safe blocks, and verifies every generated module before returning IR.
