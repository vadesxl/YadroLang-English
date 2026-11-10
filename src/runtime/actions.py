# -*- coding: utf-8 -*-
"""Risky agent ACTIONS (not secrets): exposing services, tunnels, destructive commands.

These are matched against command-like arguments of any tool call. A match opens an
incident just like a secret does, so the user decides: Block, or Allow once.
("Protect & send" makes no sense for an action, so it is not offered.)

Each rule: kind, title, why, safer, regex. Rules are deliberately specific to keep
false positives low; the generic secret detectors still run on the same arguments.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, List

from .detectors import walk_args


@dataclass
class RiskyAction:
    kind: str
    title: str
    why: str
    safer: str
    path: str
    snippet: str

    def public(self) -> dict:
        return dict(self.__dict__)


# "All interfaces" in every spelling seen in the wild (redteam review by GLM-5.3 found
# quoted, tab-separated, ::0, expanded IPv6 and env/YAML forms that slipped through).
_ALL_IF = r"(?:0\.0\.0\.0|0(?::0){7}|::0?|\[::0?\]|\*)"
_END = r"(?![\w.])"
RULES = [
    # ---- exposing services to the network ----
    ("expose_bind_all", "Starts a server open to the whole network",
     "The service will accept connections from any device on the network, and from the internet if the router forwards the port.",
     "Use --host 127.0.0.1 (or bind to localhost) unless other devices really need it.",
     # --host 0.0.0.0 | --host="0.0.0.0" | --host\t'::' | -b 0.0.0.0 | host='0.0.0.0' | host: 0.0.0.0 (YAML)
     # HOST=0.0.0.0 / BIND_ADDR=0.0.0.0 env | --urls http://+:80 / *:80 / 0.0.0.0:80 (Kestrel, uvicorn --bind)
     rf"(?:--(?:host|bind|listen|ip|addr|address)\s*[=\s]\s*|(?<![\w-])-[bH]\s+|\b(?:server_name|host|bind|listen)\s*[=:]\s*"
     rf"|\b(?!OLLAMA_HOST\b)[A-Z_]*(?:HOST|BIND|LISTEN|ADDR)[A-Z_]*\s*=\s*)['\"]?(?:https?://)?{_ALL_IF}{_END}"
     rf"|--urls?\s*[=\s]\s*['\"]?https?://[+*]:\d+|\.bind\(\s*\(\s*['\"](?:0\.0\.0\.0|::|)['\"]"),
    ("expose_ollama", "Exposes Ollama to the network",
     "Anyone on the network could run, pull or delete your local AI models.",
     "Keep OLLAMA_HOST=127.0.0.1.", rf"OLLAMA_HOST\s*=\s*['\"]?(?:https?://)?(?:{_ALL_IF}|:\d+)"),
    ("expose_docker_port", "Publishes a container port on all interfaces",
     "docker -p without an address publishes the port to every network and bypasses Windows Firewall in many setups.",
     "Use -p 127.0.0.1:PORT:PORT.", r"\bdocker(?:\s+compose)?\b[^\n]*\s-p\s+(?!127\.0\.0\.1:|localhost:)\d+:\d+"),
    ("http_server_all", "Shares a folder over HTTP",
     "python -m http.server serves the whole folder to the network by default.",
     "Add --bind 127.0.0.1, and never run it in a folder with secrets.",
     r"\bhttp\.server\b(?![^\n]*--bind\s+127\.0\.0\.1)"),
    ("public_tunnel", "Opens a public internet tunnel",
     "Tunnels (ngrok, cloudflared, localtunnel, bore) publish a local service on the internet, bypassing the router and firewall.",
     "Only open a tunnel you started yourself, with a password, and close it after use.",
     r"\b(?:ngrok\s+(?:http|tcp|tls|start)|cloudflared\s+tunnel|lt\s+--port|npx\s+localtunnel|bore\s+local|ssh\s+-R\s)"),
    ("firewall_open", "Opens a port in the firewall or turns the firewall off",
     "Changes what the internet can reach on this computer.",
     "Ask the user first; open only the exact port for the exact program.",
     r"(?:netsh\s+advfirewall\s+(?:set\s+\w+\s+state\s+off|firewall\s+add\s+rule[^\n]*action=allow)"
     r"|New-NetFirewallRule[^\n]*-Action\s+Allow|Set-NetFirewallProfile[^\n]*-Enabled\s+(?:False|0)|ufw\s+(?:allow|disable))"),
    ("rdp_enable", "Enables Remote Desktop",
     "Remote Desktop is the most attacked service on the internet.",
     "Use a VPN instead of exposing Remote Desktop.",
     r"fDenyTSConnections[^\n]*\b0\b|Enable-NetFirewallRule[^\n]*Remote Desktop"),
    # ---- destructive / irreversible ----
    ("destroy_files", "Deletes files recursively",
     "This permanently deletes a folder tree. Agents have wiped projects and home folders this way.",
     "Delete only an exact path the user named, and prefer moving to a trash folder.",
     r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?\s+(?:/|~|\*|\$HOME|\.\s*$|C:\\)|\bRemove-Item\b[^\n]*-Recurse[^\n]*-Force|\brd\s+/s\s+/q\b|\bdel\s+/s\b|\bformat\s+[a-zA-Z]:"),
    ("destroy_db", "Destroys database data",
     "DROP / TRUNCATE / DELETE without WHERE removes data permanently.",
     "Take a backup first and confirm the exact table with the user.",
     r"\b(?:DROP\s+(?:TABLE|DATABASE|SCHEMA)|TRUNCATE\s+TABLE|FLUSHALL|FLUSHDB|dropDatabase\(\))\b|\bDELETE\s+FROM\s+\w+\s*;"),
    ("git_force", "Overwrites git history on the server",
     "A force push can erase other people's work and published history.",
     "Use --force-with-lease, or ask the user first.", r"\bgit\s+push\b[^\n]*(?:--force(?!-with-lease)|\s-f\b)"),
    ("pipe_to_shell", "Runs a script straight from the internet",
     "Downloading and executing code in one step runs whatever the server sends, with your permissions.",
     "Download the script first, read it, then run it.",
     r"(?:curl|wget|iwr|Invoke-WebRequest)\b[^\n|]*\|\s*(?:sh|bash|zsh|python|iex|Invoke-Expression)\b"),
    ("disable_defender", "Turns off antivirus protection",
     "Disabling Defender removes protection against malware.",
     "Do not let an agent change antivirus settings.",
     r"Set-MpPreference[^\n]*-Disable\w+\s+\$?true|Add-MpPreference[^\n]*-ExclusionPath"),

    ("tamper_guard_env", "Turns off or changes the guard's environment",
     "Setting the guard's own environment variables is how an agent would disable its protection from the shell.",
     "The guard has deliberately no env kill-switch; changing YADRO_GUARD_* does nothing and is blocked.",
     r"(?i)\b(?:set|export)\s+YADRO_GUARD_[A-Z_]+\s*=|YADRO_GUARD_[A-Z_]+\s*=\s*(?:1|true|on)|\bSet-Item\s+Env:\s*YADRO_GUARD_\w+"),
    ("tamper_guard_files", "Modifies or deletes the guard's own files",
     "Deleting or overwriting the guard's config, vault or incident files removes or weakens the protection.",
     "Never let an agent touch the guard's own directory or its vault/config/decision files.",
     r"(?i)\b(?:rm|del|remove|rd|erase)\b[^\n]*(?:yadro[-_]guard|mcp[-_]secrets[-_]guard|(?:vault|decisions|incidents|rules)\.json)"
     r"|\bRemove-Item\b[^\n]*(?:yadro[-_]guard|mcp[-_]secrets[-_]guard)"
     r"|(?:yadro[-_]guard|mcp[-_]secrets[-_]guard)[\\/](?:config|rules)\.json"),

    # ---- Ring 1: Dangerous OS Execution & Credential Theft Rules ----
    ("powershell_enc", "Executes obfuscated Base64 PowerShell command",
     "Encoded PowerShell commands hide malicious payloads from command line inspection.",
     "Run scripts in plain text or inspect decoded script block first.",
     r"(?i)\b(?:powershell|pwsh)(?:\.exe)?\b[^\n]*-(?:enc|encodedcommand)\s+[A-Za-z0-9+/=]{10,}"),
    ("certutil_abuse", "Abuses certutil for remote file download or decode",
     "Certutil is a common LOLBIN tool used to download malware or decode payloads.",
     "Use standard curl/wget with explicit URLs, never certutil -urlcache.",
     r"(?i)\bcertutil(?:\.exe)?\b[^\n]*(?:-urlcache|-decode|-ping)"),
    ("mshta_abuse", "Executes HTML Application (MSHTA) script proxy",
     "MSHTA executes arbitrary VBScript/JScript bypassing app restrictions.",
     "Run scripts directly in supported runtime environments.",
     r"(?i)\bmshta(?:\.exe)?\b[^\n]*(?:javascript|vbscript|https?://)"),
    ("vssadmin_delete", "Deletes Volume Shadow Copies (Ransomware behavior)",
     "Deleting shadow copies prevents system restore and is a hallmark of ransomware.",
     "Never allow backup or shadow copy destruction.",
     r"(?i)\bvssadmin(?:\.exe)?\b[^\n]*delete\s+shadows|\bwbadmin(?:\.exe)?\b[^\n]*delete\s+catalog"),
    ("sam_shadow_theft", "Attempts to extract Windows SAM or Linux shadow credentials",
     "Reading or dumping password databases allows offline cracking of all user credentials.",
     "Never access SAM, SYSTEM or shadow files.",
     r"(?i)(?:/etc/shadow|\breg\s+save\s+hklm\\(?:sam|system)\b|\bsecretsdump\b)"),
    ("browser_credential_theft", "Attempts to access browser passwords or cookie stores",
     "Accessing browser SQLite databases allows stealing session cookies and saved passwords.",
     "Never read browser profile credential stores directly.",
     r"(?i)(?:Login\s+Data|Cookies|Web\s+Data|key4\.db|logins\.json)[^\n]*(?:sqlite|\.db|copy|cat|type)"),
    ("reverse_shell", "Opens an interactive reverse shell to a remote IP",
     "Reverse shells grant an attacker full remote interactive command execution.",
     "Use managed SSH connections with public-key authentication.",
     r"(?i)(?:bash\s+-i\s+>&|/dev/tcp/\d+\.\d+\.\d+\.\d+/\d+|\b(?:nc|ncat)\b[^\n]*-[ecl]|\bsocat\s+exec:)"),
    ("credential_file_dump", "Dumps local environment or secret configuration files",
     "Directly printing or copying .env or private key files exposes all system secrets.",
     "Read specific keys via application configuration, not full file dumps.",
     r"(?i)(?:(?:cat|type|more|Get-Content)\s+[^\n]*(?:\.env|\.aws/credentials|id_rsa|id_ed25519|\.kube/config))"),

    # ---- Ring 1: Dangerous OS Execution & Credential Theft Rules ----
    ("powershell_enc", "Executes obfuscated Base64 PowerShell command",
     "Encoded PowerShell commands hide malicious payloads from command line inspection.",
     "Run scripts in plain text or inspect decoded script block first.",
     r"(?i)\b(?:powershell|pwsh)(?:\.exe)?\b[^\n]*-(?:enc|encodedcommand)\s+[A-Za-z0-9+/=]{10,}"),
    ("certutil_abuse", "Abuses certutil for remote file download or decode",
     "Certutil is a common LOLBIN tool used to download malware or decode payloads.",
     "Use standard curl/wget with explicit URLs, never certutil -urlcache.",
     r"(?i)\bcertutil(?:\.exe)?\b[^\n]*(?:-urlcache|-decode|-ping)"),
    ("mshta_abuse", "Executes HTML Application (MSHTA) script proxy",
     "MSHTA executes arbitrary VBScript/JScript bypassing app restrictions.",
     "Run scripts directly in supported runtime environments.",
     r"(?i)\bmshta(?:\.exe)?\b[^\n]*(?:javascript|vbscript|https?://)"),
    ("vssadmin_delete", "Deletes Volume Shadow Copies (Ransomware behavior)",
     "Deleting shadow copies prevents system restore and is a hallmark of ransomware.",
     "Never allow backup or shadow copy destruction.",
     r"(?i)\bvssadmin(?:\.exe)?\b[^\n]*delete\s+shadows|\bwbadmin(?:\.exe)?\b[^\n]*delete\s+catalog"),
    ("sam_shadow_theft", "Attempts to extract Windows SAM or Linux shadow credentials",
     "Reading or dumping password databases allows offline cracking of all user credentials.",
     "Never access SAM, SYSTEM or shadow files.",
     r"(?i)(?:/etc/shadow|\breg\s+save\s+hklm\\(?:sam|system)\b|\bsecretsdump\b)"),
    ("browser_credential_theft", "Attempts to access browser passwords or cookie stores",
     "Accessing browser SQLite databases allows stealing session cookies and saved passwords.",
     "Never read browser profile credential stores directly.",
     r"(?i)(?:Login\s+Data|Cookies|Web\s+Data|key4\.db|logins\.json)[^\n]*(?:sqlite|\.db|copy|cat|type)"),
    ("reverse_shell", "Opens an interactive reverse shell to a remote IP",
     "Reverse shells grant an attacker full remote interactive command execution.",
     "Use managed SSH connections with public-key authentication.",
     r"(?i)(?:bash\s+-i\s+>&|/dev/tcp/\d+\.\d+\.\d+\.\d+/\d+|\b(?:nc|ncat)\b[^\n]*-[ecl]|\bsocat\s+exec:)"),
    ("credential_file_dump", "Dumps local environment or secret configuration files",
     "Directly printing or copying .env or private key files exposes all system secrets.",
     "Read specific keys via application configuration, not full file dumps.",
     r"(?i)(?:(?:cat|type|more|Get-Content)\s+[^\n]*(?:\.env|\.aws/credentials|id_rsa|id_ed25519|\.kube/config))"),

    # ---- Ring 1: Dangerous OS Execution & Credential Theft Rules ----
    ("powershell_enc", "Executes obfuscated Base64 PowerShell command",
     "Encoded PowerShell commands hide malicious payloads from command line inspection.",
     "Run scripts in plain text or inspect decoded script block first.",
     r"(?i)\b(?:powershell|pwsh)(?:\.exe)?\b[^\n]*-(?:enc|encodedcommand)\s+[A-Za-z0-9+/=]{10,}"),
    ("certutil_abuse", "Abuses certutil for remote file download or decode",
     "Certutil is a common LOLBIN tool used to download malware or decode payloads.",
     "Use standard curl/wget with explicit URLs, never certutil -urlcache.",
     r"(?i)\bcertutil(?:\.exe)?\b[^\n]*(?:-urlcache|-decode|-ping)"),
    ("mshta_abuse", "Executes HTML Application (MSHTA) script proxy",
     "MSHTA executes arbitrary VBScript/JScript bypassing app restrictions.",
     "Run scripts directly in supported runtime environments.",
     r"(?i)\bmshta(?:\.exe)?\b[^\n]*(?:javascript|vbscript|https?://)"),
    ("vssadmin_delete", "Deletes Volume Shadow Copies (Ransomware behavior)",
     "Deleting shadow copies prevents system restore and is a hallmark of ransomware.",
     "Never allow backup or shadow copy destruction.",
     r"(?i)\bvssadmin(?:\.exe)?\b[^\n]*delete\s+shadows|\bwbadmin(?:\.exe)?\b[^\n]*delete\s+catalog"),
    ("sam_shadow_theft", "Attempts to extract Windows SAM or Linux shadow credentials",
     "Reading or dumping password databases allows offline cracking of all user credentials.",
     "Never access SAM, SYSTEM or shadow files.",
     r"(?i)(?:/etc/shadow|\breg\s+save\s+hklm\\(?:sam|system)\b|\bsecretsdump\b)"),
    ("browser_credential_theft", "Attempts to access browser passwords or cookie stores",
     "Accessing browser SQLite databases allows stealing session cookies and saved passwords.",
     "Never read browser profile credential stores directly.",
     r"(?i)(?:Login\s+Data|Cookies|Web\s+Data|key4\.db|logins\.json)[^\n]*(?:sqlite|\.db|copy|cat|type)"),
    ("reverse_shell", "Opens an interactive reverse shell to a remote IP",
     "Reverse shells grant an attacker full remote interactive command execution.",
     "Use managed SSH connections with public-key authentication.",
     r"(?i)(?:bash\s+-i\s+>&|/dev/tcp/\d+\.\d+\.\d+\.\d+/\d+|\b(?:nc|ncat)\b[^\n]*-[ecl]|\bsocat\s+exec:)"),
    ("credential_file_dump", "Dumps local environment or secret configuration files",
     "Directly printing or copying .env or private key files exposes all system secrets.",
     "Read specific keys via application configuration, not full file dumps.",
     r"(?i)(?:(?:cat|type|more|Get-Content)\s+[^\n]*(?:\.env|\.aws/credentials|id_rsa|id_ed25519|\.kube/config))"),
]
_COMPILED = [(k, t, w, s, re.compile(r, re.I | re.M)) for k, t, w, s, r in RULES]


def scan_actions(args: Any, tool_name: str = "") -> List[RiskyAction]:
    # Guard-self-modification rules must only fire on real filesystem / shell
    # / code-exec tools. The internal `memory` tool stores text notes; a note
    # mentioning "yadro-guard", "config.json" or "vault" is NOT an attempt to
    # tamper with the guard and must never be blocked (memory -> memory).
    _self_tamper_tools = {"write_file", "execute_code", "terminal", "shell", "exec",
                          "bash", "powershell", "cmd", "pwsh", "edit_file", "patch",
                          "apply_patch", "run", "save_file", "append_file"}
    is_memory_tool = (tool_name or "").lower() in ("memory", "memorize", "remember")
    out: List[RiskyAction] = []
    seen = set()
    for path, text in walk_args(args):
        if not isinstance(text, str) or len(text) > 256 * 1024:
            continue
        for kind, title, why, safer, rx in _COMPILED:
            if kind in ("tamper_guard_env", "tamper_guard_files") and (is_memory_tool or tool_name not in _self_tamper_tools):
                continue
            m = rx.search(text)
            if m and kind not in seen:
                seen.add(kind)
                if "\n" in text:
                    line_start = text.rfind("\n", 0, m.start()) + 1
                    line_end = text.find("\n", m.end())
                    if line_end == -1:
                        line_end = len(text)
                    snip = text[line_start:line_end].strip()
                else:
                    snip = text.strip()
                out.append(RiskyAction(kind, title, why, safer, path, snip[:4096]))
    return out
