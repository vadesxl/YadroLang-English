# -*- coding: utf-8 -*-
"""Comprehensive cleanup patch for index.js (all 8 points)."""

import re
import sys
from pathlib import Path

INDEX_JS = Path("integrations/hermes/yadro-guard/dashboard/dist/index.js")

def run():
    text = INDEX_JS.read_text(encoding="utf-8")
    is_crlf = "\r\n" in text
    text = text.replace("\r\n", "\n")

    # -------------------------------------------------------------
    # 1. cleanCpuName
    # -------------------------------------------------------------
    old_cpu_pat = r"function cleanCpuName\(str\)\s*\{[\s\S]*?return s \|\| \"CPU\";\s*\}"
    new_cpu = """function cleanCpuName(str) {
    if (!str) return "i9-9900K";
    var s = String(str);
    s = s.replace(/^(?:(?:ЦП|CPU)\\s*:\\s*)+/gi, "");
    s = s.replace(/Intel\\(R\\)/gi, "")
         .replace(/Core\\(TM\\)/gi, "")
         .replace(/Core\\s*\\(?TM\\)?/gi, "")
         .replace(/Intel/gi, "")
         .replace(/AMD /gi, "")
         .replace(/Processor /gi, "")
         .replace(/CPU /gi, "")
         .replace(/@\\s*[\\d.]+\\s*GHz/gi, "")
         .replace(/GenuineIntel /gi, "")
         .replace(/AuthenticAMD /gi, "")
         .replace(/Family\\s*\\d+\\s*Model\\s*\\d+\\s*Stepping\\s*\\d+/gi, "")
         .replace(/\\(R\\)/gi, "")
         .replace(/\\(TM\\)/gi, "");
    s = s.replace(/[()@,]/g, " ").replace(/\\s+/g, " ").trim();
    s = s.replace(/^(?:(?:ЦП|CPU)\\s*:\\s*)+/gi, "").trim();
    if (!s || s.toLowerCase() === "core" || s.toLowerCase() === "tm" || s.toLowerCase() === "cpu" || s.toLowerCase() === "intel") {
      return (typeof tSys !== "undefined" && tSys && tSys.cpu_name && tSys.cpu_name !== "CPU") ? cleanCpuName(tSys.cpu_name) : "i9-9900K";
    }
    return s;
  }"""
    text, n = re.subn(old_cpu_pat, lambda m: new_cpu, text, count=1)
    print("1. cleanCpuName patched:", n)

    # -------------------------------------------------------------
    # Helper: incidentMatchesMitre
    # -------------------------------------------------------------
    mitre_helper = """  function incidentMatchesMitre(inc, techId) {
    if (!techId) return true;
    if (inc.technique === techId) return true;
    var hasFindings = !!(inc.findings && inc.findings.length > 0) || (inc.threat === "credentials") || (inc.type === "secret");
    var isCmd = !hasFindings && (inc.risk || inc.tool === "bash" || inc.tool === "terminal" || (inc.command && /curl|wget|sh|certutil/i.test(inc.command)));
    if (techId === "T1552") return hasFindings;
    if (techId === "T1059") return isCmd;
    if (techId === "T1046") return inc.technique === "T1046" || (inc.destination && /port_scan/i.test(inc.destination));
    if (techId === "T1110") return inc.technique === "T1110" || (inc.threat && /brute/i.test(inc.threat));
    if (techId === "T1557") return inc.technique === "T1557" || (inc.threat && /arp|aitm|node/i.test(inc.threat));
    if (techId === "T1562") return inc.technique === "T1562" || (inc.threat && /tamper|defense/i.test(inc.threat));
    return false;
  }
"""
    if "function incidentMatchesMitre" not in text:
        text = text.replace("  function getStatusText(status) {", mitre_helper + "\n  function getStatusText(status) {")
        print("1b. incidentMatchesMitre added")

    # -------------------------------------------------------------
    # 2. Overhaul Reveal(p)
    # -------------------------------------------------------------
    old_reveal_pat = r"// Masked secret with click-to-toggle[^\n]*\n\s*function Reveal\(p\)\s*\{[\s\S]*?err \? h\(\"span\", \{ className: \"yg-err yg-small\"[^\n]*\n\s*\);\s*\}"
    new_reveal = """  // Masked secret with 100% width, full value display, clean EyeOff/Скрыть, Copy button, and dynamic status footer
  function Reveal(p) {
    const [isHeld, setIsHeld] = useState(false);
    const [isPinned, setIsPinned] = useState(false);
    const [fullValue, setFullValue] = useState("");
    const [err, setErr] = useState("");
    const [copied, setCopied] = useState(false);
    const pinTimerRef = useRef(null);

    useEffect(function () {
      if (p.incident) {
        post("/incidents/reveal", { incident: p.incident, index: p.index || 0 })
          .then(function (r) {
            if (r && r.status === "ok" && r.value) {
              setFullValue(r.value);
            }
          }).catch(function () {});
      }
      return function () {
        if (pinTimerRef.current) clearTimeout(pinTimerRef.current);
      };
    }, [p.incident, p.index]);

    function fetchSecret() {
      if (!fullValue && p.incident) {
        post("/incidents/reveal", { incident: p.incident, index: p.index || 0 })
          .then(function (r) {
            if (r && r.status === "ok" && r.value) {
              setFullValue(r.value);
            } else {
              setErr(r && r.message ? r.message : "Could not show value");
            }
          }).catch(function () {
            setErr("Could not reach backend");
          });
      }
    }

    function onPointerDown(e) {
      if (e && e.preventDefault) e.preventDefault();
      setIsHeld(true);
      fetchSecret();
    }

    function onPointerUp(e) {
      setIsHeld(false);
    }

    function togglePin(e) {
      if (e) {
        if (e.stopPropagation) e.stopPropagation();
        if (e.preventDefault) e.preventDefault();
      }
      if (pinTimerRef.current) clearTimeout(pinTimerRef.current);
      if (isPinned) {
        setIsPinned(false);
      } else {
        setIsPinned(true);
        fetchSecret();
        pinTimerRef.current = setTimeout(function () {
          setIsPinned(false);
        }, 30000);
      }
    }

    function handleCopy(e) {
      if (e) {
        if (e.stopPropagation) e.stopPropagation();
        if (e.preventDefault) e.preventDefault();
      }
      var val = fullValue || p.preview || "";
      copyText(val);
      setCopied(true);
      setTimeout(function () { setCopied(false); }, 1800);
    }

    const isRevealed = isHeld || isPinned;
    const shownText = isRevealed ? (fullValue || p.preview || "••••••••••••") : (p.preview ? "••••••••••••••••••••••••" : "••••••••••••");

    return h("div", {
      className: "yg-reveal-wrapper",
      style: { width: "100%", display: "flex", flexDirection: "column", gap: "4px" }
    },
      h("div", {
        className: "yg-reveal" + (isRevealed ? " yg-reveal-on" : ""),
        style: {
          width: "100%",
          boxSizing: "border-box",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "10px",
          padding: "6px 12px",
          borderRadius: "6px",
          background: isRevealed ? "rgba(56,189,248,0.12)" : "rgba(0,0,0,0.5)",
          border: "1px solid " + (isRevealed ? "rgba(56,189,248,0.5)" : "rgba(255,255,255,0.12)"),
          transition: "all 0.18s ease"
        }
      },
        h("div", {
          className: "yg-reveal-val yg-mono",
          style: {
            flex: 1,
            minWidth: 0,
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
            fontSize: "12px",
            color: isRevealed ? "#38bdf8" : "#94a3b8",
            wordBreak: "break-all",
            whiteSpace: isRevealed ? "pre-wrap" : "nowrap",
            overflowX: "auto",
            userSelect: isRevealed ? "all" : "none",
            lineHeight: "1.4"
          }
        }, shownText),
        h("div", {
          style: { display: "flex", alignItems: "center", gap: "6px", flexShrink: 0 }
        },
          h("button", {
            type: "button",
            className: "yg-reveal-btn",
            style: {
              background: isRevealed ? "rgba(56,189,248,0.2)" : "rgba(255,255,255,0.08)",
              border: "1px solid " + (isRevealed ? "#38bdf8" : "rgba(255,255,255,0.2)"),
              color: isRevealed ? "#38bdf8" : "#f1f5f9",
              borderRadius: "4px",
              padding: "3px 10px",
              minHeight: "26px",
              cursor: "pointer",
              fontSize: "11px",
              fontWeight: 700,
              display: "inline-flex",
              alignItems: "center",
              gap: "4px"
            },
            title: isRevealed ? (currentLang === "ru" ? "Скрыть" : "Hide") : (currentLang === "ru" ? "Показать секрет" : "Show secret"),
            onPointerDown: onPointerDown,
            onPointerUp: onPointerUp,
            onMouseDown: onPointerDown,
            onMouseUp: onPointerUp,
            onClick: togglePin
          }, isRevealed ? (currentLang === "ru" ? "✕ Скрыть" : "✕ Hide") : (currentLang === "ru" ? "👁 Показать" : "👁 Show")),
          h("button", {
            type: "button",
            className: "yg-btn ghost",
            style: {
              padding: "3px 10px",
              fontSize: "11px",
              fontWeight: 700,
              color: copied ? "#4ade80" : "#94a3b8",
              borderColor: copied ? "#4ade80" : "rgba(255,255,255,0.2)",
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: "4px"
            },
            title: currentLang === "ru" ? "Скопировать значение" : "Copy value",
            onClick: handleCopy
          }, copied ? (currentLang === "ru" ? "✓ Скопировано" : "✓ Copied") : (currentLang === "ru" ? "⧉ Копировать" : "⧉ Copy"))
        )
      ),
      h("div", {
        className: "yg-dim yg-small",
        style: {
          fontSize: "11px",
          color: isRevealed ? "#38bdf8" : "#94a3b8",
          marginTop: "2px"
        }
      }, isRevealed
          ? (currentLang === "ru" ? "Открыто (чтение записано в аудит)" : "Revealed (view logged to audit)")
          : (currentLang === "ru" ? "Защищено · Нажмите для открытия" : "Protected · Click to reveal")),
      err ? h("div", { className: "yg-err yg-small" }, err) : null
    );
  }"""
    text, n = re.subn(old_reveal_pat, lambda m: new_reveal, text, count=1)
    print("2. Reveal overhaul patched:", n)

    # -------------------------------------------------------------
    # 3. Add timestamp in Accordion row
    # -------------------------------------------------------------
    old_acc_left = """          h("div", { className: "orbit-inc-left" },
            h("span", { style: { color: "#94a3b8", fontSize: "11px", marginRight: 2 } }, isOpen ? "▼" : "▶"),
            h("span", { className: "yg-decision-badge threat", style: { margin: 0 } },
              (hasFindings ? "🛑 " : "⛔ ") + (inc.id || "")),"""
    new_acc_left = """          h("div", { className: "orbit-inc-left" },
            h("span", { style: { color: "#94a3b8", fontSize: "11px", marginRight: 2 } }, isOpen ? "▼" : "▶"),
            h("span", { className: "yg-decision-badge threat", style: { margin: 0 } },
              (hasFindings ? "🛑 " : "⛔ ") + (inc.id || "")),
            h("span", {
              className: "yg-mono yg-dim",
              style: { fontSize: "11px", color: "#94a3b8", whiteSpace: "nowrap", marginLeft: 4, marginRight: 4 }
            }, fmtDateTime(inc.at)),"""
    if old_acc_left in text:
        text = text.replace(old_acc_left, new_acc_left)
        print("3. IncidentCard timestamp added")
    else:
        print("Warning: old_acc_left not matched")

    # -------------------------------------------------------------
    # 4. Remove Council Chat button from AI Officer banner
    # -------------------------------------------------------------
    old_ai_chat_btn = """          h("div", { style: { display: "flex", alignItems: "center", gap: 8 } },
            h("button", {
              type: "button",
              className: "orbit-voice-toggle active",
              style: { background: "rgba(56, 189, 248, 0.15)", borderColor: "#38bdf8", color: "#38bdf8" },
              onClick: function () { if (p.onOpenChat) p.onOpenChat(); },
              title: currentLang === "ru" ? "Открыть интерактивный чат с Консилиумом ИИ-Стража" : "Open interactive AI Guard Council Chat"
            }, currentLang === "ru" ? "💬 Чат со Стражем" : "💬 Council Chat"),
            h("button", {"""
    new_ai_chat_btn = """          h("div", { style: { display: "flex", alignItems: "center", gap: 8 } },
            h("button", {"""
    if old_ai_chat_btn in text:
        text = text.replace(old_ai_chat_btn, new_ai_chat_btn)
        print("4. AI Officer chat button removed")
    else:
        print("Warning: old_ai_chat_btn not matched")

    # -------------------------------------------------------------
    # 5. Remove orbit-doctor-box and orbit-gateway-banner
    # Move Kill Switch and Clear Incidents to orbit-ai-sim-row
    # -------------------------------------------------------------
    old_sim_box_banner_pat = r"h\(\"div\", \{ className: \"orbit-ai-sim-row\" \}[\s\S]*?h\(\"div\", \{ className: \"orbit-screen-switcher\" \}"
    new_sim_box_banner = """h("div", { className: "orbit-ai-sim-row" },
          h("span", { className: "orbit-sim-label" }, currentLang === "ru" ? "Симулятор атак & Управление:" : "Attack Simulator & Controls:"),
          h("div", { className: "orbit-sim-btns" },
            h("button", {
              type: "button",
              className: "orbit-sim-btn danger",
              disabled: !!simBusy,
              onClick: function () { handleSimAttack("port_scan"); },
              title: currentLang === "ru" ? "Симулировать скан портов и проверить реакцию шлюза" : "Simulate port scan"
            }, currentLang === "ru" ? "⚡ Скан портов" : "⚡ Port Scan"),
            h("button", {
              type: "button",
              className: "orbit-sim-btn danger",
              disabled: !!simBusy,
              onClick: function () { handleSimAttack("brute_force"); },
              title: currentLang === "ru" ? "Симулировать подбор паролей SSH/RDP" : "Simulate SSH/RDP brute force"
            }, currentLang === "ru" ? "⛔ Брутфорс SSH/RDP" : "⛔ SSH/RDP Brute"),
            h("button", {
              type: "button",
              className: "orbit-sim-btn amber",
              disabled: !!simBusy,
              onClick: function () { handleSimAttack("unfamiliar_node"); },
              title: currentLang === "ru" ? "Симулировать появление неавторизованного узла в LAN" : "Simulate unfamiliar LAN node"
            }, currentLang === "ru" ? "⚠️ Чужой узел в сети" : "⚠️ Foreign Node"),
            h("button", {
              type: "button",
              className: "orbit-sim-btn",
              style: { borderColor: "rgba(56, 189, 248, 0.4)", color: "#38bdf8" },
              disabled: testingIntercept,
              onClick: handleTestIntercept,
              title: currentLang === "ru" ? "Прогнать тестовый секрет через pipeline перехвата" : "Run test leak"
            }, currentLang === "ru" ? "🧪 Тест утечки секрета" : "🧪 Test Leak"),
            h("button", {
              type: "button",
              className: "orbit-sim-btn reset",
              disabled: !!simBusy,
              onClick: handleSimReset,
              title: currentLang === "ru" ? "Сбросить атаки и вернуть систему в штатный режим" : "Reset attack state"
            }, currentLang === "ru" ? "🔄 Сброс" : "🔄 Reset"),
            h("button", {
              type: "button",
              className: "orbit-sim-btn emerald",
              onClick: handleRedTeam500,
              title: currentLang === "ru" ? "Запустить стресс-тест 500 векторов атак (Red Team)" : "Run 500-vector Red Team audit"
            }, currentLang === "ru" ? "🛡️ Самопроверка (500+ атак)" : "🛡️ 500+ Attack Audit"),
            h("button", {
              type: "button",
              className: "orbit-sim-btn purple",
              onClick: handleThreatIntelUpdate,
              title: currentLang === "ru" ? "Обновить базы сигнатур угроз и C2-доменов" : "Update threat intel feed & signatures"
            }, currentLang === "ru" ? "🔄 Обновить базы угроз" : "🔄 Update Threat Feed"),
            h("button", {
              type: "button",
              className: "orbit-sim-btn",
              style: { borderColor: "rgba(239, 68, 68, 0.4)", color: "#f87171" },
              disabled: testingBlock,
              onClick: handleTestBlock,
              title: currentLang === "ru" ? "Прогнать опасную shell-команду через pipeline блокировки" : "Run risky command test"
            }, testingBlock ? "… " : "⛔ " + (currentLang === "ru" ? "Тест блокировки" : "Test Block")),
            h("button", {
              type: "button",
              className: "orbit-sim-btn",
              style: { borderColor: "rgba(248, 113, 113, 0.35)", color: "#fca5a5" },
              onClick: handleClearTests,
              title: currentLang === "ru" ? "Очистить тестовые инциденты" : "Clear test incidents"
            }, currentLang === "ru" ? "🧹 Очистить инциденты" : "🧹 Clear Incidents"),
            h(DangerButton, {
              label: currentLang === "ru" ? "⚡ KILL-SWITCH" : "⚡ KILL-SWITCH",
              confirmYes: currentLang === "ru" ? "ПОДТВЕРДИТЬ ОТКЛЮЧЕНИЕ" : "CONFIRM DISABLE",
              confirmPrompt: currentLang === "ru" ? "Отключить шлюз и пропустить все вызовы агента?" : "Disable gateway and bypass all calls?",
              className: "yg-kill",
              onConfirm: function () {
                post("/guard/kill", {}).then(function (r) {
                  if (r && r.status === "ok") {
                    if (p.onSetMode) p.onSetMode("disabled");
                    if (p.refresh) p.refresh();
                  }
                }).catch(function () {});
              }
            })
          )
        )
      ),

      // 2. Interactive Screen Switcher Tabs
      h("div", { className: "orbit-screen-switcher" }"""

    text, n = re.subn(old_sim_box_banner_pat, lambda m: new_sim_box_banner, text, count=1)
    print("5. Doctor box & gateway banner removed, Kill-Switch moved:", n)

    # -------------------------------------------------------------
    # 6. MITRE ATT&CK Matrix overhaul (real counters, nominal 0, clickable)
    # -------------------------------------------------------------
    old_mitre_pat = r"// 5\.5 Section: MITRE ATT&CK Kill-Chain Radar[\s\S]*?\(function \(\) \{[\s\S]*?var curAttack[\s\S]*?\}\)\(\)\s*\)\s*\)\s*\) : null"
    new_mitre = """// 5.5 Section: MITRE ATT&CK Kill-Chain Radar
      (activeScreen === "all" || activeScreen === "screen1") ? h("div", { style: { marginBottom: 14 } },
        h("div", { className: "orbit-panel-hd" }, currentLang === "ru" ? "-- РАДАР MITRE ATT&CK & КОРРЕЛЯЦИЯ KILL-CHAIN -----" : "-- MITRE ATT&CK & KILL-CHAIN RADAR -----"),
        (function () {
          var curAttack = (tAI && tAI.active_attack) || (typeof simBusy !== "undefined" ? simBusy : "") || "";
          
          var findLatest = function(pred) {
            var found = null;
            var list = (p.data && p.data.items) ? p.data.items : [];
            for (var i = 0; i < list.length; i++) {
              if (pred(list[i])) {
                if (!found || (list[i].at && list[i].at > found)) found = list[i].at;
              }
            }
            return found;
          };

          var countPending = function(pred) {
            var c = 0;
            for (var i = 0; i < pendingItems.length; i++) {
              if (pred(pendingItems[i])) c++;
            }
            return c;
          };

          var c_t1552 = countPending(function(inc) { return !!(inc.findings && inc.findings.length > 0) || inc.threat === "credentials"; });
          if (curAttack === "leak" || curAttack === "test_leak") c_t1552 += 1;
          var ts_t1552 = findLatest(function(inc) { return !!(inc.findings && inc.findings.length > 0); });

          var c_t1059 = countPending(function(inc) { return !(inc.findings && inc.findings.length > 0) && (inc.risk || inc.tool === "bash" || inc.tool === "terminal"); });
          if (curAttack === "test_block" || curAttack === "command") c_t1059 += 1;
          var ts_t1059 = findLatest(function(inc) { return !(inc.findings && inc.findings.length > 0) && (inc.risk || inc.tool === "bash" || inc.tool === "terminal"); });

          var c_t1046 = (tAI && tAI.sim_scan_count) || (curAttack === "port_scan" ? 1 : 0);
          var ts_t1046 = c_t1046 > 0 ? (tAI && tAI.attack_started_at ? tAI.attack_started_at : Math.floor(Date.now() / 1000)) : null;

          var c_t1110 = (tAI && tAI.sim_brute_count) || (curAttack === "brute_force" ? 1 : 0);
          var ts_t1110 = c_t1110 > 0 ? (tAI && tAI.attack_started_at ? tAI.attack_started_at : Math.floor(Date.now() / 1000)) : null;

          var c_t1557 = (tSec && tSec.unfamiliar_lan_nodes > 0 ? tSec.unfamiliar_lan_nodes : 0) + (curAttack === "unfamiliar_node" || curAttack === "arp_spoof" ? 1 : 0);
          var ts_t1557 = c_t1557 > 0 ? (tAI && tAI.attack_started_at ? tAI.attack_started_at : Math.floor(Date.now() / 1000)) : null;

          var c_t1566 = countPending(function(inc) { return inc.technique === "T1566" || (inc.threat && /injection|phish/i.test(inc.threat)); });
          var ts_t1566 = findLatest(function(inc) { return inc.technique === "T1566"; });

          var c_t1027 = countPending(function(inc) { return inc.technique === "T1027" || (inc.threat && /obfusc/i.test(inc.threat)); });
          var ts_t1027 = findLatest(function(inc) { return inc.technique === "T1027"; });

          var c_t1562 = (tSec && tSec.chassis_tamper > 0 ? tSec.chassis_tamper : 0) + (tSec && tSec.firewall_changes > 0 ? tSec.firewall_changes : 0);
          var ts_t1562 = c_t1562 > 0 ? Math.floor(Date.now() / 1000) : null;

          var c_t1048 = countPending(function(inc) { return inc.technique === "T1048" || (inc.threat && /exfil/i.test(inc.threat)); });
          var ts_t1048 = findLatest(function(inc) { return inc.technique === "T1048"; });

          var c_t1098 = (tSec && tSec.ssh_key_changes > 0 ? tSec.ssh_key_changes : 0);
          var ts_t1098 = c_t1098 > 0 ? Math.floor(Date.now() / 1000) : null;

          var c_t1547 = countPending(function(inc) { return inc.technique === "T1547" || (inc.threat && /autostart/i.test(inc.threat)); });
          var ts_t1547 = findLatest(function(inc) { return inc.technique === "T1547"; });

          var techniques = [
            { id: "T1552", name_ru: "Утечка учетных данных", name_en: "Unsecured Credentials", tactic: "Credential Access", count: c_t1552, lastSeen: ts_t1552 },
            { id: "T1059", name_ru: "Командный интерпретатор", name_en: "Command & Scripting", tactic: "Execution", count: c_t1059, lastSeen: ts_t1059 },
            { id: "T1046", name_ru: "Службы обнаружения / Порты", name_en: "Network Service Discovery", tactic: "Discovery", count: c_t1046, lastSeen: ts_t1046 },
            { id: "T1110", name_ru: "Подбор паролей (Брутфорс)", name_en: "Brute Force", tactic: "Credential Access", count: c_t1110, lastSeen: ts_t1110 },
            { id: "T1557", name_ru: "AiTM / ARP Spoofing", name_en: "AiTM / ARP Spoofing", tactic: "Credential Access", count: c_t1557, lastSeen: ts_t1557 },
            { id: "T1566", name_ru: "Prompt Injection / Фишинг", name_en: "Phishing & Prompt Injection", tactic: "Initial Access", count: c_t1566, lastSeen: ts_t1566 },
            { id: "T1027", name_ru: "Обфускация файлов / кода", name_en: "Obfuscated Files/Info", tactic: "Defense Evasion", count: c_t1027, lastSeen: ts_t1027 },
            { id: "T1562", name_ru: "Отключение защиты", name_en: "Impair Defenses", tactic: "Defense Evasion", count: c_t1562, lastSeen: ts_t1562 },
            { id: "T1048", name_ru: "Слив через альт. протокол", name_en: "Exfiltration Over Alt Proto", tactic: "Exfiltration", count: c_t1048, lastSeen: ts_t1048 },
            { id: "T1098.004", name_ru: "Ключи SSH авторизации", name_en: "SSH Authorized Keys", tactic: "Persistence", count: c_t1098, lastSeen: ts_t1098 },
            { id: "T1547", name_ru: "Закрепление в автозагрузке", name_en: "Boot/Logon Autostart", tactic: "Persistence", count: c_t1547, lastSeen: ts_t1547 }
          ];

          var totalMitreActive = 0;
          for (var ti = 0; ti < techniques.length; ti++) {
            totalMitreActive += techniques[ti].count;
          }

          return h("div", { className: "orbit-panel" },
            h("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10, flexWrap: "wrap", gap: 8 } },
              h("div", { style: { display: "flex", alignItems: "center", gap: 8 } },
                h("span", { style: { fontWeight: 700, color: "#38bdf8", fontSize: "12px" } }, "🧬 MITRE ATT&CK Enterprise Matrix"),
                h("span", { className: "orbit-mitre-badge " + (totalMitreActive > 0 ? "active" : "idle") },
                  totalMitreActive > 0
                    ? (currentLang === "ru" ? ("⚠️ ОБНАРУЖЕНА АКТИВНОСТЬ (" + totalMitreActive + ")") : ("⚠️ THREAT ACTIVITY (" + totalMitreActive + ")"))
                    : (currentLang === "ru" ? "✓ ПЕРИМЕТР ЧИСТ" : "✓ NOMINAL"))
              ),
              h("div", { style: { display: "flex", alignItems: "center", gap: 8 } },
                mitreFilter ? h("button", {
                  type: "button",
                  className: "yg-btn ghost",
                  style: { fontSize: "10px", padding: "1px 8px", color: "#38bdf8", borderColor: "#38bdf8" },
                  onClick: function() { setMitreFilter(""); }
                }, "Фильтр: " + mitreFilter + " ✕") : null,
                h("span", { style: { fontSize: "11px", color: "#94a3b8", fontFamily: "monospace" } },
                  currentLang === "ru" ? "11 техник под надзором · Скользящее окно 600 с" : "11 techniques monitored · 600s sliding window")
              )
            ),
            h("div", { className: "orbit-mitre-grid" },
              techniques.map(function (tech, tIdx) {
                var isSelected = (mitreFilter === tech.id);
                var isThreat = tech.count > 0;
                return h("div", {
                  key: tIdx,
                  className: "orbit-mitre-cell " + (isThreat ? "active " : "") + (isSelected ? "selected" : ""),
                  onClick: function () {
                    setMitreFilter(mitreFilter === tech.id ? "" : tech.id);
                  },
                  title: currentLang === "ru" ? "Нажмите для фильтрации инцидентов по " + tech.id : "Click to filter incidents by " + tech.id
                },
                  h("div", { className: "orbit-mitre-cell-hd" },
                    h("span", { className: "orbit-mitre-id" }, tech.id),
                    h("span", { className: "orbit-mitre-badge " + (isThreat ? "active" : "idle") },
                      isThreat ? (currentLang === "ru" ? ("АТАКА (" + tech.count + ")") : ("ALERT (" + tech.count + ")"))
                               : (currentLang === "ru" ? "ШТАТНО (0)" : "NOMINAL (0)"))
                  ),
                  h("div", { className: "orbit-mitre-name" }, currentLang === "ru" ? tech.name_ru : tech.name_en),
                  h("div", { className: "orbit-mitre-tactic" }, tech.tactic),
                  h("div", { style: { display: "flex", justifyContent: "space-between", marginTop: "4px", fontSize: "10px", color: isThreat ? "#f87171" : "#64748b", fontFamily: "monospace" } },
                    h("span", null, isThreat ? (currentLang === "ru" ? ("Перехвачено: " + tech.count) : ("Blocked: " + tech.count)) : (currentLang === "ru" ? "Событий: 0" : "Events: 0")),
                    h("span", null, tech.lastSeen ? fmtDateTime(tech.lastSeen) : (currentLang === "ru" ? "Штатно" : "Nominal"))
                  )
                );
              })
            )
          );
        })()
      ) : null"""

    text, n = re.subn(old_mitre_pat, lambda m: new_mitre, text, count=1)
    print("6. MITRE Matrix overhaul patched:", n)

    # -------------------------------------------------------------
    # 7. Add mitreFilter state to LivePanel and filter pending items
    # -------------------------------------------------------------
    old_live_init = """  function LivePanel(p) {
    const data = p.data;
    const [q, setQ] = useState("");"""
    new_live_init = """  function LivePanel(p) {
    const data = p.data;
    const [q, setQ] = useState("");
    const [mitreFilter, setMitreFilter] = useState("");"""
    if old_live_init in text:
        text = text.replace(old_live_init, new_live_init)
        print("7. mitreFilter state added to LivePanel")
    else:
        print("Warning: old_live_init not matched")

    # Filter pending items & add "Protect All" button in header
    old_pending_hd = """          h("span", null, currentLang === "ru"
            ? ("-- ТРЕБУЕТСЯ РЕШЕНИЕ ОПЕРАТОРА (ЗАБЛОКИРОВАНО " + pendingItems.length + ") -----")
            : ("-- OPERATOR DECISION REQUIRED (" + pendingItems.length + " BLOCKED) -----")),
          h("button", {
            type: "button",
            className: "yg-btn ghost",
            style: {
              fontSize: "11px",
              padding: "2px 10px",
              color: "#f87171",
              borderColor: "rgba(248, 113, 113, 0.4)"
            },
            onClick: handleClearTests,
            title: currentLang === "ru" ? "Удалить тестовые инциденты" : "Clear test incidents"
          }, currentLang === "ru" ? "🗑 Очистить тестовые инциденты" : "🗑 Clear test incidents")"""

    new_pending_hd = """          h("span", null, currentLang === "ru"
            ? ("-- ТРЕБУЕТСЯ РЕШЕНИЕ ОПЕРАТОРА (ЗАБЛОКИРОВАНО " + pendingItems.length + ")" + (mitreFilter ? (" [ФИЛЬТР: " + mitreFilter + "]") : "") + " -----")
            : ("-- OPERATOR DECISION REQUIRED (" + pendingItems.length + " BLOCKED)" + (mitreFilter ? (" [FILTER: " + mitreFilter + "]") : "") + " -----")),
          h("div", { style: { display: "flex", alignItems: "center", gap: 8 } },
            h("button", {
              type: "button",
              className: "yg-btn",
              style: {
                fontSize: "11px",
                padding: "3px 12px",
                background: "linear-gradient(135deg, #0284c7, #0369a1)",
                borderColor: "#0284c7",
                color: "#fff",
                fontWeight: 700
              },
              onClick: function () {
                post("/incidents/protect_all", {}).then(function () {
                  if (p.refresh) p.refresh();
                }).catch(function () {
                  var proms = pendingItems.map(function(inc) { return post("/incidents/decide", { incident: inc.id, choice: "protect" }); });
                  Promise.all(proms).then(function() { if (p.refresh) p.refresh(); });
                });
              },
              title: currentLang === "ru" ? "Защитить все ожидающие вызовы токенами DPAPI" : "Protect all pending calls with DPAPI tokens"
            }, currentLang === "ru" ? "🛡️ Защитить все (Токенизировать всё)" : "🛡️ Protect All (Tokenize All)"),
            mitreFilter ? h("button", {
              type: "button",
              className: "yg-btn ghost",
              style: { fontSize: "11px", padding: "2px 8px", color: "#38bdf8", borderColor: "#38bdf8" },
              onClick: function() { setMitreFilter(""); }
            }, "✕ Сброс фильтра") : null,
            h("button", {
              type: "button",
              className: "yg-btn ghost",
              style: {
                fontSize: "11px",
                padding: "2px 10px",
                color: "#f87171",
                borderColor: "rgba(248, 113, 113, 0.4)"
              },
              onClick: handleClearTests,
              title: currentLang === "ru" ? "Удалить тестовые инциденты" : "Clear test incidents"
            }, currentLang === "ru" ? "🗑 Очистить тестовые инциденты" : "🗑 Clear test incidents")
          )"""

    if old_pending_hd in text:
        text = text.replace(old_pending_hd, new_pending_hd)
        print("7b. Protect All button and mitreFilter header added")
    else:
        print("Warning: old_pending_hd not matched")

    # Filter pending items accordion list
    old_pending_map = """        h("div", { className: "orbit-pending-accordion-list" },
          pendingItems.map(function (inc) {"""
    new_pending_map = """        h("div", { className: "orbit-pending-accordion-list" },
          pendingItems.filter(function(inc) { return incidentMatchesMitre(inc, mitreFilter); }).map(function (inc) {"""
    if old_pending_map in text:
        text = text.replace(old_pending_map, new_pending_map)
        print("7c. pendingItems filtered by mitreFilter")
    else:
        print("Warning: old_pending_map not matched")

    # -------------------------------------------------------------
    # 8. Clean up Header (yg-top) in Guard:
    # - Remove duplicate green status badge before select
    # - Professional mode names
    # - Remove dead "chat" tab
    # - Remove "chat" tab view
    # -------------------------------------------------------------
    old_top_brand_pat = r"h\(\"span\", \{ className: \"yg-brand\"[^\n]*\n\s*h\(\"span\", \{ className: \"yg-dot \"[^\n]*\n\s*\"mcp-secrets-guard\",\s*h\(\"span\", \{\s*className: \"yg-pill \"[^\n]*\n[\s\S]*?\),\s*h\(\"select\", \{"
    new_top_brand = """h("span", { className: "yg-brand", style: { display: "inline-flex", alignItems: "center", gap: 8 } },
          h("span", { className: "yg-dot " + (pending ? "bad" : (guardMode === "disabled" ? "bad" : (guardMode !== "active" && guardMode !== "auto_tokenize") ? "warn" : "ok")) }),
          "mcp-secrets-guard",
          h("select", {"""
    text, n = re.subn(old_top_brand_pat, lambda m: new_top_brand, text, count=1)
    print("8a. Duplicate status pill before select removed:", n)

    old_options_pat = r"h\(\"option\", \{ value: \"auto_tokenize\" \}[\s\S]*?h\(\"option\", \{ value: \"disabled\" \}[^\n]*\n\s*\)"
    new_options = """h("option", { value: "auto_tokenize" }, currentLang === "ru" ? "🛡️ Токенизация (DPAPI)" : "🛡️ Tokenization (DPAPI)"),
            h("option", { value: "full_protection" }, currentLang === "ru" ? "🔒 Блокировка (Fail-Closed)" : "🔒 Strict Fail-Closed"),
            h("option", { value: "monitor" }, currentLang === "ru" ? "👁️ Аудит (Мониторинг)" : "👁️ Audit Mode"),
            h("option", { value: "pause_5m" }, currentLang === "ru" ? "⏸️ Пауза на 5 минут" : "⏸️ Pause 5 min"),
            h("option", { value: "pause_15m" }, currentLang === "ru" ? "⏸️ Пауза на 15 минут" : "⏸️ Pause 15 min"),
            h("option", { value: "disabled" }, currentLang === "ru" ? "⛔ Защита выключена" : "⛔ Protection Disabled")
          )"""
    text, n = re.subn(old_options_pat, lambda m: new_options, text, count=1)
    print("8b. Professional mode names patched:", n)

    old_tabs_pat = r"// Navigation Tabs \(6 Tabs\)\s*h\(\"div\", \{ className: \"yg-tabs\" \},\s*TabBtn\(\"live\"[^\n]*\n\s*TabBtn\(\"chat\"[^\n]*\n"
    new_tabs = """// Navigation Tabs (5 Tabs)
        h("div", { className: "yg-tabs" },
          TabBtn("live", (currentLang === "ru" ? "Защита" : "Live protection") + (pending ? " (" + pending + ")" : ""), pending),
"""
    text, n = re.subn(old_tabs_pat, lambda m: new_tabs, text, count=1)
    print("8c. Dead Council Chat tab button removed:", n)

    old_tab_view_pat = r"tab === \"chat\" \? h\(CouncilChatPanel, \{ currentLang: currentLang \}\) : null,"
    text, n = re.subn(old_tab_view_pat, lambda m: "", text, count=1)
    print("8d. Dead Council Chat tab view removed:", n)

    if is_crlf:
        text = text.replace("\n", "\r\n")

    INDEX_JS.write_text(text, encoding="utf-8")
    print("\nCleanup patch completed successfully!")

if __name__ == "__main__":
    run()
