# Yadro Guard roadmap after 2.1.0

Document status: engineering plan, not a claim that listed features or dates are delivered.

## Positioning

Yadro Guard checks a specific versioned policy before native object generation and produces auditable results within its implemented semantics. It does not prove the absence of every leak, verify arbitrary external code, or replace runtime security.

## Implemented in 2.1.0

- `yadro-guard` CLI with `scan`, `audit`, `compile`, and JSON policy validation;
- JSON/SARIF diagnostics;
- capability mandates, multi-label taint, and bounded interprocedural analysis;
- Yadro MCP tool-graph scanning;
- verified LLVM IR and native object emission;
- Linux, macOS, and Windows CI.

The exact status and limitations live in [FEATURE_STATUS.md](FEATURE_STATUS.md) and [THREAT_MODEL.md](THREAT_MODEL.md). Proof Seal is currently implemented in the Russian repository, not this English facade.

## Phase A: close current compiler gaps

- land return-path soundness for every non-entry helper path;
- mirror the accepted string memory model before implementation;
- implement `{ptr, i64}`, bounded printing, and exact UTF-8 lengths in separate reviewed work;
- expand Lexer, Parser, semantic-analysis, and CodeGen fuzz/adversarial corpora;
- execute documentation examples in CI.

## Phase B: restore measured frontend parity

- differential fixtures for Russian and English source pairs;
- shared semantic expectations for diagnostics, LLVM shape, and native behavior;
- explicit parity exceptions when a feature has not landed in both repositories;
- Proof Seal parity only after the Russian compiler-integration contract is stable.

Similar file or API names are not parity evidence. Each behavior needs a differential test.

## Phase C: strengthen trust

- reproducible package artifacts;
- authenticated evidence envelope as a separate layer from consistency checking;
- independently reviewed framework adapters with explicit trust boundaries;
- exact-head security reviews and published residual risks.

## Long-term production-readiness criteria

Production readiness may be claimed only after a documented support model, reproducible releases, supply-chain controls, fuzzing and coverage evidence, an independent audit, stable ABI/diagnostic policy, and closure of known high/critical findings. The current project is experimental.

## Commercial hypothesis

Target users are AI platform engineering, AppSec, and regulated product teams. Value must be demonstrated through reproducible blocked-attack scenarios, explicit false-positive/false-negative boundaries, and independently verifiable evidence. Pricing, SLA, SSO, retention, and on-prem packaging are not implemented product capabilities today.

## Do not fake progress

Do not clone Rust/C++, expand syntax without semantic need, present design as implementation, or publish a security claim without a test or proof on the current exact head.
