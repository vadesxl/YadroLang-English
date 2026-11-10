# -*- coding: utf-8 -*-
"""E2E SOC Harness Test for Yadro-Guard / MCP-Secrets-Guard.

Simulates running inside Hermes plugin environment (%LOCALAPPDATA%\\hermes\\plugins\\yadro-guard)
where repository root (src/) is not the working directory.

Validates:
1. /threat-intel/update executes and returns ok=True without "No module named 'src'".
2. /self-audit/run (Red Team 500) executes and returns ok=True with 500+ vector pass report.
3. Attack simulator routes (/simulate/port_scan, bruteforce, arp_spoof, secret_leak, reset) return ok=True.
4. /telemetry returns real hardware metrics: no "999 GB" fallbacks, real CPU % and GPU %.
"""

import asyncio
import os
import sys
import unittest
from pathlib import Path

# Simulate running outside repository root
_REPO_ROOT = Path(__file__).resolve().parents[1]
_DASHBOARD_DIR = _REPO_ROOT / "integrations" / "hermes" / "yadro-guard" / "dashboard"
if str(_DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(_DASHBOARD_DIR))

import plugin_api


class TestE2ESocHarness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure plugin_api initializes its path resolution
        plugin_api._ensure_engine_home_in_path()

    def test_01_threat_intel_update(self):
        """Verify /threat-intel/update works without 'No module named src'."""
        res = asyncio.run(plugin_api.threat_intel_update())
        self.assertEqual(res.get("status"), "ok", f"Expected status 'ok', got {res}")
        self.assertTrue(res.get("ok"), "Expected 'ok': True in response")
        self.assertIn("update", res)
        self.assertGreaterEqual(res["update"].get("total", 0), 1000)

    def test_02_self_audit_redteam_500(self):
        """Verify /self-audit/run (and /test/redteam-500) executes 500 vectors cleanly."""
        res = asyncio.run(plugin_api.run_self_audit())
        self.assertEqual(res.get("status"), "ok", f"Self-audit failed: {res}")
        self.assertTrue(res.get("ok"), "Expected 'ok': True in self-audit response")
        report = res.get("report", {})
        self.assertEqual(report.get("status"), "PASSED_100_PERCENT")
        self.assertEqual(report.get("total_vectors"), 500)
        self.assertEqual(report.get("false_positives"), 0)
        self.assertEqual(report.get("false_negatives"), 0)

        # Also test alias route
        alias_res = asyncio.run(plugin_api.run_redteam_500())
        self.assertEqual(alias_res.get("status"), "ok")
        self.assertTrue(alias_res.get("ok"))

    def test_03_attack_simulators(self):
        """Verify all attack simulation endpoints return ok=True."""
        # 1. Port scan
        r1 = asyncio.run(plugin_api.sim_port_scan())
        self.assertTrue(r1.get("ok"), f"port_scan failed: {r1}")

        # 2. Brute force
        r2 = asyncio.run(plugin_api.sim_bruteforce())
        self.assertTrue(r2.get("ok"), f"bruteforce failed: {r2}")

        # 3. ARP spoof / unfamiliar node
        r3 = asyncio.run(plugin_api.sim_arp_spoof())
        self.assertTrue(r3.get("ok"), f"arp_spoof failed: {r3}")

        # 4. Secret leak simulation
        r4 = asyncio.run(plugin_api.sim_secret_leak())
        self.assertTrue(r4.get("ok"), f"secret_leak failed: {r4}")

        # 5. Reset
        r5 = asyncio.run(plugin_api.simulate_reset())
        self.assertTrue(r5.get("ok"), f"reset failed: {r5}")

    def test_04_telemetry_no_999gb_and_real_metrics(self):
        """Verify /telemetry returns real GiB disk sizes (no 999 GB) and real CPU/GPU numbers."""
        tel = asyncio.run(plugin_api.telemetry())
        self.assertEqual(tel.get("status"), "ok")
        system = tel.get("system", {})

        # CPU check: valid percentage range
        cpu_pct = system.get("cpu_percent")
        self.assertIsInstance(cpu_pct, (int, float))
        self.assertGreaterEqual(cpu_pct, 0.0)
        self.assertLessEqual(cpu_pct, 100.0)

        # RAM check: valid GB and %
        ram_total = system.get("ram_total_gb")
        ram_used = system.get("ram_used_gb")
        ram_pct = system.get("ram_percent")
        self.assertGreater(ram_total, 0.0)
        self.assertGreater(ram_used, 0.0)
        self.assertGreater(ram_pct, 0.0)

        # Disks check: NO "999 GB" / 999.0 on any disk!
        all_disks = system.get("all_disks", [])
        self.assertGreater(len(all_disks), 0, "Expected at least 1 disk in telemetry")
        for d in all_disks:
            mount = d.get("mount", "")
            total_gb = d.get("total_gb", 0)
            # Verify no 999.0 fallback: on 1TB drives it should be GiB (~930.4 GB), never 999.0!
            self.assertNotEqual(total_gb, 999.0, f"Disk {mount} returned forbidden fake fallback 999.0 GB!")
            self.assertNotEqual(str(total_gb), "999", f"Disk {mount} returned forbidden string 999!")
            self.assertGreater(total_gb, 10.0, f"Disk {mount} capacity suspiciously small: {total_gb}")

        # GPU check: if GPU present, utilization must be float
        gpus = system.get("gpus", [])
        if gpus:
            gpu0 = gpus[0]
            gpu_pct = gpu0.get("util_pct")
            self.assertIsInstance(gpu_pct, (int, float))
            self.assertGreaterEqual(gpu_pct, 0.0)
            self.assertLessEqual(gpu_pct, 100.0)


if __name__ == "__main__":
    unittest.main()

