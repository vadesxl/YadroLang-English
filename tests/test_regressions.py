import unittest

from src.main import compile, SemanticError
from src.ethics import EthicalError


class CompilerRegressionTests(unittest.TestCase):
    def test_duplicate_function_is_rejected(self):
        source = "fn helper() { return 1 } fn helper() { return 2 } fn main() { return 0 }"
        with self.assertRaisesRegex(SemanticError, "declared more than once"):
            compile(source)

    def test_builtin_arity_is_checked(self):
        with self.assertRaisesRegex(SemanticError, "print.*expects 1"):
            compile("fn main() { return print() }")
        with self.assertRaisesRegex(SemanticError, "anonymize.*expects 1"):
            compile("fn main() { return anonymize() }")

    def test_constant_expression_division_by_zero_is_rejected(self):
        with self.assertRaisesRegex(SemanticError, "Division by zero"):
            compile("fn main() { return 10 / (3 - 3) }")

    def test_explicit_leak_fails_for_the_right_reason(self):
        source = """
        fn main() requires [NetworkAccess] {
            let secret = user.data()
            return net.send(secret)
        }
        """
        with self.assertRaisesRegex(EthicalError, "Data leak"):
            compile(source)

    def test_implicit_leak_fails_for_the_right_reason(self):
        source = """
        fn main() requires [NetworkAccess] {
            let secret = user.data()
            if secret > 0 { net.send(1) }
            return 0
        }
        """
        with self.assertRaisesRegex(EthicalError, "Implicit information flow"):
            compile(source)

    def test_sanitized_flow_compiles(self):
        source = """
        fn main() requires [NetworkAccess] {
            let secret = user.data()
            let clean = anonymize(secret)
            return net.send(clean)
        }
        """
        self.assertIn("define", compile(source))


if __name__ == "__main__":
    unittest.main()
