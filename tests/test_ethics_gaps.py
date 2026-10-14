# -*- coding: utf-8 -*-
"""Behavioral regressions for the issue #47 leaks (control-flow aware).

`test_patches_quick.py` used to only grep for strings in the compiler source
(`"| pc_labels" in source`) instead of exercising behavior. These tests check
the REAL behavior of the compiler: every hole must now be cut off.

Holes (from AUDIT_REPORT section 2.2):
  1. print(env.secret())           - print as an output sink (PATCH 1)
  2. if s { x = 1 } -> net.send(x) - implicit flow through an assignment (PATCH 2)
  3. helper: if flag { return 1 }  - implicit flow through a return (PATCH 3)
"""
import unittest

from src.main import compile
from src.ethics import EthicalError


class EthicsGapTests(unittest.TestCase):
    def test_print_leaks_secret_block(self):
        # PATCH 1: print is an output sink; a secret into print is a leak.
        code = "fn main() { print(env.secret()) }"
        with self.assertRaisesRegex(EthicalError, "Credentials"):
            compile(code)

    def test_implicit_flow_through_assignment_block(self):
        # PATCH 2: a variable assigned under a sensitive condition is tainted.
        code = (
            "fn main() requires [NetworkAccess] {\n"
            "  let x = 0\n"
            "  if env.secret() { x = 1 }\n"
            "  return net.send(x)\n"
            "}"
        )
        with self.assertRaisesRegex(EthicalError, "Credentials"):
            compile(code)

    def test_implicit_flow_through_helper_return_block(self):
        # PATCH 3: a return under a sensitive condition carries the control context.
        code = (
            "fn helper(flag) { if flag { return 1 } return 0 }\n"
            "fn main() requires [NetworkAccess] {\n"
            "  let s = env.secret()\n"
            "  return net.send(helper(s))\n"
            "}"
        )
        with self.assertRaises(EthicalError):
            compile(code)

    # --- control: baseline behavior does NOT regress ---

    def test_print_constants_need_no_mandate(self):
        # print(1) and print("string") must compile without a mandate.
        compile("fn main() { print(1) }")
        compile('fn main() { print("hello") return 0 }')

    def test_direct_leak_still_blocked(self):
        code = "fn main() requires [NetworkAccess] { return net.send(user.data()) }"
        with self.assertRaisesRegex(EthicalError, "PII"):
            compile(code)

    def test_allowed_sanitizer_passes(self):
        code = (
            "fn main() requires [NetworkAccess] {\n"
            "  let card = payment.card()\n"
            "  let safe = encrypt(card)\n"
            "  return net.send(safe)\n"
            "}"
        )
        compile(code)

    def test_loop_fixpoint_still_caught(self):
        # Sanitizer inside a loop that may never run: the taint survives.
        code = (
            "fn leak() requires [NetworkAccess] {\n"
            "  let data = user.data()\n"
            "  let i = 0\n"
            "  while i < 0 { data = anonymize(data) i = i + 1 }\n"
            "  return net.send(data)\n"
            "}\n"
            "fn main() { return 0 }"
        )
        with self.assertRaisesRegex(EthicalError, "PII"):
            compile(code)

    def test_interprocedural_parameter_leak_still_blocked(self):
        code = (
            "fn leak_out(data) requires [NetworkAccess] { return net.send(data) }\n"
            "fn caller() requires [NetworkAccess] {\n"
            "  let secret = user.data()\n"
            "  return leak_out(secret)\n"
            "}\n"
            "fn main() { return 0 }"
        )
        with self.assertRaises(EthicalError):
            compile(code)


if __name__ == "__main__":
    unittest.main()
