"""mcp-secrets-guard вЂ” Hermes dashboard plugin backend (mounted at /api/plugins/yadro-guard/).

Design:
- The analysis engine runs in a SEPARATE process (its own Python with llvmlite)
  with a hard timeout, so an engine failure can never take Hermes down.
- Code and secrets reach the engine through stdin, never through process
  arguments (those are visible to other processes and logs).
- Fail-closed: any engine problem is reported as an error, never as "clean".
- The vault never returns secret values over HTTP: only token metadata.
- History stores titles, verdicts and labels only, never the code itself.
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

try:
    from fastapi import APIRouter
    from pydantic import BaseModel
except Exception:  # pragma: no cover - local tests without FastAPI
    class APIRouter:  # type: ignore
        def get(self, *_a, **_k):
            return lambda fn: fn

        def post(self, *_a, **_k):
            return lambda fn: fn

    class BaseModel:  # type: ignore
        def __init__(self, **kw):
            self.__dict__.update(kw)

def _same_origin_guard():
    """CSRF guard for every POST: a web page in the user's browser must not be able to approve
    an incident, purge the vault or change the firewall. Browsers cannot send a custom header
    or application/json cross-origin without a CORS preflight, which this API never grants."""
    try:
        from fastapi import Request
        from fastapi.responses import JSONResponse
    except Exception:  # pragma: no cover - local tests without FastAPI
        return []

    async def guard(request: Request):
        ctype = request.headers.get("content-type", "").split(";")[0].strip().lower()
        origin = request.headers.get("origin", "")
        host = origin.split("://", 1)[-1].split("/")[0].rsplit(":", 1)[0].strip("[]").lower() if origin else ""
        ok_origin = (not origin or origin == "null" or origin.startswith(("app://", "file://"))
                     or host in ("127.0.0.1", "localhost", "::1"))
        # Web dashboard (http origin) must also send our header; Hermes Desktop's ctx.rest
        # (app:// / no origin) cannot add headers, JSON + origin check covers it.
        needs_header = origin.startswith(("http://", "https://"))
        if request.method == "POST" and (ctype != "application/json" or not ok_origin
                                         or (needs_header and request.headers.get("x-mcp-secrets-guard") != "1")):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Request refused: not from the Guard tab.")
    # `from __future__ import annotations` turns the hint into a string FastAPI cannot resolve
    # here (Request is a local import), so set the real class explicitly.
    guard.__annotations__["request"] = Request
    from fastapi import Depends
    return [Depends(guard)]


try:
    router = APIRouter(dependencies=_same_origin_guard())
except TypeError:  # pragma: no cover - fallback APIRouter without arguments
    router = APIRouter()

PLUGIN_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = PLUGIN_DIR / "config.json"
HISTORY_FILE = PLUGIN_DIR / "history.json"
TIMEOUT_S = 60
MAX_CODE = 200_000
MAX_SECRET = 4_096
MAX_HISTORY = 30
LABELS = ("PII", "Financial", "Health", "Credentials", "Location")
ENGINE_ENV = {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


def _config() -> Dict[str, str]:
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _error(message: str) -> Dict[str, Any]:
    return {"status": "error", "message": message}


def _engine(args: List[str], stdin_obj: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg = _config()
    home, python = cfg.get("engine_home"), cfg.get("python")
    if not home or not python or not Path(home).is_dir():
        return _error("mcp-secrets-guard is not set up yet. Run the installer once, then reload Hermes.")
    try:
        res = subprocess.run([python, "-m", *args], cwd=home, capture_output=True, text=True,
                             encoding="utf-8", timeout=TIMEOUT_S,
                             input=json.dumps(stdin_obj) if stdin_obj is not None else "",
                             env={**os.environ, **ENGINE_ENV})
    except subprocess.TimeoutExpired:
        return _error(f"The analyzer did not answer within {TIMEOUT_S} seconds.")
    except OSError:
        return _error("The analyzer could not be started. Check the Python path in config.json.")
    out = res.stdout.strip()
    try:
        return json.loads(out.splitlines()[-1]) if out else _error("The analyzer returned nothing.")
    except (json.JSONDecodeError, IndexError):
        return _error("The analyzer returned an unreadable answer.")


def _history() -> list:
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _remember(title: str, result: Dict[str, Any]) -> None:
    item = {"title": (title or "untitled")[:80], "status": result.get("status"),
            "labels": [l.get("label") for l in result.get("labels", [])], "at": int(time.time())}
    items = [item] + [h for h in _history() if h.get("title") != item["title"]]
    try:
        HISTORY_FILE.write_text(json.dumps(items[:MAX_HISTORY], ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


class CodeBody(BaseModel):
    code: str
    title: str = ""


class SecretBody(BaseModel):
    secret: str
    label: str
    title: str = ""


def _check_code(code: Any) -> str | None:
    if not isinstance(code, str) or not code.strip():
        return "Paste some code first."
    if len(code.encode("utf-8")) > MAX_CODE:
        return "This code is too large (limit 200 KB)."
    return None


async def _code_call(cmd: str, body: "CodeBody") -> Dict[str, Any]:
    problem = _check_code(getattr(body, "code", None))
    if problem:
        return _error(problem)
    return await asyncio.to_thread(_engine, ["src.guard_api", cmd, "--stdin", "--lang", "en"],
                                   {"code": body.code})


@router.post("/analyze")
async def analyze(body: "CodeBody") -> Dict[str, Any]:
    result = await _code_call("analyze", body)
    if result.get("status") in ("ok", "leak"):
        _remember(getattr(body, "title", "") or body.code.strip().splitlines()[0], result)
    return result


@router.post("/autofix")
async def autofix(body: "CodeBody") -> Dict[str, Any]:
    return await _code_call("autofix", body)


@router.post("/report")
async def report(body: "CodeBody") -> Dict[str, Any]:
    return await _code_call("report-text", body)


@router.get("/history")
async def history() -> Dict[str, Any]:
    return {"items": _history()}


@router.get("/vault")
async def vault() -> Dict[str, Any]:
    """Token metadata only. Secret values are never sent over HTTP."""
    result = await asyncio.to_thread(_engine, ["src.vault", "list-json"])
    return result


@router.post("/vault")
async def vault_put(body: "SecretBody") -> Dict[str, Any]:
    secret, label = getattr(body, "secret", ""), getattr(body, "label", "")
    title = str(getattr(body, "title", ""))[:80]
    if not isinstance(secret, str) or not secret:
        return _error("Enter the secret value.")
    if len(secret) > MAX_SECRET:
        return _error("This secret is too long (limit 4 KB).")
    if label not in LABELS:
        return _error("Choose what kind of data this is.")
    return await asyncio.to_thread(_engine, ["src.vault", "put-json"], {"secret": secret, "label": label, "title": title})


MAX_FILE_B64 = 14_000_000            # ~10 MB file after base64
VAULT_OPS = ("rename", "relabel", "replace", "trash", "restore", "purge", "save")
_TOKEN_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")


class FileBody(BaseModel):
    data: str                         # base64 of the file
    filename: str
    label: str
    title: str = ""


class VaultOpBody(BaseModel):
    op: str
    token: str
    title: str = ""
    label: str = ""
    secret: str = ""


@router.post("/vault/file")
async def vault_file(body: "FileBody") -> Dict[str, Any]:
    data, label = getattr(body, "data", ""), getattr(body, "label", "")
    if not isinstance(data, str) or not data:
        return _error("Choose a file first.")
    if len(data) > MAX_FILE_B64:
        return _error("This file is too large (limit 10 MB).")
    if label not in LABELS:
        return _error("Choose what kind of data this is.")
    return await asyncio.to_thread(_engine, ["src.vault", "op-json"],
                                   {"op": "file", "data": data, "label": label,
                                    "filename": str(getattr(body, "filename", ""))[:200],
                                    "title": str(getattr(body, "title", ""))[:80]})


@router.post("/vault/op")
async def vault_op(body: "VaultOpBody") -> Dict[str, Any]:
    """Manage an entry. Never returns a secret value; 'save' writes a file copy to Downloads."""
    op, token = str(getattr(body, "op", "")), str(getattr(body, "token", ""))
    if op not in VAULT_OPS:
        return _error("Unknown operation.")
    if not (token.startswith("msg_tok_") or token.startswith("yg_tok_")) or len(token) > 80 or not set(token) <= _TOKEN_CHARS:
        return _error("Unknown entry.")
    secret = getattr(body, "secret", "")
    if op == "replace" and (not isinstance(secret, str) or not secret or len(secret) > MAX_SECRET):
        return _error("Enter the new value (limit 4 KB).")
    if op == "relabel" and getattr(body, "label", "") not in LABELS:
        return _error("Choose what kind of data this is.")
    return await asyncio.to_thread(_engine, ["src.vault", "op-json"],
                                   {"op": op, "token": token, "title": str(getattr(body, "title", ""))[:80],
                                    "label": getattr(body, "label", ""), "secret": secret})


class DecisionBody(BaseModel):
    incident: str
    choice: str


def _policy():
    """Same in-process policy module the runtime hook uses, under a unique package name."""
    import importlib.util
    import sys
    loader_name = "yadro_guard_engine_loader"
    try:
        if loader_name not in sys.modules:
            spec = importlib.util.spec_from_file_location(loader_name, PLUGIN_DIR / "engine_loader.py")
            mod = importlib.util.module_from_spec(spec)
            sys.modules[loader_name] = mod
            spec.loader.exec_module(mod)
        return sys.modules[loader_name].load_policy()
    except Exception:
        return None


def _engine_module(name: str):
    import sys
    _policy()   # ensures the loader is registered
    loader = sys.modules.get("yadro_guard_engine_loader")
    try:
        return loader.load_module(name) if loader else None
    except Exception:
        return None


_EXPOSURE_CACHE: Dict[str, Any] = {}
_EXPOSURE_TTL = 30


@router.get("/exposure")
async def exposure(refresh: int = 0) -> Dict[str, Any]:
    """Read-only scan of listening ports. Cached briefly: the scan takes ~10 s."""
    cached = _EXPOSURE_CACHE.get("result")
    if cached and not refresh and time.time() - _EXPOSURE_CACHE.get("at", 0) < _EXPOSURE_TTL:
        return cached
    mod = _engine_module("exposure")
    if mod is None:
        return _error("mcp-secrets-guard is not set up yet.")
    try:
        result = await asyncio.to_thread(mod.scan)
    except Exception:
        return _error("The exposure scan failed. Nothing was changed on this computer.")
    _EXPOSURE_CACHE.update(result=result, at=time.time())
    return result


class RemedyBody(BaseModel):
    action: str
    proto: str = ""
    port: int = 0
    pid: int = -1
    fix: str = ""
    page: str = ""


REMEDY_ACTIONS = ("block_port", "unblock", "disable_service", "stop_program", "show_file", "trust", "untrust")


@router.post("/exposure/act")
async def exposure_act(body: "RemedyBody") -> Dict[str, Any]:
    """Do something about a listener. System changes ask Windows (UAC) for confirmation."""
    mod = _engine_module("remedy")
    if mod is None:
        return _error("mcp-secrets-guard is not set up yet.")
    action = str(getattr(body, "action", ""))
    try:
        if action == "undo":
            fix = str(getattr(body, "fix", ""))[:16]
            result = await asyncio.to_thread(mod.undo, fix)
        elif action == "settings":
            result = await asyncio.to_thread(mod.open_settings, str(getattr(body, "page", "")))
        elif action in REMEDY_ACTIONS:
            result = await asyncio.to_thread(mod.run, action, str(getattr(body, "proto", "")),
                                             getattr(body, "port", 0), getattr(body, "pid", -1))
        else:
            return _error("Unknown action.")
    except mod.RemedyError as e:
        return _error(str(e))
    except Exception:
        return _error("The action failed. Nothing was changed.")
    _EXPOSURE_CACHE.clear()
    return result


@router.get("/exposure/fixes")
async def exposure_fixes() -> Dict[str, Any]:
    mod = _engine_module("remedy")
    if mod is None:
        return _error("mcp-secrets-guard is not set up yet.")
    return {"status": "ok", "items": (await asyncio.to_thread(mod.journal))[:30]}


@router.get("/incidents")
async def incidents() -> Dict[str, Any]:
    pol = _policy()
    if pol is None:
        return _error("mcp-secrets-guard is not set up yet.")
    items = await asyncio.to_thread(pol.list_incidents, 100)
    return {"status": "ok", "items": items,
            "pending": sum(1 for i in items if i.get("status") == "pending")}


@router.post("/incidents/decide")
async def decide(body: "DecisionBody") -> Dict[str, Any]:
    pol = _policy()
    if pol is None:
        return _error("mcp-secrets-guard is not set up yet.")
    incident, choice = str(getattr(body, "incident", ""))[:32], str(getattr(body, "choice", ""))
    if choice not in ("protect", "block", "allow"):
        return _error("Unknown choice.")
    return await asyncio.to_thread(pol.decide, incident, choice)


class RevealBody(BaseModel):
    incident: str
    index: int


@router.post("/incidents/reveal")
async def reveal(body: "RevealBody") -> Dict[str, Any]:
    """Full value of a caught secret for the hold-to-show eye button (CSRF-guarded, audited)."""
    pol = _policy()
    if pol is None:
        return _error("mcp-secrets-guard is not set up yet.")
    incident, index = str(getattr(body, "incident", ""))[:32], getattr(body, "index", -1)
    if not isinstance(index, int) or isinstance(index, bool):
        return _error("Unknown finding.")
    return await asyncio.to_thread(pol.reveal, incident, index)


@router.get("/health")
async def health() -> Dict[str, Any]:
    cfg = _config()
    ok = bool(cfg.get("engine_home")) and Path(cfg.get("engine_home", "")).is_dir()
    return {"status": "ok" if ok else "error", "configured": ok}


def _get_hermes_session_titles() -> Dict[str, Any]:
    out: Dict[str, str] = {}
    latest_id = ""
    latest_title = ""
    db_paths = [
        Path.home() / "AppData" / "Local" / "hermes" / "state.db",
        Path.home() / "AppData" / "Local" / "Hermes" / "state.db",
        Path.home() / ".hermes" / "state.db"
    ]
    for db in db_paths:
        if db.exists():
            try:
                import sqlite3
                con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=1.0)
                cur = con.cursor()
                for sid, dname, title in cur.execute(
                    "SELECT id, display_name, title FROM sessions "
                    "WHERE display_name IS NOT NULL OR title IS NOT NULL "
                    "ORDER BY COALESCE(last_activity_at, 0) DESC"
                ):
                    t = str(dname or title or "").strip()
                    if sid and t:
                        if not latest_id:
                            latest_id = str(sid)
                            latest_title = t
                        out[str(sid)] = t
                        out[str(sid)[-6:]] = t
                con.close()
                if out:
                    break
            except Exception:
                pass
    return {"titles": out, "active_id": latest_id, "active_title": latest_title}


@router.get("/sessions/titles")
async def session_titles() -> Dict[str, Any]:
    data = await asyncio.to_thread(_get_hermes_session_titles)
    return {
        "status": "ok",
        "titles": data["titles"],
        "active_id": data["active_id"],
        "active_title": data["active_title"],
        "__isLive": True
    }


# Enrich incidents with human session titles if not already present
@router.get("/incidents")
async def incidents() -> Dict[str, Any]:
    pol = _policy()
    if pol is None:
        return _error("mcp-secrets-guard is not set up yet.")
    items = await asyncio.to_thread(pol.list_incidents, 100)
    data = await asyncio.to_thread(_get_hermes_session_titles)
    titles = data["titles"]
    for inc in items:
        if isinstance(inc.get("id"), str) and inc["id"].startswith("YG-"):
            inc["id"] = "MSG-" + inc["id"][3:]
        agent = inc.get("agent")
        if isinstance(agent, dict):
            sid = str(agent.get("session_id", ""))
            if sid and not agent.get("chat_title"):
                resolved = titles.get(sid) or titles.get(sid[-6:])
                if resolved:
                    agent["chat_title"] = resolved
                    inc["chat_title"] = resolved
    return {
        "status": "ok",
        "items": items,
        "pending": sum(1 for i in items if i.get("status") == "pending"),
        "active_session": data.get("active_id", ""),
        "active_chat_title": data.get("active_title", ""),
        "__isLive": True
    }


RULES_FILE = PLUGIN_DIR / "rules.json"


def _read_rules() -> list:
    try:
        return json.loads(RULES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write_rules(rules: list) -> None:
    try:
        RULES_FILE.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


class RuleBody(BaseModel):
    action: str = ""       # "block" | "allow"
    match_type: str = ""   # "domain" | "tool"
    match: str = ""
    incident: str = ""


@router.get("/rules")
async def list_rules() -> Dict[str, Any]:
    return {"status": "ok", "items": _read_rules()}


@router.post("/rules")
async def create_rule(body: "RuleBody") -> Dict[str, Any]:
    action = getattr(body, "action", "")
    match_type = getattr(body, "match_type", "")
    match = str(getattr(body, "match", "")).strip()
    if action not in ("block", "allow") or match_type not in ("domain", "tool") or not match:
        return _error("Invalid rule format.")
    rules = _read_rules()
    new_rule = {
        "id": "RULE-" + str(int(time.time()))[-6:],
        "action": action,
        "match_type": match_type,
        "match": match,
        "created_at": int(time.time()),
        "incident": getattr(body, "incident", "")
    }
    rules = [r for r in rules if not (r.get("match_type") == match_type and r.get("match") == match)]
    rules.insert(0, new_rule)
    _write_rules(rules[:200])
    return {"status": "ok", "rule": new_rule}


class DeleteRuleBody(BaseModel):
    id: str = ""
    match: str = ""


@router.post("/rules/delete")
async def delete_rule(body: "DeleteRuleBody") -> Dict[str, Any]:
    rid, match = getattr(body, "id", ""), getattr(body, "match", "")
    rules = _read_rules()
    before = len(rules)
    rules = [r for r in rules if r.get("id") != rid and r.get("match") != match]
    if len(rules) == before:
        return _error("Rule not found.")
    _write_rules(rules)
    return {"status": "ok"}


class IncidentOpBody(BaseModel):
    incident: str = ""
    scope: str = ""


@router.post("/incidents/delete")
async def delete_incident(body: "IncidentOpBody") -> Dict[str, Any]:
    inc_id = getattr(body, "incident", "")
    if not inc_id:
        return _error("Missing incident ID.")
    pol = _policy()
    if pol is None:
        return _error("mcp-secrets-guard is not set up yet.")
    try:
        incs = pol._read("incidents.json", [])
        new_incs = [i for i in incs if i.get("id") != inc_id]
        pol._write("incidents.json", new_incs)
        return {"status": "ok"}
    except Exception as e:
        return _error(f"Could not delete incident: {e}")


@router.post("/incidents/clear")
async def clear_incidents(body: "IncidentOpBody") -> Dict[str, Any]:
    pol = _policy()
    if pol is None:
        return _error("mcp-secrets-guard is not set up yet.")
    try:
        incs = pol._read("incidents.json", [])
        new_incs = [i for i in incs if i.get("status") == "pending"]
        pol._write("incidents.json", new_incs)
        return {"status": "ok"}
    except Exception as e:
        return _error(f"Could not clear incidents: {e}")


class ConfigUpdateBody(BaseModel):
    lang: str = ""
    arena_mode: str = ""
    fail_closed: bool | None = None
    notifications: bool | None = None
    guard_mode: str = ""
    paused_until: int | None = None


@router.get("/config")
async def get_config() -> Dict[str, Any]:
    return {"status": "ok", "config": _config()}


@router.post("/config")
async def update_config(body: "ConfigUpdateBody") -> Dict[str, Any]:
    cfg = _config()
    if getattr(body, "lang", ""):
        cfg["lang"] = getattr(body, "lang")
    if getattr(body, "arena_mode", ""):
        cfg["arena_mode"] = getattr(body, "arena_mode")
    if getattr(body, "fail_closed", None) is not None:
        cfg["fail_closed"] = bool(getattr(body, "fail_closed"))
    if getattr(body, "notifications", None) is not None:
        cfg["notifications"] = bool(getattr(body, "notifications"))
    if getattr(body, "guard_mode", ""):
        cfg["guard_mode"] = getattr(body, "guard_mode")
    if getattr(body, "paused_until", None) is not None:
        cfg["paused_until"] = int(getattr(body, "paused_until"))
    try:
        CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        return _error(f"Could not save config: {e}")
    return {"status": "ok", "config": cfg}


class GuardModeBody(BaseModel):
    mode: str = "active"             # "active" | "paused" | "disabled" | "monitor"
    duration_minutes: int = 5


@router.get("/guard/status")
async def guard_status() -> Dict[str, Any]:
    cfg = _config()
    mode = cfg.get("guard_mode", "active")
    paused_until = cfg.get("paused_until", 0)
    now = int(time.time())
    rem = max(0, paused_until - now) if paused_until else 0
    if mode == "paused" and rem <= 0:
        mode = "active"
    return {
        "status": "ok",
        "mode": mode,
        "paused_until": paused_until,
        "remaining_seconds": rem,
        "fail_closed": cfg.get("fail_closed", True)
    }


@router.post("/guard/mode")
async def guard_mode(body: "GuardModeBody") -> Dict[str, Any]:
    cfg = _config()
    mode = getattr(body, "mode", "active")
    if mode not in ("active", "paused", "disabled", "monitor"):
        return _error("Unknown mode.")
    now = int(time.time())
    if mode == "paused":
        mins = getattr(body, "duration_minutes", 5) or 5
        cfg["paused_until"] = now + (mins * 60)
    else:
        cfg["paused_until"] = 0
    cfg["guard_mode"] = mode
    try:
        CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        return _error(f"Could not save config: {e}")
    rem = max(0, cfg["paused_until"] - now) if cfg["paused_until"] else 0
    return {
        "status": "ok",
        "mode": mode,
        "paused_until": cfg["paused_until"],
        "remaining_seconds": rem,
        "fail_closed": cfg.get("fail_closed", True)
    }

