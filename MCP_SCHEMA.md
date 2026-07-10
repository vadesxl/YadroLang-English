# Yadro MCP tool-graph schema v1.0

This is a Yadro-owned analysis schema, not a claim of universal MCP manifest compatibility.

```json
{"version":"1.0","tools":[{"name":"crm.read","labels":["PII"]},{"name":"net.send","capabilities":["NetworkAccess"]}],"flows":[["crm.read","net.send"]]}
```

Each tool may declare `labels`, `sanitizes`, and `capabilities`. `flows` contains directed name pairs. The scanner validates duplicate/unknown tools, computes a bounded finite-label fixpoint across cycles, reports sensitive data reaching privileged capabilities, and flags tools with three or more dangerous capabilities as excessive agency.
