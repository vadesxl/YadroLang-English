# -*- coding: utf-8 -*-
"""Behavioral regressions for PATCH 4-6 (continuation of issue #47).

PATCH 1-3 are already applied in `src/ethics_flow.py` (class
`SoundEthicalAnalyzer`): `print` is an output sink, and assignments and returns
under a sensitive condition inherit `pc_labels`. These tests cover what
PATCH 1-3 still miss.

Numbering (as in docs/patches/compiler_fix_queue.md, Phase 3-4):
  PATCH 4 - stale merge after a sanitizer in BOTH branches of `if`
            (`_join_env(env, left, right)` returns the labels from "before" the
            branch, so the sanitized value becomes dirty again -> false block).
  PATCH 5 - function summaries must be pc-aware: the control context of the
            CALLING function flows into the callee return summary and into the
            callee effect summary.
  PATCH 6 - refinements of caller PC and the loop fixpoint: the loop condition
            labels are folded into the pc state of the fixpoint, and caller PC
            is carried transitively along helper chains.

ATTENTION about the numbering: `COMPILER_FIX_STATUS.md` used a different one
(there "PATCH 4 = caller PC", "PATCH 5 = loop fixpoint", "PATCH 6 = branch
merge"). Here it is the numbering of the `compiler_fix_queue.md` queue, which
matches issue #47.

Tests marked `[control]` are green NOW: they pin down the precision boundary
that PATCH 4-6 must not break. The rest are red and demonstrate a concrete
missing block (or a false block, for PATCH 4).
"""
import unittest

from src.main import compile
from src.ethics import EthicalError


class BehavioralTestBase(unittest.TestCase):
    """Shared assertions: a program must either compile, or have its leak cut."""

    def _compiles(self, code, context):
        """The code is safe and must compile (otherwise it is a false block)."""
        try:
            compile(code)
        except EthicalError as error:
            self.fail(
                f"{context}: the analyzer FALSELY blocks safe code "
                f"[{error.code}] {error}"
            )

    def _blocked(self, code, context, error_code=None, labels=()):
        """The code leaks and must be cut off by the ethical analyzer."""
        try:
            compile(code)
        except EthicalError as error:
            if error_code:
                self.assertEqual(
                    error.code, error_code,
                    f"{context}: expected code {error_code}, got {error.code}.")
            for label in labels:
                self.assertIn(label, str(error),
                              f"{context}: the diagnostic has no '{label}' label.")
            return error
        self.fail(
            f"{context}: leak NOT cut off - the compiler emitted LLVM IR. "
            f"This is a missing PATCH 4-6 block."
        )


class Patch4BranchMergeTests(BehavioralTestBase):
    """PATCH 4: a branch merge must not return stale labels."""

    def test_patch4_sanitizer_in_both_branches_compiles(self):
        """False block: the environment from BEFORE the `if` is mixed in.

        `x` is dirty before the branch, but both branches sanitize it again, so
        there must be no labels after the merge. Today
        `_join_env(env, left, right)` mixes in `env` (the state before the `if`)
        and returns `Credentials`.
        """
        code = (
            "fn main() requires [NetworkAccess] {\n"
            "  let flag = 0\n"
            "  let x = env.secret()\n"
            "  if flag { x = encrypt(x) } else { x = encrypt(x) }\n"
            "  return net.send(x)\n"
            "}"
        )
        self._compiles(code, "PATCH 4 / sanitizer in both branches")

    def test_patch4_helper_return_summary_has_no_stale_label(self):
        """The same defect in `_return_labels` (it feeds the return summary).

        The helper sanitizes `x` in both branches and returns it. The return
        summary must be empty, otherwise the caller receives a phantom
        `Credentials`.
        """
        code = (
            "fn helpers(flag) {\n"
            "  let x = env.secret()\n"
            "  if flag { x = encrypt(x) } else { x = encrypt(x) }\n"
            "  return x\n"
            "}\n"
            "fn main() requires [NetworkAccess] { return net.send(helpers(0)) }"
        )
        self._compiles(code, "PATCH 4 / helper return summary")

    def test_patch4_branch_with_return_also_sanitizes(self):
        """Variant: a branch that always returns also sanitizes the value.

        Only the `else` branch is live at the merge point, and there `x` is
        already clean. The current merge with the "before the `if`" environment
        makes `x` dirty again.
        """
        code = (
            "fn main() requires [NetworkAccess] {\n"
            "  let flag = 0\n"
            "  let x = env.secret()\n"
            "  if flag { x = encrypt(x) return 0 } else { x = encrypt(x) }\n"
            "  return net.send(x)\n"
            "}"
        )
        self._compiles(code, "PATCH 4 / branch with return")

    def test_patch4_partial_sanitizer_leaves_unremoved_label(self):
        """Precision: a sanitizer removes only the allowed label, the second stays.

        `encrypt` removes `Credentials`, but not `PII`. After PATCH 4 the leak
        must remain, but the diagnostic must not contain the stale
        `Credentials` - which is exactly what the merge with the "before the
        `if`" env adds today.
        """
        code = (
            "fn main() requires [NetworkAccess] {\n"
            "  let flag = 0\n"
            "  let x = user.data() + env.secret()\n"
            "  if flag { x = encrypt(x) } else { x = encrypt(x) }\n"
            "  return net.send(x)\n"
            "}"
        )
        error = self._blocked(code, "PATCH 4 / partial sanitizer",
                              error_code="YADRO-E2301", labels=("PII",))
        self.assertNotIn(
            "Credentials", str(error),
            "PATCH 4: the 'Credentials' label is stale - the merge with the "
            "state from BEFORE the branch returned it, although both branches "
            "removed it.")

    # --- [control] boundaries that PATCH 4 is not allowed to break ---

    def test_patch4_control_sanitizer_in_one_branch_only_block(self):
        """[control] An empty `else` = a path without a sanitizer, the leak stays."""
        code = (
            "fn main() requires [NetworkAccess] {\n"
            "  let flag = 0\n"
            "  let x = env.secret()\n"
            "  if flag { x = encrypt(x) }\n"
            "  return net.send(x)\n"
            "}"
        )
        self._blocked(code, "[control] PATCH 4 / sanitizer in one branch only",
                      error_code="YADRO-E2301", labels=("Credentials",))

    def test_patch4_control_empty_else_keeps_implicit_flow(self):
        """[control] PATCH 2: an assignment under a sensitive condition stays dirty.

        If PATCH 4 is implemented as "join only the branch exits" without
        substituting the "before the `if`" environment for an empty `else`,
        this test turns green erroneously.
        """
        code = (
            "fn main() requires [NetworkAccess] {\n"
            "  let x = 0\n"
            "  if env.secret() { x = 1 }\n"
            "  return net.send(x)\n"
            "}"
        )
        self._blocked(code, "[control] PATCH 2 / implicit flow through assignment",
                      error_code="YADRO-E2301", labels=("Credentials",))

    def test_patch4_control_taint_only_in_branch(self):
        """[control] Taint that appears inside a branch survives the merge."""
        code = (
            "fn main() requires [NetworkAccess] {\n"
            "  let value = 0\n"
            "  if 1 { value = env.secret() }\n"
            "  return net.send(value)\n"
            "}"
        )
        self._blocked(code, "[control] PATCH 4 / taint only in a branch",
                      error_code="YADRO-E2301", labels=("Credentials",))


class Patch5PCAwareSummaryTests(BehavioralTestBase):
    """PATCH 5: helper summaries must account for the caller control context."""

    def test_patch5_helper_with_sink_under_condition_block(self):
        """Leak: the effect (system sink) inside a helper is driven by caller pc.

        `leak()` sends a constant, but the call itself sits under `if s`, so the
        execution of the send is controlled by `Credentials`. The callee effect
        summary has no pc dimension today, so `_scan_expression` has nothing to
        consult and the leak passes.
        """
        code = (
            "fn leak() requires [NetworkAccess] { return net.send(1) }\n"
            "fn main() requires [NetworkAccess] {\n"
            "  let s = env.secret()\n"
            "  if s { return leak() }\n"
            "  return 0\n"
            "}"
        )
        self._blocked(code, "PATCH 5 / helper with sink under a sensitive condition",
                      error_code="YADRO-E2302", labels=("Credentials",))

    def test_patch5_print_in_helper_under_condition_block(self):
        """The same defect for the PATCH 1 output sink (`print`)."""
        code = (
            "fn logger() { return print(1) }\n"
            "fn main() {\n"
            "  let s = env.secret()\n"
            "  if s { return logger() }\n"
            "  return 0\n"
            "}"
        )
        self._blocked(code, "PATCH 5 / print in helper under a condition",
                      error_code="YADRO-E2302", labels=("Credentials",))

    def test_patch5_helper_value_in_argument_carries_pc(self):
        """Leak: a helper value in an ARGUMENT position does not inherit caller pc.

        `helper()` returns a constant, but the call sits under `if s`. `_labels`
        for a `Call` takes the return summary with no pc dimension, so the
        argument looks clean and `outward()` happily sends it to the network.
        """
        code = (
            "fn helper() { return 1 }\n"
            "fn outward(z) requires [NetworkAccess] { return net.send(z) }\n"
            "fn main() requires [NetworkAccess] {\n"
            "  let s = env.secret()\n"
            "  if s { return outward(helper()) }\n"
            "  return 0\n"
            "}"
        )
        self._blocked(code, "PATCH 5 / helper value in an argument",
                      labels=("Credentials",))

    # --- [control] precision boundaries of PATCH 5 ---

    def test_patch5_control_helper_with_sink_outside_condition(self):
        """[control] A helper call with a sink and an empty pc must compile."""
        code = (
            "fn leak() requires [NetworkAccess] { return net.send(1) }\n"
            "fn main() requires [NetworkAccess] { return leak() }"
        )
        self._compiles(code, "[control] PATCH 5 / helper with sink outside condition")

    def test_patch5_control_clean_helper_under_condition(self):
        """[control] A helper with no sinks and no output under a condition compiles.

        This test guards against the simplest (wrong) implementation of "block
        any call under a condition": the pc dimension of the summary must be
        empty for functions with no output effects.
        """
        code = (
            "fn helper() { return 1 }\n"
            "fn main() {\n"
            "  let s = env.secret()\n"
            "  let k = 0\n"
            "  if s { k = helper() }\n"
            "  return k\n"
            "}"
        )
        self._compiles(code, "[control] PATCH 5 / clean helper under a condition")

    def test_patch5_control_value_through_variable_already_block(self):
        """[control] The same flow through a variable is already cut by PATCH 2 (E2303)."""
        code = (
            "fn helper() { return 1 }\n"
            "fn outward(z) requires [NetworkAccess] { return net.send(z) }\n"
            "fn main() requires [NetworkAccess] {\n"
            "  let s = env.secret()\n"
            "  let k = 0\n"
            "  if s { k = helper() }\n"
            "  return outward(k)\n"
            "}"
        )
        self._blocked(code, "[control] PATCH 5 / flow through a variable",
                      error_code="YADRO-E2303", labels=("Credentials",))


class Patch6PCAndLoopFixpointTests(BehavioralTestBase):
    """PATCH 6: loop condition labels in the fixpoint pc state + transitive caller PC."""

    def test_patch6_loop_condition_becomes_sensitive_block(self):
        """Leak: the condition is clean on the first iteration and dirty on the second.

        `while f { x = 1 f = s }`: on iteration 1 the condition is clean, on
        iteration 2 it is already `Credentials`, so `x = 1` executes under a
        sensitive pc. `_flow_loop` computes the fixpoint over the environment
        only, while pc is frozen at the "before the loop" value, so
        `_scan_body` sees the body with an empty pc.
        """
        code = (
            "fn main() requires [NetworkAccess] {\n"
            "  let s = env.secret()\n"
            "  let f = 0\n"
            "  let x = 0\n"
            "  while f { x = 1 f = s }\n"
            "  return net.send(x)\n"
            "}"
        )
        self._blocked(code, "PATCH 6 / loop condition becomes sensitive",
                      error_code="YADRO-E2301", labels=("Credentials",))

    def test_patch6_sink_in_loop_under_new_sensitive_condition_block(self):
        """Leak: a sink INSIDE the loop whose condition becomes sensitive.

        On the second iteration `net.send(1)` executes under pc = `Credentials`,
        that is an implicit flow. The body is scanned with the "before the loop"
        pc - empty.
        """
        code = (
            "fn main() requires [NetworkAccess] {\n"
            "  let s = env.secret()\n"
            "  let f = 0\n"
            "  while f { net.send(1) f = s }\n"
            "  return 0\n"
            "}"
        )
        self._blocked(code, "PATCH 6 / sink inside the loop",
                      error_code="YADRO-E2302", labels=("Credentials",))

    def test_patch6_transitive_helper_chain_under_condition_block(self):
        """Leak: caller PC must reach the sink through two helpers.

        `level2()` contains no sinks itself, but it calls `level3()`, which
        does. The single rule "pc is not empty and the callee reaches a sink" is
        not enough: the effect summary must be monotone and collapse into a
        fixpoint (`_compute_summaries`), otherwise the intermediate link stays
        invisible.
        """
        code = (
            "fn level3() requires [NetworkAccess] { return net.send(1) }\n"
            "fn level2() requires [NetworkAccess] { return level3() }\n"
            "fn main() requires [NetworkAccess] {\n"
            "  let s = env.secret()\n"
            "  if s { return level2() }\n"
            "  return 0\n"
            "}"
        )
        self._blocked(code, "PATCH 6 / transitive helper chain",
                      error_code="YADRO-E2302", labels=("Credentials",))

    # --- [control] boundaries that PATCH 6 is not allowed to break ---

    def test_patch6_control_sanitizer_in_loop_still_block(self):
        """[control] Zero iterations are possible, so the dirt survives (loop fixpoint)."""
        code = (
            "fn main() requires [NetworkAccess] {\n"
            "  let data = user.data()\n"
            "  let i = 0\n"
            "  while i < 0 { data = anonymize(data) i = i + 1 }\n"
            "  return net.send(data)\n"
            "}"
        )
        self._blocked(code, "[control] PATCH 6 / sanitizer in a loop",
                      error_code="YADRO-E2301", labels=("PII",))

    def test_patch6_control_sink_in_loop_under_constant_pc_block(self):
        """[control] Already caught by PATCH 2: the loop condition is sensitive at once."""
        code = (
            "fn main() requires [NetworkAccess] {\n"
            "  let s = env.secret()\n"
            "  let i = 0\n"
            "  while s { print(1) i = i + 1 }\n"
            "  return 0\n"
            "}"
        )
        self._blocked(code, "[control] PATCH 6 / sink in a loop under a constant pc",
                      error_code="YADRO-E2302", labels=("Credentials",))

    def test_patch6_control_loop_without_labels_compiles(self):
        """[control] A loop without sensitive data must compile."""
        code = (
            "fn main() requires [NetworkAccess] {\n"
            "  let i = 0\n"
            "  let x = 0\n"
            "  while i < 0 { x = 1 }\n"
            "  return net.send(x)\n"
            "}"
        )
        self._compiles(code, "[control] PATCH 6 / loop without labels")

    def test_patch6_control_implicit_flow_through_helper_parameter_block(self):
        """[control] Implicit flow through a helper PARAMETER is cut by the leak summary.

        The contrast with PATCH 5: the parameter flow is caught (E2303), the
        sink effect under caller pc is not.
        """
        code = (
            "fn wrapper(z) requires [NetworkAccess] {\n"
            "  if z { return net.send(1) }\n"
            "  return 0\n"
            "}\n"
            "fn main() requires [NetworkAccess] {\n"
            "  let s = env.secret()\n"
            "  return wrapper(s)\n"
            "}"
        )
        self._blocked(code, "[control] PATCH 6 / helper parameter",
                      error_code="YADRO-E2303", labels=("Credentials",))


if __name__ == "__main__":
    unittest.main()





