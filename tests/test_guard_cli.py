import io
import json
import tempfile
import unittest
from pathlib import Path
from src.guard import run, EXIT_OK, EXIT_POLICY, EXIT_SOURCE


class GuardCliTests(unittest.TestCase):
    def source(self, text):
        handle = tempfile.NamedTemporaryFile("w", suffix=".yad", delete=False, encoding="utf-8")
        handle.write(text); handle.close(); return handle.name

    def test_json_policy_violation_and_exit_code(self):
        path = self.source("fn main() requires [NetworkAccess] { return net.send(user.data()) }")
        out, err = io.StringIO(), io.StringIO()
        self.assertEqual(EXIT_POLICY, run(["scan", path, "--format", "json"], out, err))
        self.assertEqual("YADRO-E2301", json.loads(err.getvalue())["code"])

    def test_sarif_violation_and_success_are_valid(self):
        bad = self.source("fn main() requires [NetworkAccess] { return net.send(user.data()) }")
        out, err = io.StringIO(), io.StringIO()
        self.assertEqual(EXIT_POLICY, run(["scan", bad, "--format", "sarif"], out, err))
        self.assertEqual("2.1.0", json.loads(err.getvalue())["version"])
        good = self.source("fn main() { return 0 }")
        out, err = io.StringIO(), io.StringIO()
        self.assertEqual(EXIT_OK, run(["scan", good, "--format", "sarif"], out, err))
        self.assertEqual([], json.loads(out.getvalue())["runs"][0]["results"])

    def test_invalid_policy_has_source_exit(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            handle.write('{"version":"9"}'); path = handle.name
        self.assertEqual(EXIT_SOURCE, run(["policy", "check", path], io.StringIO(), io.StringIO()))

    def test_custom_policy_is_applied_and_then_reset(self):
        source = self.source("fn main() requires [ToolExecution] { return agent.execute(crm.customer()) }")
        policy = Path(tempfile.mkstemp(suffix=".json")[1])
        policy.write_text(json.dumps({"version":"1.0", "sources":{"crm.customer":"PII"},
                                      "sinks":{"agent.execute":"ToolExecution"}}), encoding="utf-8")
        self.assertEqual(EXIT_POLICY, run(["scan", source, "--policy", str(policy)], io.StringIO(), io.StringIO()))
        plain = self.source("fn main() { return crm.customer() }")
        self.assertEqual(EXIT_SOURCE, run(["scan", plain], io.StringIO(), io.StringIO()))


if __name__ == "__main__": unittest.main()
