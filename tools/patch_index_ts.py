# -*- coding: utf-8 -*-
from pathlib import Path

index_path = Path("integrations/hermes/yadro-guard/dashboard/dist/index.js")
text = index_path.read_text(encoding="utf-8")

old_snippet = """          var c_t1562 = (tSec && tSec.chassis_tamper > 0 ? tSec.chassis_tamper : 0) + (tSec && tSec.firewall_changes > 0 ? tSec.firewall_changes : 0);
          var ts_t1562 = c_t1562 > 0 ? Math.floor(Date.now() / 1000) : null;

          var c_t1048 = countPending(function(inc) { return inc.technique === "T1048" || (inc.threat && /exfil/i.test(inc.threat)); });
          var ts_t1048 = findLatest(function(inc) { return inc.technique === "T1048"; });

          var c_t1098 = (tSec && tSec.ssh_key_changes > 0 ? tSec.ssh_key_changes : 0);
          var ts_t1098 = c_t1098 > 0 ? Math.floor(Date.now() / 1000) : null;"""

new_snippet = """          var c_t1562 = (tSec && tSec.chassis_tamper > 0 ? tSec.chassis_tamper : 0) + (tSec && tSec.firewall_changes > 0 ? tSec.firewall_changes : 0);
          var ts_t1562 = c_t1562 > 0 ? (tAI && tAI.attack_started_at ? tAI.attack_started_at : findLatest(function(inc) { return inc.technique === "T1562"; })) : null;

          var c_t1048 = countPending(function(inc) { return inc.technique === "T1048" || (inc.threat && /exfil/i.test(inc.threat)); });
          var ts_t1048 = findLatest(function(inc) { return inc.technique === "T1048"; });

          var c_t1098 = (tSec && tSec.ssh_key_changes > 0 ? tSec.ssh_key_changes : 0);
          var ts_t1098 = c_t1098 > 0 ? (tAI && tAI.attack_started_at ? tAI.attack_started_at : findLatest(function(inc) { return inc.technique === "T1098" || inc.technique === "T1098.004"; })) : null;"""

assert old_snippet in text, "old_snippet not found in index.js"
text = text.replace(old_snippet, new_snippet)
index_path.write_text(text, encoding="utf-8")
print("index.js patched successfully.")

