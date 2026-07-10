# YadroLang type system

YadroLang infers a minimal static type for every expression before LLVM code generation.

- `i64`: integer literals, arithmetic, system APIs and legacy fallthrough.
- `bool`: `true`, `false`, equality and ordered comparisons.
- `string`: string literals and variables; currently supported by `print`.

Arithmetic accepts only `i64`. Ordered comparisons accept only `i64` and return `bool`. Equality requires matching non-string operands. Function parameter and return types are inferred across call sites, including recursion. Assignments cannot change a variable's type. Statements after an unconditional return are rejected.

For source compatibility, `if` and `while` accept `bool` and legacy `i64` truthiness (`0` is false, non-zero is true). String truthiness is forbidden.
