# YadroLang (English Prototype)

English-facade prototype of YadroLang — a systems language with a compiler-level "Ethical Analyzer" (interprocedural taint analysis, capability mandates, UB prevention).

This is a translated mirror of the original Russian-language project. Core logic is identical; keywords, identifiers, and messages are in English.

## Usage
```
python -m src.main file.yad          # build native object file kernel.o
python -m src.main file.yad --ir     # print LLVM IR
```

## Language keywords
`fn`, `main`, `let`, `if` / `else`, `while`, `return`, `requires [NetworkAccess]`, `print`
