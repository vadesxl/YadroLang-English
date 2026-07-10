import io
import json
import tempfile
import unittest
from src.mcp_guard import run, EXIT_OK, EXIT_POLICY


class McpGuardTests(unittest.TestCase):
    def manifest(self, data):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(data, handle); handle.close(); return handle.name

    def test_pii_exfiltration(self):
        path = self.manifest({"version":"1.0", "tools":[
            {"name":"crm.read", "labels":["PII"]},
            {"name":"net.send", "capabilities":["NetworkAccess"]}],
            "flows":[["crm.read","net.send"]]})
        self.assertEqual(EXIT_POLICY, run(["scan", path], io.StringIO(), io.StringIO()))

    def test_credential_leak_and_excessive_agency(self):
        path = self.manifest({"version":"1.0", "tools":[
            {"name":"vault.read", "labels":["Credentials"]},
            {"name":"agent.run", "capabilities":["NetworkAccess","ToolExecution","SecretAccess"]}],
            "flows":[["vault.read","agent.run"]]})
        out = io.StringIO(); self.assertEqual(EXIT_POLICY, run(["scan", path, "--format", "json"], out, io.StringIO()))
        codes = {item["code"] for item in json.loads(out.getvalue())["findings"]}
        self.assertEqual({"YADRO-MCP-2301","YADRO-MCP-2401"}, codes)

    def test_safe_sanitized_flow(self):
        path = self.manifest({"version":"1.0", "tools":[
            {"name":"crm.read", "labels":["PII"]},
            {"name":"privacy.redact", "sanitizes":["PII"]},
            {"name":"net.send", "capabilities":["NetworkAccess"]}],
            "flows":[["crm.read","privacy.redact"],["privacy.redact","net.send"]]})
        self.assertEqual(EXIT_OK, run(["scan", path], io.StringIO(), io.StringIO()))


if __name__ == "__main__": unittest.main()
