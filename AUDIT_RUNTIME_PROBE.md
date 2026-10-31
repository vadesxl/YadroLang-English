# mcp-secrets-guard (yadro-guard) — runtime probe of the 5 guard modes

Audit type: black-box runtime probe of the guard backend in a live environment
(no modifications to engine/core logic). Performed 2026-10-31.

Method: a single throwaway `python -c` script switched `set_mode()` through the
real shared mode config in `%LOCALAPPDATA%\yadro-guard` and, for every mode, fed
a synthetic test secret (an API key and a payment card number) into
`policy.check()` (`tool="terminal"`). Every state file (mode config, incident
journal, vault, decisions) was snapshotted before the run and restored in
`finally` so the probe leaves the live state untouched.

## 1. Mode -> `policy.check()` verdict

| Mode | Effective mode | `policy.check()` result | Expected | Verdict |
|---|---|---|---|---|
| `full_protection` | `full_protection` | **BLOCK** (`action=block`, incident `pending`) | block | PASS |
| `monitor` | `monitor` | **ALLOW**, incident recorded with `status=audited` | allow + audit record | PASS |
| `pause_5m` | `pause_5m` | **ALLOW**, instant, `paused_until=now+300s` | instant allow | PASS |
| `pause_15m` | `pause_15m` | **ALLOW**, instant, `paused_until=now+900s` | instant allow | PASS |
| `disabled` | `disabled` | **ALLOW**, instant, `paused_until=0` | instant allow | PASS |

All five branches behave as specified. Code trace confirms:
`monitor` -> early return `None` after `_new_incident(..., status="audited")`
(`src/runtime/policy.py`); `pause_*`/`disabled` -> early allow before detection;
`full_protection`/`active` -> block with quarantine.

## 2. SHA-256 integrity check

The `_EXPECTED_HASHES` in `integrations/hermes/yadro-guard/__init__.py` were
compared against the engine files under `engine_home` (repo root) with the same
CRLF->LF normalization used by `_check_integrity()`.

| File | Expected (head) | Actual (head) | Match |
|---|---|---|---|
| `src/runtime/policy.py` | `b5c26a77` | `b5c26a77` | YES |
| `src/runtime/detectors.py` | `6a687822` | `6a687822` | YES |
| `src/runtime/actions.py` | `bdcf27eb` | `bdcf27eb` | YES |
| `src/runtime/aim_detect.py` | `6782fd03` | `6782fd03` | YES |

Result: 4/4 match (100%).

## Findings / notes (no core logic changed)

- The runtime hook behaves fail-closed and mode-aware as documented.
- In the deployed plugin the `engine_home` is read from
  `integrations/hermes/yadro-guard/config.json`, which is absent in this checkout;
  a missing/empty config makes `_check_integrity()` return `cannot-read-config`
  and (by fail-closed policy) blocks all guarded tools until the plugin is
  configured.
- `monitor` allows the call but still quarantines the detected secret into the
  encrypted vault (same `_quarantine` path used on block); consider this when
  treating "audit" as a pure pass-through.
