import unittest
from unittest.mock import patch

from checkout_pilot import staging_summary


class SummaryTests(unittest.TestCase):
    def test_evidence(self):
        cases = [
            ([], "session_absent"),
            ([(0, "normal")], "no_decoy_visits"),
            ([(0, "a"), (2, "a")], "single_decoy"),
            ([(0, "a"), (61, "b")], "outside_window"),
            ([(0, "a"), (50, "a"), (100, "b")], "qualifying_pair"),
        ]
        for visits, expected in cases:
            with self.subTest(expected=expected):
                events = [(0, "control", "shop")] + [(t, "drill", p) for t, p in visits]
                report = staging_summary(sorted(events), {"a", "b"}, "drill")
                self.assertEqual(report["drill_evidence"], expected)
                self.assertEqual(report["result"], "PASS" if expected == "qualifying_pair" else "REVIEW")

    def test_independent_evidence_catches_missing_alert(self):
        with patch("checkout_pilot.detect", return_value=[]):
            report = staging_summary([(0, "d", "a"), (1, "d", "b")], {"a", "b"}, "d")
        self.assertEqual(report["review_reasons"], ["detector_mismatch", "no_control_sessions"])
