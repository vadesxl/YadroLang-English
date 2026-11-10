# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

text = Path("integrations/hermes/yadro-guard/dashboard/dist/index.js").read_text(encoding="utf-8")
idx = text.find('function TabBtn(')
if idx != -1:
    print(text[idx:idx+400])
