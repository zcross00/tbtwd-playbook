"""Tests for milestones.py's burn-down: python3 -m unittest discover -s kit/board (kit/test.sh)"""
import datetime as dt
import unittest

import milestones as m

TODAY = dt.date(2026, 10, 25)
# Recorded from the live milestones on 2026-10-25.
FACILITIES = ("Dates (groomed 2026-10-25): about 15 PRs (13 plus 15% for bounces), 760k output "
              "tokens estimated, one PR at a time. 50%: Oct 30. 90%: Nov 3. The dates leave out")
NPC = "Dates (2026-10-25 grooming): 50% Oct 28, 90% Nov 1. Not committed yet"


def issue(n, state="open", created="2026-10-24T00:00:00Z", labels=(), closed=None):
    return {"number": n, "state": state, "created_at": created, "closed_at": closed,
            "labels": [{"name": l} for l in labels]}


class Dates(unittest.TestCase):
    def test_both_formats_the_threads_wrote(self):
        self.assertEqual(m.planning_dates(FACILITIES, TODAY), (dt.date(2026, 10, 30), dt.date(2026, 11, 3)))
        self.assertEqual(m.planning_dates(NPC, TODAY), (dt.date(2026, 10, 28), dt.date(2026, 11, 1)))

    def test_no_dates_yet(self):
        self.assertEqual(m.planning_dates("Goal: x. Done when: y.", TODAY), (None, None))
        self.assertEqual(m.planning_dates(None, TODAY), (None, None))

    def test_january_after_october_is_next_year(self):
        self.assertEqual(m.planning_dates("50%: Jan 3. 90%: Jan 9.", TODAY)[1], dt.date(2027, 1, 9))

    def test_grooming_date_else_creation(self):
        created = dt.date(2026, 10, 24)
        self.assertEqual(m.groomed_on(FACILITIES, created), dt.date(2026, 10, 25))
        self.assertEqual(m.groomed_on(NPC, created), dt.date(2026, 10, 25))
        self.assertEqual(m.groomed_on("Goal: fixed on 2026-10-01. No dates.", created), created)


class Estimates(unittest.TestCase):
    def test_newest_estimate_wins_and_body_counts(self):
        self.assertEqual(m.estimate([{"body": "board: estimate=60"}]), 60)
        self.assertEqual(m.estimate([{"body": "board: estimate=60"}, {"body": "board: estimate=100 status=Ready"}]), 100)
        self.assertIsNone(m.estimate([{"body": "no board line"}]))

    def test_refs_in_a_pr_body(self):
        self.assertEqual(m.refs("Docs only.\n\nRefs #587, #588 and #631\nSee #9 too"), {587, 588, 631})
        self.assertEqual(m.refs(None), set())


class Risk(unittest.TestCase):
    def test_left_over_rate_against_the_90_date(self):
        d90 = dt.date(2026, 11, 3)
        self.assertFalse(m.at_risk(600, 150, TODAY, d90))   # 4 days, Oct 29
        self.assertTrue(m.at_risk(1500, 150, TODAY, d90))   # 10 days, Nov 4
        self.assertFalse(m.at_risk(5000, 150, TODAY, None))  # no date, nothing to miss

    def test_a_line_uses_its_own_rate_once_it_has_a_day(self):
        ms = {"number": 9, "title": "Frontier economy pays", "created_at": "2026-10-25T01:00:00Z",
              "due_on": None, "description": "Dates (groomed 2026-10-23): 50%: Oct 26. 90%: Oct 27."}
        issues = [issue(1), issue(2, "closed", closed="2026-10-24T00:00:00Z")]
        comments = {1: [{"body": "board: estimate=100"}], 2: [{"body": "board: estimate=40"}]}
        # 40k done over 2 days is 20k a day, so 100k left lands on Oct 30: past Oct 27.
        out = m.line(ms, issues, comments, [], None, TODAY)
        self.assertIn("AT RISK", out)
        self.assertIn("100k left", out)
        self.assertIn("1 open, 1 closed", out)


class Line(unittest.TestCase):
    def test_counts_merged_prs_added_issues_and_corrections(self):
        ms = {"number": 13, "title": "CI and queue health", "created_at": "2026-10-25T01:00:00Z",
              "due_on": "2026-11-08T00:00:00Z", "description": "Dates (groomed 2026-10-25): 50%: Nov 2. 90%: Nov 8."}
        issues = [issue(414), issue(716, created="2026-10-25T02:18:00Z"), issue(682, labels=["verification"])]
        comments = {414: [{"body": "board: estimate=60"}], 716: [{"body": "board: estimate=60"}]}
        prs = [{"merged_at": "2026-10-25T03:00:00Z", "body": "Refs #716"},
               {"merged_at": "2026-10-24T03:00:00Z", "body": "Refs #414"},   # before grooming
               {"merged_at": None, "body": "Refs #414"},                     # closed unmerged
               {"merged_at": "2026-10-25T04:00:00Z", "body": "Refs #9"}]     # another milestone
        out = m.line(ms, issues, comments, prs, None, TODAY)
        for part in ("120k left (+1 unestimated)", "1 PRs merged since Oct 25", "0 added",
                     "1 corrections open", "50% Nov 02 / 90% Nov 08", "COMMITTED 2026-11-08", "ON TRACK"):
            self.assertIn(part, out)

    def test_committed_milestone_counts_green_nights_once_its_issues_close(self):
        ms = {"number": 13, "title": "CI", "created_at": "2026-10-25T01:00:00Z",
              "due_on": "2026-11-08T00:00:00Z", "description": "Dates (groomed 2026-10-25): 50%: Nov 2. 90%: Nov 8."}
        issues = [issue(414, "closed", closed="2026-10-29T00:00:00Z")]
        runs = [{"conclusion": "success", "updated_at": "2026-10-31T03:00:00Z"},
                {"conclusion": "success", "updated_at": "2026-10-30T03:00:00Z"}]
        self.assertIn("2 green nights", m.line(ms, issues, {}, [], runs, TODAY))
        self.assertIn("no nightly run yet (#414)", m.line(ms, issues, {}, [], None, TODAY))

    def test_a_milestone_without_dates_says_so(self):
        ms = {"number": 4, "title": "Organizations that last", "created_at": "2026-10-25T01:00:00Z",
              "due_on": None, "description": "Goal: x. Done when: y."}
        out = m.line(ms, [issue(651)], {}, [], None, TODAY)
        self.assertIn("0k left (+1 unestimated)", out)
        self.assertTrue(out.endswith("50% ? / 90% ?, NOT DATED"))


class FiftyPercent(unittest.TestCase):
    MS = {"number": 9, "title": "Frontier economy pays", "created_at": "2026-10-25T01:00:00Z",
          "due_on": "2026-11-08T00:00:00Z", "description": "Dates (groomed 2026-10-25): 50%: Nov 2. 90%: Nov 8."}

    def test_an_open_milestone_past_its_50_date_says_by_how_much(self):
        out = m.line(self.MS, [issue(1)], {1: [{"body": "board: estimate=10"}]}, [], None, dt.date(2026, 11, 5))
        self.assertIn("PAST ITS 50% DATE by 3 days", out)

    def test_work_left_that_runs_past_the_50_date_is_behind(self):
        # 1,500k at the planned 150k a day is 10 days from Oct 25: Nov 4, past Nov 2, not Nov 8.
        out = m.line(self.MS, [issue(1)], {1: [{"body": "board: estimate=1500"}]}, [], None, TODAY)
        self.assertIn("ON TRACK, BEHIND ITS 50% DATE", out)

    def test_a_passed_playtest_waits_on_merge_instead(self):
        ms = dict(self.MS, description=self.MS["description"] + "\nSigned off: 2026-10-28, Zac's pass.")
        out = m.line(ms, [issue(1)], {1: [{"body": "board: estimate=10"}]}, [], None, dt.date(2026, 11, 5))
        self.assertIn("PLAYTEST PASSED, WAITING ON MERGE", out)
        self.assertNotIn("PAST ITS 50% DATE", out)
        not_yet = dict(self.MS, description=self.MS["description"] + "\nSigned off: not yet")
        self.assertIn("PAST ITS 50% DATE", m.line(not_yet, [issue(1)], {}, [], None, dt.date(2026, 11, 5)))

    def test_nothing_said_on_time_or_once_closed(self):
        self.assertNotIn("50% DATE", m.line(self.MS, [issue(1)], {1: [{"body": "board: estimate=60"}]}, [], None, TODAY))
        done = [issue(1, "closed", closed="2026-10-28T00:00:00Z")]
        self.assertNotIn("50% DATE", m.line(self.MS, done, {}, [], None, dt.date(2026, 11, 5)))


class GreenNights(unittest.TestCase):
    def test_the_nightly_line(self):
        runs = [{"status": "in_progress", "conclusion": None, "created_at": "2026-11-02T08:17:00Z", "updated_at": ""},
                {"status": "completed", "conclusion": "failure", "created_at": "2026-11-01T08:17:00Z",
                 "updated_at": "2026-11-01T09:00:00Z"},
                {"status": "completed", "conclusion": "success", "created_at": "2026-10-31T08:17:00Z",
                 "updated_at": "2026-10-31T09:00:00Z"}]
        self.assertEqual(m.nightly(runs), "Nightly main run: last 2026-11-01 failure, 0 green in a row")
        self.assertEqual(m.nightly(runs[2:]), "Nightly main run: last 2026-10-31 success, 1 green in a row")
        self.assertEqual(m.nightly([]), "Nightly main run: none yet (#414)")
        self.assertEqual(m.nightly(None), "Nightly main run: none yet (#414)")

    def test_streak_stops_at_a_red_night_and_skips_cancelled(self):
        runs = [{"conclusion": "success", "updated_at": "2026-11-03T03:00:00Z"},
                {"conclusion": "cancelled", "updated_at": "2026-11-02T03:00:00Z"},
                {"conclusion": "success", "updated_at": "2026-11-01T03:00:00Z"},
                {"conclusion": "failure", "updated_at": "2026-10-31T03:00:00Z"},
                {"conclusion": "success", "updated_at": "2026-10-30T03:00:00Z"}]
        self.assertEqual(m.green_streak(runs, "2026-10-29T00:00:00Z"), 2)

    def test_nights_before_the_last_issue_closed_dont_count(self):
        runs = [{"conclusion": "success", "updated_at": "2026-11-01T03:00:00Z"},
                {"conclusion": "success", "updated_at": "2026-10-28T03:00:00Z"}]
        self.assertEqual(m.green_streak(runs, "2026-10-29T00:00:00Z"), 1)


if __name__ == "__main__":
    unittest.main()
