# Semantic surface parity

`spec/semantic_surface.json` is a machine-readable contract for the public semantic surface shared by the Russian and English prototypes. It covers normalized keyword roles, AST categories, types, built-in roles, capabilities, diagnostic families, CLI commands, and exit codes. Localized spellings are intentionally excluded from equality.

This check does **not** prove full compiler equivalence, identical LLVM IR, identical diagnostics, or behavioral equivalence for every program. Paired fixtures and compiler tests remain required.

## Two separate signals

`snapshot-parity` is the mandatory reproducible check. It compares the current checkout with one reviewed, immutable counterpart commit and verifies that both copies of `check_parity.py` are byte-identical. Green means this exact pair of snapshots has the same declared surface. It does not mean both live `main` branches are currently equal.

`pin-freshness` reads only counterpart Git reference metadata with `git ls-remote`; it never checks out or executes moving-branch code. A stale pin emits a visible warning so pin rot cannot stay silent, while the security-sensitive parity result remains reproducible.

Both checkout steps use `persist-credentials: false`; workflow permissions are `contents: read`; Python 3.11 is explicitly provisioned.

## Coordinated update runbook

1. Prepare matching contract and validator changes in both repositories and test the candidate pair locally.
2. Merge each reviewed contract PR only after its ordinary platform CI passes.
3. Open reciprocal pin-update PRs using the resulting immutable merge SHAs.
4. Require `snapshot-parity` and the normal Linux, macOS, and Windows checks on both pin PRs.
5. Merge the reciprocal pins and run each workflow manually once. A later counterpart-only commit may make freshness warn again without invalidating the reviewed snapshot pair.

Never replace the immutable counterpart ref with a moving branch in `snapshot-parity`.
