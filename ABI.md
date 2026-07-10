# LLVM ABI v1

- User symbols: deterministic `yadro_fn_v1_*` mangling.
- Entry implementation: `yadro_entry_v1_*`; native wrapper remains C `main`.
- External symbols: deterministic `yadro_ext_v1_*` mangling.
- Values at storage, function argument, and return boundaries are i64.
- Transient comparison values are i1 and zero-extended at ABI boundaries.
- Strings are internal constant byte arrays and currently only accepted as direct `print` literals.
- One external policy symbol has one arity per module; mismatches are compile errors.
