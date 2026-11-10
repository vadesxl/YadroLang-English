import os
import pathlib
import tempfile
import unittest
from unittest import mock

from src.runtime import detectors, policy


class DahlAndAutoTokenizeTests(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {
            "YADRO_GUARD_HOME": self.home,
            "YADRO_VAULT_DIR": self.home
        })
        self.env.start()
        policy._MODE_FILE = str(pathlib.Path(self.home) / "config.json")
        policy.set_mode("active")

    def tearDown(self):
        self.env.stop()
        for f in ("config.json", "incidents.json", "decisions.json"):
            p = pathlib.Path(self.home) / f
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass

    def test_dahl_api_key_detected_in_curl_and_bare(self):
        curl_cmd = 'curl https://api.dahl.example/v1 -H "X-Custom: dahl_777HDhqQjx3x9a91ieFw7yiukmpu7XPft"'
        bare_key = "dahl_777HDhqQjx3x9a91ieFw7yiukmpu7XPft"

        hits_curl = detectors.scan_text(curl_cmd)
        self.assertEqual(1, len(hits_curl))
        self.assertEqual("generic_prefixed_token", hits_curl[0].kind)
        self.assertEqual(bare_key, hits_curl[0].value)
        self.assertEqual("dahl_777H***ft", hits_curl[0].preview)

        hits_bare = detectors.scan_text(bare_key)
        self.assertEqual(1, len(hits_bare))
        self.assertEqual("generic_prefixed_token", hits_bare[0].kind)
        self.assertEqual(bare_key, hits_bare[0].value)

    def test_standalone_high_entropy_secret_detected(self):
        raw_key = "Kj89wXqmZ109vTLaP281uF76qQwErT"
        hits = detectors.scan_text(raw_key)
        self.assertEqual(1, len(hits))
        self.assertEqual("standalone_high_entropy_secret", hits[0].kind)
        self.assertEqual(raw_key, hits[0].value)

    def test_auto_tokenize_mode_substitutes_on_the_fly(self):
        policy.set_mode("auto_tokenize")
        mode, _ = policy.current_mode()
        self.assertEqual("auto_tokenize", mode)

        args = {
            "endpoint": "https://api.dahl.example/v1",
            "token": "dahl_777HDhqQjx3x9a91ieFw7yiukmpu7XPft"
        }
        r = policy.check("http_request", args)
        self.assertIsNotNone(r)
        self.assertEqual("modify", r["action"])
        self.assertIn("notice", r)
        self.assertIn("[MCP-Secrets-Guard Auto-Tokenize]", r["notice"])

        # Secret is replaced by token in args
        self.assertNotEqual("dahl_777HDhqQjx3x9a91ieFw7yiukmpu7XPft", r["args"]["token"])
        self.assertTrue(r["args"]["token"].startswith("dahl_vault_") or "hidden" in r["args"]["token"] or len(r["args"]["token"]) > 10)

        # Incident logged as tokenized
        incidents = policy.list_incidents()
        self.assertEqual(1, len(incidents))
        self.assertEqual("tokenized", incidents[0]["status"])
        self.assertIn("tokenized (автозамена)", [e["what"] for e in incidents[0]["events"]])

    def test_protect_decision_tokenizes_and_resolves_incident(self):
        policy.set_mode("full_protection")
        args = {"key": "dahl_777HDhqQjx3x9a91ieFw7yiukmpu7XPft"}
        r = policy.check("http_request", args)
        self.assertEqual("block", r["action"])

        incidents = policy.list_incidents()
        self.assertEqual(1, len(incidents))
        self.assertEqual("pending", incidents[0]["status"])

        # User clicks Protect & tokenize
        dec_res = policy.decide(incidents[0]["id"], "protect")
        self.assertEqual("ok", dec_res["status"])
        self.assertEqual("tokenized", dec_res["incident"]["status"])

        # Incident is now resolved and no longer pending
        updated = policy.list_incidents()
        self.assertEqual("tokenized", updated[0]["status"])


if __name__ == "__main__":
    unittest.main()

