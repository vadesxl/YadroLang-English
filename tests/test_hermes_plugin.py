import asyncio
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "integrations" / "hermes" / "yadro-guard"


def _load_api(plugin_folder):
    spec = importlib.util.spec_from_file_location("yg_plugin_api", plugin_folder / "dashboard" / "plugin_api.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class HermesPluginTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        (self.folder / "dashboard").mkdir()
        (self.folder / "dashboard" / "plugin_api.py").write_text(
            (PLUGIN / "dashboard" / "plugin_api.py").read_text(encoding="utf-8"), encoding="utf-8")
        (self.folder / "config.json").write_text(
            json.dumps({"engine_home": str(ROOT), "python": sys.executable}), encoding="utf-8")
        self.api = _load_api(self.folder)

    def body(self, code, title=""):
        return self.api.CodeBody(code=code, title=title)

    def test_manifest_like_hermes(self):
        m = json.loads((PLUGIN / "dashboard" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("yadro-guard", m["name"])
        for key in ("entry", "css", "api", "tab"):
            self.assertIn(key, m)
        for file in (m["entry"], m["css"], m["api"]):
            self.assertTrue((PLUGIN / "dashboard" / file).exists(), file)

    @unittest.skipUnless((ROOT / "src" / "guard_api.py").exists(), "YadroLang checker is not part of this repo")
    def test_analysis_of_pasted_code_and_history_without_code(self):
        code = "fn main() requires [NetworkAccess] {\n  let key = env.secret()\n  return net.send(key)\n}"
        r = asyncio.run(self.api.analyze(self.body(code, "payment agent")))
        self.assertEqual("leak", r["status"])
        self.assertEqual("Credentials & keys", r["labels"][0]["label"])
        self.assertTrue(r["autofix"]["verified"])
        history = asyncio.run(self.api.history())["items"]
        self.assertEqual("payment agent", history[0]["title"])
        self.assertNotIn("env.secret", json.dumps(history))   # the code itself is not written to history

    def test_empty_code_and_broken_secret_are_rejected(self):
        self.assertEqual("error", asyncio.run(self.api.analyze(self.body("   ")))["status"])
        bad = self.api.SecretBody(secret="x", label="Passwords")
        self.assertEqual("error", asyncio.run(self.api.vault_put(bad))["status"])

    def test_without_config_honest_error(self):
        (self.folder / "config.json").unlink()
        self.assertEqual("error", asyncio.run(self.api.analyze(self.body("fn main() { return 0 }")))["status"])
        self.assertFalse(asyncio.run(self.api.health())["configured"])

    def test_frontend_without_dangerous_constructs(self):
        import re
        js = (PLUGIN / "dashboard" / "dist" / "index.js").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/", "", js, flags=re.S)   # no comments
        self.assertNotIn("dangerouslySetInnerHTML", code)
        self.assertNotIn("innerHTML", code)
        self.assertNotIn("eval(", code)
        self.assertIn('sandbox: ""', js)              # report in iframe without scripts
        self.assertIn('register("yadro-guard"', js)

    def test_csrf_foreign_site_cannot_click_buttons(self):
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient
        except Exception:
            self.skipTest("FastAPI не установлен (есть внутри Hermes)")
        app = FastAPI()
        app.include_router(self.api.router, prefix="/p")
        c = TestClient(app)
        body = '{"incident":"YG-NONE","choice":"allow"}'
        def code(**h):
            return c.post("/p/incidents/decide", content=body, headers=h).status_code
        self.assertEqual(403, code(**{"content-type": "text/plain", "origin": "https://evil.example"}))
        self.assertEqual(403, code(**{"content-type": "application/json", "origin": "https://evil.example",
                                     "x-yadro-guard": "1"}))
        self.assertEqual(403, code(**{"content-type": "application/json", "origin": "http://127.0.0.1:9119"}))
        self.assertEqual(200, code(**{"content-type": "application/json", "origin": "http://127.0.0.1:9119",
                                     "x-yadro-guard": "1"}))
        self.assertEqual(200, code(**{"content-type": "application/json"}))      # Hermes Desktop (without Origin)
        self.assertEqual(200, c.get("/p/health").status_code)

    def test_desktop_half_assembled_and_within_sdk(self):
        import re, subprocess
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "build_desktop_plugin.py"), "--check"],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(0, r.returncode, r.stdout)
        js = (PLUGIN / "desktop" / "plugin.js").read_text(encoding="utf-8")
        imports = set(re.findall(r'^import .*? from "([^"]+)";', js, flags=re.M))
        self.assertEqual({"react", "@hermes/plugin-sdk"}, imports)
        self.assertIn('export default {', js)
        self.assertNotIn("eval(", js)
        self.assertNotIn("innerHTML", js)

    def test_interface_renders_and_decision_is_sent(self):
        import shutil, subprocess
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js не установлен")
        r = subprocess.run([node, str(ROOT / "tests" / "js" / "render_guard_page.mjs"),
                            str(PLUGIN / "dashboard" / "dist" / "index.js")],
                           capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(0, r.returncode, r.stderr or r.stdout)


if __name__ == "__main__":
    unittest.main()
