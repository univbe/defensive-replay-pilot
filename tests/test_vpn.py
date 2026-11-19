import json
from pathlib import Path
import subprocess
import sys
import unittest


class VPNTests(unittest.TestCase):
    def test_structured_self_test(self):
        script = Path(__file__).resolve().parents[1] / "vpn_replay.py"
        output = subprocess.check_output([sys.executable, str(script), "--json"], timeout=10)
        report = json.loads(output)
        self.assertEqual(report["self_test"], "PASS")
        cases = report["cases"]
        self.assertEqual(len(cases), 4)
        self.assertTrue(all(case["final_up"] for case in cases))
        failures = [case for case in cases if not case["policy_passed"]]
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["agent"], "faulty_agent")
        self.assertTrue(failures[0]["flagged_report"])
        self.assertEqual((failures[0]["writes"], failures[0]["drops"]), (2, 1))
