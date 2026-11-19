import unittest

from checkout_pilot import detect


class DetectionTests(unittest.TestCase):
    def test_window_and_identity(self):
        cases = [
            ("inclusive", [(0, "a", "d1"), (60, "a", "d2")], [("a", 60, 60)]),
            ("late", [(0, "a", "d1"), (60.001, "a", "d2")], []),
            ("split", [(0, "a", "d1"), (0, "b", "d2")], []),
            ("repeat", [(0, "a", "d1"), (1, "a", "d1")], []),
            ("expired then renewed", [(0, "a", "d1"), (50, "a", "d1"),
                                      (100, "a", "d2"), (101, "a", "d1")], [("a", 100, 50)]),
        ]
        for name, events, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(detect(events, {"d1", "d2"}), expected)
