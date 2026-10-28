"""mcp-secrets-guard runtime hook for Hermes Agent.

Registers a ``pre_tool_call`` hook: before ANY agent tool runs (terminal,
browser, HTTP, file writes, MCP tools, messaging ...), its arguments are scanned
for secrets and sensitive data. A finding blocks the action and opens an
incident in the Guard tab, where the user chooses:
Protect & send / Block & quarantine / Allow once.

Fail-closed: if the guard itself fails, the tool call is BLOCKED, never silently
allowed. (Hermes also blocks on hook timeout for pre_tool_call.)
There is no environment-variable kill switch: an agent must never be able to turn
off its own guard. Attempts to modify the guard's own files, config or env are
blocked as tampering by the engine's action rules.

The detectors and policy are pure Python (no llvmlite), so they are imported
in-process from the engine folder configured in config.json.
"""
from __future__ import annotations

import logging
import hashlib
import os
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# SHA-256 of core runtime modules — tampered files trigger fail-closed block.
_EXPECTED_HASHES = {
    "src/runtime/policy.py":      "e622af7cfe095ad8c69f624da215d2bd884e5f522572003e0ba31b05e1bd2527",
    "src/runtime/detectors.py":   "487c974c016352ac2c0e4b72079584b990caf202f2b8d70aa8b18dac2e11e0bf",
    "src/runtime/actions.py":    "bd82b5a6942f7b4d1072117e2c121cf504422d5749989f1515d859db834b1c54",
    "src/runtime/aim_detect.py": "6782fd03b83c69769ac83305b0682b09ef95cf10cc65b37563b867a36bd02afd",
}

def _check_integrity() -> str | None:
    """Verify SHA-256 of critical runtime modules. Returns None if all match,
    or a string describing the first mismatch for the error message."""
    import importlib.util, sys
    # engine_home() logic duplicated here to avoid a circular import
    plugin_dir = Path(__file__).resolve().parent
    config_path = plugin_dir / "config.json"
    try:
        import json as _json
        cfg = _json.loads(config_path.read_text(encoding="utf-8"))
        home = Path(cfg["engine_home"]).resolve()
    except Exception:
        return "cannot-read-config"
    for rel_path, expected in _EXPECTED_HASHES.items():
        fp = home / rel_path
        try:
            # Normalize CRLF->LF so the Windows CI checkout (CRLF) matches
            # the local LF hashes — otherwise integrity fails closed on every
            # Windows runner. The LF forms are what is pinned in _EXPECTED_HASHES.
            data = fp.read_bytes().replace(b'\r\n', b'\n')
            actual = hashlib.sha256(data).hexdigest()
        except Exception:
            return f"cannot-read:{rel_path}"
        if actual != expected:
            return f"tampered:{rel_path}:{actual[:8]}!=expected"
    return None

def _load_policy():
    global _policy, _load_error
    if _policy is not None:
        return _policy
    integrity = _check_integrity()
    if integrity:
        msg = (f"⛔ mcp-secrets-guard integrity check failed ({integrity}). "
               "The runtime may have been tampered with. "
               "Blocked for safety. Reinstall the plugin.")
        logger.error("yadro-guard: INTEGRITY CHECK FAILED: %s", integrity)
        _load_error = msg
        return None
    try:
        from .engine_loader import load_policy
        _policy = load_policy()
    except Exception as exc:  # pragma: no cover - reported via fail-closed message
        _load_error = f"{type(exc).__name__}: {exc}"[:200]
        logger.error("yadro-guard: cannot load runtime policy: %s", _load_error)
    return _policy

_PLUGIN_DIR = Path(__file__).resolve().parent
_policy = None
_load_error = ""

# Read-only / internal tools that cannot exfiltrate data by themselves.
# read_file / search_files / glob are NOT skipped: their path args are checked for
# references to sensitive local files (see runtime.detectors.scan_sensitive_paths).
# Everything NOT listed here is scanned (unknown tools are guarded by default).
_SKIP_TOOLS = frozenset({"list_dir", "todo_write", "clarify"})


def _load_policy():
    global _policy, _load_error
    if _policy is not None:
        return _policy
    try:
        from .engine_loader import load_policy
        _policy = load_policy()
    except Exception as exc:  # pragma: no cover - reported via fail-closed message
        _load_error = f"{type(exc).__name__}: {exc}"[:200]
        logger.error("yadro-guard: cannot load runtime policy: %s", _load_error)
    return _policy


def _on_pre_tool_call(tool_name: str = "", args: Any = None, **ctx: Any) -> Optional[dict]:
    if tool_name in _SKIP_TOOLS:
        return None
    policy = _load_policy()
    if policy is None:
        return {"action": "block",
                "message": "⛔ mcp-secrets-guard is installed but its engine could not be loaded, so this action "
                           f"was blocked for safety. Reinstall the plugin. ({_load_error})"}
    try:
        return policy.check(tool_name, args, ctx)
    except Exception as exc:
        logger.exception("yadro-guard: check failed")
        return {"action": "block",
                "message": f"⛔ mcp-secrets-guard could not check this action ({type(exc).__name__}), "
                           "so it was blocked for safety."}


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
