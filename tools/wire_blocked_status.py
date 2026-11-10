# -*- coding: utf-8 -*-
from pathlib import Path

path = Path("integrations/hermes/yadro-guard/dashboard/dist/index.js")
text = path.read_text(encoding="utf-8")
is_crlf = "\r\n" in text
text = text.replace("\r\n", "\n")

old_text = '("-- OPERATOR DECISION REQUIRED (" + pendingItems.length + " BLOCKED)"'
new_text = '("-- OPERATOR DECISION REQUIRED (" + (blockedStatusText || (pendingItems.length + " BLOCKED")) + ")"'

old_text_ru = '("-- ТРЕБУЕТСЯ РЕШЕНИЕ ОПЕРАТОРА (ЗАБЛОКИРОВАНО " + pendingItems.length + ")"'
new_text_ru = '("-- ТРЕБУЕТСЯ РЕШЕНИЕ ОПЕРАТОРА (" + (blockedStatusText || ("ЗАБЛОКИРОВАНО " + pendingItems.length)) + ")"'

if old_text in text:
    text = text.replace(old_text, new_text)
    print("Replaced EN header")
else:
    print("Warning: old_text not found")

if old_text_ru in text:
    text = text.replace(old_text_ru, new_text_ru)
    print("Replaced RU header")
else:
    print("Warning: old_text_ru not found")

if is_crlf:
    text = text.replace("\n", "\r\n")

path.write_text(text, encoding="utf-8")
print("Done!")

