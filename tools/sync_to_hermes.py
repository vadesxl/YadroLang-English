# -*- coding: utf-8 -*-
"""Synchronize yadro-guard plugin files to Hermes plugin directory and restart gateway."""

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "integrations" / "hermes" / "yadro-guard"
DST_DIR = Path(r"C:\Users\vades\AppData\Local\hermes\plugins\yadro-guard")

def sync():
    if not DST_DIR.exists():
        print(f"Error: destination {DST_DIR} does not exist.")
        return False

    # 1. Sync embedded src into AppData destination for standalone zero-dependency runtime
    src_runtime_repo = REPO_ROOT / "src"
    dst_embedded = DST_DIR / "src"

    if src_runtime_repo.exists():
        if dst_embedded.exists():
            shutil.rmtree(dst_embedded, ignore_errors=True)
        shutil.copytree(src_runtime_repo, dst_embedded, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        print(f"Copied runtime src -> {dst_embedded}")

    files_to_sync = [
        "__init__.py",
        "engine_loader.py",
        "plugin.yaml",
        "desktop/plugin.js",
        "dashboard/plugin_api.py",
        "dashboard/dist/index.js",
        "dashboard/dist/style.css",
    ]

    for rel in files_to_sync:
        src = SRC_DIR / rel
        dst = DST_DIR / rel
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"Copied: {rel} ({src.stat().st_size} bytes)")
        else:
            print(f"Warning: source file not found: {src}")

    # Write clean UTF-8 config.json in destination
    cfg_path = DST_DIR / "config.json"
    cfg_data = {
        "paused_until": 0,
        "guard_mode": "auto_tokenize",
        "python": r"C:\Users\vades\AppData\Local\Programs\Python\Python313\python.exe",
        "engine_home": str(REPO_ROOT),
        "lang": "ru"
    }
    cfg_path.write_text(json.dumps(cfg_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {cfg_path} with clean UTF-8 config")

    # Remove pycache in destination and all subdirectories
    for pc in DST_DIR.rglob("__pycache__"):
        try:
            shutil.rmtree(pc, ignore_errors=True)
            print(f"Cleared: {pc}")
        except Exception:
            pass

    print("\nSync completed successfully.")
    return True

if __name__ == "__main__":
    sync()
