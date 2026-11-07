import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import digest  # noqa: E402

SINCE = "2026-11-07T00:00:00Z"


def fake(path):
    if "/issues/comments" in path:
        return [{"updated_at": "2026-11-07T01:00:00Z", "user": {"login": "team-b"},
                 "issue_url": "https://api.github.com/repos/o/hub/issues/3",
                 "body": "Yes, take them.", "html_url": "u3c"},
                {"updated_at": "2026-11-07T01:05:00Z", "user": {"login": "stranger"},
                 "issue_url": "https://api.github.com/repos/o/hub/issues/3",
                 "body": "spam", "html_url": "u3s"}]
    if "/issues?" in path:
        return [{"number": 3, "title": "Who takes m67?", "state": "open", "html_url": "u3",
                 "created_at": "2026-11-07T00:30:00Z", "updated_at": "2026-11-07T01:00:00Z",
                 "user": {"login": "team-a"}, "labels": [{"name": "question"}]},
                {"number": 4, "title": "Teams page", "state": "open", "html_url": "u4",
                 "pull_request": {}, "created_at": "2026-11-06T00:00:00Z",
                 "updated_at": "2026-11-07T00:40:00Z", "user": {"login": "team-b"}, "labels": []}]
    return []


class DigestTest(unittest.TestCase):
    def test_theirs_first_ours_marked_outsiders_ignored(self):
        out = digest.render([("o/hub", digest.collect("o/hub", SINCE, fake))],
                            "team-a", {"team-a", "team-b"})
        lines = out.splitlines()
        self.assertEqual(lines[0], "## o/hub")
        self.assertTrue(lines[1].startswith("- [team-b] updated PR #4"))
        self.assertTrue(lines[2].startswith("- [team-b] comment on #3: Yes, take them."))
        self.assertEqual(lines[3], "(1 item(s) of this team's own, not listed)")
        self.assertNotIn("spam", out)
        self.assertIn("ignored 1 item(s)", out)

    def test_nothing_new(self):
        self.assertEqual(digest.render([("o/hub", [])], "a", {"a"}), "NOTHING NEW")
        own = [{"at": "t", "login": "a", "line": "x"}]
        self.assertTrue(digest.render([("o/hub", own)], "a", {"a"}).startswith("NOTHING NEW\n"))


if __name__ == "__main__":
    unittest.main()
