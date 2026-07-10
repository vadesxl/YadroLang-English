# Yadro Guard CLI

```bash
python -m src.guard version
python -m src.guard scan examples/test.yad
python -m src.guard scan examples/leak.yad --format json
python -m src.guard scan examples/leak.yad --format sarif
python -m src.guard audit examples/safe.yad
python -m src.guard compile examples/test.yad -o kernel.o
python -m src.guard policy check policies/example.json
```

## Exit codes

- `0`: success
- `2`: policy violation
- `3`: source, syntax, semantic, filesystem, or policy-format error
- `4`: internal compiler error

## Policy format

Version `1.0` JSON policies may add sources, sinks, and label-specific sanitizers. Labels are restricted to the built-in finite lattice: `PII`, `Financial`, `Health`, `Credentials`, and `Location`.

SARIF output follows SARIF 2.1.0 and is suitable for GitHub Code Scanning upload.
