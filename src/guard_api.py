# -*- coding: utf-8 -*-
"""MCP Secrets Guard - code/script analysis backend for the Guard dashboard tab.

Invoked by the dashboard (dashboard/plugin_api.py) as::

    python -m src.guard_api analyze  --stdin --lang en
    python -m src.guard_api autofix  --stdin --lang en
    python -m src.guard_api report-text --stdin --lang en

The requested JSON document is read from stdin and the result is printed as a
single JSON line on stdout (the dashboard reads the last line). Pure Python, no
network, fail-closed: any internal error returns {"status": "error"}.

This backend analyses arbitrary agent scripts and commands (Python, Bash, JS,
JSON, MCP payloads) for two things:
  * secret leakage    -> runtime.detectors (same engine as the live hook)
  * dangerous actions -> runtime.actions   (expose, tunnel, bulk deletes, ...)

The reply shape matches what desktop/plugin.js / dist/index.js (Result) expects:
  clean   -> status/lines/sanitized/known_gaps
  leak    -> status/line/code/why/labels/sources/sink/quarantine + embedded autofix
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

from src.runtime import detectors, actions

KNOWN_GAPS = [
    "Static scan of the pasted text only: it does not follow values at runtime.",
    "It cannot see what the program was given from the environment or secrets in other files.",
    "A secret that is split, encoded or assembled at runtime is not caught here.",
    "Check the plain text for anything this scanner may not model.",
]

# per-label quarantine options shown in the 'How to send it legally' block
PROTECT: Dict[str, list] = {
    "Credentials": [("Store in the vault", "vault.stash"), ("Encrypt at rest", "crypto.encrypt"),
                    ("Use a secret reference", "env.secret")],
    "Financial": [("Tokenize", "vault.tokenize"), ("Encrypt", "crypto.encrypt")],
    "PII": [("Mask", "redact.mask"), ("Pseudonymize", "anon.pseudonymize")],
    "Health": [("Encrypt", "crypto.encrypt"), ("Anonymize", "anon.anonymize")],
    "Location": [("Aggregate", "anon.aggregate")],
}

_SINK_HUMAN = {
    "private_key": "a private key is present in the code", "seed_phrase": "a wallet seed phrase is in the code",
    "card_number": "a payment card number is in the code", "email": "an email address is in the code",
    "jwt": "a session token is in the code", "github_token": "a GitHub token is in the code",
    "openai_key": "an OpenAI API key is in the code", "sensitive_file": "a path to a sensitive local file is in the code",
}


def _line_of(text: str, pos: int) -> int:
    return 1 + text.count("\n", 0, pos)


def _line_text(text: str, pos: int) -> str:
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    return text[start:end if end != -1 else len(text)].strip()


def _sink_human(f) -> str:
    for k, msg in _SINK_HUMAN.items():
        if f.kind == k:
            return msg
    return "sensitive data is present in the code"


def _quarantine(labels) -> list:
    return [{"label": lbl, "options": [{"human": h, "fn": fn} for h, fn in PROTECT.get(lbl, [("Store in the vault", "vault.stash")])]}
            for lbl in labels]


def _autofix(code: str, findings) -> Dict[str, Any]:
    """Replace every secret value with a safe placeholder; mark verified if the result rescans clean."""
    fixed = code
    first = findings[0]
    for f in sorted(findings, key=lambda x: x.start, reverse=True):
        if 0 <= f.start < f.end <= len(fixed):
            fixed = fixed[:f.start] + f"[protected:{f.kind}]" + fixed[f.end:]
    verified = bool(findings) and not detectors.scan_text(fixed)
    return {"before": _line_text(code, first.start), "after": _line_text(fixed, first.start),
            "verified": verified, "fixed_code": fixed, "count": len(findings)}


def analyze(code: str) -> Dict[str, Any]:
    findings = detectors.scan_text(code)
    risky = actions.scan_actions({"script": code})
    if not findings and not risky:
        return {"status": "ok", "lines": len(code.splitlines()) or 1, "sanitized": [], "known_gaps": KNOWN_GAPS}
    if findings:
        f = findings[0]
        return {
            "status": "leak", "line": _line_of(code, f.start), "code": _line_text(code, f.start),
            "why": f.title + ": " + _sink_human(f),
            "labels": sorted({x.label for x in findings}),
            "sources": [], "sink": {"name": f.kind, "human": _sink_human(f)},
            "quarantine": _quarantine(sorted({x.label for x in findings})),
            "autofix": _autofix(code, findings),
            "risky": [a.public() for a in risky], "known_gaps": KNOWN_GAPS,
        }
    a = risky[0]
    return {"status": "leak", "line": 0, "code": a.snippet[:240], "why": a.title + ". " + a.why,
            "labels": [], "sources": [], "sink": {"name": a.kind, "human": a.title}, "quarantine": [],
            "autofix": None, "risky": [x.public() for x in risky], "known_gaps": KNOWN_GAPS}


def report_html(code: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """HTML report for the sandboxed iframe. Fields are the plain, esc-free summary."""
    if result.get("status") == "ok":
        body = "<p>No secrets or dangerous actions were found in the pasted code.</p>"
    else:
        body = "<p>Line %s: %s</p>" % (result.get("line", "?"), _esc(str(result.get("why", ""))))
        q = result.get("quarantine") or []
        if q:
            body += "<p>Protections:</p><ul>" + "".join("<li>%s</li>" % _esc(it["label"]) for it in q) + "</ul>"
    html = ("<!doctype html><html lang=en><meta charset=utf-8><title>MCP Secrets Guard report</title>"
            "<body style='font:13px/1.5 system-ui;padding:16px;color:#222'>"
            "<h3>MCP Secrets Guard - report</h3>" + body + "</body></html>")
    return {"html": html}


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def run(argv=None, stdin=None, stdout=None) -> int:
    stdout = stdout or sys.stdout
    parser = argparse.ArgumentParser(prog="src.guard_api")
    parser.add_argument("command", choices=("analyze", "autofix", "report-text"))
    parser.add_argument("--stdin", action="store_true")
    parser.add_argument("--lang", default="en")
    args = parser.parse_args(argv)
    try:
        doc = json.loads((stdin or sys.stdin).read() or "{}")
    except ValueError:
        stdout.write(json.dumps({"status": "error", "message": "bad request"}))
        return 3
    code = doc.get("code", "")
    if not isinstance(code, str):
        stdout.write(json.dumps({"status": "error", "message": "no code to analyse"}))
        return 3
    try:
        if args.command == "report-text":
            result = report_html(code, analyze(code))
        elif args.command == "autofix":
            result = analyze(code)
            if isinstance(result, dict) and result.get("status") == "leak" and result.get("autofix"):
                result = {"status": "ok", "autofix": result["autofix"], "known_gaps": KNOWN_GAPS}
            else:
                result = {"status": "ok", "autofix": None, "known_gaps": KNOWN_GAPS}
        else:
            result = analyze(code)
    except Exception as exc:  # fail closed
        stdout.write(json.dumps({"status": "error", "message": "analyzer error: %s" % type(exc).__name__}))
        return 3
    stdout.write(json.dumps(result, ensure_ascii=False))
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
