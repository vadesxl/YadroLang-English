# -*- coding: utf-8 -*-
"""MITRE ATT&CK Threat Mapping and Multi-Stage Kill-Chain Correlation Engine.

Maps raw security events (Ingress and Egress) to MITRE ATT&CK tactics & techniques
and correlates temporally proximate alerts (within a 10-minute sliding window)
into multi-stage attack chains ('MULTI-STAGE KILL CHAIN DETECTED') with severity
escalation to CRITICAL.
"""

from __future__ import annotations

import collections
import dataclasses
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclasses.dataclass(frozen=True)
class MitreTechnique:
    technique_id: str
    technique_name: str
    tactic_id: str
    tactic_name: str
    description_ru: str
    description_en: str
    base_severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    base_score: int     # 0..100


# Standard MITRE ATT&CK definitions for Yadro Guard
TECHNIQUES: Dict[str, MitreTechnique] = {
    "T1552": MitreTechnique(
        technique_id="T1552",
        technique_name="Unsecured Credentials",
        tactic_id="TA0006",
        tactic_name="Credential Access",
        description_ru="Попытка доступа или утечки незащищенных учетных данных (API-ключи, токены, мнемоники)",
        description_en="Unsecured credentials exposure attempt (API keys, tokens, mnemonics)",
        base_severity="HIGH",
        base_score=85,
    ),
    "T1048": MitreTechnique(
        technique_id="T1048",
        technique_name="Exfiltration Over Alternative Protocol",
        tactic_id="TA0010",
        tactic_name="Exfiltration",
        description_ru="Эксфильтрация конфиденциальных данных во внешнюю сеть через альтернативные каналы",
        description_en="Exfiltration of sensitive data to external perimeter over alternative protocol",
        base_severity="HIGH",
        base_score=88,
    ),
    "T1059": MitreTechnique(
        technique_id="T1059",
        technique_name="Command and Scripting Interpreter",
        tactic_id="TA0002",
        tactic_name="Execution",
        description_ru="Исполнение недоверенных команд и скриптов (pipe to shell, powershell -enc, certutil)",
        description_en="Execution of untrusted commands and scripts (pipe to shell, powershell -enc, certutil)",
        base_severity="HIGH",
        base_score=90,
    ),
    "T1046": MitreTechnique(
        technique_id="T1046",
        technique_name="Network Service Discovery",
        tactic_id="TA0007",
        tactic_name="Discovery",
        description_ru="Сканирование сети и разведка открытых локальных сетевых служб",
        description_en="Network service scanning and host port enumeration discovery",
        base_severity="MEDIUM",
        base_score=60,
    ),
    "T1110": MitreTechnique(
        technique_id="T1110",
        technique_name="Brute Force",
        tactic_id="TA0006",
        tactic_name="Credential Access",
        description_ru="Попытки подбора учетных записей или паролей (SSH, RDP, Event ID 4625)",
        description_en="Brute force authentication guessing against remote services (SSH, RDP)",
        base_severity="HIGH",
        base_score=85,
    ),
    "T1557": MitreTechnique(
        technique_id="T1557",
        technique_name="Adversary-in-the-Middle (ARP Cache Poisoning)",
        tactic_id="TA0006",
        tactic_name="Credential Access",
        description_ru="Появление недоверенного MAC-адреса / отравление ARP-кэша в локальной подсети",
        description_en="Adversary-in-the-Middle attempt via ARP cache poisoning / rogue node",
        base_severity="CRITICAL",
        base_score=92,
    ),
    "T1098.004": MitreTechnique(
        technique_id="T1098.004",
        technique_name="SSH Authorized Keys Modification",
        tactic_id="TA0003",
        tactic_name="Persistence",
        description_ru="Закрепление в системе через модификацию ключей ~/.ssh/authorized_keys",
        description_en="Account persistence through ~/.ssh/authorized_keys file modification",
        base_severity="CRITICAL",
        base_score=95,
    ),
    "T1547": MitreTechnique(
        technique_id="T1547",
        technique_name="Boot or Logon Autostart Execution",
        tactic_id="TA0003",
        tactic_name="Persistence",
        description_ru="Закрепление через системный автозапуск, службы или реестр Windows",
        description_en="Persistence via boot or logon autostart keys, systemd or Windows registry",
        base_severity="HIGH",
        base_score=85,
    ),
    "T1566": MitreTechnique(
        technique_id="T1566",
        technique_name="Phishing & Indirect Prompt Injection",
        tactic_id="TA0001",
        tactic_name="Initial Access",
        description_ru="Непрямая промпт-инъекция, кириллический гомоглиф-фишинг или скрытая манипуляция ИИ",
        description_en="Indirect prompt injection, Cyrillic homoglyph phishing or LLM manipulation",
        base_severity="HIGH",
        base_score=88,
    ),
    "T1027": MitreTechnique(
        technique_id="T1027",
        technique_name="Obfuscated Files or Information",
        tactic_id="TA0005",
        tactic_name="Defense Evasion",
        description_ru="Обфускация вредоносной нагрузки (Base64, Hex, Zero-Width, Unicode homoglyphs)",
        description_en="Payload obfuscation through multi-layer encoding or zero-width steganography",
        base_severity="MEDIUM",
        base_score=70,
    ),
    "T1562": MitreTechnique(
        technique_id="T1562",
        technique_name="Impair Defenses",
        tactic_id="TA0005",
        tactic_name="Defense Evasion",
        description_ru="Попытка отключения файрвола, модификации правил безопасности или обхода контроля",
        description_en="Attempt to disable security guard, kill firewall rules or bypass controls",
        base_severity="CRITICAL",
        base_score=94,
    ),
}


@dataclasses.dataclass
class MitreEvent:
    event_id: str
    timestamp: float
    technique_id: str
    tactics: List[str]
    details: Dict[str, Any]
    session_id: str = ""
    host: str = ""


@dataclasses.dataclass
class KillChainReport:
    is_kill_chain: bool
    summary_ru: str
    summary_en: str
    severity: str
    risk_score: int
    stages_count: int
    stages: List[Dict[str, Any]]
    tactics: List[str]
    techniques: List[str]
    emergency_action_ru: str
    emergency_action_en: str


class MitreCorrelator:
    """Sliding-window correlator identifying multi-stage attack chains."""

    WINDOW_SECONDS = 600.0  # 10 minutes

    def __init__(self, window_seconds: float = 600.0) -> None:
        self.window_seconds = window_seconds
        self._history: collections.deque[MitreEvent] = collections.deque(maxlen=2000)

    def map_event(
        self,
        event_type: str,
        content: str = "",
        details: Optional[Dict[str, Any]] = None,
        tool_name: str = "",
        destination: str = "",
    ) -> List[MitreTechnique]:
        """Maps an individual raw security observation to MITRE ATT&CK techniques."""
        matched: List[MitreTechnique] = []
        details = details or {}
        text = (content + " " + str(details) + " " + destination).lower()
        tool = tool_name.lower()

        # 1. Credentials & Exfiltration (T1552 + T1048)
        is_credential = False
        if event_type in ("secret_leak", "credential", "finding") or "token" in event_type or "leak" in event_type:
            is_credential = True
        elif any(k in text for k in ("authorization: bearer", "sk-ant-", "sk-proj-", "ghp_", "xoxb-", "bip-39", "bip39", "seed phrase")):
            is_credential = True

        if is_credential:
            matched.append(TECHNIQUES["T1552"])
            if destination or any(kw in text for kw in ("http://", "https://", "curl", "webhook", "transfer")):
                matched.append(TECHNIQUES["T1048"])

        # 2. Execution via Command Interpreters / Pipes (T1059)
        pipe_patterns = (
            "curl | bash", "curl|bash", "curl | sh", "curl|sh", "wget | bash",
            "powershell -enc", "powershell -e ", "powershell /e ",
            "certutil -urlcache", "certutil.exe -decode", "cmd.exe /c", "/bin/sh -c",
            "pipe to shell", "bash -c"
        )
        if (
            any(p in text for p in pipe_patterns)
            or re.search(r"(?:curl|wget)\b.*?\|\s*(?:bash|sh)", text)
            or re.search(r"powershell\b.*?(?:-enc|-e\b)", text)
            or "certutil" in text
            or event_type in ("pipe_to_shell", "remote_exec", "eval_exploit")
        ):
            matched.append(TECHNIQUES["T1059"])

        # 3. Discovery / Port Scanning (T1046)
        if event_type in ("port_scan", "network_discovery", "scan_ports") or "port_scan" in text or "nmap" in text:
            matched.append(TECHNIQUES["T1046"])

        # 4. Brute Force (T1110)
        if (
            event_type in ("bruteforce", "ssh_brute", "rdp_brute", "auth_failure")
            or "4625" in text
            or "failed password for" in text
            or "подбор пароля" in text
        ):
            matched.append(TECHNIQUES["T1110"])

        # 5. Adversary-in-the-Middle / ARP Spoofing (T1557)
        if (
            event_type in ("arp_spoof", "mitm", "rogue_node", "unfamiliar_node")
            or "arp cache" in text
            or "arp_spoof" in text
            or "чужой mac" in text
        ):
            matched.append(TECHNIQUES["T1557"])

        # 6. Persistence: SSH Authorized Keys (T1098.004) or Autostart (T1547)
        if "authorized_keys" in text or event_type == "ssh_key_tamper":
            matched.append(TECHNIQUES["T1098.004"])
        elif any(kw in text for kw in ("runonce", "currentversion\\run", "/etc/init.d", "systemd/system")) or event_type == "autostart_tamper":
            matched.append(TECHNIQUES["T1547"])

        # 7. Initial Access: Prompt Injection / Cyrillic Phishing (T1566)
        if (
            event_type in ("prompt_injection", "homoglyph_phishing", "aitm_phishing", "taint_ingestion")
            or any(kw in text for kw in ("ignore previous instructions", "system prompt override", "evilginx", "login."))
        ):
            matched.append(TECHNIQUES["T1566"])

        # 8. Defense Evasion: Obfuscation (T1027)
        if (
            event_type in ("obfuscation", "zero_width", "hex_payload")
            or "zero-width" in text
            or "base64_encoded" in text
            or details.get("obfuscated")
        ):
            matched.append(TECHNIQUES["T1027"])

        # 9. Defense Evasion: Impair Defenses (T1562)
        if (
            event_type in ("firewall_tamper", "kill_guard", "stop_service")
            or any(kw in text for kw in ("netsh advfirewall set", "kill-switch", "disable firewall", "tamper guard"))
        ):
            matched.append(TECHNIQUES["T1562"])

        # Deduplicate while preserving order
        seen = set()
        unique_matches = []
        for m in matched:
            if m.technique_id not in seen:
                seen.add(m.technique_id)
                unique_matches.append(m)

        return unique_matches

    def record_event(
        self,
        event_id: str,
        event_type: str,
        content: str = "",
        details: Optional[Dict[str, Any]] = None,
        session_id: str = "",
        host: str = "",
        timestamp: Optional[float] = None,
        destination: str = "",
    ) -> List[MitreTechnique]:
        """Records an event and returns the mapped MITRE techniques."""
        ts = timestamp if timestamp is not None else time.time()
        techs = self.map_event(event_type, content, details, destination=destination)
        tactics = list({t.tactic_name for t in techs})
        for t in techs:
            evt = MitreEvent(
                event_id=event_id,
                timestamp=ts,
                technique_id=t.technique_id,
                tactics=[t.tactic_name],
                details=details or {},
                session_id=session_id,
                host=host or "local_host",
            )
            self._history.append(evt)
        return techs

    def correlate(
        self,
        session_id: str = "",
        host: str = "",
        now: Optional[float] = None,
    ) -> KillChainReport:
        """Analyzes recorded events within the sliding window for multi-stage Kill-Chains."""
        current_ts = now if now is not None else time.time()
        cutoff = current_ts - self.window_seconds

        # Filter events in sliding window
        recent_events = [
            e for e in self._history
            if e.timestamp >= cutoff
            and (not session_id or e.session_id == session_id or not e.session_id)
            and (not host or e.host == host or not e.host)
        ]

        # Extract distinct techniques and tactics
        seen_techniques: Set[str] = set()
        stages: List[Dict[str, Any]] = []

        for e in sorted(recent_events, key=lambda x: x.timestamp):
            t_def = TECHNIQUES.get(e.technique_id)
            if not t_def:
                continue
            seen_techniques.add(e.technique_id)
            stages.append({
                "event_id": e.event_id,
                "timestamp": e.timestamp,
                "relative_time_sec": round(current_ts - e.timestamp, 1),
                "technique_id": t_def.technique_id,
                "technique_name": t_def.technique_name,
                "tactic_id": t_def.tactic_id,
                "tactic_name": t_def.tactic_name,
                "severity": t_def.base_severity,
                "score": t_def.base_score,
                "session_id": e.session_id,
                "host": e.host,
            })

        distinct_techs = sorted(list(seen_techniques))
        distinct_tactics = sorted(list({TECHNIQUES[t].tactic_name for t in distinct_techs if t in TECHNIQUES}))

        # Kill-chain condition: >= 2 distinct techniques within 10 minutes
        is_kill_chain = len(distinct_techs) >= 2

        if is_kill_chain:
            severity = "CRITICAL"
            risk_score = min(100, 85 + len(distinct_techs) * 5)
            summary_en = (
                f"MULTI-STAGE KILL CHAIN DETECTED: {len(distinct_techs)} distinct techniques "
                f"across {len(distinct_tactics)} tactics identified in the last 10 minutes "
                f"({', '.join(distinct_techs)})."
            )
            summary_ru = (
                f"ОБНАРУЖЕНА МНОГОЭТАПНАЯ ЦЕПОЧКА АТАКИ (KILL CHAIN): {len(distinct_techs)} техник "
                f"в рамках {len(distinct_tactics)} тактик за последние 10 минут "
                f"({', '.join(distinct_techs)})."
            )
            action_en = "Emergency Containment: Activate Kill-Switch, isolate host network interface, and quarantine sessions."
            action_ru = "Экстренное сдерживание: активировать Kill-Switch, изолировать сетевой периметр и заморозить скомпрометированные сессии."
        else:
            if distinct_techs:
                top_t = TECHNIQUES[distinct_techs[0]]
                severity = top_t.base_severity
                risk_score = top_t.base_score
                summary_en = f"Single-technique observation: {top_t.technique_id} ({top_t.technique_name})."
                summary_ru = f"Одиночное наблюдение техники: {top_t.technique_id} ({top_t.technique_name})."
                action_en = "Standard mitigation: continue monitoring and verify policy filters."
                action_ru = "Стандартная фильтрация: продолжать наблюдение и валидацию политик."
            else:
                severity = "INFO"
                risk_score = 0
                summary_en = "Perimeter quiet. No suspicious MITRE ATT&CK techniques identified."
                summary_ru = "Периметр спокоен. Подозрительных техник MITRE ATT&CK не зафиксировано."
                action_en = "No action required."
                action_ru = "Действий не требуется."

        return KillChainReport(
            is_kill_chain=is_kill_chain,
            summary_ru=summary_ru,
            summary_en=summary_en,
            severity=severity,
            risk_score=risk_score,
            stages_count=len(stages),
            stages=stages,
            tactics=distinct_tactics,
            techniques=distinct_techs,
            emergency_action_ru=action_ru,
            emergency_action_en=action_en,
        )

    def get_matrix_status(self) -> Dict[str, Any]:
        """Returns the full MITRE ATT&CK matrix coverage status."""
        active_techs = {e.technique_id for e in self._history}
        tactics_coverage: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)
        for t_id, t in TECHNIQUES.items():
            tactics_coverage[t.tactic_name].append({
                "id": t.technique_id,
                "name": t.technique_name,
                "active": t.technique_id in active_techs,
                "severity": t.base_severity,
                "score": t.base_score,
            })
        return {
            "total_techniques": len(TECHNIQUES),
            "active_techniques": len(active_techs),
            "tactics": dict(tactics_coverage),
        }

    def clear(self) -> None:
        """Clears all historical events."""
        self._history.clear()


# Global Singleton
_CORRELATOR: Optional[MitreCorrelator] = None


def get_mitre_correlator() -> MitreCorrelator:
    global _CORRELATOR
    if _CORRELATOR is None:
        _CORRELATOR = MitreCorrelator()
    return _CORRELATOR
