"""Hermes runtime hook for mcp-secrets-guard.

Intercepts LLM tool invocations before execution, checks arguments for
sensitive data (API keys, private keys, passwords, credentials), and blocks
or tokenizes dangerous calls according to the active policy.

Integrity self-check:
Every startup hashes the core engine files against pinned values. Any modification
(e.g., adversary editing policy.py to whitelist their exfiltration endpoint) is
blocked as tampering by the engine's action rules.
"""
from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


# SHA-256 of core runtime modules — tampered files trigger fail-closed block.
_EXPECTED_HASHES = {
    "src/runtime/policy.py":      "8e59ae7db52106f6fa22c5ad8b086fca1f4c7dc9c061193bbc9e1e2f9d4778d7",
    "src/runtime/detectors.py":   "4ff9bbae387896196282e6680781ce670e46f0280842aee2beab78569f2dc0cc",
    "src/runtime/actions.py":    "f5e862d97c7ff11a5f3a4ece2dfdeae4c0f7026981c5741487bc1b57566dd50d",
    "src/runtime/aim_detect.py": "6782fd03b83c69769ac83305b0682b09ef95cf10cc65b37563b867a36bd02afd",
}

def _check_integrity() -> str | None:
    """Verify SHA-256 of critical runtime modules. Returns None if all match,
    or a string describing the first mismatch for the error message."""
    import importlib.util, sys
    plugin_dir = Path(__file__).resolve().parent
    config_path = plugin_dir / "config.json"
    if not config_path.is_file():
        return "cannot-read-config"
    home = None
    try:
        import json as _json
        cfg = _json.loads(config_path.read_text(encoding="utf-8"))
        if "engine_home" in cfg:
            cand = Path(cfg["engine_home"]).resolve()
            if (cand / "src" / "runtime" / "policy.py").is_file():
                home = cand
    except Exception:
        pass
    if not home and (plugin_dir / "src" / "runtime" / "policy.py").is_file():
        home = plugin_dir
    if not home or not home.is_dir():
        cand_roots = [
            plugin_dir.parent.parent.parent,
            Path.cwd(),
            Path(r"E:\загрузки\.gemini\antigravity\scratch\YadroLang-English-repo"),
        ]
        for cand in cand_roots:
            if cand and (cand / "src" / "runtime" / "policy.py").is_file():
                home = cand
                break
    if not home or not home.is_dir():
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

_PLUGIN_DIR = Path(__file__).resolve().parent
# Point the runtime policy's shared mode file at THIS plugin's config.json so the
# mode selected in the Guard tab dashboard reaches the hook in-process.
os.environ["YADRO_GUARD_MODE_FILE"] = os.environ.get("YADRO_GUARD_MODE_FILE", str(_PLUGIN_DIR / "config.json"))
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


def _on_pre_tool_call(tool_name: str = "", args: Any = None, **ctx: Any) -> Optional[dict]:
    if tool_name in _SKIP_TOOLS:
        return None
    policy = _load_policy()
    if policy is None:
        return {
            "action": "block",
            "message": "⛔ mcp-secrets-guard is installed but its engine could not be loaded, so this action "
                       f"was blocked for safety. Reinstall the plugin. ({_load_error})",
            "tool": tool_name,
        }
    try:
        return policy.check(tool_name, args, ctx)
    except Exception as exc:
        logger.exception("yadro-guard: check failed")
        return {
            "action": "block",
            "message": f"⛔ mcp-secrets-guard could not check this action ({type(exc).__name__}), "
                       "so it was blocked for safety.",
            "tool": tool_name,
        }


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)


hook = _on_pre_tool_call
