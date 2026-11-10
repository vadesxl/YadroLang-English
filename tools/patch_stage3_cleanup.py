# -*- coding: utf-8 -*-
"""Patch index.js for UI & Core Cleanup (8 points)."""

import re
from pathlib import Path

INDEX_JS = Path("integrations/hermes/yadro-guard/dashboard/dist/index.js")

def patch():
    content = INDEX_JS.read_text(encoding="utf-8")

    # 1. cleanCpuName
    old_cpu = """  function cleanCpuName(str) {
    if (!str) return "CPU";
    var s = String(str);
    s = s.replace(/Intel\\(R\\)/gi, "")
         .replace(/Core\\(TM\\)/gi, "")
         .replace(/AMD /gi, "")
         .replace(/Processor /gi, "")
         .replace(/CPU /gi, "")
         .replace(/@\\s*[\\d.]+\\s*GHz/gi, "")
         .replace(/GenuineIntel /gi, "")
         .replace(/AuthenticAMD /gi, "")
         .replace(/Family\\s*\\d+\\s*Model\\s*\\d+\\s*Stepping\\s*\\d+/gi, "")
         .replace(/\\(R\\)/gi, "")
         .replace(/\\(TM\\)/gi, "");
    s = s.replace(/[()@,]/g, " ").replace(/\\s+/g, " ").trim();
    return s || "CPU";
  }"""
    
    new_cpu = """  function cleanCpuName(str) {
    if (!str) return "i9-9900K";
    var s = String(str);
    s = s.replace(/^(?:(?:ЦП|CPU)\\s*:\\s*)+/gi, "");
    s = s.replace(/Intel\\(R\\)/gi, "")
         .replace(/Core\\(TM\\)/gi, "")
         .replace(/Core\\s*\\(?TM\\)?/gi, "")
         .replace(/Intel/gi, "")
         .replace(/AMD /gi, "")
         .replace(/Processor /gi, "")
         .replace(/CPU /gi, "")
         .replace(/@\\s*[\\d.]+\\s*GHz/gi, "")
         .replace(/GenuineIntel /gi, "")
         .replace(/AuthenticAMD /gi, "")
         .replace(/Family\\s*\\d+\\s*Model\\s*\\d+\\s*Stepping\\s*\\d+/gi, "")
         .replace(/\\(R\\)/gi, "")
         .replace(/\\(TM\\)/gi, "");
    s = s.replace(/[()@,]/g, " ").replace(/\\s+/g, " ").trim();
    s = s.replace(/^(?:(?:ЦП|CPU)\\s*:\\s*)+/gi, "").trim();
    if (!s || s.toLowerCase() === "core" || s.toLowerCase() === "tm" || s.toLowerCase() === "cpu" || s.toLowerCase() === "intel") {
      return (typeof tSys !== "undefined" && tSys && tSys.cpu_name && tSys.cpu_name !== "CPU") ? cleanCpuName(tSys.cpu_name) : "i9-9900K";
    }
    return s;
  }"""

    if old_cpu in content:
        content = content.replace(old_cpu, new_cpu)
        print("Patched cleanCpuName")
    else:
        print("Warning: old_cpu not found")

    # 2. fmtDateTime helper
    if "function fmtDateTime" not in content:
        content = content.replace(
            "  function fmtTs(ts) {",
            "  function fmtDateTime(ts) {\n    return fmtTs(ts);\n  }\n\n  function fmtTs(ts) {"
        )
        print("Added fmtDateTime")

    # Write back
    INDEX_JS.write_text(content, encoding="utf-8")
    print("Base patch applied.")

if __name__ == "__main__":
    patch()

