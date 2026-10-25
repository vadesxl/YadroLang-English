# -*- coding: utf-8 -*-
"""MCP Secrets Guard - code/script analysis backend for the Guard dashboard tab.

Invoked by the dashboard (dashboard/plugin_api.py) as::

    python -m src.guard_api scan  <file.yad>
    python -m src.guard_api autofix <file.yad>
    python -m src.guard_api report-text --stdin

Supports TWO analysis pipelines:
  - YadroLang files (.yad / .яд): full compiler + EthicalAnalyzer (semantic)
  - Everything else (Python, Bash, JS, MCP, plain text): runtime detectors + actions (generic)

Contract (GuardApiTests in tests/test_vault_and_api.py):
  analyze(path)            -> analyze a file (path str, not code)
  analyze_text(code, lang) -> analyze code string; raises InputError on empty
  report_text(code, lang)  -> {"status": "ok", "html": ...}
  fix(path)               -> autofix YadroLang file in place
  main(argv)              -> CLI entry point (compatible with existing tests)
  InputError              -> exception class (inherits ValueError)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict

# ------------------------------------------------------------------ generic scanner (always)
from src.runtime import detectors, actions

# ------------------------------------------------------------------ YadroLang compiler (may not be in all repo variants)
try:
    from src.lexer import Lexer, LexerError
    from src.syntax import Parser, ParserError
    from src.ethics import EthicalAnalyzer, EthicalError
    from src import ethics_v21 as _runtime
    _YADRO_AVAILABLE = True
except ImportError:
    _YADRO_AVAILABLE = False
    Lexer = LexerError = None
    Parser = ParserError = None
    EthicalAnalyzer = EthicalError = None
    _runtime = None

# ------------------------------------------------------------------ exceptions
class InputError(ValueError):
    """Raised for empty input or syntax errors in analyze_text."""
    pass

# ------------------------------------------------------------------ constants
KNOWN_GAPS = [
    "Static scan of the pasted text only: it does not follow values at runtime.",
    "It cannot see what the program was given from the environment or secrets in other files.",
    "A secret that is split, encoded or assembled at runtime is not caught here.",
    "Check the plain text for anything this scanner may not model.",
]

# Label display names
_LABELS_RU = {
    "Credentials": "Учётные данные и ключи",
    "Financial": "Финансы",
    "PII": "ПДн",
    "Health": "Здоровье",
    "Location": "Локация",
}
_LABELS_EN = {
    "Credentials": "Credentials & keys",
    "Financial": "Financial",
    "PII": "PII",
    "Health": "Health",
    "Location": "Location",
}

# Protection/quarantine options
_PROTECT_RU = {
    "Credentials": [("Хранить в vault", "vault.stash"), ("Шифровать", "encrypt"), ("Секретная ссылка", "env.secret")],
    "Financial":   [("Токенизировать", "vault.tokenize"), ("Шифровать", "encrypt")],
    "PII":         [("Маскировать", "redact.mask"), ("Псевдонимизировать", "anon.pseudonymize")],
    "Health":      [("Шифровать", "encrypt"), ("Анонимизировать", "anon.anonymize")],
    "Location":    [("Агрегировать", "anon.aggregate")],
}
_PROTECT_EN = {
    "Credentials": [("Store in vault", "vault.stash"), ("Encrypt at rest", "encrypt"), ("Use secret reference", "env.secret")],
    "Financial":   [("Tokenize", "vault.tokenize"), ("Encrypt", "encrypt")],
    "PII":         [("Mask", "redact.mask"), ("Pseudonymize", "anon.pseudonymize")],
    "Health":      [("Encrypt", "encrypt"), ("Anonymize", "anon.anonymize")],
    "Location":    [("Aggregate", "anon.aggregate")],
}

_SINK_HUMAN_RU = {
    "net.send": "отправку в сеть", "net.request": "сетевой запрос",
    "file.write": "запись в файл", "db.write": "запись в БД",
    "log.info": "лог", "email.send": "отправку email",
}
_SINK_HUMAN_EN = {
    "net.send": "network send", "net.request": "network request",
    "file.write": "file write", "db.write": "database write",
    "log.info": "log output", "email.send": "email send",
}

# Keywords that identify YadroLang source
_YADRO_RU_KW = {"функ", "вернуть", "если", "пока", "переменная", "секрет", "сеть", "доступ", "требует", "старт", "тело"}
_YADRO_EN_KW = {"fn", "func", "function", "return", "if", "while", "let", "var", "const", "requires", "start", "body"}


def _detect_yadro_lang(source: str) -> str:
    """Detect 'ru', 'en', or 'yadro' (mixed/unknown) based on keyword presence."""
    src_lower = source.lower()
    has_ru = any(kw in src_lower for kw in _YADRO_RU_KW)
    has_en = any(kw in src_lower for kw in _YADRO_EN_KW)
    if has_ru and not has_en:
        return "ru"
    if has_en and not has_ru:
        return "en"
    return "yadro"  # mixed or unknown

# ------------------------------------------------------------------ RU -> EN translation
# The compiler's lexer/ethics only know English YadroLang. guard_api translates Russian
# keywords + API names to English before compiling, then reports line numbers from the
# ORIGINAL source. Translation is token-for-token on the same line, so line numbers match.
_YADRO_KEYWORD_RU = {
    "функ": "fn", "вернуть": "return", "пусть": "let", "переменная": "let",
    "если": "if", "иначе": "else", "пока": "while",
    "правда": "true", "ложь": "false", "требует": "requires",
    "истина": "true", "ложно": "false",
}
_YADRO_MANDATE_RU = {
    "ДоступСети": "NetworkAccess", "ДоступИнтернет": "NetworkAccess",
    "ЗаписьДиска": "DiskWrite", "ЗаписьБД": "DatabaseWrite",
    "ЧтениеБД": "DatabaseRead", "ДоступЛога": "LogAccess",
    "ЗаписьФайла": "DiskWrite", "ДоступКСети": "NetworkAccess",
}
_YADRO_API_RU = {
    "среда.секрет": "env.secret", "сеть.отправить": "net.send",
    "сеть.запрос": "net.request", "сеть.пост": "net.post",
    "сеть.редирект": "http.redirect", "вебсокет.отправить": "ws.send",
    "файл.записать": "file.write", "файл.удалить": "file.delete",
    "файл.дописать": "file.append", "бд.записать": "db.write",
    "бд.вставить": "db.insert", "бд.обновить": "db.update",
    "бд.удалить": "db.delete", "бд.запрос": "db.query",
    "журнал.инфо": "log.info", "журнал.отладка": "log.debug",
    "журнал.ошибка": "log.error", "консоль.лог": "console.log",
    "апи.вызов": "api.call", "почта.отправить": "email.send",
    "смс.отправить": "sms.send", "пользователь.данные": "user.data",
    "пользователь.имя": "user.name", "пользователь.почта": "user.email",
    "пользователь.телефон": "user.phone", "пользователь.адрес": "user.address",
    "пользователь.ид": "user.id", "личное.читать": "personal.read",
    "запрос.тело": "request.body", "запрос.параметры": "request.params",
    "куки.получить": "cookie.get", "сессия.получить": "session.get",
    "платеж.карта": "payment.card", "счет.баланс": "account.balance",
    "транзакция.получить": "transaction.get", "банк.счет": "bank.account",
    "пациент.запись": "patient.record", "медицина.история": "medical.history",
    "диагноз.получить": "diagnosis.get", "хранилище.читать": "vault.read",
    "ключ.приватный": "key.private", "гео.локация": "geo.location",
    "гпс.координаты": "gps.coordinates", "файл.читать": "file.read",
    "сеть.принять": "net.accept", "бд.читать": "db.read",
    "анонимизировать": "anonymize", "хешировать": "hash",
    "шифровать": "encrypt", "маскировать": "mask",
    "редкактировать": "redact", "изъять": "redact",
    "токенизировать": "tokenize", "псевдонимизировать": "pseudonymize",
    "агрегировать": "aggregate", "проверить_согласие": "check_consent",
}
_CYRILLIC = "А-Яа-яЁё"


def _translate_ru_yadro(source: str) -> str:
    """Translate Russian YadroLang source to the English form the compiler understands."""
    out = source
    # 1) dotted API names and standalone sanitizer/source/sink names (longest first)
    api_keys = sorted(_YADRO_API_RU, key=len, reverse=True)
    for ru in api_keys:
        out = out.replace(ru, _YADRO_API_RU[ru])
    # 2) mandate labels inside [...] : ДоступСети -> NetworkAccess
    for ru, en in _YADRO_MANDATE_RU.items():
        out = out.replace(ru, en)
    # 3) keywords on term boundaries (don't match inside longer Cyrillic words)
    for ru, en in _YADRO_KEYWORD_RU.items():
        out = _regex_replace_word(out, ru, en)
    return out


import re as _re


def _regex_replace_word(text: str, ru: str, en: str) -> str:
    rx = _re.compile(r"(?<![A-Za-zа-яёА-ЯЁ0-9])%s(?![A-Za-zа-яёА-ЯЁ0-9])" % _re.escape(ru))
    return rx.sub(en, text)

# ------------------------------------------------------------------ YadroLang detection
def _is_yadro_content(source: str) -> bool:
    src_lower = source.lower()
    return any(kw in src_lower for kw in _YADRO_RU_KW | _YADRO_EN_KW)


def _is_yadro_file(path: str) -> bool:
    p = Path(path)
    ext = p.suffix.lower()
    if ext in {".yad", ".yd", ".yad_lang", ".яд", ".jad"}:
        return True
    if ext == ".txt":
        return False  # .txt always goes to generic unless content says otherwise
    try:
        first = ""
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    first = stripped
                    break
        if first:
            return _is_yadro_content(first)
    except Exception:
        pass
    return False


# ------------------------------------------------------------------ line utilities
def _line_of(text: str, pos: int) -> int:
    return 1 + text.count("\n", 0, max(0, pos))


def _line_at(text: str, line_num: int) -> str:
    lines = text.splitlines()
    if 1 <= line_num <= len(lines):
        return lines[line_num - 1].strip()
    return (lines[0] if lines else "").strip()


def _extract_line_from_msg(msg: str) -> int:
    import re
    m = re.search(r"line (\d+)", msg)
    return int(m.group(1)) if m else 1


# ------------------------------------------------------------------ generic scanner
def _generic_analyze(code: str, lang: str = "en") -> Dict[str, Any]:
    findings = detectors.scan_text(code)
    risky = actions.scan_actions({"script": code})
    if not findings and not risky:
        return {"status": "ok", "lines": len(code.splitlines()) or 1,
                "sanitized": [], "known_gaps": KNOWN_GAPS}

    labels_map = _LABELS_EN if lang == "en" else _LABELS_RU
    protect_map = _PROTECT_EN if lang == "en" else _PROTECT_RU

    if findings:
        f = findings[0]
        labels = sorted({x.label for x in findings})
        quarantine = [
            {"label": labels_map.get(lbl, lbl),
             "options": [{"human": h, "fn": fn} for h, fn in protect_map.get(lbl, [("Store in vault", "vault.stash")])]}
            for lbl in labels
        ]
        autofix = _generic_autofix(code, findings, lang)
        return {
            "status": "leak",
            "line": _line_of(code, f.start),
            "code": _line_at(code, _line_of(code, f.start)),
            "why": f.title + ": " + _sink_human(f.kind, lang),
            "labels": [{"label": labels_map.get(lbl, lbl)} for lbl in labels],
            "sources": [],
            "sink": {"name": f.kind, "human": _sink_human(f.kind, lang)},
            "quarantine": quarantine,
            "autofix": autofix,
            "risky": [a.public() for a in risky],
            "known_gaps": KNOWN_GAPS,
        }

    a = risky[0]
    return {
        "status": "leak", "line": 0, "code": a.snippet[:240],
        "why": a.title + ". " + a.why,
        "labels": [], "sources": [], "sink": {"name": a.kind, "human": a.title},
        "quarantine": [], "autofix": None,
        "risky": [a.public() for a in risky],
        "known_gaps": KNOWN_GAPS,
    }


def _sink_human(kind: str, lang: str) -> str:
    return (_SINK_HUMAN_EN if lang == "en" else _SINK_HUMAN_RU).get(kind, "sensitive data")


def _generic_autofix(code: str, findings, lang: str) -> Dict[str, Any]:
    fixed = code
    first = findings[0]
    for f in sorted(findings, key=lambda x: x.start, reverse=True):
        if 0 <= f.start < f.end <= len(fixed):
            fixed = fixed[:f.start] + f"[protected:{f.kind}]" + fixed[f.end:]
    verified = bool(findings) and not detectors.scan_text(fixed)
    return {
        "before": _line_at(code, _line_of(code, first.start)),
        "after": _line_at(fixed, _line_of(code, first.start)),
        "verified": verified, "fixed_code": fixed, "count": len(findings),
    }


# ------------------------------------------------------------------ YadroLang scanner
def _yadro_analyze(source: str, path: str, lang: str = "en") -> Dict[str, Any]:
    if not _YADRO_AVAILABLE:
        return {"status": "error", "message": "YadroLang compiler not available in this repo variant",
                "known_gaps": KNOWN_GAPS}

    # Translate Russian YadroLang to the English the compiler understands.
    # report line numbers from the ORIGINAL source (translation is line-preserved).
    detected = _detect_yadro_lang(source)
    has_russian = (detected == "ru")
    work_source = _translate_ru_yadro(source) if has_russian else source
    # Use 'ru' labels if Russian YadroLang, 'en' otherwise
    effective_lang = "ru" if has_russian else "en"

    try:
        tokens = Lexer(work_source).tokens()
        ast = Parser(tokens).parse()
    except Exception as e:
        # Catch any syntax error (LexerError, ParserError, or their stubs) by name
        err_name = type(e).__name__
        if err_name in ("LexerError", "ParserError"):
            return {"status": "error", "message": f"Syntax error in YadroLang: {e}"}
        # A preserved/sanitized construction that the parser rejects: report as error
        if err_name in ("EthicalError", "EntryPointError", "SemanticError"):
            return {"status": "error", "message": f"YadroLang: {e}"}
        raise  # re-raise anything else

    analyzer = EthicalAnalyzer()
    try:
        analyzer.check(ast)
    except EthicalError as e:
        code_str = getattr(e, "code", "YADRO-E2999")
        line_num = _extract_line_from_msg(str(e))

        # Find the audit entry that matches
        entry = None
        for ent in analyzer.audit_trail:
            if ent.line == line_num:
                entry = ent
                break
        if entry is None and analyzer.audit_trail:
            entry = analyzer.audit_trail[-1]

        label = entry.label if entry else "Credentials"
        sink_name = entry.sink if entry else "net.send"
        snippet = entry.detail if (entry and entry.detail) else _line_at(source, line_num)

        labels_map = _LABELS_RU if effective_lang == "ru" else _LABELS_EN
        protect_map = _PROTECT_RU if effective_lang == "ru" else _PROTECT_EN
        human_label = labels_map.get(label, label)

        quarantine = [{
            "label": human_label,
            "options": [{"human": h, "fn": fn}
                        for h, fn in protect_map.get(label, [("Store in vault", "vault.stash")])]
        }]

        autofix = _yadro_autofix(source, entry, label, lang, is_russian=has_russian)
        return {
            "status": "leak",
            "line": line_num,
            "code_language": effective_lang,
            "code": code_str,
            "code_error_code": code_str,
            "why": f"[{code_str}] Data leak: {label} data reaches {sink_name} without allowed sanitizer.",
            "labels": [{"label": human_label}],
            "sources": [],
            "sink": {"name": sink_name, "human": _sink_human(sink_name, lang)},
            "quarantine": quarantine,
            "autofix": autofix,
            "risky": [],
            "known_gaps": KNOWN_GAPS,
        }

    return {"status": "ok", "code_language": effective_lang,
            "lines": len(source.splitlines()), "sanitized": [], "known_gaps": KNOWN_GAPS}


def _yadro_autofix(source: str, entry, label: str, lang: str, is_russian: bool = False) -> Dict[str, Any]:
    """Wrap leaky sink call with the first compliant sanitizer for the label."""
    if _runtime is None:
        return {"wrapper": "encrypt", "verified": False, "fixed_code": source}

    compliance = getattr(_runtime, "COMPLIANCE", {})
    sanitizers = compliance.get(label, set())
    wrapper = "encrypt" if "encrypt" in sanitizers else next(iter(sanitizers), "encrypt")

    if entry:
        line_num = entry.line or 1
        sink = entry.sink
        # Work in the TRANSLATED source (English YadroLang that the compiler sees)
        line_text = _line_at(source, line_num)
        work_source = _translate_ru_yadro(source) if is_russian else source
        work_line = _line_at(work_source, line_num)
        if sink in work_line:
            import re as _re_af
            m = _re_af.search(r"{}\s*\(".format(_re_af.escape(sink)), work_line)
            if m:
                paren_start = m.end() - 1
                depth = 1
                pos = paren_start + 1
                while pos < len(work_line) and depth > 0:
                    c = work_line[pos]
                    if c == '(':
                        depth += 1
                    elif c == ')':
                        depth -= 1
                    pos += 1
                if depth == 0:
                    arg_text = work_line[paren_start+1:pos-1].strip()
                    if arg_text:
                        new_arg = "{}({})".format(wrapper, arg_text.split(',')[0].strip())
                        work_fixed = work_line[:paren_start+1] + new_arg + work_line[pos-1:]
                        # Replace the line in the work source
                        work_lines = work_source.splitlines()
                        work_lines[line_num-1] = work_fixed
                        fixed_work = "\n".join(work_lines)
                        # For Russian, we need to keep the Russian keywords - use a targeted fix
                        if is_russian:
                            # Find Russian sink equivalent and fix only that call
                            ru_sink = next((ru for ru, en in _YADRO_API_RU.items() if en == sink), sink)
                            if ru_sink and ru_sink in line_text:
                                # Find the Russian sink call pattern
                                import re as _re2
                                m_r = _re2.search(r"({})\s*\(".format(_re2.escape(ru_sink)), line_text)
                                if m_r:
                                    p_start = m_r.end() - 1
                                    d_r = 1
                                    p_r = p_start + 1
                                    while p_r < len(line_text) and d_r > 0:
                                        cr = line_text[p_r]
                                        if cr == '(':
                                            d_r += 1
                                        elif cr == ')':
                                            d_r -= 1
                                        p_r += 1
                                    if d_r == 0:
                                        arg_r = line_text[p_start+1:p_r-1].strip()
                                        new_arg_r = "{}({})".format(wrapper, arg_r.split(',')[0].strip())
                                        fixed = source.replace(line_text, line_text[:p_start+1] + new_arg_r + line_text[p_r-1:], 1)
                                    else:
                                        fixed = source
                                else:
                                    fixed = source
                            else:
                                fixed = source
                        else:
                            fixed = fixed_work
                    else:
                        fixed = source
                else:
                    fixed = source
            else:
                fixed = source
        else:
            fixed = source
    else:
        fixed = source

    # Verify: for Russian sources, translate fixed code first, then verify
    verified = False
    try:
        to_verify = _translate_ru_yadro(fixed) if is_russian else fixed
        tokens2 = Lexer(to_verify).tokens()
        ast2 = Parser(tokens2).parse()
        analyzer2 = EthicalAnalyzer()
        analyzer2.check(ast2)
        verified = True
    except Exception:
        pass

    return {"wrapper": wrapper, "verified": verified, "fixed_code": fixed}


# ------------------------------------------------------------------ public API

def analyze(path: str) -> Dict[str, Any]:
    """Analyze a file (path string). Dispatches to YadroLang or generic scanner."""
    p = Path(path)
    if not p.exists():
        return {"status": "error", "message": f"File not found: {path}"}

    ext = p.suffix.lower()
    BLOCKED_EXTENSIONS = {
        ".exe", ".dll", ".so", ".dylib", ".bin", ".png", ".jpg", ".jpeg",
        ".gif", ".mp3", ".mp4", ".pdf", ".zip", ".tar", ".gz", ".rar",
    }
    try:
        source = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {"status": "error", "message": "Unsupported file type"}

    if not source.strip():
        return {"status": "error", "message": "Empty input"}

    # YadroLang detection: only by explicit .yad/.яд extension (or known Yadro name).
    # Anything else (including .txt) goes to the generic scanner, so the tab is omnivorous.
    is_yadro = ext in {".yad", ".yd", ".yad_lang", ".яд", ".jad"}
    if is_yadro and _YADRO_AVAILABLE:
        return _yadro_analyze(source, path, _detect_yadro_lang(source))

    return _generic_analyze(source, "en")


def analyze_text(code: str, lang: str = "en") -> Dict[str, Any]:
    """Analyze a code string. Raises InputError on empty input."""
    if not code or not code.strip():
        raise InputError("Empty input")

    if _YADRO_AVAILABLE and _is_yadro_content(code[:500]):
        return _yadro_analyze(code, "<analyze_text>", lang)

    return _generic_analyze(code, lang)


def report_text(code: str, lang: str = "en") -> Dict[str, Any]:
    """Return HTML report dict with status+html fields. Content is XSS-safe."""
    try:
        result = analyze_text(code, lang)
    except InputError as e:
        result = {"status": "error", "message": str(e)}

    if result.get("status") == "ok":
        body = "<p>No leaks found.</p>"
    elif result.get("status") == "leak":
        body = "<p>Line %s: %s</p>" % (
            result.get("line", "?"), _esc(str(result.get("why", ""))))
        q = result.get("quarantine") or []
        if q:
            body += "<p>Protections:</p><ul>" + \
                "".join("<li>%s</li>" % _esc(it.get("label", "")) for it in q) + \
                "</ul>"
    else:
        body = "<p>%s</p>" % _esc(str(result.get("message", "")))

    body += ("<p><em>Honest limits</em>: this scanner cannot track values across runtime, "
             "cannot see environment variables or secrets in other files, "
             "and encoded/split secrets may slip through.</p>")

    html = (
        '<!doctype html><html lang=en><meta charset=utf-8>'
        '<title>MCP Secrets Guard report</title>'
        '<body style="font:13px/1.5 system-ui;padding:16px;color:#222">'
        '<h3>MCP Secrets Guard — report</h3>'
        + body +
        '</body></html>'
    )
    return {"status": "ok", "html": html}


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&#39;"))


def fix(path: str) -> Dict[str, Any]:
    """Autofix a YadroLang file. Writes fixed code back to the file."""
    p = Path(path)
    if not p.exists():
        return {"status": "error", "message": f"File not found: {path}"}

    if not _is_yadro_file(path):
        raise InputError(f"fix() only supports YadroLang files, got: {path}")

    if not _YADRO_AVAILABLE:
        return {"status": "error", "message": "YadroLang compiler not available",
                "known_gaps": KNOWN_GAPS}

    source = p.read_text(encoding="utf-8")
    result = _yadro_analyze(source, path, _detect_yadro_lang(source))

    if result.get("status") != "leak":
        return {"status": "ok", "written": str(p)}  # already clean

    autofix_data = result.get("autofix", {})
    fixed_code = autofix_data.get("fixed_code", source)
    p.write_text(fixed_code, encoding="utf-8")
    return {"status": "fixed", "written": str(p)}


# ------------------------------------------------------------------ CLI entry point
EXIT_OK = 0
EXIT_SOURCE = 3


def run(argv=None, stdin=None, stdout=None) -> int:
    stdout = stdout or sys.stdout
    stdin = stdin or sys.stdin
    # Windows CI / console defaults to CP1252; force UTF-8 so Russian YadroLang
    # keywords (функ, вернуть) never trip UnicodeDecodeError/EncodeError.
    for stream in (sys.stdin, sys.stdout, getattr(sys, "stderr", None)):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):
            pass
    parser = argparse.ArgumentParser(prog="src.guard_api")
    parser.add_argument("command", choices=("analyze", "scan", "autofix", "report-text"))
    parser.add_argument("--stdin", action="store_true")
    parser.add_argument("--lang", default="en")
    parser.add_argument("file", nargs="?")          # positional: scan <file>, autofix <file>
    args = parser.parse_args(argv)

    try:
        if args.command == "scan":
            if not args.file:
                return _fail(stdout, "usage: scan <file>")
            r = analyze(args.file)
            stdout.write(json.dumps(r, ensure_ascii=False))
            return EXIT_OK if r.get("status") != "error" else EXIT_SOURCE

        elif args.command == "autofix":
            if not args.file:
                return _fail(stdout, "usage: autofix <file>")
            r = fix(args.file)
            stdout.write(json.dumps(r, ensure_ascii=False))
            return EXIT_OK if r.get("status") != "error" else EXIT_SOURCE

        elif args.command == "analyze":
            # Stdin mode (used by dashboard plugin_api via /analyze)
            try:
                data = json.loads(stdin.read() or "{}")
            except ValueError:
                return _fail(stdout, "bad JSON input")
            code = data.get("code", "")
            try:
                r = analyze_text(code, args.lang)
            except InputError as e:
                r = {"status": "error", "message": str(e)}
            stdout.write(json.dumps(r, ensure_ascii=False))
            return EXIT_OK if r.get("status") != "error" else EXIT_SOURCE

        elif args.command == "report-text":
            # Read JSON doc from stdin (args.stdin means --stdin flag was given)
            try:
                data = json.loads(stdin.read() or "{}")
            except ValueError:
                return _fail(stdout, "bad JSON input")
            code = data.get("code", "")
            r = report_text(code, args.lang)
            stdout.write(json.dumps(r, ensure_ascii=False))
            return EXIT_OK

    except InputError as e:
        stdout.write(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        return EXIT_SOURCE
    except Exception as exc:
        stdout.write(json.dumps({"status": "error", "message": f"{type(exc).__name__}: {exc}"},
                               ensure_ascii=False))
        return EXIT_SOURCE
    return EXIT_OK


def _fail(stdout, msg: str) -> int:
    stdout.write(json.dumps({"status": "error", "message": msg}, ensure_ascii=False))
    return EXIT_SOURCE


def main(argv=None) -> int:
    try:
        return run(argv)
    except SystemExit:
        return 3  # argparse errors exit(2); map to our error code


if __name__ == "__main__":
    main()
