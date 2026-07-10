import unittest
from src.main import compile
from src.ethics import EthicalError, EthicalAnalyzer
from src.lexer import Lexer
from src.syntax import Parser


class EthicalAnalyzerV21Tests(unittest.TestCase):
    def test_wrong_sanitizer_does_not_clear_financial_label(self):
        source = """
        fn main() requires [NetworkAccess] {
          let card = payment.card()
          let wrong = anonymize(card)
          return net.send(wrong)
        }
        """
        with self.assertRaisesRegex(EthicalError, "Financial"):
            compile(source)

    def test_allowed_sanitizer_clears_financial_label(self):
        source = """
        fn main() requires [NetworkAccess] {
          let card = payment.card()
          let safe = encrypt(card)
          return net.send(safe)
        }
        """
        compile(source)

    def test_return_summary_preserves_concrete_label(self):
        source = """
        fn read_card() { return payment.card() }
        fn main() requires [NetworkAccess] { return net.send(read_card()) }
        """
        with self.assertRaisesRegex(EthicalError, "Financial"):
            compile(source)

    def test_multi_label_return_is_preserved(self):
        source = """
        fn combine(a, b) { return a + b }
        fn main() requires [NetworkAccess] {
          let mixed = combine(user.data(), env.secret())
          return net.send(mixed)
        }
        """
        with self.assertRaises(EthicalError) as caught:
            compile(source)
        self.assertIn("PII", str(caught.exception))
        self.assertIn("Credentials", str(caught.exception))

    def test_sanitization_is_written_to_audit_trail(self):
        source = "fn main() { let x = payment.card() let y = encrypt(x) return y }"
        ast = Parser(Lexer(source).tokens()).parse()
        analyzer = EthicalAnalyzer()
        analyzer.check(ast)
        self.assertTrue(any(entry.status == "SANITIZED" and entry.label == "Financial"
                            for entry in analyzer.audit_trail))

    def test_reserved_policy_symbol_cannot_be_spoofed(self):
        source = "fn anonymize(x) { return 0 } fn main() { return anonymize(user.data()) }"
        with self.assertRaisesRegex(EthicalError, "Reserved policy symbol"):
            compile(source)


if __name__ == "__main__":
    unittest.main()
