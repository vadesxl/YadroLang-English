# Yadro Proof Seal v1

Status: normative design until public v1 freeze, not an implemented command and not a release claim.

## Purpose and scope

The Yadro Proof Seal (`.yproof`) is a deterministic compile-time evidence artifact. It links successful policy analysis to a verified LLVM module and the exact bytes of a native object. The Seal proves only a versioned policy contract relative to the listed assumptions — not general AI ethicality, not completeness, and not a whole-program formal proof.

V1 core is unsigned. Self-digest detects corruption/mismatch, but not authenticity or provenance. Machine-readable trust state: `{"mode":"unsigned","authenticity":"not-provided"}`. `inspect` is not a security gate. DSSE/Sigstore is a future separate phase.

## Pipeline

```text
source -> parse -> semantics/types -> Ethical Checker -> immutable evidence
                                                       |
                                    LLVM CodeGen -> parse/verify
                                                       |
                                      native object -> exact digest
                                                       |
                                    canonical seal -> atomic write
```

The Seal is absent on policy violation, LLVM failure, or object emission failure.

## Two-stage verifier dispatch

Verifier bounded preflight:

1. reads no more than 1 MiB;
2. parses JSON with duplicate-key rejection and depth 16;
3. extracts only `schema`, `subject.policy_schema_version`, `subject.llvm_normalization_version` as bounded strings;
4. selects the exact validator/canonicalizer tuple;
5. an unsupported tuple yields a controlled version diagnostic;
6. then full strict validation runs with unknown-field rejection.

Preflight does not accept a proof as valid and does not hash it.

## Deterministic core

Schema: `yadro-proof-seal-1.0`.

Canonical bytes:

- UTF-8 without BOM, exactly one trailing LF;
- strings are NFC Unicode scalar sequences, surrogate code points forbidden;
- object keys sorted by Unicode code point;
- compact separators, non-ASCII emitted directly;
- integers only `0..9007199254740991`, floats forbidden;
- duplicate/unknown fields forbidden;
- semantic sets unique and sorted by canonical UTF-8 bytes;
- `call_sites` and `assumptions` sorted by `id`;
- no timestamps, hostnames, usernames, or absolute paths.

`seal_sha256` is excluded from the payload:

```text
SHA-256("YADRO-PROOF-SEAL\0" || "1.0\0" || canonical_payload_without_seal_sha256)
```

Received document bytes must match the canonical encoding. Self-digest is not authentication.

## Bounds

V1: seal 1 MiB, depth 16, 10,000 call sites, 256 entries, 2,000 assumptions, 32 values per semantic set, 256 UTF-8 bytes per identifier, 512 UTF-8 bytes per diagnostic module path. Bounds are checked before proportional allocation.

## Subject binding

Subject stores visible `policy_schema_version = yadro-policy-1.0`, `llvm_normalization_version = yadro-llvm-normalization-1.0`, exact source/policy/normalized LLVM/artifact SHA-256, target triple, and artifact kind. The verifier never substitutes current defaults.

Without source/IR, the verifier independently confirms only the available bindings; source/LLVM/analysis remain compiler attestations whose authenticity depends on the trust mode.

## Stable evidence identities

Module ID:

```text
SHA-256("YADRO-MODULE\0" || frontend || "\0" || exact_source_bytes)
```

A serialized call site contains `id`, `module_id`, `semantic_kind`, `caller`, `callee`, `span`, semantic evidence sets, and `status`. `compiler.frontend` is taken from the top-level compiler identity and is not duplicated. The V1 semantic-kind vocabulary contains one stable non-localized value: `call`.

Call-site ID:

```text
SHA-256("YADRO-CALL-SITE\0" || frontend || "\0" || module_id || "\0" || caller || "\0" || callee || "\0" || semantic_kind || "\0" || start_byte || "\0" || end_byte || "\0" || ordinal)
```

This formula matches the shared Phase 1 implementation: the domain separator already contains a terminal NUL, then identity fields are joined with a single NUL. `module_id` is lowercase SHA-256. `semantic_kind` must be `call`. The verifier reconstructs the inputs and compares the serialized/computed ID via constant-time comparison.

Assumption ID:

```text
SHA-256("YADRO-ASSUMPTION\0" || canonical_assumption_without_id)
```

The old pre-freeze draft without `module_id`/`semantic_kind` was unverifiable and is intentionally not supported. This is a schema correction before the public v1 freeze.

Span invariants: `start_byte <= end_byte`, offsets and ordinal are in the safe-integer range. Mapping a span to a source node remains a compiler attestation while a source-free verifier has no source bytes.

A diagnostic module path is not an identity, uses `/`, is relative, and forbids empty, `.`/`..`, controls, drive, and UNC segments.

## Evidence model

Typed immutable evidence comes from the Ethical Checker. Each reachable effectful call records content-bound identity/span, caller/callee ABI, reachable entries, required/declared capabilities, incoming/outgoing labels, sanitizers/declassification, policy rules, implicit labels, assumptions, and `allowed` status. A violation produces diagnostics and no seal.

An external assumption stores content ID, ABI symbol/signature, capability, taint transform, trusted-sanitizer flag, ownership/lifetime, no-retain, and optional implementation digest. The compiler proves properties only relative to these assumptions.

## Identity is not completeness

The verifier confirms the identity of only the recorded call sites. A malicious or buggy producer can still omit evidence. Completeness requires future compiler integration and coverage invariants. `verify_bytes` confirms consistency, not authenticity. No part of the v1 unsigned seal claims production readiness or a formal proof of general ethicality.

## Offline verifier

The verifier uses no network, no plugins, and does not execute the artifact. It checks schema, bounds, NFC/scalars, ordering, paths, content IDs, canonical bytes, self/policy/artifact digests, and bounded object headers. ELF/Mach-O/COFF format/machine must match the artifact kind and target triple. Filename is not proof.

## Exit classes

`0` structural/binding match with trust state; `2` compile-time policy violation; `3` malformed/unsupported/mismatch; `4` internal failure.

## Required tests

- byte-identical canonical output and golden domain vectors;
- every array rejects unsorted/duplicate values;
- version preflight before strict schema;
- NFC, surrogates, duplicate/unknown fields, truncation, size/depth, and non-canonical bytes fail in a controlled way;
- forged call-site ID with recomputed outer seal fails;
- mutation of frontend/module/caller/callee/semantic_kind/span/ordinal is detected;
- identity domain separation for module/call-site/assumption;
- path, reference, artifact/policy/target swaps fail;
- Linux/macOS/Windows, no skips, hard failures, and finite timeouts.

## Phases

1. Immutable evidence and canonical serializer.
2. Bounded preflight, strict verifier, and unsigned result.
3. LLVM/object binding and atomic output.
4. Ethical Checker/MCP export and completeness invariants.
5. Standard authenticated envelope and English parity.

Each phase passes a separate exact-head review. This document implements no commands.

