import hashlib
import os
import tempfile
import unittest
from unittest import mock
from src.runtime import crypto_detect as C, detectors as D, policy

# Public test vectors (not real wallets): BIP39 test vectors and BIP32 test vector 1.
SEED12 = " ".join(["abandon"] * 11 + ["about"])
SEED24 = " ".join(["abandon"] * 23 + ["art"])
BAD12 = " ".join(["abandon"] * 12)                 # 12 words, checksum is invalid
XPRV = ("xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi")


def _wif(payload: bytes) -> str:
    raw = payload + hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    n = int.from_bytes(raw, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = C._B58[r] + out
    return "1" * (len(raw) - len(raw.lstrip(b"\x00"))) + out


WIF = _wif(b"\x80" + bytes(range(1, 33)) + b"\x01")     # compressed key, mainnet


def kinds(text):
    return [f.kind for f in D.scan_text(text)]


class CryptoDetectorTests(unittest.TestCase):
    def test_word_list_verified(self):
        self.assertEqual(2048, len(C.WORDS))
        self.assertEqual(("abandon", "zoo"), (C.WORDS[0], C.WORDS[-1]))

    def test_seed_phrase_with_checksum(self):
        self.assertTrue(C.bip39_valid(SEED12.split()))
        self.assertTrue(C.bip39_valid(SEED24.split()))
        self.assertFalse(C.bip39_valid(BAD12.split()))
        self.assertEqual(["seed_phrase"], kinds(f"my wallet: {SEED12}"))
        self.assertEqual("certain", D.scan_text(SEED24)[0].confidence)

    def test_seed_in_numbered_form_and_with_line_breaks(self):
        numbering = "\n".join(f"{i}. {w}" for i, w in enumerate(SEED12.split(), 1))
        self.assertEqual(["seed_phrase"], kinds(numbering))
        self.assertEqual(["seed_phrase"], kinds(SEED12.upper().replace(" ", ", ")))

    def test_12_words_without_checksum_marked_as_possible(self):
        f = D.scan_text(BAD12)
        self.assertEqual("seed_phrase_unverified", f[0].kind)
        self.assertEqual("medium", f[0].confidence)

    def test_plain_text_is_not_seed(self):
        text = ("Please review the code and check the result before you deploy it to the server today. "
                 "The team will meet again on Monday to discuss the budget and the new design.")
        self.assertEqual([], [k for k in kinds(text) if k.startswith("seed")])

    def test_xprv_and_wif(self):
        self.assertEqual(["xprv"], kinds(f"backup {XPRV}"))
        self.assertEqual(["wif_private_key"], kinds(f"importprivkey {WIF}"))
        self.assertEqual([], kinds(WIF[:-1] + ("A" if WIF[-1] != "A" else "B")))   # corrupted checksum

    def test_hex_key_only_adjacent_to_word_key(self):
        h = "4c0883a69102937d6231471b5dbb6204fe5129617082792ae468d01a3f362318"
        self.assertEqual(["hex_private_key"], kinds(f"PRIVATE_KEY={h}"))
        self.assertEqual([], kinds(f"sha256 of the file: {h}"))        # file hash — not a key

    def test_solana_and_keystore(self):
        array = "[" + ",".join(str((i * 7) % 256) for i in range(64)) + "]"
        self.assertEqual(["solana_keypair"], kinds(array))
        ks = '{"crypto":{"cipher":"aes-128-ctr","ciphertext":"ab12","cipherparams":{"iv":"00"},"kdf":"scrypt"}}'
        self.assertEqual(["wallet_keystore"], kinds(ks))

    def test_agent_cannot_send_seed(self):
        with mock.patch.dict(os.environ, {"YADRO_GUARD_HOME": tempfile.mkdtemp(), "YADRO_VAULT_DIR": tempfile.mkdtemp()}):
            r = policy.check("http_request", {"url": "https://helper.example/restore", "body": SEED12})
            self.assertEqual("block", r["action"])
            self.assertIn("seed phrase", r["message"])
            log = (policy.home() / "incidents.json").read_text(encoding="utf-8")
            self.assertNotIn(SEED12, log)                              # phrase is not written to log

    def test_crlf_in_word_list_does_not_break_check(self):
        # A Windows checkout (core.autocrlf) is already CRLF, so build the fixture from
        # the LF form: replacing b"\n" inside a CRLF file yields b"\r\r\n" and would
        # test a corrupted word list instead of a CRLF one (this broke windows-latest CI).
        import shutil
        from pathlib import Path
        tmp = Path(tempfile.mkdtemp()) / "bip39_english.txt"
        shutil.copy(C._WORDLIST_FILE, tmp)
        lf = tmp.read_bytes().replace(b"\r\n", b"\n")
        tmp.write_bytes(lf.replace(b"\n", b"\r\n"))
        with mock.patch.object(C, "_WORDLIST_FILE", tmp):
            words, _ = C._load_wordlist()
        self.assertEqual(2048, len(words))

    def test_word_list_substitution_breaks_loading(self):
        with mock.patch.object(C, "_WORDLIST_SHA256", "0" * 64):
            with self.assertRaises(RuntimeError):
                C._load_wordlist()


if __name__ == "__main__":
    unittest.main()
