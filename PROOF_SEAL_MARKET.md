# Yadro Proof Seal: market gap

Research date: 2026-07-11. This is an engineering comparison of publicly described capabilities, not vendor certification and not a patent search.

| Category / example | Main control point | MCP | IFC / taint | Exact native artifact binding | Offline verification | Explicit FFI assumptions |
|---|---|---:|---:|---:|---:|---:|
| Cisco MCP Scanner | server/config scan | yes | partial | no | no | no |
| MCP Firewall / MCP Visor | runtime gateway | yes | policy dependent | no | no | no |
| Lakera Agent Security | discovery/runtime protection | yes | runtime context | no | no | no |
| AgentPerms | observed behavior and runtime authorization | yes | no | no | no | no |
| SAST / taint platforms | source/PR scan | varies | yes | usually no | reports, not artifact proof | usually no |
| Sigstore / DSSE / SLSA attestations | supply-chain identity/provenance | agnostic | no | yes | authenticated metadata | no semantic AI flow proof |
| PCAA / proof-derived authorization research | pre-action/runtime certificate | agnostic | contract dependent | sometimes execution binding | model dependent | model dependent |
| Yadro Proof Seal design | compile-time policy evidence | Yadro schema | yes | LLVM + exact object | unsigned structural v1, authenticated future | yes |

## Conclusion

The surveyed sample covers scanning, runtime interception, software provenance, and research action certificates well when taken separately. No direct product analog combining compile-time capability/taint evidence, verified LLVM binding, exact native object binding, offline source-free inspection, and explicit FFI assumptions was found.

Unsigned Proof Seal v1 provides no authenticity and does not protect against coordinated replacement of all inputs. It requires a trusted delivery channel or a future standard authenticated envelope. This is the fundamental difference between structural binding and signed attestation.

## Positioning

Do not say:

- "proves that the AI is good";
- "the whole program is formally proven";
- "replaces runtime security";
- "the only solution in the world";
- "an unsigned proof protects against an active substituting attacker".

Say:

- compile-time evidence for a specific versioned policy contract;
- proof structurally bound to the exact emitted native artifact;
- auditable capabilities, data flows and external assumptions;
- offline inspection without executing the artifact;
- authenticity requires a trusted channel or a future standard envelope;
- no policy evaluation in the application hot path.

## Public reference points

- Cisco AI Defense MCP Scanner: scan MCP servers for threats.
- MCP Firewall and MCP Visor: runtime policy gateway and audit.
- Lakera Agent Security: discovery and real-time agent protection.
- AgentPerms: observed behavior to least-privilege policy.
- Sigstore/DSSE/SLSA: standard supply-chain signing and provenance patterns.
- Research on proof-carrying agent actions, proof-derived authorization and information-flow control for agents.

A refreshed competitor review and legal/patent search are required before any market claim for release.

