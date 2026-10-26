# -*- coding: utf-8 -*-
"""Remove records from the vault that are not secrets at all: filesystem paths.

Why this exists: older builds quarantined a blocked *file path* as if it were a secret.
The path then matched the vault's exact-match detector, every later scan of the same path
produced a "leaked credential" incident, and the dashboard showed a path as an SSH key.

What it does:
  * reads vault.json, decrypts only to classify (no audit entries, no values printed);
  * picks text records whose value really looks like a local filesystem path;
  * dry run by default; ``--apply`` moves them to the 30-day trash (never deletes forever);
  * writes a timestamped backup of vault.json before touching anything.

Usage:
    python tools/vault_cleanup_paths.py             # show the plan
    python tools/vault_cleanup_paths.py --apply     # move confirmed paths to trash
    python tools/vault_cleanup_paths.py --apply --json
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import vault  # noqa: E402

PATH_TITLE_HINT = "local file"


def looks_like_path(value: str) -> bool:
    """A path, not a credential: drive letter, UNC, or a backslash-heavy token."""
    v = (value or "").strip()
    if not v or len(v) > 1024 or "\n" in v:
        return False
    if re.match(r"^[A-Za-z]:[\\/]", v):
        return True
    if v.startswith(("\\\\", "//")):
        return True
    return "\\" in v and " " not in v


def _decode(record: dict) -> str | None:
    if record.get("kind", "text") != "text":
        return None
    try:
        return vault._dpapi(base64.b64decode(record["blob"]), False).decode("utf-8")
    except Exception:
        return None


def scan() -> dict:
    """Return {"candidates": [...], "total": n, "skipped": [...]} without changing anything."""
    data = vault._load()
    candidates, skipped = [], []
    for token, record in data["items"].items():
        if record.get("deleted"):
            continue
        title = str(record.get("title") or "")
        value = _decode(record)
        if value is None:
            continue
        if looks_like_path(value):
            candidates.append({"token": token, "title": title,
                               "hinted": PATH_TITLE_HINT in title.lower()})
        elif PATH_TITLE_HINT in title.lower():
            skipped.append({"token": token, "title": title, "reason": "title hints a path, value is not"})
    return {"candidates": candidates, "skipped": skipped,
            "total": len(data["items"]), "active": sum(1 for r in data["items"].values() if not r.get("deleted"))}


def apply_trash(tokens: list) -> str:
    path = vault.vault_path()
    backup = path.with_name(path.name + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(path, backup)
    for token in tokens:
        vault.to_trash(token)
    return str(backup)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="tools/vault_cleanup_paths.py")
    parser.add_argument("--apply", action="store_true", help="move confirmed path records to trash")
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    args = parser.parse_args(argv)

    report = scan()
    tokens = [c["token"] for c in report["candidates"]]
    backup = None
    if args.apply and tokens:
        backup = apply_trash(tokens)
        report = scan()
        report["trashed"] = tokens
        report["backup"] = backup

    report["dry_run"] = not args.apply
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        print(f"vault: {report['active']} active records")
        print(f"paths to remove: {len(report['candidates'])}")
        for c in report["candidates"]:
            print(f"  - {c['token']}  {c['title'][:70]}")
        if report["skipped"]:
            print("kept (title looks like a path, value does not):")
            for s in report["skipped"]:
                print(f"  ! {s['token']}  {s['title'][:70]}")
        if args.apply and tokens:
            print(f"moved to trash: {len(tokens)}  (restorable within 30 days)")
            print(f"backup: {backup}")
        elif tokens:
            print("dry run: nothing changed. Add --apply to move these to trash.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
