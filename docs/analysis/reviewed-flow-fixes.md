# Reviewed flow and return-path fixes

## Origin

Return-path code and tests come from `restore-return-path-soundness` at `e65241acc735e79ddd66b1b90c026deb46253162`. Its older README and roadmap changes are not carried forward. Control-flow patches 1-6 were already present in `main`; this change repairs gaps found while reviewing that implementation.

## Behavior

- Helper leak summaries join branch exits, preserving direct and implicit labels while allowing label-specific sanitization on both paths.
- Return, parameter-leak and caller-PC summaries converge together, including transitive helper effects that become visible after PC summaries change.
- Sensitive numeric entry results are rejected before LLVM IR. The native wrapper prints the entry result outside the source body, so both direct and implicit return labels require an output check. `audit` checks this output too and is conservative when inferred types are unavailable.
- Helpers must return on every path before the LLVM backend is created. The entry function keeps its documented implicit zero return.
- The CRLF word-list test normalizes its initial fixture before converting to CRLF, avoiding an unintended CRCRLF file on Windows. Runtime integrity validation is unchanged.

## Regressions

`tests/test_ethics_gaps.py`, `tests/test_ethics_gaps_patch456.py`, `tests/test_return_paths.py` and `tests/test_reviewed_flow.py` compile actual source programs or assert the appropriate rejection. Added cases cover branch-assigned helper parameters, implicit helper flows, branch sanitization, joint transitive summaries, numeric entry output and rejection before backend creation.

An older positive control returned a secret-dependent value that the native wrapper printed. The positive case now returns a constant; its original output behavior is retained as a negative regression.

## Limits

This is static analysis of declared policy, not a whole-program noninterference proof or an AI ethics certificate. External sanitizer semantics, ABI implementations and trusted toolchains need independent assurance. The v2.1.0 release tag is unchanged; these are later `main` changes.
