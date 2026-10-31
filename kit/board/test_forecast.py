"""Tests for forecast.py's daily re-forecast: python3 -m unittest discover -s kit/board (kit/test.sh)"""
import datetime as dt
import unittest

import forecast as f

NOW = dt.datetime(2026, 10, 31, 10, 0)
TODAY = dt.date(2026, 10, 31)


def issue(n, state="open", closed=None, reason=None):
    return {"number": n, "state": state, "closed_at": closed, "state_reason": reason}


def ms(desc="Goal: x.", due="2026-11-03T07:00:00Z", **kw):
    return {"number": 7, "title": "Test milestone", "description": desc, "due_on": due, **kw}


class Pace(unittest.TestCase):
    def test_estimate_closed_in_three_days_over_three(self):
        issues = [issue(1, "closed", "2026-10-30T09:00:00Z"), issue(2, "closed", "2026-10-29T00:00:00Z"),
                  issue(3, "closed", "2026-10-27T00:00:00Z")]  # outside the window
        self.assertEqual(f.pace(issues, {1: 200, 2: 100, 3: 900}, NOW), 100)

    def test_not_planned_and_small_closes_give_no_pace(self):
        issues = [issue(1, "closed", "2026-10-30T09:00:00Z", "not_planned"),
                  issue(2, "closed", "2026-10-30T09:00:00Z")]
        self.assertIsNone(f.pace(issues, {1: 500, 2: 40}, NOW))

    def test_unestimated_counts_as_one_normal_pr(self):
        issues = [issue(1, "closed", "2026-10-30T09:00:00Z"), issue(2, "closed", "2026-10-30T10:00:00Z")]
        self.assertEqual(f.pace(issues, {}, NOW), 40)

    def test_an_estimate_written_in_tokens_reads_as_thousands(self):
        self.assertEqual(f.k(100000), 100)
        self.assertEqual(f.k(200), 200)
        self.assertEqual(f.k(None), 60)


class OpenMilestones(unittest.TestCase):
    ISSUES = [issue(1, "closed", "2026-10-30T09:00:00Z"), issue(2), issue(3)]

    # m13's grooming line, which quotes Zac (10-31).
    GROOMING = ('Forecast dates (2026-10-30): 50% Nov 1, 90% Nov 3. Due Nov 3, was Nov 8 '
                '(Zac: "keep it at nov 8", cmsg_x).\nGoal: x.')

    def test_forecast_moves_the_due_date_and_writes_its_line_on_top(self):
        d, desc, report = f.plan_open(ms(self.GROOMING), self.ISSUES, {1: 300, 2: 150, 3: 60}, NOW, TODAY)
        # 210k left at 100k a day: 3 days, plus the playtest day.
        self.assertEqual(d, dt.date(2026, 11, 4))
        self.assertTrue(desc.startswith("Forecast (2026-10-31, kit/board/forecast.py): due Nov 4 "
                                        "(50% Nov 4, 90% Nov 4: one date, from measured pace). "
                                        "210k left at 100k a day"))
        # A thread's own line, with Zac's words, is kept below.
        self.assertTrue(desc.endswith("\n\n" + self.GROOMING))
        self.assertIn("was 2026-11-03", report)

    def test_only_its_own_line_is_replaced(self):
        _, first, _ = f.plan_open(ms(self.GROOMING), self.ISSUES, {1: 300, 2: 150, 3: 60}, NOW, TODAY)
        later = dt.datetime(2026, 11, 1, 10, 0)
        _, second, _ = f.plan_open(ms(first, due="2026-11-04T12:00:00Z"), self.ISSUES,
                                   {1: 300, 2: 150, 3: 60}, later, later.date())
        self.assertTrue(second.startswith("Forecast (2026-11-01, kit/board/forecast.py)"))
        self.assertEqual(second.count("kit/board/forecast.py"), 1)
        self.assertTrue(second.endswith(self.GROOMING))

    def test_a_line_from_before_the_kit_is_replaced_too(self):
        old = "Forecast (2026-10-30, tools/board/forecast.py): due Nov 3.\n\n" + self.GROOMING
        _, desc, _ = f.plan_open(ms(old), self.ISSUES, {1: 300, 2: 150, 3: 60}, NOW, TODAY)
        self.assertNotIn("tools/board/forecast.py", desc)
        self.assertTrue(desc.endswith(self.GROOMING))

    def test_milestones_py_reads_the_forecast_as_its_dates(self):
        import milestones
        _, desc, _ = f.plan_open(ms(self.GROOMING), self.ISSUES, {1: 300, 2: 150, 3: 60}, NOW, TODAY)
        self.assertEqual(milestones.planning_dates(desc, TODAY), (dt.date(2026, 11, 4), dt.date(2026, 11, 4)))

    def test_a_description_without_a_forecast_line_gets_one_on_top(self):
        _, desc, _ = f.plan_open(ms("Goal: x."), self.ISSUES, {1: 300, 2: 150, 3: 60}, NOW, TODAY)
        self.assertTrue(desc.startswith("Forecast ("))
        self.assertTrue(desc.endswith("\n\nGoal: x."))

    def test_same_date_moves_nothing(self):
        d, _, report = f.plan_open(ms(due="2026-11-04T12:00:00Z"), self.ISSUES,
                                   {1: 300, 2: 150, 3: 60}, NOW, TODAY)
        self.assertIsNone(d)
        self.assertNotIn("was", report)

    def test_no_pace_keeps_the_date(self):
        # Not started, queued behind another milestone, or dated by an outside plan.
        self.assertEqual(f.plan_open(ms(), [issue(2)], {2: 150}, NOW, TODAY)[:2], (None, None))

    def test_date_fixed_is_never_moved(self):
        out = f.plan_open(ms("Goal: x.\nDate fixed: Valve's review window."), self.ISSUES,
                          {1: 300, 2: 150}, NOW, TODAY)
        self.assertEqual(out[:2], (None, None))


class ClosedMilestones(unittest.TestCase):
    def test_reports_forecast_against_close_and_sets_due_to_close(self):
        # Closed 00:02 UTC on Oct 31 is Oct 30 on Zac's clock.
        d, desc, report = f.plan_closed(ms(closed_at="2026-10-31T00:02:00Z"), TODAY)
        self.assertEqual(d, dt.date(2026, 10, 30))
        self.assertTrue(desc.endswith("\n\nClosed 2026-10-30, 4 days early: its last due date was Nov 3."))
        self.assertIn("4 days early", report)

    def test_late_and_on_time(self):
        self.assertEqual(f.closed_line(dt.date(2026, 11, 5), dt.date(2026, 11, 4)),
                         "Closed 2026-11-05, 1 day late: its last due date was Nov 4.")
        self.assertIsNone(f.plan_closed(ms(due="2026-10-30T12:00:00Z", closed_at="2026-10-30T20:00:00Z"),
                                        TODAY)[0])

    def test_old_closes_are_left_alone(self):
        self.assertIsNone(f.plan_closed(ms(closed_at="2026-10-01T00:00:00Z"), TODAY)[2])


if __name__ == "__main__":
    unittest.main()
