# -*- coding: utf-8 -*-
"""Adversary-in-the-Middle (AiTM / Evilginx) detector.

Catches the URL-credential phishing that an AiTM proxy performs: the attacker
registers a domain that LOOKS like a real brand login and forwards the victim's
session tokens / auth codes / SAML responses to a third-party host.

Heuristics (pure Python, no network):
    homoglyph_brand   a known brand name where Latin letters were swapped for
                      visually identical Cyrillic / confusable ones (e.g. мicrosoft.com);
    brand_typo_host   a host label that is a misspelling of a known brand
                      (e.g. microsoftoffce.com instead of microsoft);
    fake_auth_host    an auth-ish subdomain (login/account/secure/office/outlook/
                      microsoftonline/...) that is NOT one of the canonical real
                      brand SSO endpoints (typofarmed look-alike);
    punycode_domain   an xn-- punycode label, the standard trick to pack an ASCII
                      label into an IDN so it renders as a brand but resolves elsewhere;
    sso_token_param   a session/auth token (code=, id_token=, SAMLResponse=,
                      access_token=, session=, state=) passed in a URL to a
                      third-party / non-local host - the signature of a token-stealer.

scan(text) -> list[Finding] reusing the engine Finding dataclass.
"""
from __future__ import annotations

import re
from typing import List

from .detectors import Finding

# visually-identical Latin look-alikes (lowercase + uppercase) used by homoglyph campaigns
_CONF = {
    "а": "a", "е": "e", "о": "o", "р": "p",
    "с": "c", "у": "y", "х": "x", "в": "b",
    "н": "h", "к": "k", "м": "m", "т": "t",
    "и": "i", "ы": "u", "з": "z",
    "А": "A", "Е": "E", "О": "O", "Р": "P",
    "С": "C", "У": "Y", "Х": "X", "В": "B",
    "Н": "H", "К": "K", "М": "M", "Т": "T",
    "И": "I", "Ы": "U", "З": "Z",
}

_BRANDS = (
    "microsoft", "microsoftonline", "microsoft365", "office", "outlook",
    "google", "gmail", "apple", "icloud", "amazon", "github",
    "facebook", "instagram", "adobe", "netflix", "paypal", "dropbox",
    "telegram", "twitter", "x", "yandex", "mail", "linkedin", "roblox",
    "steam", "whatsapp", "broadcom", "securelogin",
)
# legit longer brand-like host labels so we don't mistake them for typos
_LEGIT_BRAND_LABELS = {"microsoftonline", "microsoft365", "microsoftstore"}

# canonical real SSO / auth endpoints
_LEGIT_AUTH_HOSTS = {
    "login.microsoftonline.com", "login.microsoft.com", "login.live.com",
    "account.microsoft.com", "account.google.com", "accounts.google.com",
    "accounts.youtube.com", "login.google.com", "appleid.apple.com",
    "id.apple.com", "account.apple.com", "auth.icloud.com",
    "github.com", "www.github.com", "login.github.com", "facebook.com",
    "www.facebook.com", "m.facebook.com", "instagram.com",
    "authy.com", "login.yahoo.com",
    "www.office.com", "office.com", "outlook.com", "www.outlook.com",
    "login.adobe.com", "auth.adobe.com", "www.amazon.com",
    "www.netflix.com", "www.paypal.com", "www.dropbox.com",
    "web.telegram.org", "twitter.com", "x.com", "login.yandex.ru",
    "e.mail.ru", "www.linkedin.com", "auth.roblox.com",
    "store.steampowered.com", "web.whatsapp.com",
}

_AUTH_WORDS = (
    "login", "account", "accounts", "signin", "sign-in", "auth", "secure",
    "office", "outlook", "microsoftonline", "microsoft365", "sso",
    "verify", "verification", "confirm", "recover", "password",
    "session", "identity", "idp", "passport",
)

_TOKEN_PARAMS = (
    "code", "id_token", "samlresponse", "access_token", "session",
    "state", "token", "auth", "sessionkey", "session_id", "sid",
    "jwt", "assertion", "creds", "pwd", "passwd",
)

# an URL-ish authority: scheme optional, host, optional port, optional path/query
_HOST_RE = re.compile(
    r"(?i)(?P<scheme>[a-z][a-z0-9+.\-]*://)?(?P<host>[^\s/@:#?\"'<>]{2,}(\.[^\s/@:#?\"'<>]+)+)(?::\d+)?(?P<suff>[^\s\"'<>]*)",
)
# auth-looking label at a label boundary
_AUTH_RE = re.compile(
    r"(?i)(?:^|\.)(?:login|account|accounts|signin|sign-in|auth|secure|"
    r"office|outlook|microsoftonline|microsoft365|sso|verify|verification|"
    r"confirm|recover|password|session|identity|idp|passport)(?:\.|$)"
)
_PUNY_RE = re.compile(r"(?i)(?:^|\.)xn--")
# a token= param with a non-trivial value inside a URL query
_TOKENPARAM_RE = re.compile(
    r"(?i)[?&](?:code|id_token|samlresponse|access_token|session|state|token|"
    r"auth|sessionkey|session_id|sid|jwt|assertion|pwd|passwd)=(?P<val>[^&#\s]{4,})"
)


def _is_local(host):
    h = host.strip("[]")
    return h in ("localhost", "127.0.0.1", "::1") or h.endswith(".local") or h.endswith(".lan")


def _registrable(host):
    labels = host.strip(".").split(".")
    if len(labels) >= 3:
        return ".".join(labels[-2:])
    return host


def scan(text):
    """Return AiTM-related findings (list of Finding) for `text`."""
    if not isinstance(text, str) or not text:
        return []
    text = text[:524288]
    found = []
    seen = set()

    for m in _HOST_RE.finditer(text):
        host = (m.group("host") or "").lower()
        if not host or host in seen:
            continue
        if any(c in host for c in " \t"):
            continue
        seen.add(host)
        start, end = m.start("host"), m.end("host")

        # 1) punycode domain
        if _PUNY_RE.search(host):
            _add(found, "punycode_domain", "Credentials",
                 "Punycode (IDN) domain - possible AiTM look-alike",
                 start, end, host, "medium")

        # 2) homoglyph brand
        if any(ord(c) > 127 for c in host):
            norm = "".join(_CONF.get(ch, ch) for ch in host).lower()
            if any(len(b) >= 6 and b in norm for b in _BRANDS):
                _add(found, "homoglyph_brand", "Credentials",
                     "Brand name hidden by Unicode confusables (homoglyph domain)",
                     start, end, host, "high")

        # 3) brand-typo host label (e.g. microsoftoffce.com)
        for label in host.split("."):
            if not label or label in _LEGIT_BRAND_LABELS or len(label) < 5:
                continue
            for b in _BRANDS:
                if b in _LEGIT_BRAND_LABELS or len(b) < 5:
                    continue
                lw = label.lower()
                if lw != b and lw.startswith(b):
                    _add(found, "brand_typo_host", "Credentials",
                         "Host misspells a known brand - possible typofarmed login page",
                         start, end, host, "medium")
                    break

        # 4) fake-auth subdomain
        if _AUTH_RE.search(host):
            if host not in _LEGIT_AUTH_HOSTS and _registrable(host) not in _LEGIT_AUTH_HOSTS:
                _add(found, "fake_auth_host", "Credentials",
                     "Auth-looking subdomain/host not canonical - suspected typofarmed login",
                     start, end, host, "medium")

        # 5) SSO token in URL query to external host
        suff = m.group("suff") or ""
        if "?" in suff or "=" in suff:
            tm = _TOKENPARAM_RE.search(suff)
            if tm and not _is_local(host):
                val = tm.group("val")
                _add(found, "sso_token_param", "Credentials",
                     "Session/auth token passed in URL query string to external host",
                     start, end, val, "medium")

    found.sort(key=lambda f: f.start)
    return found


def _add(found, kind, label, title, start, end, value, conf):
    for f in found:
        if f.start == start and f.kind == kind:
            return
    found.append(Finding(kind, label, title, start, end, value, conf, "url"))
