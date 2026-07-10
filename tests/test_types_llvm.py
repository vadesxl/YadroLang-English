import unittest
from llvmlite import binding as llvm
from src.main import compile
from src.typesys import TypeCheckError


class TypesAndLLVMTests(unittest.TestCase):
    def verified(self, source):
        text = compile(source); module = llvm.parse_assembly(text); module.verify(); return text

    def test_bool_literals_and_comparison(self):
        self.verified("fn main() { let x = true if x { return 1 } else { return 0 } }")
        self.verified("fn main() { if 2 > 1 { return 1 } return 0 }")

    def test_string_printing(self):
        self.verified('fn main() { print("hello") return 0 }')

    def test_mixed_arithmetic_rejected(self):
        with self.assertRaisesRegex(TypeCheckError, "requires i64"):
            compile("fn main() { return true + 1 }")

    def test_string_condition_rejected(self):
        with self.assertRaisesRegex(TypeCheckError, "condition"):
            compile('fn main() { if "x" { return 1 } return 0 }')

    def test_mixed_returns_rejected(self):
        with self.assertRaisesRegex(TypeCheckError, "return type"):
            compile('fn main() { if true { return 1 } else { return "x" } }')

    def test_unreachable_after_return_rejected(self):
        with self.assertRaisesRegex(TypeCheckError, "unreachable"):
            compile("fn main() { return 1 print(2) }")

    def test_nested_call_and_recursion(self):
        self.verified("fn id(x) { return x } fn twice(x) { return id(id(x)) } fn main() { return twice(2) }")
        self.verified("fn down(x) { if x > 0 { return down(x - 1) } return 0 } fn main() { return down(3) }")


if __name__ == "__main__": unittest.main()
