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
from src import ethics_v21 as policy_runtime
from src.codegen import CodegenError

VERSION = "2.1.0-dev"
EXIT_OK = 0
EXIT_POLICY = 2
EXIT_SOURCE = 3
EXIT_INTERNAL = 4
KNOWN_LABELS = frozenset(policy_runtime.ALL_LABELS)


class PolicyError(ValueError):
    pass


def load_policy(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("version") != "1.0":
        raise PolicyError("policy.version must be '1.0'")
    for key in ("sources", "sinks", "sanitizers"):
        if key in data and not isinstance(data[key], dict):
            raise PolicyError(f"policy.{key} must be an object")
    for name, label in data.get("sources", {}).items():
        if not isinstance(name, str) or label not in KNOWN_LABELS:
            raise PolicyError(f"invalid source policy: {name!r} -> {label!r}")
    for name, capability in data.get("sinks", {}).items():
        if not isinstance(name, str) or not isinstance(capability, str) or not capability:
            raise PolicyError(f"invalid sink policy: {name!r}")
    for name, labels in data.get("sanitizers", {}).items():
        if not isinstance(name, str) or not isinstance(labels, list) or not set(labels) <= KNOWN_LABELS:
            raise PolicyError(f"invalid sanitizer policy: {name!r}")
    return data


def apply_policy(data):
    policy_runtime.SOURCES.update(data.get("sources", {}))
    policy_runtime.SINKS.update(data.get("sinks", {}))
    for sanitizer, labels in data.get("sanitizers", {}).items():
        policy_runtime.SANITIZERS.add(sanitizer)
        for label in labels:
            policy_runtime.COMPLIANCE.setdefault(label, set()).add(sanitizer)
    compiler.SYSTEM_API_ARITY.update({name: 0 for name in data.get("sources", {})})
    compiler.SYSTEM_API_ARITY.update({name: 1 for name in data.get("sinks", {})})
    compiler.SYSTEM_API_ARITY.update({name: 1 for name in data.get("sanitizers", {})})
    compiler.SYSTEM_API = set(compiler.SYSTEM_API_ARITY)


def diagnostic(error, path):
    text = str(error)
    line_match = re.search(r"line (\d+)", text)
    return {
        "tool": "yadro-guard",
        "version": VERSION,
        "path": str(path),
        "code": getattr(error, "code", "YADRO-SOURCE"),
        "line": int(line_match.group(1)) if line_match else 1,
        "message": text,
    }


def to_sarif(item):
    level = "error"
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "Yadro Guard", "version": VERSION,
                                  "rules": [{"id": item["code"], "name": item["code"]}]}},
            "results": [{"ruleId": item["code"], "level": level,
                         "message": {"text": item["message"]},
                         "locations": [{"physicalLocation": {
                             "artifactLocation": {"uri": item["path"]},
                             "region": {"startLine": item["line"]}}}]}]
        }]
    }


def emit(value, output_format, stream):
    if output_format == "text":
        if isinstance(value, dict) and "message" in value:
            print(f'{value["path"]}:{value["line"]}: {value["message"]}', file=stream)
        else:
            print(value, file=stream)
    elif output_format == "json":
        print(json.dumps(value, ensure_ascii=False, indent=2), file=stream)
    elif output_format == "sarif":
        print(json.dumps(to_sarif(value), ensure_ascii=False, indent=2), file=stream)


def read_source(path):
    return Path(path).read_text(encoding="utf-8")


def run_scan(args, stdout, stderr):
    try:
        if args.policy:
            apply_policy(load_policy(args.policy))
        compiler.compile(read_source(args.source))
        emit({"status": "ok", "path": args.source, "version": VERSION}, args.format, stdout)
        return EXIT_OK
    except EthicalError as error:
        emit(diagnostic(error, args.source), args.format, stderr)
        return EXIT_POLICY
    except (OSError, UnicodeError, json.JSONDecodeError, PolicyError,
            compiler.EntryPointError, compiler.SemanticError,
            ParserError, LexerError) as error:
        emit(diagnostic(error, args.source), args.format, stderr)
        return EXIT_SOURCE
    except Exception as error:
        emit(diagnostic(error, args.source), args.format, stderr)
        return EXIT_INTERNAL


def run_compile(args, stdout, stderr):
    try:
        if args.policy:
            apply_policy(load_policy(args.policy))
        ir_code = compiler.compile(read_source(args.source), emit_ir=args.ir)
        if not args.ir:
            compiler.build_native(ir_code, args.output)
        return EXIT_OK
    except EthicalError as error:
        emit(diagnostic(error, args.source), args.format, stderr)
        return EXIT_POLICY
    except (OSError, UnicodeError, json.JSONDecodeError, PolicyError,
            compiler.EntryPointError, compiler.SemanticError,
            ParserError, LexerError, CodegenError) as error:
        emit(diagnostic(error, args.source), args.format, stderr)
        return EXIT_SOURCE
    except Exception as error:
        emit(diagnostic(error, args.source), args.format, stderr)
        return EXIT_INTERNAL


def run_audit(args, stdout, stderr):
    try:
        if args.policy:
            apply_policy(load_policy(args.policy))
        source = read_source(args.source)
        ast = Parser(Lexer(source).tokens()).parse()
        compiler._check_unique_functions(ast)
        compiler._check_entry_point(ast)
        compiler._check_calls(ast)
        compiler._check_expressions(ast)
        analyzer = EthicalAnalyzer()
        analyzer.check(ast)
        if args.format == "json":
            emit({"status": "ok", "findings": [entry.__dict__ for entry in analyzer.audit_trail]}, "json", stdout)
        else:
            print(analyzer.generate_audit_report(), file=stdout)
        return EXIT_OK
    except EthicalError as error:
        emit(diagnostic(error, args.source), args.format, stderr)
        return EXIT_POLICY
    except (OSError, UnicodeError, json.JSONDecodeError, PolicyError,
            compiler.EntryPointError, compiler.SemanticError,
            ParserError, LexerError) as error:
        emit(diagnostic(error, args.source), args.format, stderr)
        return EXIT_SOURCE
    except Exception as error:
        emit(diagnostic(error, args.source), args.format, stderr)
        return EXIT_INTERNAL


def parser():
    root = argparse.ArgumentParser(prog="yadro-guard")
    sub = root.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("source")
    common.add_argument("--policy")
    common.add_argument("--format", choices=("text", "json", "sarif"), default="text")
    sub.add_parser("scan", parents=[common])
    compile_parser = sub.add_parser("compile", parents=[common])
    compile_parser.add_argument("-o", "--output", default="kernel.o")
    compile_parser.add_argument("--ir", action="store_true")
    audit_parser = sub.add_parser("audit", parents=[common])
    audit_parser.set_defaults(format="text")
    policy = sub.add_parser("policy")
    policy_sub = policy.add_subparsers(dest="policy_command", required=True)
    check = policy_sub.add_parser("check")
    check.add_argument("path")
    sub.add_parser("version")
    return root


def run(argv=None, stdout=sys.stdout, stderr=sys.stderr):
    args = parser().parse_args(argv)
    if args.command == "version":
        print(VERSION, file=stdout)
        return EXIT_OK
    if args.command == "policy":
        try:
            load_policy(args.path)
            print(f"valid policy: {args.path}", file=stdout)
            return EXIT_OK
        except (OSError, UnicodeError, json.JSONDecodeError, PolicyError) as error:
            print(f"invalid policy: {error}", file=stderr)
            return EXIT_SOURCE
    if args.command == "scan":
        return run_scan(args, stdout, stderr)
    if args.command == "compile":
        return run_compile(args, stdout, stderr)
    return run_audit(args, stdout, stderr)


def main():
    raise SystemExit(run())


if __name__ == "__main__":
    main()
