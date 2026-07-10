# Semantic surface parity

`spec/semantic_surface.json` is a machine-readable contract for the public semantic surface shared by the Russian and English prototypes. It covers normalized keyword roles, AST categories, types, built-in roles, capabilities, diagnostic families, CLI commands, and exit codes. Localized spellings are intentionally excluded from equality.

This check does **not** prove full compiler equivalence, identical LLVM IR, identical diagnostics, or behavioral equivalence for every program. Paired fixtures and compiler tests remain required.

## CI trust model

The workflow compares the current checkout with an explicitly pinned commit of the Russian repository. It also requires both copies of `tools/check_parity.py` to have the same SHA-256 digest before using the validator. Network data is therefore tied to a reviewed immutable Git commit, not a moving branch.

Any semantic contract or validator change must be made in both repositories. After both PRs merge, update each workflow's counterpart commit pin in a follow-up synchronization PR. The scheduled and manual runs continuously verify the last mutually reviewed contract pair.
