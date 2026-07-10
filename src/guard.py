# -*- coding: utf-8 -*-
"""Commercial Yadro Guard command-line interface."""
import argparse
import json
import re
import sys
from pathlib import Path

from src import main as compiler
from src.lexer import Lexer, LexerError
from src.syntax import Parser, ParserError
from src.ethics import EthicalAnalyzer, EthicalError
from src import ethics_v21 as runtime

VERSION = "2.1.0-dev"
EXIT_OK, EXIT_POLICY, EXIT_SOURCE, EXIT_INTERNAL = 0, 2, 3, 4
KNOWN_LABELS = frozenset(runtime.ALL_LABELS)
_BASE_SOURCES = dict(runtime.SOURCES)
_BASE_SINKS = dict(runtime.SINKS)
_BASE_SANITIZERS = set(runtime.SANITIZERS)
_BASE_COMPLIANCE = {key: set(value) for key, value in runtime.COMPLIANCE.items()}
_BASE_ARITY = dict(compiler.SYSTEM_API_ARITY)


class PolicyError(ValueError):
    pass


def reset_policy():
    runtime.SOURCES.clear(); runtime.SOURCES.update(_BASE_SOURCES)
    runtime.SINKS.clear(); runtime.SINKS.update(_BASE_SINKS)
    runtime.SANITIZERS.clear(); runtime.SANITIZERS.update(_BASE_SANITIZERS)
    runtime.COMPLIANCE.clear(); runtime.COMPLIANCE.update({key: set(value) for key, value in _BASE_COMPLIANCE.items()})
    compiler.SYSTEM_API_ARITY.clear(); compiler.SYSTEM_API_ARITY.update(_BASE_ARITY)
    compiler.SYSTEM_API = set(compiler.SYSTEM_API_ARITY)


def load_policy(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("version") != "1.0":
        raise PolicyError("policy.version must be '1.0'")
    for key in ("sources", "sinks", "sanitizers"):
        if key in data and not isinstance(data[key], dict):
            raise PolicyError(f"policy.{key} must be an object")
    for name, label in data.get("sources", {}).items():
        if not isinstance(name, str) or label not in KNOWN_LABELS:
            raise PolicyError(f"invalid source: {name!r} -> {label!r}")
    for name, capability in data.get("sinks", {}).items():
        if not isinstance(name, str) or not isinstance(capability, str) or not capability:
            raise PolicyError(f"invalid sink: {name!r}")
    for name, labels in data.get("sanitizers", {}).items():
        if not isinstance(name, str) or not isinstance(labels, list) or not set(labels) <= KNOWN_LABELS:
            raise PolicyError(f"invalid sanitizer: {name!r}")
    return data


def apply_policy(data):
    reset_policy()
    runtime.SOURCES.update(data.get("sources", {}))
    runtime.SINKS.update(data.get("sinks", {}))
    for sanitizer, labels in data.get("sanitizers", {}).items():
        runtime.SANITIZERS.add(sanitizer)
        for label in labels:
            runtime.COMPLIANCE.setdefault(label, set()).add(sanitizer)
    compiler.SYSTEM_API_ARITY.update({name: 0 for name in data.get("sources", {})})
    compiler.SYSTEM_API_ARITY.update({name: 1 for name in data.get("sinks", {})})
    compiler.SYSTEM_API_ARITY.update({name: 1 for name in data.get("sanitizers", {})})
    compiler.SYSTEM_API = set(compiler.SYSTEM_API_ARITY)


def diagnostic(error, path):
    text = str(error)
    line = re.search(r"line (\d+)", text)
    return {"tool": "yadro-guard", "version": VERSION, "path": str(path),
            "code": getattr(error, "code", "YADRO-SOURCE"),
            "line": int(line.group(1)) if line else 1, "message": text}


def sarif(item=None):
    results, rules = [], []
    if item:
        rules = [{"id": item["code"], "name": item["code"]}]
        results = [{"ruleId": item["code"], "level": "error",
                    "message": {"text": item["message"]},
                    "locations": [{"physicalLocation": {
                        "artifactLocation": {"uri": item["path"]},
                        "region": {"startLine": item["line"]}}}]}]
    return {"$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": "2.1.0",
            "runs": [{"tool": {"driver": {"name": "Yadro Guard", "version": VERSION,
                                              "rules": rules}}, "results": results}]}


def emit(value, output_format, stream):
    if output_format == "text":
        if isinstance(value, dict) and "message" in value:
            print(f'{value["path"]}:{value["line"]}: {value["message"]}', file=stream)
        else:
            print(value, file=stream)
    elif output_format == "json":
        print(json.dumps(value, ensure_ascii=False, indent=2), file=stream)
    else:
        item = value if isinstance(value, dict) and "message" in value else None
        print(json.dumps(sarif(item), ensure_ascii=False, indent=2), file=stream)


def prepare(args):
    reset_policy()
    if getattr(args, "policy", None):
        apply_policy(load_policy(args.policy))
    return Path(args.source).read_text(encoding="utf-8")


def classify(error):
    if isinstance(error, EthicalError):
        return EXIT_POLICY
    if isinstance(error, (OSError, UnicodeError, json.JSONDecodeError, PolicyError,
                          compiler.EntryPointError, compiler.SemanticError,
                          ParserError, LexerError)):
        return EXIT_SOURCE
    return EXIT_INTERNAL


def scan(args, stdout):
    compiler.compile(prepare(args))
    emit({"status": "ok", "path": args.source, "version": VERSION}, args.format, stdout)


def compile_command(args, stdout):
    ir_code = compiler.compile(prepare(args), emit_ir=args.ir)
    if not args.ir:
        compiler.build_native(ir_code, args.output)


def audit(args, stdout):
    source = prepare(args)
    ast = Parser(Lexer(source).tokens()).parse()
    compiler._check_unique_functions(ast); compiler._check_entry_point(ast)
    compiler._check_calls(ast); compiler._check_expressions(ast)
    analyzer = EthicalAnalyzer(); analyzer.check(ast)
    if args.format == "json":
        emit({"status": "ok", "findings": [entry.__dict__ for entry in analyzer.audit_trail]}, "json", stdout)
    elif args.format == "sarif":
        emit({"status": "ok"}, "sarif", stdout)
    else:
        print(analyzer.generate_audit_report(), file=stdout)


def build_parser():
    root = argparse.ArgumentParser(prog="yadro-guard")
    sub = root.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("source"); common.add_argument("--policy")
    common.add_argument("--format", choices=("text", "json", "sarif"), default="text")
    sub.add_parser("scan", parents=[common])
    cp = sub.add_parser("compile", parents=[common]); cp.add_argument("-o", "--output", default="kernel.o"); cp.add_argument("--ir", action="store_true")
    sub.add_parser("audit", parents=[common])
    pp = sub.add_parser("policy"); psub = pp.add_subparsers(dest="policy_command", required=True)
    check = psub.add_parser("check"); check.add_argument("path")
    sub.add_parser("version")
    return root


def run(argv=None, stdout=sys.stdout, stderr=sys.stderr):
    args = build_parser().parse_args(argv)
    if args.command == "version":
        print(VERSION, file=stdout); return EXIT_OK
    if args.command == "policy":
        try:
            load_policy(args.path); print(f"valid policy: {args.path}", file=stdout); return EXIT_OK
        except Exception as error:
            print(f"invalid policy: {error}", file=stderr); return classify(error)
    action = {"scan": scan, "compile": compile_command, "audit": audit}[args.command]
    try:
        action(args, stdout); return EXIT_OK
    except Exception as error:
        emit(diagnostic(error, args.source), args.format, stderr)
        return classify(error)
    finally:
        reset_policy()


def main():
    raise SystemExit(run())


if __name__ == "__main__":
    main()
