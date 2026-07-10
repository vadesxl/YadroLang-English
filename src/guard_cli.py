# -*- coding: utf-8 -*-
"""Unified Yadro Guard console entry point."""
import sys
from src import guard, mcp_guard_v2
from src.guard_policy import strict_load_policy, strict_classify

_original_classify = guard.classify
guard.load_policy = strict_load_policy

def _classify(error):
    if error.__class__.__name__ == "TypeCheckError":
        return guard.EXIT_SOURCE
    return _original_classify(error)
guard.classify = _classify


def run(argv=None, stdout=sys.stdout, stderr=sys.stderr):
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "mcp":
        return mcp_guard_v2.run(args[1:], stdout, stderr)
    if args == ["--version"]:
        args = ["version"]
    return guard.run(args, stdout, stderr)


def main():
    raise SystemExit(run())

if __name__ == "__main__":
    main()
