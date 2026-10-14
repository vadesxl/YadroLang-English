import unittest
from src.runtime import detectors as d

# Synthetic values collected at runtime: not in the source
# whole tokens, so GitHub secret scanners don't raise an alarm.
GH = "gh" + "p_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
AWS = "AK" + "IA" + "QWERTYUIOP123456"
GOOGLE = "AI" + "za" + "Sy" + "A" * 10 + "b" * 10 + "C" * 13
CARD = "4111 1111 1111 1111"
IBAN = "CH93 0076 2011 6238 5295 7"


def kinds(text, **kw):
    return [f.kind for f in d.scan_text(text, **kw)]


class DetectorTests(unittest.TestCase):
    def test_provider_tokens(self):
        self.assertEqual(["github_token"], kinds(f"curl -H 'x: {GH}' api"))
        self.assertEqual(["aws_access_key"], kinds(f"key={AWS}"))
        self.assertEqual(["google_api_key"], kinds(f"?k={GOOGLE}"))

    def test_bypasses_found_redteam_deepseek(self):
        # AWS: other key prefixes and secret key (DeepSeek V4 review).
        self.assertEqual(["aws_access_key"], kinds("id=AID" + "A" + "QWERTYUIOP123456"))
        self.assertEqual(["aws_access_key"], kinds("AROA" + "ABCDEFGHIJKLMNOP"))
        secret = "wJalrXUtnFEMI/K7MDENG/bPxRfiCY" + "EXAMPLEKEY"
        f = d.scan_text(f"aws_secret_access_key = {secret}")
        self.assertEqual(["aws_secret_key"], [x.kind for x in f])
        self.assertEqual(secret, f[0].value)

    def test_card_only_with_valid_checksum(self):
        self.assertEqual(["card_number"], kinds(f"pay {CARD} now"))
        self.assertEqual([], kinds("order 4111 1111 1111 1112"))        # Luhn doesn't check out
        self.assertEqual([], kinds("phone 0000 0000 0000 0000"))        # garbage

    def test_iban_with_mod97(self):
        self.assertEqual(["iban"], kinds(f"to {IBAN}"))
        self.assertEqual([], kinds("to CH93 0076 2011 6238 5295 8"))

    def test_password_in_url_and_bearer(self):
        self.assertEqual(["password_in_url"], kinds("postgres://admin:Sup3rS3cret@db:5432/x"))
        f = d.scan_text("Authorization: Bearer abcDEF123ghiJKL456mnoPQR789stu")
        self.assertEqual("generic_secret", f[0].kind)

    def test_low_entropy_and_examples_not_detected(self):
        self.assertEqual([], kinds("password = aaaaaaaaaaaaaaaaaaaa"))
        self.assertEqual([], kinds("api_key = your_api_key_here_please"))

    def test_vault_secret_takes_priority(self):
        f = d.scan_text("send my-own-value-42 now", known_secrets=[("my-own-value-42", "Credentials", "")])
        self.assertEqual(["vault_secret"], [x.kind for x in f])
        self.assertEqual("certain", f[0].confidence)

    def test_preview_masks_value(self):
        f = d.scan_text(f"x {GH}")[0]
        self.assertNotIn(GH, str(f.public()))
        self.assertTrue(f.preview.startswith("ghp_") and "***" in f.preview)

    def test_nested_arguments_and_editing(self):
        args = {"url": "https://api.x", "headers": {"Authorization": f"token {GH}"}, "body": [f"card {CARD}"]}
        f = d.scan_args(args)
        self.assertEqual({"headers.Authorization", "body[0]"}, {x.path for x in f})
        clean = d.redact_args(args, f, lambda f: "[REDACTED]")
        self.assertEqual("token [REDACTED]", clean["headers"]["Authorization"])
        self.assertEqual("card [REDACTED]", clean["body"][0])
        self.assertEqual(f"token {GH}", args["headers"]["Authorization"])  # original untouched
        self.assertEqual([], d.scan_args(clean))


if __name__ == "__main__":
    unittest.main()
