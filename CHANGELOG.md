# Changelog

All notable changes to YadroLang English are documented here.

## [2.0.0] - 2026-07-10

### Security
- Fixed invalid AST line-field access in the Ethical Analyzer.
- Security regression tests now assert the exact failure reason, preventing Python crashes from masquerading as successful policy blocks.
- Added explicit and implicit information-flow regression coverage.

### Compiler
- Reject duplicate function declarations before symbol-table construction.
- Validate arity for built-in sources, sinks, sanitizers, and `print`.
- Detect computed constant division by zero.
- Detect signed i64 division overflow for `INT64_MIN / -1`.
- Convert filesystem, LLVM, and code-generation failures into controlled diagnostics.

### CI
- Added deterministic regression tests on Ubuntu, Windows, and macOS.
- Added timeouts and concurrency cancellation to avoid stale or duplicated runs.
- Preserved the full legacy YADRO CI suite.

### Product
- Added a production-readiness audit.
- Added the 30-day Yadro Guard commercial roadmap.
