"""Tests for release_notes.py: python3 -m unittest discover -s kit/releases (kit/test.sh)"""
import json
import subprocess
import sys
import unittest
from unittest import mock

import release_notes as rn


def rel(tag, at, body="Notes.", name=None, sha="a" * 40):
    return {"tag_name": tag, "created_at": f"2026-10-{at}T00:00:00Z", "body": body,
            "name": name or tag, "target_commitish": sha, "id": hash(tag)}


def ms(n, state="open"):
    return {"number": n, "title": f"Milestone {n}", "state": state, "html_url": f"https://x/milestone/{n}"}


def plan(releases, states=None):
    states = states or {}
    return rn.plan(releases, lambda n: ms(n, states.get(n, "open")), lambda n: [n * 10, n * 10 + 1])


class Plan(unittest.TestCase):
    def test_links_the_milestone_issues_and_commit(self):
        [(r, name, body)] = plan([rel("m15-playtest-1", "27")])
        self.assertIn("[15. Milestone 15](https://x/milestone/15) (open)", body)
        self.assertIn("#150, #151", body)
        self.assertIn("[aaaaaaa](https://github.com/zcross00/sovereign-space/commit/" + "a" * 40 + ")", body)
        self.assertIn("This is the build to play.", body)
        self.assertTrue(body.endswith("Notes."))
        self.assertEqual(name, "m15-playtest-1")

    def test_older_builds_point_at_the_newest(self):
        out = {r["tag_name"]: (name, body) for r, name, body in plan([rel("m15-playtest-1", "27"), rel("m15-playtest-3", "29")])}
        name, body = out["m15-playtest-1"]
        self.assertEqual(name, "m15-playtest-1 (superseded)")
        self.assertIn("Superseded by [m15-playtest-3]", body)
        self.assertIn("This is the build to play.", out["m15-playtest-3"][1])

    def test_a_closed_milestone_says_its_playtest_passed(self):
        [(_, _, body)] = plan([rel("m19-playtest-1", "28")], {19: "closed"})
        self.assertIn("The milestone is closed: Zac's playtest passed.", body)

    def test_an_old_tag_belongs_to_its_milestone(self):
        out = {r["tag_name"]: body for r, _, body in plan([rel("s6-playtest-1", "27"), rel("m12-playtest-2", "28")])}
        self.assertIn("Superseded by [m12-playtest-2]", out["s6-playtest-1"])

    def test_other_releases_are_left_alone(self):
        self.assertEqual(plan([rel("v1.0", "27")]), [])

    def test_running_again_changes_nothing(self):
        [(r, name, body)] = plan([rel("m3-playtest-1", "27")])
        self.assertEqual(plan([dict(r, body=body, name=name)]), [])

    def test_an_old_header_is_replaced_not_stacked(self):
        [(r, name, body)] = plan([rel("m3-playtest-1", "27")])
        [(_, _, again)] = plan([dict(r, body=body, name=name)], {3: "closed"})
        self.assertEqual(again.count(rn.MARK), 1)
        self.assertTrue(again.endswith("Notes."))

    def test_a_retired_name_isnt_marked_twice(self):
        out = {r["tag_name"]: name for r, name, _ in plan([rel("m15-playtest-2", "28", name="m15-playtest-2 (retired, use m15-playtest-3)"), rel("m15-playtest-3", "29")])}
        self.assertEqual(out["m15-playtest-2"], "m15-playtest-2 (retired, use m15-playtest-3)")


# Milestone 22's description: curly quotes (byte 0x9d isn't cp1252) and an arrow.
QUOTED = {"number": 22, "title": "Playtests that record themselves \u2192 timeline", "state": "closed",
          "html_url": "https://x/milestone/22",
          "description": "Zac: \u201ca \u201cplaytest\u201d mode\u201d \u2192 a packaged output"}


class Unicode(unittest.TestCase):
    """#1324: the hosted Windows build decoded gh's output as cp1252 and crashed."""

    def test_gh_reads_its_output_as_utf8(self):
        real = subprocess.run

        def fake_gh(cmd, **kw):
            # gh's real bytes, through the decoding the call asks for; asking
            # for none gets the Windows runner's cp1252.
            kw.setdefault("encoding", "cp1252")
            out = json.dumps(QUOTED, ensure_ascii=False)
            script = f"import sys; sys.stdout.buffer.write({out.encode('utf-8')!r})"
            return real([sys.executable, "-c", script], **kw)

        with mock.patch.object(rn.subprocess, "run", fake_gh):
            self.assertEqual(rn.gh("repos/x/milestones/22"), QUOTED)

    def test_plan_keeps_curly_quotes_and_arrows(self):
        [(_, _, body)] = rn.plan([rel("m22-playtest-1", "30")], lambda n: QUOTED, lambda n: [1147])
        self.assertIn("[22. Playtests that record themselves \u2192 timeline](https://x/milestone/22) (closed)", body)


if __name__ == "__main__":
    unittest.main()
