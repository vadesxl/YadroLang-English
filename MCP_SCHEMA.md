# Yadro Guard MCP security manifest v1.0

This is a **Yadro-specific static security schema**, not a universal importer for every MCP server configuration.

Root fields are exactly `version`, `tools`, and optional `flows`. Unknown fields fail closed.

Each tool has:
- `name`: unique non-empty string
- `labels`: optional sensitive output labels
- `sanitizes`: labels removed at this node
- `capabilities`: one or more known privileged effects

Supported labels: PII, Financial, Health, Credentials, Location.
Supported capabilities: NetworkAccess, DiskWrite, DatabaseWrite, DatabaseRead, ToolExecution, SecretAccess, LogAccess.

Flows are `[source, target]` edges. Cycles are supported by a bounded finite-lattice fixpoint. Output is deterministic text, JSON, or SARIF 2.1.0. Unknown tools, edges, labels, capabilities, duplicate tools, and unknown fields are rejected.
