# -*- coding: utf-8 -*-
"""YadroLang Ethical Analyzer v2.0 - Compile-time safety guarantees.

Three-tier security model:

  1. MANDATES (capabilities). Dangerous system APIs (network, disk, database)
     are only callable from functions whose signature explicitly declares the
     matching mandate via 'requires [...]'. Mandates are checked transitively:
     if function A calls B which requires [NetworkAccess], then A must also
     declare [NetworkAccess]. Result: all external interactions are visible
     in function signatures. Hiding side-effects is impossible.

  2. EXPLICIT TAINT ANALYSIS (data-flow). Data from sources of personal/sensitive
     information is marked as 'tainted' with a specific LABEL (PII, Financial,
     Health). Taint propagates through assignments, binary operations, and
     function calls. If tainted data reaches a sink (network/disk/log) without
     passing through an appropriate sanitizer - compilation fails.

  3. IMPLICIT FLOW DETECTION (control-flow). If a branch condition depends on
     tainted data, ANY sink call inside that branch is flagged - even if the
     argument itself is not tainted. This prevents information leakage through
     control-flow side channels (e.g., sending different values based on
     personal data conditions).

Code is law. Hiding malicious behavior is impossible.
"""
from src.syntax import (Program, Function, Return, Let, Assign,
                           If, While, NumberLit, StringLit, Ident, Binary, Call)


# ---------------------------------------------------------------------------
# Taint labels - WHAT kind of sensitive data is involved
# ---------------------------------------------------------------------------
class TaintLabel:
    PII = "PII"               # Personally Identifiable Information
    FINANCIAL = "Financial"    # Financial data (accounts, transactions)
    HEALTH = "Health"          # Health/medical records (HIPAA)
    CREDENTIALS = "Credentials"  # Passwords, tokens, API keys
    LOCATION = "Location"      # Geolocation data


# ---------------------------------------------------------------------------
# Sink -> required mandate mapping (expanded)
# ---------------------------------------------------------------------------
SINKS = {
    # Network
    "net.send":       "NetworkAccess",
    "net.request":    "NetworkAccess",
    "net.post":       "NetworkAccess",
    "http.redirect":  "NetworkAccess",
    "ws.send":        "NetworkAccess",
    # Disk
    "file.write":     "DiskWrite",
    "file.delete":    "DiskWrite",
    "file.append":    "DiskWrite",
    # Database
    "db.write":       "DatabaseWrite",
    "db.insert":      "DatabaseWrite",
    "db.update":      "DatabaseWrite",
    "db.delete":      "DatabaseWrite",
    "db.query":       "DatabaseRead",
    # Logging (PII in logs is a GDPR violation)
    "log.info":       "LogAccess",
    "log.debug":      "LogAccess",
    "log.error":      "LogAccess",
    "console.log":    "LogAccess",
    # External services
    "api.call":       "NetworkAccess",
    "email.send":     "NetworkAccess",
    "sms.send":       "NetworkAccess",
}

# ---------------------------------------------------------------------------
# Sources of sensitive data -> taint label
# ---------------------------------------------------------------------------
SOURCES = {
    # PII sources
    "user.data":        TaintLabel.PII,
    "user.name":        TaintLabel.PII,
    "user.email":       TaintLabel.PII,
    "user.phone":       TaintLabel.PII,
    "user.address":     TaintLabel.PII,
    "user.id":          TaintLabel.PII,
    "personal.read":    TaintLabel.PII,
    "request.body":     TaintLabel.PII,
    "request.params":   TaintLabel.PII,
    "cookie.get":       TaintLabel.PII,
    "session.get":      TaintLabel.PII,
    # Financial sources
    "payment.card":     TaintLabel.FINANCIAL,
    "account.balance":  TaintLabel.FINANCIAL,
    "transaction.get":  TaintLabel.FINANCIAL,
    "bank.account":     TaintLabel.FINANCIAL,
    # Health sources
    "patient.record":   TaintLabel.HEALTH,
    "medical.history":  TaintLabel.HEALTH,
    "diagnosis.get":    TaintLabel.HEALTH,
    # Credentials
    "env.secret":       TaintLabel.CREDENTIALS,
    "vault.read":       TaintLabel.CREDENTIALS,
    "key.private":      TaintLabel.CREDENTIALS,
    # Location
    "geo.location":     TaintLabel.LOCATION,
    "gps.coordinates":  TaintLabel.LOCATION,
    # Generic I/O (potentially tainted)
    "file.read":        TaintLabel.PII,
    "net.accept":       TaintLabel.PII,
    "db.read":          TaintLabel.PII,
}

# ---------------------------------------------------------------------------
# Sanitizers - functions that declassify tainted data
# ---------------------------------------------------------------------------
SANITIZERS = {
    "anonymize",
    "check_consent",
    "hash",
    "encrypt",
    "mask",
    "redact",
    "tokenize",
    "pseudonymize",
    "aggregate",
}

# ---------------------------------------------------------------------------
# Compliance policies - which labels require which sanitizers
# ---------------------------------------------------------------------------
COMPLIANCE = {
    TaintLabel.PII:         {"anonymize", "hash", "pseudonymize", "redact", "mask", "check_consent"},
    TaintLabel.FINANCIAL:   {"encrypt", "tokenize", "mask", "hash"},
    TaintLabel.HEALTH:      {"anonymize", "redact", "pseudonymize", "encrypt"},
    TaintLabel.CREDENTIALS: {"encrypt", "hash", "tokenize"},
    TaintLabel.LOCATION:    {"anonymize", "aggregate", "redact"},
}


class EthicalError(Exception):
    ...


class AuditEntry:
    """Single entry in the data-flow audit trail."""
    __slots__ = ("source", "label", "path", "sink", "line", "status", "detail")

    def __init__(self, source, label, path, sink, line, status, detail=""):
        self.source = source
        self.label = label
        self.path = path
        self.sink = sink
        self.line = line
        self.status = status     # "BLOCKED" | "SANITIZED" | "IMPLICIT_FLOW"
        self.detail = detail

    def __repr__(self):
        return (f"[{self.status}] {self.label}: {self.source} -> "
                f"{' -> '.join(self.path)} -> {self.sink} (line {self.line})"
                f"{': ' + self.detail if self.detail else ''}")


class EthicalAnalyzer:
    def __init__(self):
        self.functions = {}
        self.audit_trail = []    # list of AuditEntry

    def check(self, prog: Program):
        self.functions = {f.name: f for f in prog.functions}
        self.audit_trail = []
        self._compute_return_summaries()
        self._compute_param_summaries()
        for f in prog.functions:
            self._mandates(f)
            self._taint(f)
        return self.audit_trail

    # -----------------------------------------------------------------------
    # Return summaries (fixpoint)
    # -----------------------------------------------------------------------
    def _compute_return_summaries(self):
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

    # -----------------------------------------------------------------------
    # Level 1: Mandate (capability) checking
    # -----------------------------------------------------------------------
    def _mandates(self, f: Function):
        for stmt in f.body:
            for call in self._all_calls_in(stmt):
                needed = SINKS.get(call.name)
                if needed and needed not in f.mandates:
                    self.audit_trail.append(AuditEntry(
                        source="N/A", label="MANDATE", path=[f.name],
                        sink=call.name, line=call.string,
                        status="BLOCKED",
                        detail=f"Missing mandate [{needed}]"))
                    raise EthicalError(
                        f"Function '{f.name}' (line {call.string}) calls "
                        f"'{call.name}', requiring mandate [{needed}], "
                        f"but mandate is not declared in signature. "
                        f"Add: fn {f.name}(...) requires [{needed}]")
                target = self.functions.get(call.name)
                if target:
                    for m in target.mandates:
                        if m not in f.mandates:
                            self.audit_trail.append(AuditEntry(
                                source="N/A", label="MANDATE", path=[f.name, target.name],
                                sink=call.name, line=call.string,
                                status="BLOCKED",
                                detail=f"Transitive mandate [{m}] missing"))
                            raise EthicalError(
                                f"Function '{f.name}' (line {call.string}) "
                                f"calls '{target.name}', requiring [{m}], "
                                f"but does not declare [{m}] itself.")

    # -----------------------------------------------------------------------
    # Level 2: Explicit taint analysis (data-flow)
    # -----------------------------------------------------------------------
    def _taint(self, f: Function):
        tainted = set()
        taint_labels = {}        # var_name -> set of TaintLabel
        implicit_depth = 0       # nesting depth of tainted conditions
        self._taint_body(f.body, tainted, taint_labels, implicit_depth)

    def _taint_body(self, body, tainted, taint_labels, implicit_depth):
        for u in body:
            self._taint_stmt(u, tainted, taint_labels, implicit_depth)

    def _taint_stmt(self, u, tainted: set, taint_labels: dict, implicit_depth: int):
        if isinstance(u, Let):
            self._check_sinks(u.value, tainted, taint_labels, implicit_depth)
            if self._is_tainted(u.value, tainted):
                tainted.add(u.name)
                taint_labels[u.name] = self._get_labels(u.value, tainted, taint_labels)
            else:
                tainted.discard(u.name)
                taint_labels.pop(u.name, None)

        elif isinstance(u, Assign):
            self._check_sinks(u.value, tainted, taint_labels, implicit_depth)
            if self._is_tainted(u.value, tainted):
                tainted.add(u.name)
                taint_labels[u.name] = self._get_labels(u.value, tainted, taint_labels)
            else:
                tainted.discard(u.name)
                taint_labels.pop(u.name, None)

        elif isinstance(u, Return):
            self._check_sinks(u.value, tainted, taint_labels, implicit_depth)

        elif isinstance(u, If):
            self._check_sinks(u.condition, tainted, taint_labels, implicit_depth)
            # --- IMPLICIT FLOW: if condition is tainted, increase depth ---
            cond_tainted = self._is_tainted(u.condition, tainted)
            child_depth = implicit_depth + 1 if cond_tainted else implicit_depth

            branch = tainted.copy()
            branch_labels = dict(taint_labels)
            self._taint_body(u.then_branch, branch, branch_labels, child_depth)

            branch2 = tainted.copy()
            branch2_labels = dict(taint_labels)
            self._taint_body(u.else_branch, branch2, branch2_labels, child_depth)

            tainted |= (branch | branch2)
            for k in (branch_labels.keys() | branch2_labels.keys()):
                merged = branch_labels.get(k, set()) | branch2_labels.get(k, set())
                if merged:
                    taint_labels[k] = merged

        elif isinstance(u, While):
            self._check_sinks(u.condition, tainted, taint_labels, implicit_depth)
            cond_tainted = self._is_tainted(u.condition, tainted)
            child_depth = implicit_depth + 1 if cond_tainted else implicit_depth
            while True:
                to = len(tainted)
                body_tainted = tainted.copy()
                body_labels = dict(taint_labels)
                self._taint_body(u.body, body_tainted, body_labels, child_depth)
                tainted |= body_tainted
                for k, v in body_labels.items():
                    taint_labels.setdefault(k, set()).update(v)
                if len(tainted) == to:
                    break
        else:
            self._check_sinks(u, tainted, taint_labels, implicit_depth)

    # -----------------------------------------------------------------------
    # Level 3: Implicit flow detection
    # -----------------------------------------------------------------------
    def _check_implicit_flow(self, call, implicit_depth, taint_labels):
        """If we are inside a branch whose condition depends on tainted data,
        ANY sink call is suspicious - even with clean arguments."""
        if implicit_depth > 0 and call.name in SINKS:
            labels_in_scope = set()
            for lset in taint_labels.values():
                labels_in_scope |= lset
            label_str = ", ".join(sorted(labels_in_scope)) if labels_in_scope else "unknown"
            self.audit_trail.append(AuditEntry(
                source="implicit-condition", label=label_str,
                path=[f"branch-depth-{implicit_depth}"],
                sink=call.name, line=call.string,
                status="IMPLICIT_FLOW",
                detail=f"Sink '{call.name}' is inside a branch conditioned on "
                       f"sensitive data. Information may leak through control flow."))
            raise EthicalError(
                f"Implicit information flow (line {call.string}): "
                f"sink '{call.name}' is called inside a branch whose condition "
                f"depends on sensitive data ({label_str}). "
                f"Even though the argument is not directly tainted, the branch "
                f"structure reveals information about the sensitive value. "
                f"Move the sink call outside the tainted branch, or sanitize "
                f"the condition variable first.")

    # -----------------------------------------------------------------------
    # Label tracking
    # -----------------------------------------------------------------------
    def _get_labels(self, v, tainted: set, taint_labels: dict) -> set:
        """Collect all taint labels from an expression."""
        if isinstance(v, (NumberLit, StringLit)):
            return set()
        if isinstance(v, Ident):
            return taint_labels.get(v.name, set())
        if isinstance(v, Binary):
            return self._get_labels(v.left, tainted, taint_labels) | \
                   self._get_labels(v.right, tainted, taint_labels)
        if isinstance(v, Call):
            if v.name in SANITIZERS and v.name not in self.functions:
                return set()
            label = SOURCES.get(v.name)
            if label:
                return {label}
            result = set()
            for a in v.arguments:
                result |= self._get_labels(a, tainted, taint_labels)
            return result
        return set()

    # -----------------------------------------------------------------------
    # Sink checking (with implicit flow awareness)
    # -----------------------------------------------------------------------
    def _check_sinks(self, v, tainted: set, taint_labels: dict, implicit_depth: int):
        if v is None:
            return
        if isinstance(v, Call):
            # Level 3: implicit flow check
            self._check_implicit_flow(v, implicit_depth, taint_labels)

            if v.name in SINKS:
                for arg in v.arguments:
                    if self._is_tainted(arg, tainted):
                        labels = self._get_labels(arg, tainted, taint_labels)
                        label_str = ", ".join(sorted(labels)) if labels else "sensitive"
                        self.audit_trail.append(AuditEntry(
                            source="direct", label=label_str,
                            path=[], sink=v.name, line=v.string,
                            status="BLOCKED",
                            detail=f"Tainted data ({label_str}) flows to sink"))
                        raise EthicalError(
                            f"Data leak (line {v.string}): {label_str} data "
                            f"reaches sink '{v.name}' without sanitization. "
                            f"Wrap data in a sanitizer "
                            f"({' / '.join(sorted(SANITIZERS))}).")
            else:
                target = self.functions.get(v.name)
                if target:
                    leaks = self.param_summary.get(v.name, set())
                    for i, arg in enumerate(v.arguments):
                        if (i < len(target.parameters)
                                and target.parameters[i] in leaks
                                and self._is_tainted(arg, tainted)):
                            labels = self._get_labels(arg, tainted, taint_labels)
                            label_str = ", ".join(sorted(labels)) if labels else "sensitive"
                            self.audit_trail.append(AuditEntry(
                                source="interprocedural", label=label_str,
                                path=[v.name, target.parameters[i]],
                                sink="transitive", line=v.string,
                                status="BLOCKED",
                                detail=f"Tainted arg leaks through param '{target.parameters[i]}'"))
                            raise EthicalError(
                                f"Data leak (line {v.string}): {label_str} data "
                                f"is passed to '{v.name}' through parameter "
                                f"'{target.parameters[i]}', which leaks to a sink internally. "
                                f"Wrap data in a sanitizer "
                                f"({' / '.join(sorted(SANITIZERS))}).")
            for arg in v.arguments:
                self._check_sinks(arg, tainted, taint_labels, implicit_depth)
        elif isinstance(v, Binary):
            self._check_sinks(v.left, tainted, taint_labels, implicit_depth)
            self._check_sinks(v.right, tainted, taint_labels, implicit_depth)

    # -----------------------------------------------------------------------
    # Taint checking
    # -----------------------------------------------------------------------
    def _is_tainted(self, v, tainted: set) -> bool:
        if isinstance(v, (NumberLit, StringLit)):
            return False
        if isinstance(v, Ident):
            return v.name in tainted
        if isinstance(v, Binary):
            return self._is_tainted(v.left, tainted) or self._is_tainted(v.right, tainted)
        if isinstance(v, Call):
            if v.name in SANITIZERS and v.name not in self.functions:
                return False
            if v.name in SOURCES:
                return True
            if getattr(self, "return_summary", {}).get(v.name, False):
                return True
            return any(self._is_tainted(a, tainted) for a in v.arguments)
        return False

    # -----------------------------------------------------------------------
    # Parameter summaries (fixpoint)
    # -----------------------------------------------------------------------
    def _compute_param_summaries(self):
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
                if self._expression_leaks(u.condition, tainted):
                    return True
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

    # -----------------------------------------------------------------------
    # Helper: collect all Call nodes inside a statement
    # -----------------------------------------------------------------------
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

    # -----------------------------------------------------------------------
    # Audit report generation
    # -----------------------------------------------------------------------
    def generate_audit_report(self):
        """Generate a structured compliance audit report."""
        report = []
        report.append("=" * 60)
        report.append("YADROLANG ETHICAL ANALYZER - AUDIT REPORT")
        report.append("=" * 60)
        blocked = [e for e in self.audit_trail if e.status == "BLOCKED"]
        implicit = [e for e in self.audit_trail if e.status == "IMPLICIT_FLOW"]
        sanitized = [e for e in self.audit_trail if e.status == "SANITIZED"]
        report.append(f"\nTotal findings: {len(self.audit_trail)}")
        report.append(f"  Blocked (explicit flow):  {len(blocked)}")
        report.append(f"  Blocked (implicit flow):  {len(implicit)}")
        report.append(f"  Sanitized (passed):       {len(sanitized)}")
        if self.audit_trail:
            report.append("\n--- Detailed findings ---")
            for entry in self.audit_trail:
                report.append(str(entry))
        report.append("\n" + "=" * 60)
        return "\n".join(report)
