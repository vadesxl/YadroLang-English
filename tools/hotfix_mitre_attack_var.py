"""Hotfix for _ATTACK_STATE_TYPE undefined ReferenceError in dist/index.js."""
import pathlib

path = pathlib.Path("integrations/hermes/yadro-guard/dashboard/dist/index.js")
content = path.read_text(encoding="utf-8")

old_snippet = '''          h("div", { className: "orbit-mitre-grid" },
            [
              { id: "T1552", name_ru: "Утечка учетных данных", name_en: "Unsecured Credentials", tactic: "Credential Access", active: (tSec.secrets_intercepted > 0) },
              { id: "T1059", name_ru: "Командный интерпретатор", name_en: "Command & Scripting", tactic: "Execution", active: (tSec.dangerous_commands_blocked > 0) },
              { id: "T1046", name_ru: "Службы обнаружения / Порты", name_en: "Network Service Discovery", tactic: "Discovery", active: (aiIsAlert && _ATTACK_STATE_TYPE === "port_scan") },
              { id: "T1110", name_ru: "Подбор паролей (Брутфорс)", name_en: "Brute Force", tactic: "Credential Access", active: (aiIsAlert && _ATTACK_STATE_TYPE === "brute_force") },
              { id: "T1557", name_ru: "AiTM / ARP Spoofing", name_en: "AiTM / ARP Spoofing", tactic: "Credential Access", active: (tSec.unfamiliar_lan_nodes > 0) },
              { id: "T1566", name_ru: "Prompt Injection / Фишинг", name_en: "Phishing & Prompt Injection", tactic: "Initial Access", active: false },
              { id: "T1027", name_ru: "Обфускация файлов / кода", name_en: "Obfuscated Files/Info", tactic: "Defense Evasion", active: false },
              { id: "T1562", name_ru: "Отключение защиты", name_en: "Impair Defenses", tactic: "Defense Evasion", active: (tSec.firewall_changes > 0 || tSec.chassis_tamper > 0) },
              { id: "T1048", name_ru: "Слив через альт. протокол", name_en: "Exfiltration Over Alt Proto", tactic: "Exfiltration", active: false },
              { id: "T1098.004", name_ru: "Ключи SSH авторизации", name_en: "SSH Authorized Keys", tactic: "Persistence", active: (tSec.ssh_key_changes > 0) },
              { id: "T1547", name_ru: "Закрепление в автозагрузке", name_en: "Boot/Logon Autostart", tactic: "Persistence", active: false }
            ].map(function (tech, tIdx) {
              return h("div", { key: tIdx, className: "orbit-mitre-cell " + (tech.active ? "active" : "") },
                h("div", { className: "orbit-mitre-cell-hd" },
                  h("span", { className: "orbit-mitre-id" }, tech.id),
                  h("span", { className: "orbit-mitre-badge " + (tech.active ? "active" : "idle") },
                    tech.active ? (currentLang === "ru" ? "АТАКА" : "ALERT") : (currentLang === "ru" ? "ШТАТНО" : "OK"))
                ),
                h("div", { className: "orbit-mitre-name" }, currentLang === "ru" ? tech.name_ru : tech.name_en),
                h("div", { className: "orbit-mitre-tactic" }, tech.tactic)
              );
            })
          )'''

new_snippet = '''          h("div", { className: "orbit-mitre-grid" },
            (function () {
              var curAttack = (tAI && tAI.active_attack) || (typeof simBusy !== "undefined" ? simBusy : "") || "";
              return [
                { id: "T1552", name_ru: "Утечка учетных данных", name_en: "Unsecured Credentials", tactic: "Credential Access", active: (tSec.secrets_intercepted > 0) },
                { id: "T1059", name_ru: "Командный интерпретатор", name_en: "Command & Scripting", tactic: "Execution", active: (tSec.dangerous_commands_blocked > 0) },
                { id: "T1046", name_ru: "Службы обнаружения / Порты", name_en: "Network Service Discovery", tactic: "Discovery", active: (aiIsAlert && curAttack === "port_scan") },
                { id: "T1110", name_ru: "Подбор паролей (Брутфорс)", name_en: "Brute Force", tactic: "Credential Access", active: (aiIsAlert && curAttack === "brute_force") },
                { id: "T1557", name_ru: "AiTM / ARP Spoofing", name_en: "AiTM / ARP Spoofing", tactic: "Credential Access", active: (tSec.unfamiliar_lan_nodes > 0 || (aiIsAlert && (curAttack === "arp_spoof" || curAttack === "unfamiliar_node"))) },
                { id: "T1566", name_ru: "Prompt Injection / Фишинг", name_en: "Phishing & Prompt Injection", tactic: "Initial Access", active: false },
                { id: "T1027", name_ru: "Обфускация файлов / кода", name_en: "Obfuscated Files/Info", tactic: "Defense Evasion", active: false },
                { id: "T1562", name_ru: "Отключение защиты", name_en: "Impair Defenses", tactic: "Defense Evasion", active: (tSec.firewall_changes > 0 || tSec.chassis_tamper > 0) },
                { id: "T1048", name_ru: "Слив через альт. протокол", name_en: "Exfiltration Over Alt Proto", tactic: "Exfiltration", active: false },
                { id: "T1098.004", name_ru: "Ключи SSH авторизации", name_en: "SSH Authorized Keys", tactic: "Persistence", active: (tSec.ssh_key_changes > 0) },
                { id: "T1547", name_ru: "Закрепление в автозагрузке", name_en: "Boot/Logon Autostart", tactic: "Persistence", active: false }
              ].map(function (tech, tIdx) {
                return h("div", { key: tIdx, className: "orbit-mitre-cell " + (tech.active ? "active" : "") },
                  h("div", { className: "orbit-mitre-cell-hd" },
                    h("span", { className: "orbit-mitre-id" }, tech.id),
                    h("span", { className: "orbit-mitre-badge " + (tech.active ? "active" : "idle") },
                      tech.active ? (currentLang === "ru" ? "АТАКА" : "ALERT") : (currentLang === "ru" ? "ШТАТНО" : "OK"))
                  ),
                  h("div", { className: "orbit-mitre-name" }, currentLang === "ru" ? tech.name_ru : tech.name_en),
                  h("div", { className: "orbit-mitre-tactic" }, tech.tactic)
                );
              });
            })()
          )'''

assert old_snippet in content, "old_snippet not found in dist/index.js"
content = content.replace(old_snippet, new_snippet, 1)
path.write_text(content, encoding="utf-8")
print("Hotfix applied to dist/index.js successfully.")

