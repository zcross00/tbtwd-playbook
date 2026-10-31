"""Tests for the wiki's pages: python3 -m unittest discover -s kit/wiki (kit/test.sh)"""
import datetime as dt
import os
import shutil
import subprocess
import unittest

import gen

TODAY = dt.date(2026, 10, 30)
DESC = "Goal: x.\n\nDates (groomed 2026-10-27): 50%: Nov 2. 90%: Nov 5."


def milestone(n, title="Windows that behave", due=None, created="2026-10-27T00:00:00Z", **kw):
    return {"number": n, "title": title, "description": DESC, "due_on": due, "created_at": created, **kw}


def issue(n, state="open", body="", created="2026-10-27T00:00:00Z", closed=None):
    return {"number": n, "state": state, "title": f"Issue {n}", "body": body, "labels": [],
            "created_at": created, "closed_at": closed}


class Rows(unittest.TestCase):
    def test_counts_and_verdict(self):
        issues = [issue(1), issue(2, "closed", closed="2026-10-29T00:00:00Z")]
        comments = {1: [{"body": "board: estimate=60"}], 2: [{"body": "board: estimate=40"}]}
        r = gen.milestone_row(milestone(18), issues, comments, [], None, TODAY)
        self.assertEqual((r["open"], r["closed"]), (1, 1))
        self.assertEqual(r["left"], "60k left")
        self.assertEqual(r["dates"], "Nov 02 → Nov 05")
        self.assertIn("ON TRACK", r["flags"])
        self.assertFalse(r["playtest_owed"])

    def test_all_closed_is_a_playtest_owed(self):
        issues = [issue(1, "closed", closed="2026-10-29T00:00:00Z")]
        r = gen.milestone_row(milestone(18), issues, {1: []}, [], None, TODAY)
        self.assertTrue(r["playtest_owed"])
        self.assertIn("Playtest: [Windows that behave](Milestone-18)",
                      gen.status_page([r], [], [], "Nightly", TODAY))


class Roadmap(unittest.TestCase):
    def test_bars_run_to_the_committed_date_and_names_lose_colons(self):
        page = gen.roadmap_page([milestone(26, "Internal: checks, restored", due="2026-11-17T07:00:00Z")],
                                [], [], TODAY)
        self.assertIn("  m26 Internal  checks  restored :active, m26, 2026-10-27, 2026-11-17", page)

    def test_a_milestone_with_no_dates_is_listed_not_drawn(self):
        ms = milestone(30)
        ms["description"] = "No dates yet"
        page = gen.roadmap_page([ms], [], [], TODAY)
        self.assertIn("Not dated yet: [Windows that behave](Milestone-30)", page)
        self.assertNotIn(":active, m30", page)


class Decisions(unittest.TestCase):
    def test_pending_and_decided(self):
        ds = [issue(5, created="2026-10-26T00:00:00Z"),
              issue(6, "closed", body="Question\n\n> yes extend the board\n", closed="2026-10-30T01:00:00Z")]
        page = gen.decisions_page(ds, TODAY)
        self.assertIn("| 2026-10-26 | 4 days |", page)
        self.assertIn("| 2026-10-30 | yes extend the board |", page)
        flags = gen.decision_flags(ds, TODAY)
        self.assertEqual(flags, ["DECISION WAITING #5 Issue 5: 4 days"])

    def test_a_moved_decision_keeps_its_day(self):
        d = issue(8, "closed", body="Decided: 2026-10-17\n\n> no offline", closed="2026-10-30T00:00:00Z")
        self.assertIn("| 2026-10-17 | no offline |", gen.decisions_page([d], TODAY))

    def test_a_decided_issue_without_his_words_is_flagged(self):
        flags = gen.decision_flags([issue(7, "closed", body="no quote", closed="2026-10-30T00:00:00Z")], TODAY)
        self.assertEqual(len(flags), 1)
        self.assertTrue(flags[0].startswith("DECISION UNQUOTED #7"))

    def test_pipes_in_his_words_stay_in_their_cell(self):
        self.assertEqual(gen.cell("a | b\nc"), "a \\| b c")


class HandPages(unittest.TestCase):
    def test_review_dates_are_checked_in_the_project_checkout(self):
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "docs"))
            with open(os.path.join(root, "docs", "DEVELOPMENT-PROCESS.md"), "w") as f:
                f.write("# Process\n\nLast reviewed: 2026-10-29\n")
            with open(os.path.join(root, "docs", "VISION.md"), "w") as f:
                f.write("# Vision\n")
            with mock.patch.object(gen, "ROOT", root):
                flags = gen.review_flags(TODAY)
        self.assertEqual(flags, ["STALE PAGE VISION.md: docs/VISION.md has no 'Last reviewed:' line"])

    def test_a_missing_page_is_flagged_not_fatal(self):
        from unittest import mock
        with mock.patch.object(gen, "ROOT", "/nonexistent"):
            self.assertTrue(all("is missing" in f for f in gen.review_flags(TODAY)))


class Publish(unittest.TestCase):
    def test_publish_sh_parses(self):
        # The first run on the PC died on a parse error (an apostrophe in ${GH_TOKEN:?...}).
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "publish.sh")
        # By its PATH entry: on Windows a bare "bash" finds System32's (WSL) first.
        r = subprocess.run([shutil.which("bash"), "-n", path], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
