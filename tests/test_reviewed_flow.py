"""Behavioral regressions found while reviewing the preserved fix branches."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from src.main import compile
from src.ethics import EthicalError
from src.typesys import TypeCheckError

from src.guard_cli import run

class ReviewedFlowTests(unittest.TestCase):
    def test_helper_branch_assignment(self):
        with self.assertRaises(EthicalError):
            compile('fn helper(value, flag) requires [NetworkAccess] { let x = 0 if flag { x = value } else { x = 0 } net.send(x) return 0 } fn main() requires [NetworkAccess] { helper(user.data(), 1) return 0 }')

    def test_helper_branch_control(self):
        with self.assertRaises(EthicalError):
            compile('fn helper(flag) requires [NetworkAccess] { let x = 0 if flag { x = 1 } net.send(x) return 0 } fn main() requires [NetworkAccess] { helper(user.data()) return 0 }')

    def test_transitive_control_summary(self):
        with self.assertRaises(EthicalError):
            compile('fn relay(flag) requires [NetworkAccess] { if flag { emit() } return 0 } fn emit() requires [NetworkAccess] { net.send(1) return 0 } fn main() requires [NetworkAccess] { relay(user.data()) return 0 }')

    def test_entry_return(self):
        with self.assertRaises(EthicalError):
            compile('fn main() { return env.secret() }')

    def test_entry_helper_return(self):
        with self.assertRaises(EthicalError):
            compile('fn helper() { return env.secret() } fn main() { return helper() }')

    def test_entry_implicit_return(self):
        with self.assertRaises(EthicalError):
            compile('fn main() { if env.secret() { return 1 } else { return 0 } }')

    def test_entry_implicit_assignment(self):
        with self.assertRaises(EthicalError):
            compile('fn helper() { return 1 } fn main() { let s = env.secret() let k = 0 if s { k = helper() } return k }')

    def test_helper_branch_sanitization(self):
        compile('fn helper(value, flag) requires [NetworkAccess] { if flag { value = anonymize(value) } else { value = anonymize(value) } net.send(value) return 0 } fn main() requires [NetworkAccess] { helper(user.data(), 1) return 0 }')

    def test_entry_sanitized_return(self):
        compile('fn main() { return anonymize(user.data()) }')

    def test_entry_clean(self):
        compile('fn main() { print(1) }')

    def test_audit_checks_entry_output(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'case.yad'
            path.write_text('fn main() { return env.secret() }', encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            self.assertEqual(2, run(["audit", str(path), "--format", "json"], stdout, stderr))
            self.assertEqual('YADRO-E2301', json.loads(stderr.getvalue())["code"])

    def test_missing_return_rejected_before_codegen(self):
        with mock.patch("src.main.Codegen") as backend:
            with self.assertRaises(TypeCheckError):
                compile('fn helper(x) { if x { return 1 } } fn main() { return helper(1) }')
            backend.assert_not_called()
