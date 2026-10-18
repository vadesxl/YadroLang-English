# -*- coding: utf-8 -*-
"""Quarantine vault: the real secret stays local, only a token goes out.

    python -m src.vault put  --label Credentials   (secret is read from stdin)
    python -m src.vault get  <token> --i-have-mandate (retrieve the original)
    python -m src.vault list                          (metadata only)
    python -m src.vault forget <token>

Protection:
- Windows DPAPI encryption (CryptProtectData): the key is tied to the Windows
  user account, the vault file is useless on another PC/user. No third-party libs.
- Fail-closed: if reliable encryption is unavailable (not Windows), the vault REFUSES
  to save — it never writes the secret in plaintext.
- Token is random (secrets.token_hex): the secret cannot be recovered from it.
- Releasing the original requires an explicit mandate and is logged in the issuance log.
- Token format yg_tok_<label>_<hex>: the label is visible, the value is not.
"""
import base64
import json
import os
import secrets
import sys
import time
from pathlib import Path

VAULT_VERSION = 1
_labels = {"ПДн", "Финансы", "Здоровье", "УчетныеДанные", "Локация"}
_token_en_label = {"ПДн": "PII", "Финансы": "Financial", "Здоровье": "Health",
                    "УчетныеДанные": "Credentials", "Локация": "Location"}
_entropy = b"yadro-guard-vault-v1"


class VaultError(Exception):
    pass


# ---------- DPAPI ----------
def _cipher_available() -> bool:
    return os.name == "nt"


def _dpapi(data: bytes, encrypt: bool) -> bytes:
    if not _cipher_available():
        raise VaultError("reliable encryption is unavailable on this OS: the vault refuses to store secrets")
    import ctypes
    from ctypes import wintypes

    class BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    def blob(b):
        buf = ctypes.create_string_buffer(b, len(b))
        return BLOB(len(b), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))), buf

    entry, _hold = blob(data)
    entr, _hold2 = blob(_entropy)
    output = BLOB()
    crypt32, kernel32 = ctypes.windll.crypt32, ctypes.windll.kernel32
    CRYPTPROTECT_UI_FORBIDDEN = 0x1
    fn = crypt32.CryptProtectData if encrypt else crypt32.CryptUnprotectData
    ok = fn(ctypes.byref(entry), None, ctypes.byref(entr), None, None,
            CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(output))
    if not ok:
        raise VaultError("DPAPI could not process the data (different user/PC or corrupted file)")
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        kernel32.LocalFree(output.pbData)


# ---------- vault ----------
def vault_path():
    base = os.environ.get("YADRO_VAULT_DIR") or (Path(os.environ.get("LOCALAPPDATA", Path.home())) / "yadro-guard")
    return Path(base) / "vault.json"


def _load():
    p = vault_path()
    if not p.exists():
        return {"version": VAULT_VERSION, "items": {}, "audit": []}
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("version") != VAULT_VERSION or not isinstance(data.get("items"), dict):
        raise VaultError("unknown vault format")
    return data


def _save(data):
    p = vault_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    temporary = p.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(temporary, p)  # atomic: the vault is never "half-written"


def put(secret: str, label: str, title: str = "") -> str:
    if label not in _labels:
        raise VaultError(f"unknown label: {label}")
    if not secret:
        raise VaultError("empty secret")
    cipher = _dpapi(secret.encode("utf-8"), True)  # fails BEFORE writing if there is no encryption
    # Token is ASCII-only: it goes into HTTP headers, URLs, and JSON of external services.
    token = f"msg_tok_{_token_en_label[label]}_{secrets.token_hex(16)}"
    data = _load()
    data["items"][token] = {"label": label, "created": int(time.time()),
                             "title": str(title)[:MAX_NAME] if title else "",
                             "source": "manual",
                             "blob": base64.b64encode(cipher).decode("ascii")}
    _save(data)
    return token


def put_unique(secret: str, label: str, fingerprint: str, title: str = "") -> str:
    """Like put(), but the same secret (by SHA-256) is stored only once."""
    data = _load()
    for token, record in data["items"].items():
        if record.get("fp") == fingerprint:
            return token
    token = put(secret, label)
    data = _load()
    data["items"][token]["fp"] = fingerprint
    data["items"][token]["title"] = title[:80]
    data["items"][token]["source"] = "runtime-quarantine"
    _save(data)
    return token


_label_en = {"ПДн": "PII", "Финансы": "Financial", "Здоровье": "Health",
             "УчетныеДанные": "Credentials", "Локация": "Location"}
MAX_FOR_CHECK = 500
MAX_FILE_FOR_CHECK = 4096


def known_values():
    """(value, label_en, name) for precise search of your secrets in agent traffic.
    Decryption only in process memory; values never leak outside."""
    if not _cipher_available() or not vault_path().exists():
        return []
    out = []
    for record in list(_load()["items"].values())[:MAX_FOR_CHECK]:
        if record.get("deleted"):
            continue
        if record.get("kind") == "file":          # we also search for small text files (.env, keys) in traffic
            if record.get("size", 0) > MAX_FILE_FOR_CHECK:
                continue
            try:
                text = _dpapi(base64.b64decode(record["blob"]), False).decode("utf-8").strip()
            except (VaultError, ValueError):
                continue
            if len(text) >= 16:
                out.append((text, _label_en.get(record["label"], "Credentials"),
                            record.get("title") or "A file from your vault"))
            continue
        try:
            value = _dpapi(base64.b64decode(record["blob"]), False).decode("utf-8")
        except (VaultError, ValueError):
            continue
        out.append((value, _label_en.get(record["label"], "Credentials"),
                    record.get("title") or "A secret from your vault"))
    return out


def get(token: str, mandate: bool, reason: str = "") -> str:
    if not mandate:
        raise VaultError("releasing the original requires an explicit mandate (--i-have-mandate)")
    data = _load()
    record = data["items"].get(token)
    if not record or record.get("deleted"):         # value is not released from the trash
        raise VaultError("token not found")
    secret = _dpapi(base64.b64decode(record["blob"]), False).decode("utf-8")
    data["audit"].append({"token": token, "at": int(time.time()), "reason": reason[:200]})
    _save(data)
    return secret


def items(with_trash: bool = False):
    """Metadata only: token, label, time. Values are not decrypted."""
    data = _load()
    if _clear_trash(data):
        _save(data)
    out = []
    for t, z in data["items"].items():
        if z.get("deleted") and not with_trash:
            continue
        d = {"token": t, "label": _label_en.get(z["label"], z["label"]), "created": z["created"],
             "title": z.get("title", ""), "source": z.get("source", "manual")}
        if with_trash:
            d.update(kind=z.get("kind", "text"), filename=z.get("filename", ""), size=z.get("size", 0),
                     changed=z.get("changed", 0), deleted=z.get("deleted", 0))
        out.append(d)
    return out


def forget(token: str) -> bool:
    data = _load()
    was = data["items"].pop(token, None) is not None
    if was:
        _save(data)
    return was


# ---------- record management: files, name, replacement, trash ----------
MAX_FILE = 10 * 1024 * 1024          # 10 MB: DPAPI and JSON safe are designed for small files
MAX_NAME = 80
TRASH_DAYS = 30


def _record(data, token: str):
    record = data["items"].get(token)
    if not record:
        raise VaultError("record not found")
    return record


def _filename(name: str) -> str:
    """Name only, no folders or Windows-forbidden characters (path traversal protection)."""
    name = (name or "").replace("\\", "/").split("/")[-1]
    name = "".join("_" if (ord(c) < 32 or c in '<>:"|?*') else c for c in name).strip(" .")
    return (name or "file")[:120]


def put_file(contents: bytes, filename: str, label: str, title: str = "") -> str:
    """File is encrypted entirely (DPAPI). Only token and metadata are exposed."""
    if not isinstance(contents, (bytes, bytearray)) or not contents:
        raise VaultError("empty file")
    if len(contents) > MAX_FILE:
        raise VaultError("file larger than 10 MB")
    if label not in _labels:
        raise VaultError(f"unknown label: {label}")
    import hashlib
    cipher = _dpapi(bytes(contents), True)
    token = f"msg_tok_{_token_en_label[label]}_{secrets.token_hex(16)}"
    name = _filename(filename)
    data = _load()
    data["items"][token] = {"label": label, "created": int(time.time()), "kind": "file",
                              "blob": base64.b64encode(cipher).decode("ascii"), "filename": name,
                              "size": len(contents), "sha256": hashlib.sha256(contents).hexdigest(),
                              "title": (title or name)[:MAX_NAME], "source": "manual"}
    _save(data)
    return token


def rename(token: str, title: str) -> None:
    title = (title or "").strip()
    if not title:
        raise VaultError("empty name")
    data = _load()
    _record(data, token)["title"] = title[:MAX_NAME]
    _save(data)


def change_label(token: str, label: str) -> None:
    """Only the data type description changes; the token stays the same to avoid breaking agents."""
    if label not in _labels:
        raise VaultError(f"unknown label: {label}")
    data = _load()
    _record(data, token)["label"] = label
    _save(data)


def replace(token: str, secret: str) -> None:
    """New value under the same token (key changed). Old value is not shown."""
    if not secret:
        raise VaultError("empty secret")
    data = _load()
    record = _record(data, token)
    if record.get("kind") == "file":
        raise VaultError("this is a file: upload a new file")
    record["blob"] = base64.b64encode(_dpapi(secret.encode("utf-8"), True)).decode("ascii")
    record["changed"] = int(time.time())
    record.pop("fp", None)
    _save(data)


def to_trash(token: str) -> None:
    data = _load()
    _record(data, token)["deleted"] = int(time.time())
    _save(data)


def restore(token: str) -> None:
    data = _load()
    _record(data, token).pop("deleted", None)
    _save(data)


def delete_forever(token: str) -> None:
    data = _load()
    if not _record(data, token).get("deleted"):
        raise VaultError("first move the record to trash")
    data["items"].pop(token)
    _save(data)


def _clear_trash(data) -> bool:
    term = int(time.time()) - TRASH_DAYS * 86400
    old = [t for t, z in data["items"].items() if z.get("deleted") and z["deleted"] < term]
    for t in old:
        data["items"].pop(t)
    return bool(old)


LABELS_EN = {"PII": "ПДн", "Financial": "Финансы", "Health": "Здоровье",
             "Credentials": "УчетныеДанные", "Location": "Локация"}


def put_json():
    """For integrations: JSON {"secret": "...", "label": "Credentials"|"УчетныеДанные"} to stdin.

    Secret is passed only via stdin (not via process arguments, not to log).
    Response: {"status": "ok", "token": ..., "label": ...} or {"status": "error", "message": ...}.
    """
    try:
        data = json.loads(sys.stdin.read() or "{}")
        label = LABELS_EN.get(data.get("label", ""), data.get("label", ""))
        title = str(data.get("title", "")).strip()[:MAX_NAME]
        token = put(str(data.get("secret", "")), label, title=title)
        return {"status": "ok", "token": token, "label": data.get("label"), "title": title}
    except VaultError as e:
        return {"status": "error", "message": str(e)}
    except (ValueError, TypeError):
        return {"status": "error", "message": "bad request"}


def _downloads_folder() -> Path:
    if os.name == "nt":
        try:   # the real Downloads folder, even if it was moved to another drive
            import ctypes
            import uuid
            g = (ctypes.c_byte * 16).from_buffer_copy(uuid.UUID("374DE290-123F-4565-9164-39C4925E467B").bytes_le)
            buf = ctypes.c_wchar_p()
            if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(g), 0, None, ctypes.byref(buf)) == 0:
                path = Path(buf.value)
                ctypes.windll.ole32.CoTaskMemFree(buf)
                return path
        except Exception:
            pass
    return Path.home() / "Downloads"


def save_file(token: str, folder=None) -> str:
    """Decrypt the file and write a copy to Downloads — only on an explicit user command.
    The contents are not sent over HTTP: the file is written to this PC's disk, the output goes to the log."""
    data = _load()
    record = _record(data, token)
    if record.get("kind") != "file":
        raise VaultError("this is not a file")
    contents = _dpapi(base64.b64decode(record["blob"]), False)
    where = Path(folder) if folder else _downloads_folder()
    where.mkdir(parents=True, exist_ok=True)
    name = _filename(record.get("filename", "file"))
    stem, suf = os.path.splitext(name)
    target, n = where / name, 1
    while target.exists():
        target, n = where / f"{stem} ({n}){suf}", n + 1
    with open(target, "xb") as f:          # x: never overwrite an existing file
        f.write(contents)
    data["audit"].append({"token": token, "at": int(time.time()), "reason": "saved to disk by the user"})
    _save(data)
    return str(target)


def operation_json() -> dict:
    """For integrations: JSON {"op": ..., "token": ..., ...} on stdin. Does not return secret values."""
    try:
        z = json.loads(sys.stdin.read() or "{}")
        op, token = z.get("op"), str(z.get("token", ""))
        label = LABELS_EN.get(z.get("label", ""), z.get("label", ""))
        if op == "file":
            contents = base64.b64decode(str(z.get("data", "")), validate=True)
            return {"status": "ok", "token": put_file(contents, str(z.get("filename", "")), label,
                                                           str(z.get("title", "")))}
        if op == "save":
            return {"status": "ok", "path": save_file(token)}
        actions = {"rename": lambda: rename(token, str(z.get("title", ""))),
                    "relabel": lambda: change_label(token, label),
                    "replace": lambda: replace(token, str(z.get("secret", ""))),
                    "trash": lambda: to_trash(token), "restore": lambda: restore(token),
                    "purge": lambda: delete_forever(token)}
        if op not in actions:
            return {"status": "error", "message": "unknown operation"}
        actions[op]()
        return {"status": "ok"}
    except VaultError as e:
        return {"status": "error", "message": str(e)}
    except (ValueError, TypeError, OSError):
        return {"status": "error", "message": "bad request"}


def main(argv=None):
    import argparse
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["put-json"]:
        result = put_json()
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["status"] == "ok" else 3
    if args == ["op-json"]:
        result = operation_json()
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["status"] == "ok" else 3
    if args == ["list-json"]:
        try:
            print(json.dumps({"status": "ok", "items": items(with_trash=True)}, ensure_ascii=False))
            return 0
        except (VaultError, ValueError, OSError):
            print(json.dumps({"status": "error", "message": "The vault is not available."}))
            return 3
    p = argparse.ArgumentParser(prog="yadro-guard vault")
    sub = p.add_subparsers(dest="cmd", required=True)
    put = sub.add_parser("put"); put.add_argument("--label", required=True)
    get = sub.add_parser("get"); get.add_argument("token")
    get.add_argument("--i-have-mandate", action="store_true"); get.add_argument("--reason", default="")
    sub.add_parser("list")
    fg = sub.add_parser("forget"); fg.add_argument("token")
    a = p.parse_args(args)
    try:
        if a.cmd == "put":
            secret = sys.stdin.read().rstrip("\r\n")  # not from arguments: doesn't show up in command history
            print(put(secret, a.label))
        elif a.cmd == "get":
            print(get(a.token, a.i_have_mandate, a.reason))
        elif a.cmd == "list":
            print(json.dumps(items(), ensure_ascii=False, indent=1))
        else:
            print("deleted" if forget(a.token) else "not found")
        return 0
    except VaultError as e:
        print(f"vault: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
