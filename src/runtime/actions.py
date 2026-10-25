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
    group: str = "danger"       # exposure | destructive | tamper | danger
    title_ru: str = ""
    why_ru: str = ""
    safer_ru: str = ""

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
]
# Russian copy of every rule, kept next to the rule so the dashboard never has to
# translate rule texts by itself (the journal may be read months later).
RU_TEXT = {
    "expose_bind_all": (
        "Открывает сервер на всю сеть",
        "Сервис будет принимать подключения с любого устройства в сети, а при пробросе порта на роутере - и из интернета.",
        "Используйте --host 127.0.0.1 (привязку к localhost), если другим устройствам это действительно не нужно."),
    "expose_ollama": (
        "Открывает Ollama в сеть",
        "Любой в сети сможет запускать, скачивать и удалять ваши локальные ИИ-модели.",
        "Оставьте OLLAMA_HOST=127.0.0.1."),
    "expose_docker_port": (
        "Публикует порт контейнера на всех интерфейсах",
        "docker -p без адреса публикует порт во все сети и часто обходит брандмауэр Windows.",
        "Используйте -p 127.0.0.1:ПОРТ:ПОРТ."),
    "http_server_all": (
        "Раздает папку по HTTP",
        "python -m http.server по умолчанию отдаёт всю папку в сеть.",
        "Добавьте --bind 127.0.0.1 и не запускайте это в папке с секретами."),
    "public_tunnel": (
        "Открывает публичный туннель в интернет",
        "Туннели (ngrok, cloudflared, localtunnel, bore) публикуют локальный сервис в интернете в обход роутера и брандмауэра.",
        "Открывайте только свой туннель, с паролем, и закрывайте его после использования."),
    "firewall_open": (
        "Открывает порт в брандмауэре или отключает его",
        "Меняет то, что интернет может достучаться на этом компьютере.",
        "Сначала спросите пользователя; открывайте только конкретный порт для конкретной программы."),
    "rdp_enable": (
        "Включает удалённый рабочий стол",
        "Remote Desktop - самая атакуемая служба в интернете.",
        "Используйте VPN вместо публикации удалённого рабочего стола."),
    "destroy_files": (
        "Рекурсивно удаляет файлы",
        "Это безвозвратно удаляет дерево папок. Агенты так уже стирали проекты и домашние каталоги.",
        "Удаляйте только точный путь, который назвал пользователь, и лучше переносите в корзину."),
    "destroy_db": (
        "Уничтожает данные базы",
        "DROP / TRUNCATE / DELETE без WHERE удаляют данные навсегда.",
        "Сначала сделайте резервную копию и подтвердите конкретную таблицу у пользователя."),
    "git_force": (
        "Перезаписывает историю git на сервере",
        "Force push может стереть чужую работу и опубликованную историю.",
        "Используйте --force-with-lease или сначала спросите пользователя."),
    "pipe_to_shell": (
        "Запускает скрипт прямо из интернета",
        "Скачивание и запуск в один шаг выполняет всё, что пришлёт сервер, с вашими правами.",
        "Скачайте скрипт, прочитайте его, и только потом запускайте."),
    "disable_defender": (
        "Отключает защиту от вирусов",
        "Отключение Defender убирает защиту от вредоносных программ.",
        "Не позволяйте агенту менять настройки антивируса."),
    "tamper_guard_env": (
        "Отключает или меняет окружение шлюза",
        "Именно так агент попытался бы отключить защиту из командной строки.",
        "У шлюза намеренно нет выключателя через переменные окружения: менять YADRO_GUARD_* бесполезно и блокируется."),
    "tamper_guard_files": (
        "Изменяет или удаляет файлы шлюза",
        "Удаление или перезапись конфигурации, сейфа или журнала инцидентов снимает или ослабляет защиту.",
        "Никогда не давайте агенту трогать каталог шлюза и его файлы сейфа, конфигурации и решений."),
}

# Category shown in the dashboard ("Что обнаружено") for each rule.
RULE_GROUP = {
    "expose_bind_all": "exposure", "expose_ollama": "exposure",
    "expose_docker_port": "exposure", "http_server_all": "exposure",
    "public_tunnel": "exposure", "firewall_open": "exposure", "rdp_enable": "exposure",
    "destroy_files": "destructive", "destroy_db": "destructive", "git_force": "destructive",
    "disable_defender": "destructive", "pipe_to_shell": "danger",
    "tamper_guard_env": "tamper", "tamper_guard_files": "tamper",
}

_COMPILED = [(k, t, w, s, re.compile(r, re.I | re.M)) for k, t, w, s, r in RULES]


def scan_actions(args: Any) -> List[RiskyAction]:
    out: List[RiskyAction] = []
    seen = set()
    for path, text in walk_args(args):
        if not isinstance(text, str) or len(text) > 256 * 1024:
            continue
        for kind, title, why, safer, rx in _COMPILED:
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
                ru = RU_TEXT.get(kind, ("", "", ""))
                out.append(RiskyAction(kind, title, why, safer, path, snip[:4096],
                                       RULE_GROUP.get(kind, "danger"), ru[0], ru[1], ru[2]))
    return out
