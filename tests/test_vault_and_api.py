import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from src import vault

try:                                   # the English mirror ships the vault without the YadroLang checker
    from src import guard_api
except ImportError:
    guard_api = None


@unittest.skipUnless(os.name == "nt", "DPAPI есть только в Windows")
class VaultTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"YADRO_VAULT_DIR": self.folder})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_secret_not_stored_in_plaintext(self):
        token = vault.put("SuperSecret-12345", "УчетныеДанные")
        self.assertTrue(token.startswith("yg_tok_Credentials_"))
        self.assertTrue(token.isascii())
        raw = vault.vault_path().read_text(encoding="utf-8")
        self.assertNotIn("SuperSecret-12345", raw)
        self.assertNotIn("SuperSecret", token)

    def test_issuance_only_with_mandate_and_logged(self):
        token = vault.put("4111-1111", "Финансы")
        with self.assertRaises(vault.VaultError):
            vault.get(token, mandate=False)
        self.assertEqual("4111-1111", vault.get(token, mandate=True, reason="аудит"))
        log = json.loads(vault.vault_path().read_text(encoding="utf-8"))["audit"]
        self.assertEqual(token, log[-1]["token"])

    def test_list_without_values_and_forget(self):
        token = vault.put("x", "ПДн")
        entries = vault.items()
        self.assertEqual(["created", "label", "source", "title", "token"], sorted(entries[0]))
        self.assertNotIn("blob", entries[0])                     # ciphertext is not exposed
        self.assertTrue(vault.forget(token))
        self.assertEqual([], vault.items())

    def test_unknown_label_and_corrupted_blob(self):
        with self.assertRaises(vault.VaultError):
            vault.put("x", "Пароль")
        token = vault.put("x", "ПДн")
        data = json.loads(vault.vault_path().read_text(encoding="utf-8"))
        data["items"][token]["blob"] = "AAAA"
        vault.vault_path().write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(vault.VaultError):
            vault.get(token, mandate=True)


@unittest.skipUnless(os.name == "nt", "DPAPI есть только в Windows")
class VaultManagementTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"YADRO_VAULT_DIR": self.folder})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_file_encrypted_and_saved_as_copy(self):
        data = b"OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwx\n"
        token = vault.put_file(data, "..\\..\\secret<1>.env", "УчетныеДанные")
        raw = vault.vault_path().read_text(encoding="utf-8")
        self.assertNotIn("sk-proj", raw)
        record = [x for x in vault.items(with_trash=True) if x["token"] == token][0]
        self.assertEqual(("file", "secret_1_.env", len(data)), (record["kind"], record["filename"], record["size"]))
        where = Path(self.folder) / "out"
        p1, p2 = vault.save_file(token, where), vault.save_file(token, where)
        self.assertEqual(data, Path(p1).read_bytes())
        self.assertNotEqual(p1, p2)                                  # does not overwrite
        self.assertTrue(Path(p1).resolve().is_relative_to(where.resolve()))   # without leaving the folder
        self.assertIn(("OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwx", "Credentials", "secret_1_.env"),
                      vault.known_values())                          # small file is searched in traffic

    def test_rename_label_replacement_without_token_change(self):
        token = vault.put("old-value-1", "ПДн")
        vault.rename(token, "  Мой ключ  ")
        vault.change_label(token, "Финансы")
        vault.replace(token, "new-value-2")
        z = [x for x in vault.items() if x["token"] == token][0]
        self.assertEqual(("Мой ключ", "Financial"), (z["title"], z["label"]))
        self.assertEqual("new-value-2", vault.get(token, mandate=True))
        with self.assertRaises(vault.VaultError):
            vault.rename(token, "   ")

    def test_trash_restore_and_permanent_deletion(self):
        token = vault.put("trash-me-123456", "ПДн")
        with self.assertRaises(vault.VaultError):
            vault.delete_forever(token)                            # first the trash
        vault.to_trash(token)
        self.assertEqual([], vault.items())
        with self.assertRaises(vault.VaultError):
            vault.get(token, mandate=True)                       # not issued from the trash
        self.assertNotIn("trash-me-123456", [v[0] for v in vault.known_values()])   # remote not searched
        vault.restore(token)
        self.assertEqual(1, len(vault.items()))
        vault.to_trash(token)
        vault.delete_forever(token)
        self.assertEqual([], vault.items(with_trash=True))

    def test_trash_cleared_after_30_days(self):
        token = vault.put("old", "ПДн")
        vault.to_trash(token)
        d = json.loads(vault.vault_path().read_text(encoding="utf-8"))
        d["items"][token]["deleted"] -= 31 * 86400
        vault.vault_path().write_text(json.dumps(d), encoding="utf-8")
        self.assertEqual([], vault.items(with_trash=True))

    def test_operations_via_json_and_limits(self):
        import base64, io
        def op(**k):
            with mock.patch("sys.stdin", io.StringIO(json.dumps(k))):
                return vault.operation_json()
        r = op(op="file", data=base64.b64encode(b"hello").decode(), filename="a.txt", label="PII")
        self.assertEqual("ok", r["status"])
        self.assertEqual("ok", op(op="rename", token=r["token"], title="x")["status"])
        self.assertEqual("error", op(op="replace", token=r["token"], secret="y")["status"])  # file not text
        self.assertEqual("error", op(op="nope")["status"])
        self.assertEqual("error", op(op="file", data="!!!", filename="a", label="PII")["status"])
        with self.assertRaises(vault.VaultError):
            vault.put_file(b"x" * (vault.MAX_FILE + 1), "big.bin", "ПДн")


class FailClosedVaultTests(unittest.TestCase):
    def test_without_encryption_fails_and_file_not_written(self):
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.dict(os.environ, {"YADRO_VAULT_DIR": folder}), \
                mock.patch.object(vault, "_cipher_available", return_value=False):
            with self.assertRaises(vault.VaultError):
                vault.put("secret", "ПДн")
            self.assertFalse(vault.vault_path().exists())


@unittest.skipIf(guard_api is None, "src/guard_api.py is not part of this repo")
class GuardApiTests(unittest.TestCase):
    def file(self, text, name="p.яд"):
        p = Path(tempfile.mkdtemp()) / name
        p.write_text(text, encoding="utf-8")
        return str(p)

    def test_leak_gives_human_labels_quarantine_and_autofix(self):
        r = guard_api.analyze(self.file("функ старт() требует [ДоступСети] {\n  пусть к = среда.секрет()\n  вернуть сеть.отправить(к)\n}"))
        self.assertEqual("leak", r["status"])
        self.assertEqual("Учётные данные и ключи", r["labels"][0]["label"])
        self.assertEqual("отправку в сеть", r["sink"]["human"])
        self.assertTrue(r["quarantine"][0]["options"])
        self.assertTrue(r["autofix"]["verified"])

    def test_english_source_and_response(self):
        code = "fn main() requires [NetworkAccess] {\n  let key = env.secret()\n  # \"env.secret\" in text\n  return net.send(key)\n}\n"
        r = guard_api.analyze_text(code, "en")
        self.assertEqual("leak", r["status"])
        self.assertEqual("en", r["code_language"])
        self.assertEqual(4, r["line"])                         # user source line number
        self.assertEqual("YADRO-E2301", r["code"])
        self.assertEqual("net.send", r["sink"]["name"])
        self.assertEqual("Credentials & keys", r["labels"][0]["label"])
        self.assertEqual("encrypt", r["autofix"]["wrapper"])
        self.assertIn('"env.secret" in text', r["autofix"]["fixed_code"])  # comment untouched
        self.assertEqual("ok", guard_api.analyze_text(r["autofix"]["fixed_code"], "en")["status"])
        self.assertTrue(r["known_gaps"])                      # fair limits always visible

    def test_empty_and_broken_code_honest_error(self):
        with self.assertRaises(guard_api.InputError):
            guard_api.analyze_text("   ", "en")
        r = guard_api.analyze_text("fn main( {", "en")
        self.assertEqual("error", r["status"])
        self.assertTrue(r["message"].startswith("Syntax error"))

    def test_english_report_escapes(self):
        r = guard_api.report_text('fn main() { return 0 }\n# <script>alert(1)</script>', "en")
        self.assertEqual("ok", r["status"])
        self.assertNotIn("<script", r["html"].lower())
        self.assertIn("No leaks found", r["html"])
        self.assertIn("Honest limits", r["html"])

    def test_fix_writes_file_that_passes(self):
        path = self.file("функ старт() требует [ДоступСети] { вернуть сеть.отправить(пользователь.данные()) }")
        r = guard_api.fix(path)
        self.assertEqual("fixed", r["status"])
        self.assertEqual("ok", guard_api.analyze(r["written"])["status"])

    def test_foreign_extension_rejected(self):
        self.assertEqual("error", guard_api.analyze(self.file("x", "secrets.txt"))["status"])

    def test_cli_always_one_json_and_codes(self):
        import contextlib, io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = guard_api.main(["scan", self.file("функ старт() { вернуть 0 }")])
        self.assertEqual(0, code)
        self.assertEqual("ok", json.loads(out.getvalue())["status"])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(3, guard_api.main(["bogus"]))
        json.loads(out.getvalue())


if __name__ == "__main__":
    unittest.main()
