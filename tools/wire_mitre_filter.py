# -*- coding: utf-8 -*-
from pathlib import Path

path = Path("integrations/hermes/yadro-guard/dashboard/dist/index.js")
text = path.read_text(encoding="utf-8")
is_crlf = "\r\n" in text
text = text.replace("\r\n", "\n")

target1 = 'var stSimBusy = useState(""), simBusy = stSimBusy[0], setSimBusy = stSimBusy[1];'
repl1 = target1 + '\n    var stMitre = useState(""), mitreFilter = (p.mitreFilter !== undefined ? p.mitreFilter : stMitre[0]), setMitreFilter = (p.onSelectMitreFilter || stMitre[1]);'

target2 = 'activeFocal: activeFocal,\n        onSelectIncident: handleSelectIncident'
repl2 = 'activeFocal: activeFocal,\n        mitreFilter: mitreFilter,\n        onSelectMitreFilter: setMitreFilter,\n        onSelectIncident: handleSelectIncident'

if target1 in text:
    text = text.replace(target1, repl1, 1)
    print("target1 replaced")
else:
    print("Warning: target1 not found")

if target2 in text:
    text = text.replace(target2, repl2, 1)
    print("target2 replaced")
else:
    print("Warning: target2 not found")

if is_crlf:
    text = text.replace("\n", "\r\n")

path.write_text(text, encoding="utf-8")
print("Done!")

