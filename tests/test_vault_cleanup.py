# -*- coding: utf-8 -*-
"""The vault cleanup tool must remove paths and keep real secrets."""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("vault_cleanup_paths", ROOT / "tools" / "vault_cleanup_paths.py")
CLEANUP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLEANUP)

from src import vault  # noqa: E402


class VaultCleanupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"YADRO_VAULT_DIR": self.tmp})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_path_records_are_trashed_and_secrets_kept(self):
        if not vault._cipher_available():
            self.skipTest("DPAPI is only available on Windows")
        path_hinted = vault.put("E:/repo/integrations/hermes/yadro-guard/__init__.py", "УчетныеДанные",
                                "A path to a sensitive local file (env, ssh keys, wallet, guard state)")
        path_untitled = vault.put("C:\\Users\\me\\secrets\\prod.env", "УчетныеДанные", "")
        real_key = vault.put("sk-proj-" + "A1b2C3d4" * 5, "УчетныеДанные", "OpenAI Secret Key")
        url_secret = vault.put("https://user:pass@example.com/hook", "УчетныеДанные", "Password inside a URL")

        plan = CLEANUP.scan()
        tokens = {c["token"] for c in plan["candidates"]}
        self.assertEqual({path_hinted, path_untitled}, tokens)

        CLEANUP.apply_trash(sorted(tokens))
        left = {i["token"] for i in vault.items()}
        self.assertEqual({real_key, url_secret}, left)
        trashed = {i["token"] for i in vault.items(with_trash=True) if i.get("deleted")}
        self.assertEqual({path_hinted, path_untitled}, trashed)

    def test_dry_run_changes_nothing(self):
        if not vault._cipher_available():
            self.skipTest("DPAPI is only available on Windows")
        token = vault.put("E:/tmp/secret.txt", "УчетныеДанные", "path")
        CLEANUP.main([])
        self.assertIn(token, {i["token"] for i in vault.items()})


if __name__ == "__main__":
    unittest.main()
