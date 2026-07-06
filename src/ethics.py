# -*- coding: utf-8 -*-
"""Ethical analyzer YadroLang - law on level compilation.

Two_tier model safety AI:

  1. MANDATES (capabilities). Dangerous system API (net, disk) is_called
     only from_ functions, v signature which explicitly declared corresponding
     mandate 'requires [...]'. Mandate is_checked transitively: if_branch function A
     calls B, requiring [NetworkAccess], then A also must declare its.
     Result: everything interaction s the_world visible v signatures. Hide cannot.

  2. TAINT-Analysis (flow_based, along variables). Data from_ sources personal
     information are_marked as_ 'tainted'. Taint propagates through
     assignment, binary operations i calls functions. If tainted
     value reaches sink (net/disk) without passing through sanitizer -
     compilation falls. Clear can only explicitly: wrap v sanitizer
     (anonymization / check consent).

Law to code. Hide malicious behavior impossible.
"""
from src.syntax import (Program, Function, Return, Let, Assign,
                           If, While, NumberLit, StringLit, Ident, Binary, Call)


# Sink -> mandate, which it requires.
SINKS = {
    "net.send": "NetworkAccess",
    "net.request": "NetworkAccess",
    "file.write": "DiskWrite",
    "file.delete": "DiskWrite",
}

# Sources personal/sensitive data. Their result is_tainted.
SOURCES = {
    "user.data",
    "user.name",
    "personal.read",
    "file.read",
    "net.accept",
}

# Sanitizers. Their result guaranteed clean (anonymization/consent).
SANITIZERS = {
    "anonymize",
    "anonymize",
    "check_consent",
    "hash",
}


class EthicalError(Exception):
    ...


class EthicalAnalyzer:
    def __init__(self):
        self.functions = {}

    def check(self, prog: Program):
        self.functions = {f.name: f for f in prog.functions}
        self._compute_return_summaries()   # which functions return taint
        self._compute_param_summaries()  # which parameters leak v sink
        for f in prog.functions:
            self._mandates(f)
            self._taint(f)

    def _compute_return_summaries(self):
        """Fixpoint: for_ each functions - may whether its RETURN_ carry taint,
        arisen inside it (from_ sources or_ from_ tainting calls).
        Parameters consider clean: taint through argument is_caught on place
        call separately. Monotonic growth from False - correctly for_ recursion."""
        self.return_summary = {name: False for name in self.functions}
        while True:
            changed = False
            for name, f in self.functions.items():
                if self.return_summary[name]:
                    continue
                if self._body_returns_taint(f.body, set()):
                    self.return_summary[name] = True
                    changed = True
            if not changed:
                break

    def _body_returns_taint(self, body, tainted: set) -> bool:
        ret = False
        for u in body:
            if isinstance(u, (Let, Assign)):
                if self._is_tainted(u.value, tainted):
                    tainted.add(u.name)
                else:
                    tainted.discard(u.name)
            elif isinstance(u, Return):
                if u.value is not None and self._is_tainted(u.value, tainted):
                    ret = True
            elif isinstance(u, If):
                a = tainted.copy(); b = tainted.copy()
                ret = self._body_returns_taint(u.then_branch, a) or ret
                ret = self._body_returns_taint(u.else_branch, b) or ret
                tainted |= a | b
            elif isinstance(u, While):
                while True:
                    to = len(tainted)
                    ret = self._body_returns_taint(u.body, tainted) or ret
                    if len(tainted) == to:
                        break
        return ret

    # --- Level 1: mandates (capabilities) ---
    def _mandates(self, f: Function):
        for stmt in f.body:
            for call in self._all_calls_in(stmt):
                needed = SINKS.get(call.name)
                if needed and needed not in f.mandates:
                    raise EthicalError(
                        f"Function '{f.name}' (string {call.string}) calls "
                        f"'{call.name}', requiring mandate [{needed}], "
                        f"but mandate not_ declared v signature. "
                        f"Add: fn {f.name}(...) requires [{needed}]")
                # transitive check user_defined functions
                target = self.functions.get(call.name)
                if target:
                    for m in target.mandates:
                        if m not in f.mandates:
                            raise EthicalError(
                                f"Function '{f.name}' (string {call.string}) "
                                f"calls '{target.name}', requiring [{m}], "
                                f"but itself mandate [{m}] not_ declares.")

    # --- Level 2: flow_based taint-analysis ---
    def _taint(self, f: Function):
        tainted = set()          # names tainted variables
        for stmt in f.body:
            self._taint_stmt(stmt, tainted)

    def _taint_stmt(self, u, tainted: set):
        if isinstance(u, Let):
            self._check_sinks(u.value, tainted)   # sink v initializer
            if self._is_tainted(u.value, tainted):
                tainted.add(u.name)
            else:
                tainted.discard(u.name)
        elif isinstance(u, Assign):
            self._check_sinks(u.value, tainted)   # sink v right part
            if self._is_tainted(u.value, tainted):
                tainted.add(u.name)
            else:
                tainted.discard(u.name)
        elif isinstance(u, Return):
            self._check_sinks(u.value, tainted)
        elif isinstance(u, If):
            self._check_sinks(u.condition, tainted)
            branch = tainted.copy()
            for s in u.then_branch:
                self._taint_stmt(s, branch)
            branch2 = tainted.copy()
            for s in u.else_branch:
                self._taint_stmt(s, branch2)
            tainted |= (branch | branch2)   # conservative merge branches
        elif isinstance(u, While):
            self._check_sinks(u.condition, tainted)
            # Body may execute 0..N time. Iterate analysis body to
            # CURRENT fixpoint: repeat, while_loop set tainted
            # grows. Taint only Is_added (sanitizer inside loop
            # not_ guaranteed - iterations may be 0). On last pass
            # sinks are_checked already on stabilized set, therefore
            # chains a=b; b=c; c=source(); sink(a) are_caught.
            while True:
                to = len(tainted)
                body_tainted = tainted.copy()
                for s in u.body:
                    self._taint_stmt(s, body_tainted)
                tainted |= body_tainted
                if len(tainted) == to:
                    break
        else:
            self._check_sinks(u, tainted)

    def _compute_param_summaries(self):
        """Fixpoint: for_ each functions - set its parameters, which,
        being tainted, leak v sink (directly or_ transitively through
        calls other functions). Closes interprocedural leak through argument."""
        self.param_summary = {name: set() for name in self.functions}
        changed = True
        while changed:
            changed = False
            for name, f in self.functions.items():
                for p in f.parameters:
                    if p in self.param_summary[name]:
                        continue
                    if self._param_leaks_in_body(f.body, {p}):
                        self.param_summary[name].add(p)
                        changed = True

    def _param_leaks_in_body(self, body, tainted: set) -> bool:
        """Leaks whether from_ set tainted names even that-then v sink inside body."""
        for u in body:
            if isinstance(u, (Let, Assign)):
                if self._expression_leaks(u.value, tainted):
                    return True
                if self._is_tainted(u.value, tainted):
                    tainted.add(u.name)
                else:
                    tainted.discard(u.name)
            elif isinstance(u, Return):
                if u.value is not None and self._expression_leaks(u.value, tainted):
                    return True
            elif isinstance(u, If):
                if self._expression_leaks(u.condition, tainted):
                    return True
                branch_a = set(tainted)
                branch_b = set(tainted)
                if self._param_leaks_in_body(u.then_branch, branch_a):
                    return True
                if self._param_leaks_in_body(u.else_branch, branch_b):
                    return True
                tainted |= branch_a | branch_b
            elif isinstance(u, While):
                # Condition may itself contain sink.
                if self._expression_leaks(u.condition, tainted):
                    return True
                # Loop may not_ execute nor time: taint only Add
                # (body analyze on copy i merge), else_branch lose taint
                # parameter for_ sink AFTER loop.
                while True:
                    to = len(tainted)
                    body_tainted = set(tainted)
                    if self._param_leaks_in_body(u.body, body_tainted):
                        return True
                    if self._expression_leaks(u.condition, body_tainted):
                        return True
                    tainted |= body_tainted
                    if len(tainted) == to:
                        break
            else:
                if self._expression_leaks(u, tainted):
                    return True
        return False

    def _expression_leaks(self, v, tainted: set) -> bool:
        """Contains whether expression sink (direct Or_ transitive) s tainted argument."""
        if v is None or isinstance(v, (NumberLit, StringLit, Ident)):
            return False
        if isinstance(v, Binary):
            return (self._expression_leaks(v.left, tainted)
                    or self._expression_leaks(v.right, tainted))
        if isinstance(v, Call):
            if v.name in SINKS:
                if any(self._is_tainted(a, tainted) for a in v.arguments):
                    return True
            else:
                target = self.functions.get(v.name)
                if target:
                    leaks = self.param_summary.get(v.name, set())
                    for i, a in enumerate(v.arguments):
                        if (i < len(target.parameters)
                                and target.parameters[i] in leaks
                                and self._is_tainted(a, tainted)):
                            return True
            return any(self._expression_leaks(a, tainted) for a in v.arguments)
        return False

    def _check_sinks(self, v, tainted: set):
        """Finds calls sinks i checks, that their arguments not_ tainted."""
        if v is None:
            return
        if isinstance(v, Call):
            if v.name in SINKS:
                for arg in v.arguments:
                    if self._is_tainted(arg, tainted):
                        raise EthicalError(
                            f"Leak Data (string {v.string}): personal data "
                            f"leave through sink '{v.name}' without clearing. "
                            f"Wrap data v sanitizer "
                            f"({' / '.join(sorted(SANITIZERS))}).")
            else:
                # Interprocedural check: tainted argument leaves v parameter,
                # which inside called functions leaks v sink.
                target = self.functions.get(v.name)
                if target:
                    leaks = self.param_summary.get(v.name, set())
                    for i, arg in enumerate(v.arguments):
                        if (i < len(target.parameters)
                                and target.parameters[i] in leaks
                                and self._is_tainted(arg, tainted)):
                            raise EthicalError(
                                f"Leak Data (string {v.string}): personal data "
                                f"are_passed v '{v.name}' through parameter "
                                f"'{target.parameters[i]}', which inside leaves v sink. "
                                f"Wrap data v sanitizer "
                                f"({' / '.join(sorted(SANITIZERS))}).")
            for arg in v.arguments:
                self._check_sinks(arg, tainted)
        elif isinstance(v, Binary):
            self._check_sinks(v.left, tainted)
            self._check_sinks(v.right, tainted)

    def _is_tainted(self, v, tainted: set) -> bool:
        """IsTainted whether expression although even partially?"""
        if isinstance(v, (NumberLit, StringLit)):
            return False
        if isinstance(v, Ident):
            return v.name in tainted
        if isinstance(v, Binary):
            return self._is_tainted(v.left, tainted) or self._is_tainted(v.right, tainted)
        if isinstance(v, Call):
            # Built_in sanitizer clears ONLY if_branch its not_ overrode.
            # Else attacker declares fn hash(x){return x} i "cleans"
            # personal data along name. Overridden name analyze as_
            # regular user_defined function (passthrough along arguments).
            if v.name in SANITIZERS and v.name not in self.functions:
                return False                      # result sanitizer clean
            if v.name in SOURCES:
                return True                       # source personal data
            # user_defined function, returning taint (along summary)
            if getattr(self, "return_summary", {}).get(v.name, False):
                return True
            # else_branch is_tainted, if_branch is_tainted any argument (passthrough)
            return any(self._is_tainted(a, tainted) for a in v.arguments)
        return False

    # --- helper: build all calls inside statement ---
    def _all_calls_in(self, u):
        out = []

        def walk_expr(v):
            if isinstance(v, Call):
                out.append(v)
                for a in v.arguments:
                    walk_expr(a)
            elif isinstance(v, Binary):
                walk_expr(v.left); walk_expr(v.right)

        def walk_stmt(s):
            if isinstance(s, (Let, Assign, Return)):
                if getattr(s, "value", None) is not None:
                    walk_expr(s.value)
            elif isinstance(s, If):
                walk_expr(s.condition)
                for x in s.then_branch: walk_stmt(x)
                for x in s.else_branch: walk_stmt(x)
            elif isinstance(s, While):
                walk_expr(s.condition)
                for x in s.body: walk_stmt(x)
            else:
                walk_expr(s)

        walk_stmt(u)
        return out
