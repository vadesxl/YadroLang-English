# Benchmarks

`python benchmarks/run.py` reports median and p95 milliseconds for full compile-to-verified-IR, Ethical Analyzer, and MCP graph scan. CI runs on GitHub-hosted Ubuntu with Python 3.11 and pinned llvmlite 0.43.0.

Numbers are directional engineering baselines, not hardware-independent performance claims. The JSON schema is `yadro-benchmark-1.0`; a measured baseline is committed only after CI execution.
