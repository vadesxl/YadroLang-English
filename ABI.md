# Native ABI v1

- User functions are mangled as `yadro_fn_<source-name>`.
- The YadroLang entry point `main` is emitted as `yadro_main`; the native wrapper owns symbol `main`.
- System APIs are mangled as `yadro_ext_v1_<qualified_name>` with dots replaced by underscores.
- Parameters and returns use signed i64. Source `bool` is zero-extended at ABI boundaries.
- `printf`, `main`, `yadro_main`, and `ext.*`-prefixed source symbols are reserved.
- An external symbol may have exactly one signature per module. Signature mismatch is a code-generation error.
- String ABI is not yet stable; only direct string printing is supported.
