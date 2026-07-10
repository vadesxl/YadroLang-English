# Benchmarks

Measured on GitHub-hosted Ubuntu, Python 3.11.15, pinned llvmlite 0.43.0:

| Path | Median | p95 | Rounds |
|---|---:|---:|---:|
| Compile to verified LLVM IR | 1.4378 ms | 2.3291 ms | 40 |
| Ethical Analyzer | 0.1742 ms | 0.2106 ms | 80 |
| MCP graph scan | 0.4222 ms | 0.5283 ms | 120 |

Run `python -m benchmarks.run` to reproduce. These are directional engineering baselines, not hardware-independent performance claims. Machine-readable data lives in `benchmarks/baseline.json` using schema `yadro-benchmark-1.0`.
