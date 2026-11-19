import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def compare(base, candidate):
    return subprocess.run(
        [sys.executable, str(ROOT / "checkout_pilot.py"), candidate,
         "--baseline", base, "--decoy", "fixture-a", "--decoy", "fixture-b",
         "--drill-session", "drill"],
        cwd=ROOT, capture_output=True, text=True, timeout=10,
    )


class ReleaseComparisonTests(unittest.TestCase):
    def test_release_verdicts(self):
        for base, candidate, verdict, code in [
            ("pass", "pass", "PASS", 0),
            ("pass", "incomplete", "REGRESSION", 1),
            ("pass", "late", "REGRESSION", 1),
            ("incomplete", "pass", "BASELINE_NEEDS_REVIEW", 1),
            ("late", "late", "BASELINE_NEEDS_REVIEW", 1),
        ]:
            with self.subTest(base=base, candidate=candidate):
                result = compare(f"examples/checkout-{base}.csv", f"examples/checkout-{candidate}.csv")
                self.assertEqual(result.returncode, code)
                report = json.loads(result.stdout)
                self.assertEqual(report["result"], verdict)
                self.assertEqual(report["baseline"]["result"], "PASS" if base == "pass" else "REVIEW")
                self.assertEqual(report["candidate"]["result"], "PASS" if candidate == "pass" else "REVIEW")
                for marker in ["examples/", "fixture-a", "fixture-b", "2026-01", "shopper"]:
                    self.assertNotIn(marker, result.stdout + result.stderr)

    def test_unreadable_baseline_suppresses_partial_report(self):
        result = compare("PRIVATE-missing.csv", "examples/checkout-pass.csv")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("PRIVATE", result.stderr)
