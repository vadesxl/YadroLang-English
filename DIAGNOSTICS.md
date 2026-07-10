# Diagnostics

Stable families:

- `YADRO-T1xxx`: type and reachability errors.
- `YADRO-E21xx`: reserved policy symbols.
- `YADRO-E22xx`: capability mandate violations.
- `YADRO-E23xx`: explicit/interprocedural/implicit information-flow violations.
- `YADRO-E29xx`: bounded-analysis convergence failures.
- `YADRO-MCP-23xx`: MCP sensitive-flow violations.
- `YADRO-MCP-24xx`: excessive agency.

CLI exits: 0 success, 2 policy violation, 3 source/policy-format error, 4 internal compiler error.
