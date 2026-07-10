# -*- coding: utf-8 -*-
"""Fail-closed policy validation and CLI error classification."""
import json
from pathlib import Path
from src import guard
from src.typecheck import TypeCheckError

ALLOWED_KEYS = frozenset({"version", "sources", "sinks", "sanitizers"})


def strict_load_policy(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise guard.PolicyError("policy root must be an object")
    unknown = sorted(set(data) - ALLOWED_KEYS)
    if unknown:
        raise guard.PolicyError(f"unknown policy field(s): {', '.join(unknown)}")
    if data.get("version") != "1.0":
        raise guard.PolicyError("policy.version must be '1.0'")
    for key in ("sources", "sinks", "sanitizers"):
        if key in data and not isinstance(data[key], dict):
            raise guard.PolicyError(f"policy.{key} must be an object")
    for name, label in data.get("sources", {}).items():
        if not isinstance(name, str) or label not in guard.KNOWN_LABELS:
            raise guard.PolicyError(f"invalid source: {name!r}")
    for name, capability in data.get("sinks", {}).items():
        if not isinstance(name, str) or not isinstance(capability, str) or not capability:
            raise guard.PolicyError(f"invalid sink: {name!r}")
    for name, labels in data.get("sanitizers", {}).items():
        if not isinstance(name, str) or not isinstance(labels, list) or not set(labels) <= guard.KNOWN_LABELS:
            raise guard.PolicyError(f"invalid sanitizer: {name!r}")
    builtins = set(guard._BASE_SOURCES) | set(guard._BASE_SINKS) | set(guard._BASE_SANITIZERS)
    custom = set(data.get("sources", {})) | set(data.get("sinks", {})) | set(data.get("sanitizers", {}))
    collisions = sorted(builtins & custom)
    if collisions:
        raise guard.PolicyError(f"custom policy collides with builtin symbol(s): {', '.join(collisions)}")
    return data


def strict_classify(error):
    if isinstance(error, guard.EthicalError):
        return guard.EXIT_POLICY
    if isinstance(error, TypeCheckError):
        return guard.EXIT_SOURCE
    return guard.classify(error)
