# YadroLang type system

The strict semantic layer has three source types: `i64`, `bool`, and `string`.

- Numeric literals and system APIs are `i64`.
- Arithmetic requires two `i64` operands.
- Comparisons require `i64` operands and produce `bool`.
- Conditions accept `bool`; legacy `i64` truthiness remains supported (`0` false, non-zero true).
- Function parameters use the stable ABI v1 type `i64` until typed parameter syntax is introduced.
- Function returns are inferred and must agree on every path.
- `bool` is lowered to `i64` at the ABI boundary.
- String literals are supported as direct `print` arguments. Storing, returning, or passing strings is rejected with a migration diagnostic until the string ABI is finalized.
- Statements after a guaranteed return are rejected as unreachable.

This keeps the language small and clear while preventing LLVM type mismatches.
