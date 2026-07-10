# YadroLang inferred type system

YadroLang keeps its concise syntax and infers four internal types: `i64`, `bool`, `string`, and `unknown` during constraint solving.

- Number literals and system APIs are `i64`.
- `true` / `false` are `bool`.
- Arithmetic requires `i64`; comparisons return `bool`.
- `if` and `while` accept `bool`, plus legacy `i64` truthiness (`0` false, non-zero true).
- String values are currently restricted to direct `print("...")` literals. Storage, return, comparison, and system-API transport are rejected.
- Function parameter and return types are inferred to a fixpoint. Mixed return types are errors.
- A function with no explicit return keeps the legacy implicit `return 0` behavior.
- Statements after an unconditional return, or after an if/else where both branches return, are rejected.

LLVM ABI v1 normalizes booleans to `i64` at variable, call, and return boundaries while preserving `i1` for transient comparison results.
