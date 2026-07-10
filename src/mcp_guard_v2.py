# -*- coding: utf-8 -*-
"""Bounded, deterministic scanner for the Yadro Guard MCP schema v1.0.

This is a Yadro-specific security manifest, not a universal MCP importer.
"""
import argparse
import json
import sys
from pathlib import Path

EXIT_OK, EXIT_POLICY, EXIT_SOURCE, EXIT_INTERNAL = 0, 2, 3, 4
LABELS = frozenset({"PII", "Financial", "Health", "Credentials", "Location"})
CAPABILITIES = frozenset({"NetworkAccess", "DiskWrite", "DatabaseWrite", "DatabaseRead", "ToolExecution", "SecretAccess", "LogAccess"})
ROOT_KEYS = frozenset({"version", "tools", "flows"})
TOOL_KEYS = frozenset({"name", "labels", "sanitizes", "capabilities"})
MAX_TOOLS = 10000


class ManifestError(ValueError): pass


def _reject_unknown(mapping, allowed, where):
    unknown = sorted(set(mapping) - allowed)
    if unknown: raise ManifestError(f"unknown {where} field(s): {', '.join(unknown)}")


def load(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict): raise ManifestError("manifest root must be an object")
    _reject_unknown(data, ROOT_KEYS, "manifest")
    if data.get("version") != "1.0" or not isinstance(data.get("tools"), list):
        raise ManifestError("manifest requires version '1.0' and a tools array")
    if len(data["tools"]) > MAX_TOOLS: raise ManifestError(f"too many tools (max {MAX_TOOLS})")
    tools = {}
    for raw in data["tools"]:
        if not isinstance(raw, dict): raise ManifestError("every tool must be an object")
        _reject_unknown(raw, TOOL_KEYS, "tool")
        name = raw.get("name")
        if not isinstance(name, str) or not name.strip(): raise ManifestError("every tool requires a non-empty name")
        if name in tools: raise ManifestError(f"duplicate tool: {name}")
        labels, sanitizes, capabilities = set(raw.get("labels", [])), set(raw.get("sanitizes", [])), set(raw.get("capabilities", []))
        if not labels <= LABELS or not sanitizes <= LABELS: raise ManifestError(f"unknown label on tool: {name}")
        if not capabilities <= CAPABILITIES: raise ManifestError(f"unknown capability on tool: {name}")
        tools[name] = {"labels": labels, "sanitizes": sanitizes, "capabilities": capabilities}
    raw_flows = data.get("flows", [])
    if not isinstance(raw_flows, list): raise ManifestError("flows must be an array")
    edges = set()
    for edge in raw_flows:
        if not isinstance(edge, list) or len(edge) != 2 or edge[0] not in tools or edge[1] not in tools:
            raise ManifestError(f"invalid flow edge: {edge!r}")
        edges.add((edge[0], edge[1]))
    return tools, sorted(edges)


def analyze(tools, edges):
    state = {name: set(tool["labels"]) for name, tool in tools.items()}
    for _ in range(len(tools) * len(LABELS) + 1):
        changed = False
        for source, target in edges:
            merged = state[target] | (state[source] - tools[target]["sanitizes"])
            if merged != state[target]: state[target] = merged; changed = True
        if not changed: break
    else: raise RuntimeError("MCP graph fixpoint bound exceeded")
    incoming = {name: 0 for name in tools}
    for _, target in edges: incoming[target] += 1
    findings = []
    for name in sorted(tools):
        dangerous = tools[name]["capabilities"] & CAPABILITIES
        if state[name] and dangerous:
            findings.append({"code":"YADRO-MCP-2301", "severity":"error", "tool":name,
                             "labels":sorted(state[name]), "capabilities":sorted(dangerous),
                             "message":f"Sensitive data reaches privileged MCP tool '{name}'"})
        if len(dangerous) >= 3:
            findings.append({"code":"YADRO-MCP-2401", "severity":"error", "tool":name,
                             "capabilities":sorted(dangerous), "message":f"MCP tool '{name}' has excessive agency"})
    findings.sort(key=lambda item: (item["code"], item["tool"]))
    summary = {"tools": len(tools), "flows": len(edges), "cycles_supported": True,
               "roots": sorted(name for name, count in incoming.items() if count == 0),
               "unreachable": sorted(name for name, count in incoming.items() if count == 0 and not tools[name]["labels"])}
    return findings, summary


def sarif(findings, path):
    rules = [{"id": code, "name": code} for code in sorted({item["code"] for item in findings})]
    results = [{"ruleId": item["code"], "level": item["severity"], "message":{"text":item["message"]},
                "locations":[{"physicalLocation":{"artifactLocation":{"uri":Path(path).resolve().as_uri()}, "region":{"startLine":1}}}]} for item in findings]
    return {"$schema":"https://json.schemastore.org/sarif-2.1.0.json", "version":"2.1.0",
            "runs":[{"tool":{"driver":{"name":"Yadro Guard MCP", "version":"2.1.0", "rules":rules}}, "results":results}]}


def run(argv=None, stdout=sys.stdout, stderr=sys.stderr):
    parser=argparse.ArgumentParser(prog="yadro-guard mcp"); parser.add_argument("command",choices=("scan",)); parser.add_argument("manifest"); parser.add_argument("--format",choices=("text","json","sarif"),default="text"); parser.add_argument("--quiet",action="store_true")
    args=parser.parse_args(argv)
    try: findings, summary = analyze(*load(args.manifest))
    except (OSError,UnicodeError,json.JSONDecodeError,ManifestError) as error: print(f"invalid MCP manifest: {error}",file=stderr); return EXIT_SOURCE
    except Exception as error: print(f"internal MCP scanner error: {error}",file=stderr); return EXIT_INTERNAL
    if not args.quiet:
        if args.format=="json": print(json.dumps({"findings":findings,"summary":summary},indent=2),file=stdout)
        elif args.format=="sarif": print(json.dumps(sarif(findings,args.manifest),indent=2),file=stdout)
        else:
            for item in findings: print(f'{item["code"]}: {item["message"]}',file=stdout)
            if not findings: print("MCP tool graph is policy-clean",file=stdout)
    return EXIT_POLICY if findings else EXIT_OK


def main(): raise SystemExit(run())
if __name__=="__main__": main()
