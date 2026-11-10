# -*- coding: utf-8 -*-
from pathlib import Path
import json

file_path = Path("integrations/hermes/yadro-guard/engine_loader.py")
text = file_path.read_text(encoding="utf-8")

old_func = """def engine_home() -> Path | None:
    try:
        home = Path(json.loads((_PLUGIN_DIR / "config.json").read_text(encoding="utf-8"))["engine_home"])
        return home if (home / "src" / "runtime" / "policy.py").is_file() else None
    except Exception:
        return None"""

new_func = """def engine_home() -> Path | None:
    if (_PLUGIN_DIR / "src" / "runtime" / "policy.py").is_file():
        return _PLUGIN_DIR
    try:
        cfg = json.loads((_PLUGIN_DIR / "config.json").read_text(encoding="utf-8"))
        home_str = cfg.get("engine_home")
        if home_str:
            home = Path(home_str)
            if (home / "src" / "runtime" / "policy.py").is_file():
                return home
    except Exception:
        pass
    cand_roots = [
        _PLUGIN_DIR.parent.parent.parent,
        Path.cwd(),
        Path(r"E:\\загрузки\\.gemini\\antigravity\\scratch\\YadroLang-English-repo"),
    ]
    for cand in cand_roots:
        if cand and (cand / "src" / "runtime" / "policy.py").is_file():
            return cand
    return None"""

text = text.replace(old_func.replace("\r\n", "\n"), new_func)
file_path.write_text(text, encoding="utf-8")
print("Engine loader patched successfully.")

