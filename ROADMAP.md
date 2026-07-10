# Yadro Guard commercial roadmap

## Positioning

**Promise:** prove before deployment that an AI agent cannot send sensitive data or invoke privileged tools outside policy.

**Buyer:** AI platform engineering, application security, compliance, and regulated product teams.

**Wedge:** CI scanner and policy compiler for MCP/agent tool graphs. Runtime competitors add latency; Yadro Guard provides compile-time evidence with zero policy overhead in the hot path.

## 30-day MVP

### Week 1: Trustworthy compiler
- Structured regression tests and crash-proof diagnostics.
- Label-preserving interprocedural summaries.
- Label-specific declassification policies.
- Fuzz Lexer and Parser; publish coverage and threat model.

### Week 2: Product surface
- `yadro guard scan` CLI.
- Versioned YAML policy format for sources, sinks, labels, capabilities, and sanitizers.
- JSON and SARIF reports for GitHub code scanning.
- Stable diagnostic codes and machine-readable output.

### Week 3: Agent integrations
- MCP manifest and tool-call graph importer.
- Python and TypeScript adapters for popular agent frameworks.
- Three demos: PII exfiltration, secret leakage, and excessive agency.
- Signed audit evidence with policy/compiler versions.

### Week 4: Pilot-ready release
- Reproducible binaries for Windows, Linux, and macOS.
- Benchmarks, installation docs, sample policies, and migration guide.
- Free open-source CLI; paid team policy packs and on-prem enterprise build.
- Recruit 3 design partners in finance, healthcare, and internal developer platforms.

## Pricing hypothesis

- Community: free CLI and core policies.
- Team: EUR 499/month for CI, SARIF, shared policies, and support.
- Enterprise: from EUR 15k/year for on-prem, custom policy packs, SSO, audit retention, and SLA.

## Non-goals for the MVP

Do not clone Rust/C++, build a package ecosystem, or expand syntax for its own sake. Commercial proof comes from blocked agent attacks, low false-positive rates, and audit evidence buyers can trust.
