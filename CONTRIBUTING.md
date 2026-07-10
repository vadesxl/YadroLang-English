# Contributing to YadroLang

Thank you for your interest in contributing to YadroLang!

## How to Contribute

### Reporting Bugs

1. Check existing [issues](https://github.com/vadesxl/YadroLang-English/issues)
2. Open a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - YadroLang version and OS

### Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `python -m pytest` (if applicable)
5. Ensure CI passes: all examples in `examples/` must compile or reject as expected
6. Submit a Pull Request

### Adding Test Cases

New `.yad` examples are always welcome! Place them in `examples/` and add corresponding CI steps in `.github/workflows/run.yml`.

### Code Style

- Python code: PEP 8
- YadroLang examples: use descriptive filenames (e.g., `implicit_flow_leak.yad`)
- Comments in English for this repository

## Project Structure

```
src/
  lexer.py      - Tokenizer
  syntax.py     - Parser (AST)
  ethics.py     - Ethical Analyzer v2.0
  codegen.py    - LLVM IR generator
  main.py       - CLI entry point
examples/       - Test cases (.yad files)
std/            - Standard library
```

## License

By contributing, you agree that your contributions will be licensed under GPL-3.0.
