"""Tests for sync.py's board: line parsing: python3 -m unittest discover -s kit/board (kit/test.sh)"""
import datetime as dt
import unittest

import sync

TEAMS = {"team:a": {"field": "A sprint", "prefix": "A", "start": "2026-11-07", "days": 7, "count": 3,
                    "plan": {"1": [49, 27], "2": [27, 57]}},
         "team:b": {"field": "B sprint", "prefix": "B", "start": "2026-11-09", "days": 7, "count": 3,
                    "plan": {"1": [52]}}}


def said(*bodies):
    return sync.board_values([{"body": b} for b in bodies])


class BoardLines(unittest.TestCase):
    def test_the_four_lines_skipped_on_10_23_now_apply(self):
        # #582: each was dropped by the replay sync of 2026-10-23.
        self.assertEqual(said("board: estimate=5 status=Code review"),
                         {"estimate": "5", "status": "In progress"})
        self.assertEqual(said("board: estimate=2 status=Code review")["status"], "In progress")
        self.assertEqual(said("board: status=PR ready (#575), estimate 25k, actual ~22k output tokens."),
                         {"status": "In progress"})
        self.assertEqual(said("board: actual=30 (final for the build)"), {"actual": "30"})

    def test_board_options_pass_through_in_their_own_case(self):
        for s in sync.STATUSES:
            self.assertEqual(said(f"board: status={s.upper()}")["status"], s)

    def test_every_lifecycle_stage_maps_to_a_board_option(self):
        for stage, status in sync.STAGE_STATUS.items():
            self.assertIn(status, sync.STATUSES)
            self.assertEqual(said(f"board: status={stage}")["status"], status)

    def test_a_longer_name_wins_over_its_prefix(self):
        self.assertEqual(said("board: status=In review")["status"], "In review")
        self.assertEqual(said("board: status=Ready")["status"], "Ready")

    def test_a_word_that_only_starts_like_a_status_is_left_for_the_skip(self):
        self.assertEqual(said("board: status=Readying")["status"], "Readying")
        self.assertEqual(said("board: status=Blocked")["status"], "Blocked")

    def test_numbers_and_days_drop_trailing_prose(self):
        self.assertEqual(said("board: estimate=60k tokens day=2026-10-24 (Sat)"),
                         {"estimate": "60", "day": "2026-10-24"})
        self.assertEqual(said("board: actual=12.5")["actual"], "12.5")

    def test_a_value_with_no_number_is_left_for_the_skip(self):
        self.assertEqual(said("board: actual=~22k")["actual"], "~22k")
        self.assertEqual(said("board: day=tomorrow")["day"], "tomorrow")

    def test_the_newest_line_wins(self):
        self.assertEqual(said("board: actual=30 (final)", "board: actual=31")["actual"], "31")



class TeamSprints(unittest.TestCase):
    def sprint(self, labels, milestone, closed=None):
        return sync.sprint_for(set(labels), milestone, closed and dt.date.fromisoformat(closed), TEAMS)

    def test_an_open_issue_goes_in_the_latest_sprint_listing_its_milestone(self):
        self.assertEqual(self.sprint(["team:a"], 49), ("A sprint", "2026-11-07"))
        self.assertEqual(self.sprint(["team:a"], 27), ("A sprint", "2026-11-14"))
        self.assertEqual(self.sprint(["team:b"], 52), ("B sprint", "2026-11-09"))

    def test_a_closed_issue_stays_in_the_sprint_it_closed_in(self):
        self.assertEqual(self.sprint(["team:a"], 27, "2026-11-10"), ("A sprint", "2026-11-07"))
        self.assertEqual(self.sprint(["team:a"], 27, "2026-11-15"), ("A sprint", "2026-11-14"))
        self.assertIsNone(self.sprint(["team:a"], 57, "2026-11-10"))

    def test_no_team_label_or_milestone_outside_the_plan_gets_no_sprint(self):
        self.assertIsNone(self.sprint([], 49))
        self.assertIsNone(self.sprint(["team:b"], 49))
        self.assertIsNone(self.sprint(["team:a"], 52))
        self.assertIsNone(self.sprint(["team:a"], None))

    def test_a_new_field_gets_numbered_week_long_iterations(self):
        its = sync.sprint_iterations(TEAMS["team:a"])
        self.assertEqual([i["title"] for i in its], ["A 1", "A 2", "A 3"])
        self.assertEqual([i["startDate"] for i in its], ["2026-11-07", "2026-11-14", "2026-11-21"])
        self.assertEqual({i["duration"] for i in its}, {7})


if __name__ == "__main__":
    unittest.main()
