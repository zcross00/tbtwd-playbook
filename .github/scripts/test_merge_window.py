import datetime as dt
import unittest

from merge_window import verdict, window_open

UTC = dt.timezone.utc


class WindowTest(unittest.TestCase):
    def test_saturday_eleven_central_is_open(self):
        # 2026-11-07 is a Saturday, CST (UTC-6): 11:00 local = 17:00 UTC.
        self.assertTrue(window_open(dt.datetime(2026, 11, 7, 17, 0, tzinfo=UTC)))
        self.assertTrue(window_open(dt.datetime(2026, 11, 8, 5, 59, tzinfo=UTC)))

    def test_before_and_after_are_closed(self):
        self.assertFalse(window_open(dt.datetime(2026, 11, 7, 16, 59, tzinfo=UTC)))
        self.assertFalse(window_open(dt.datetime(2026, 11, 8, 6, 0, tzinfo=UTC)))
        self.assertFalse(window_open(dt.datetime(2026, 11, 4, 17, 0, tzinfo=UTC)))

    def test_daylight_saving(self):
        # 2026-10-31 is a Saturday, CDT (UTC-5): 11:00 local = 16:00 UTC.
        self.assertTrue(window_open(dt.datetime(2026, 10, 31, 16, 0, tzinfo=UTC)))
        self.assertFalse(window_open(dt.datetime(2026, 10, 31, 15, 59, tzinfo=UTC)))

    def test_emergency_needs_label_and_line(self):
        wed = dt.datetime(2026, 11, 4, 17, 0, tzinfo=UTC)
        self.assertEqual(verdict(wed, [], "")[0], "failure")
        self.assertEqual(verdict(wed, ["emergency"], "no line")[0], "failure")
        self.assertEqual(verdict(wed, [], 'Emergency: owner "go"')[0], "failure")
        body = 'Change\n\nEmergency: owner, 2026-11-04: "merge it now, CI is down"\n'
        self.assertEqual(verdict(wed, ["emergency"], body)[0], "success")


if __name__ == "__main__":
    unittest.main()
