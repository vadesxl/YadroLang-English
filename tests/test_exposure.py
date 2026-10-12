import os
import unittest
from unittest import mock
from src.runtime import exposure as E, services as S

NETSTAT = """
  Proto  Local Address          Foreign Address        State           PID
  TCP    0.0.0.0:135            0.0.0.0:0              LISTENING       1808
  TCP    0.0.0.0:445            0.0.0.0:0              LISTENING       4
  TCP    0.0.0.0:1236           0.0.0.0:0              LISTENING       4340
  TCP    0.0.0.0:5432           0.0.0.0:0              LISTENING       700
  TCP    0.0.0.0:11434          0.0.0.0:0              LISTENING       701
  TCP    127.0.0.1:18434        0.0.0.0:0              LISTENING       22656
  TCP    192.168.1.177:6379     0.0.0.0:0              LISTENING       702
  TCP    192.168.1.177:51000    52.1.1.1:443           ESTABLISHED     900
  TCP    [::]:445               [::]:0                 LISTENING       4
  UDP    0.0.0.0:5353           *:*                                    900
  UDP    127.0.0.1:1900         *:*                                    900
"""
TASKS = '"System","4","Services","0","1 K"\n"svchost.exe","1808","Services","0","1 K"\n' \
        '"AsusUpdateCheck.exe","4340","Services","0","1 K"\n"postgres.exe","700","Console","1","1 K"\n' \
        '"ollama.exe","701","Console","1","1 K"\n"llama-server.exe","22656","Console","1","1 K"\n' \
        '"redis-server.exe","702","Console","1","1 K"\n"chrome.exe","900","Console","1","1 K"\n'


def listeners(allowed=None):
    names = E.parse_tasklist(TASKS)
    out = []
    for l in E.parse_netstat(NETSTAT):
        l.process = names.get(l.pid, "unknown")
        if allowed is not None and E.classify_reach(l.address) != "this_computer":
            l.firewall = "allowed" if l.port in allowed else "not verified"
        out.append(E.assess(l))
    return {(l.address, l.port): l for l in out}


class ExposureTests(unittest.TestCase):
    def test_parsing_only_listening_and_udp(self):
        l = E.parse_netstat(NETSTAT)
        self.assertNotIn(51000, [x.port for x in l])           # ESTABLISHED is not listening
        self.assertIn(("UDP", 5353), [(x.proto, x.port) for x in l])
        self.assertIn("::", [x.address for x in l])

    def test_accessibility_classes(self):
        self.assertEqual("all_networks", E.classify_reach("0.0.0.0"))
        self.assertEqual("all_networks", E.classify_reach("::"))
        self.assertEqual("this_computer", E.classify_reach("127.0.0.1"))
        self.assertEqual("this_computer", E.classify_reach("::1"))
        self.assertEqual("local_network", E.classify_reach("192.168.1.177"))
        self.assertEqual("all_networks", E.classify_reach("8.8.8.8"))

    def test_open_db_and_model_critical(self):
        l = listeners()
        self.assertEqual(S.CRITICAL, l[("0.0.0.0", 5432)].severity)
        self.assertEqual("PostgreSQL database", l[("0.0.0.0", 5432)].service)
        self.assertEqual(S.CRITICAL, l[("0.0.0.0", 11434)].severity)
        self.assertIn("OLLAMA_HOST=127.0.0.1", l[("0.0.0.0", 11434)].fix)

    def test_localhost_is_safe_even_for_ai(self):
        l = listeners()[("127.0.0.1", 18434)]
        self.assertEqual(S.INFO, l.severity)
        self.assertEqual("this_computer", l.reach)
        self.assertEqual("Nothing to do.", l.fix)

    def test_local_network_one_step_lower(self):
        self.assertEqual(S.HIGH, listeners()[("192.168.1.177", 6379)].severity)

    def test_system_windows_do_not_scare(self):
        self.assertEqual(S.INFO, listeners()[("0.0.0.0", 135)].severity)
        self.assertEqual(S.MEDIUM, listeners()[("0.0.0.0", 445)].severity)     # SMB honestly marked
        self.assertEqual(S.MEDIUM, listeners()[("0.0.0.0", 1236)].severity)    # ASUS service

    def test_firewall_explicitly_allows_open_db(self):
        l = listeners(allowed={5432})[("0.0.0.0", 5432)]
        self.assertEqual(S.CRITICAL, l.severity)          # risk is not underestimated based on guesses
        self.assertIn("firewall-allows", l.tags)

    def test_udp_discovery_is_quiet(self):
        l = listeners()[("0.0.0.0", 5353)]
        self.assertEqual(S.INFO, l.severity)
        self.assertEqual("Nothing to do.", l.fix)

    # ---- firewall: verdict from local policy ----
    @staticmethod
    def _fw(rules, default_in=(1, 1, 1), current=2, enabled=(True, True, True), modify=0, block_all=(False,) * 3):
        return {"current": current, "modify_state": modify, "enabled": list(enabled),
                "default_in": list(default_in), "block_all": list(block_all), "rules": rules, "paths": {}}

    @staticmethod
    def _rule(**kw):
        r = {"name": "r", "action": 1, "protocol": 6, "ports": "*", "app": None, "service": None,
             "profiles": 2147483647, "remote": "*", "local": "*", "ifaces": "All", "group": None, "package": False}
        r.update(kw)
        return r

    def _l(self, port=5432, proto="TCP", process="postgres.exe"):
        return E.Listener(proto, "0.0.0.0", port, 700, process=process)

    def test_fw_program_rule_by_path_allows(self):
        fw = self._fw([self._rule(name="PG", app=r"C:\PG\postgres.exe", remote="LocalSubnet")])
        v = E.firewall_verdict(self._l(), fw, [], r"c:\pg\POSTGRES.exe")
        self.assertEqual(("allowed", "PG", "local network"), v)

    def test_fw_foreign_program_does_not_count(self):
        fw = self._fw([self._rule(app=r"C:\Other\x.exe")], default_in=(0, 0, 0))
        self.assertEqual("blocked", E.firewall_verdict(self._l(), fw, [], r"C:\PG\postgres.exe")[0])

    def test_fw_default_block_without_rules(self):
        self.assertEqual(("blocked", "", "default"), E.firewall_verdict(self._l(), self._fw([], (0, 0, 0)), [], ""))

    def test_fw_disabled_and_group_policy(self):
        self.assertEqual("off", E.firewall_verdict(self._l(), self._fw([], enabled=(True, False, True)), [], "")[0])
        self.assertEqual("not verified", E.firewall_verdict(self._l(), self._fw([], modify=1), [], "")[0])
        self.assertEqual("not verified", E.firewall_verdict(self._l(), None, [], "")[0])

    def test_fw_block_with_restrictions_is_not_passed_off_as_block(self):
        # block only for some addresses (usually sandboxes) -> honestly "not verified"
        fw = self._fw([self._rule(action=0, protocol=256, ports=None, remote="0.0.0.0-126.255.255.255")], (0, 0, 0))
        self.assertEqual("not verified", E.firewall_verdict(self._l(), fw, [], "")[0])

    def test_fw_port_keywords_and_wfd_do_not_decide(self):
        fw = self._fw([self._rule(app="System", ports="IPHTTPS"),
                       self._rule(app="System", group="@wlansvc.dll,-36865")], (0, 0, 0))
        self.assertEqual("not verified", E.firewall_verdict(self._l(445, process="System"), fw, [], "")[0])

    def test_fw_store_apps_rule_does_not_affect_regular_programs(self):
        fw = self._fw([self._rule(name="Xbox", protocol=256, package=True)], (0, 0, 0))
        self.assertEqual("blocked", E.firewall_verdict(self._l(), fw, [], r"C:\PG\postgres.exe")[0])

    def test_fw_service_and_port_range(self):
        fw = self._fw([self._rule(name="NTP", protocol=17, ports="100-200", service="W32Time")], (0, 0, 0))
        l = self._l(123, "UDP", "svchost.exe")
        self.assertEqual("allowed", E.firewall_verdict(l, fw, ["W32Time"], "")[0])
        self.assertEqual("blocked", E.firewall_verdict(l, fw, ["Dnscache"], "")[0])

    # ---- IPv4 + IPv6 in one line, svchost by service name ----
    def test_ipv4_and_ipv6_merge(self):
        l = E.parse_netstat(NETSTAT)
        for x in l:
            x.process = "System"
            E.assess(x)
        merged = [x for x in E.merge_dual_stack(l) if x.port == 445]
        self.assertEqual(1, len(merged))
        self.assertEqual(["0.0.0.0", "::"], merged[0].addresses)

    def test_merge_takes_worst_verdict(self):
        a, b = self._l(), self._l()
        b.address = "::"
        a.firewall, b.firewall, b.firewall_rule = "blocked", "allowed", "X"
        for x in (a, b):
            E.assess(x)
        m = E.merge_dual_stack([a, b])
        self.assertEqual(1, len(m))
        self.assertEqual(("allowed", "X"), (m[0].firewall, m[0].firewall_rule))

    def test_svchost_123_is_time_service(self):
        l = E.Listener("UDP", "0.0.0.0", 123, 37212, process="svchost.exe", services=["W32Time"])
        E.assess(l)
        self.assertEqual("Windows Time (NTP)", l.service)
        self.assertEqual(S.INFO, l.severity)

    def test_parse_services(self):
        t = '"svchost.exe","37212","W32Time"\n"System","4","N/A"\n"svchost.exe","1808","RpcEptMapper,RpcSs"\n'
        self.assertEqual({37212: ["W32Time"], 1808: ["RpcEptMapper", "RpcSs"]}, E.parse_services(t))

    # ---- what can be done with a port ----
    def test_actions_for_smb_ollama_and_system(self):
        from src.runtime import remedy as R
        smb = E.Listener("TCP", "0.0.0.0", 445, 4, process="System")
        E.assess(smb)
        self.assertEqual(["block_port", "disable_service", "trust"], R.actions_for(smb, False, False))
        self.assertIn("shared folders", R.what_breaks(smb))
        self.assertEqual("sharing", R.settings_for(smb))
        ollama = E.Listener("TCP", "0.0.0.0", 11434, 701, process="ollama.exe")
        E.assess(ollama)
        self.assertEqual(["unblock", "stop_program", "show_file", "untrust"], R.actions_for(ollama, True, True))
        rpc = E.Listener("TCP", "0.0.0.0", 135, 1808, process="svchost.exe", services=["RpcSs"])
        E.assess(rpc)
        self.assertNotIn("stop_program", R.actions_for(rpc, False, False))   # Windows is not killed
        local = E.Listener("TCP", "127.0.0.1", 18434, 9, process="llama-server.exe")
        E.assess(local)
        self.assertNotIn("block_port", R.actions_for(local, False, False))

    def test_actions_check_input_and_live_port(self):
        from src.runtime import remedy as R
        with mock.patch.object(R.E, "_run", return_value=""), mock.patch.object(R, "_is_windows", return_value=True):
            for bad in (("block_port", "ICMP", 1, 1), ("block_port", "TCP", 70000, 1), ("trust", "TCP", "x", 1)):
                with self.assertRaises(R.RemedyError):
                    R.run(*bad)
            with self.assertRaises(R.RemedyError):           # port is no longer listening
                R.run("block_port", "TCP", 445, 4)

    def test_blocking_goes_through_uac_and_is_cancelled(self):
        import tempfile
        from src.runtime import remedy as R
        live = E.Listener("TCP", "0.0.0.0", 5432, 700, process="postgres.exe")
        live.reach = "all_networks"
        scripts = []
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"YADRO_GUARD_HOME": d}), \
                mock.patch.object(R, "_live", return_value=live), mock.patch.object(R, "_is_windows", return_value=True), \
                mock.patch.object(R, "_elevated", side_effect=scripts.append):
            r = R.run("block_port", "TCP", 5432, 700)
            self.assertIn("New-NetFirewallRule -Name 'YadroGuard-Block-TCP-5432'", scripts[0])
            self.assertIn("-LocalPort 5432", scripts[0])
            self.assertEqual({"YadroGuard-Block-TCP-5432"}, R.guard_rules())
            R.undo(r["fix"])
            self.assertIn("Remove-NetFirewallRule -Name 'YadroGuard-Block-TCP-5432'", scripts[1])
            self.assertEqual(set(), R.guard_rules())
            with self.assertRaises(R.RemedyError):
                R.undo(r["fix"])                              # does not roll back twice
            R.run("trust", "TCP", 5432, 700)
            self.assertIn("TCP:5432:postgres.exe", R.trusted())
            self.assertEqual(1, len(scripts) - 1)             # trust does not touch the system

    def test_uac_cancellation_honestly(self):
        from src.runtime import remedy as R
        class UacCancelled:
            returncode = 1223
        with mock.patch.object(R.subprocess, "run", return_value=UacCancelled()):
            with self.assertRaisesRegex(R.RemedyError, "cancelled"):
                R._elevated("Get-Date")

    @unittest.skipUnless(os.name == "nt", "Windows only")
    def test_live_scan_of_this_machine(self):
        r = E.scan(with_firewall=False)
        self.assertEqual("ok", r["status"])
        self.assertTrue(r["listeners"])
        self.assertTrue(0 <= r["score"] <= 100)
        self.assertTrue(all(x["reach"] in ("this_computer", "local_network", "all_networks") for x in r["listeners"]))
        self.assertTrue(r["limits"])


if __name__ == "__main__":
    unittest.main()
