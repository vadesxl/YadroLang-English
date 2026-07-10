import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

class PackagingSubprocessTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "src.guard_cli", *args], text=True, capture_output=True, check=False)

    def test_version_entry_point(self):
        result = self.run_cli("--version")
        self.assertEqual(0, result.returncode)
        self.assertIn("2.1.0", result.stdout)

    def test_type_error_is_source_error_not_internal(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yad", delete=False, encoding="utf-8") as handle:
            handle.write('fn main() { return true + 1 }'); path = handle.name
        result = self.run_cli("scan", path, "--format", "json")
        self.assertEqual(3, result.returncode)
        self.assertIn("YADRO-T", json.loads(result.stderr)["message"])

    def test_unknown_and_builtin_collision_policy_fail_closed(self):
        cases = [
            {"version":"1.0", "unknown":{}},
            {"version":"1.0", "sources":{"user.data":"PII"}},
        ]
        for data in cases:
            policy = Path(tempfile.mkstemp(suffix=".json")[1]); policy.write_text(json.dumps(data), encoding="utf-8")
            result = self.run_cli("policy", "check", str(policy))
            self.assertEqual(3, result.returncode)

if __name__ == "__main__": unittest.main()
