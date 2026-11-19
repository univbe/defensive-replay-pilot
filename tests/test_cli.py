import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def run_trace(path, session="drill", a="fixture-a", b="fixture-b"):
    return subprocess.run(
        [sys.executable, str(ROOT / "checkout_pilot.py"), str(path),
         "--drill-session", session, "--decoy", a, "--decoy", b],
        capture_output=True, text=True, timeout=10,
    )


class CommandTests(unittest.TestCase):
    def test_published_examples(self):
        for name, code, reasons in [
            ("pass", 0, []), ("late", 1, ["outside_window"]),
            ("incomplete", 1, ["single_decoy"]),
        ]:
            with self.subTest(name=name):
                result = run_trace(ROOT / "examples" / f"checkout-{name}.csv")
                self.assertEqual(result.returncode, code)
                self.assertEqual(json.loads(result.stdout)["review_reasons"], reasons)

    def test_private_values_stay_local(self):
        header = "event_time,session_id,route_label\n"
        first = "2026-01-01T00:00:00Z,PRIVATE-drill,PRIVATE-a\n"
        second = "2026-01-01T01:01:00+01:00,PRIVATE-drill,PRIVATE-b\n"
        normal = "2026-01-01T00:00:00Z,PRIVATE-control,PRIVATE-checkout\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "PRIVATE-trace.csv"
            for payload, code in [
                (header + first + second + normal, 0),
                (header + first + second, 1),
                (header + first + second + (first + second).replace("drill", "other"), 1),
                (header + first.replace("00:00:00Z", "00:00:00"), 2),
                (header + "PRIVATE-invalid,PRIVATE-drill,PRIVATE-route\n", 2),
                (header + "bad,row,extra,PRIVATE\n", 2),
                ("PRIVATE-header\n", 2),
            ]:
                with self.subTest(code=code, payload=payload):
                    path.write_text(payload, encoding="utf-8")
                    result = run_trace(path, "PRIVATE-drill", "PRIVATE-a", "PRIVATE-b")
                    self.assertEqual(result.returncode, code)
                    self.assertNotIn("PRIVATE", result.stdout + result.stderr)
                    if code == 2:
                        self.assertEqual(result.stdout, "")
