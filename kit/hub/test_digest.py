import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import digest  # noqa: E402

SINCE = "2026-11-07T00:00:00Z"
OWN_LOGINS = {"a": "login-a", "b": "login-b"}
SHARED = {"a": "login-a", "b": "login-a"}


def issue(n, login, body="", labels=(), pr=False, created="2026-11-07T00:30:00Z"):
    i = {"number": n, "title": f"t{n}", "state": "open", "html_url": f"u{n}", "body": body,
         "created_at": created, "updated_at": f"2026-11-07T00:{n:02d}:00Z",
         "user": {"login": login}, "labels": [{"name": l} for l in labels]}
    if pr:
        i["pull_request"] = {}
    return i


def comment(n, login, body, minute):
    return {"updated_at": f"2026-11-07T01:{minute:02d}:00Z", "user": {"login": login},
            "issue_url": f"https://api.github.com/repos/o/hub/issues/{n}", "body": body,
            "html_url": f"u{n}c{minute}"}


def fake(issues, comments):
    def f(path):
        if "/issues/comments" in path:
            return comments
        if "/issues?" in path:
            return issues
        return []
    return f


class DigestTest(unittest.TestCase):
    def run_digest(self, issues, comments, roster, team="a"):
        items = digest.collect("o/hub", SINCE, fake(issues, comments))
        return digest.render([("o/hub", items)], team, roster)

    def test_own_logins(self):
        out = self.run_digest([issue(3, "login-a", labels=["question"]),
                               issue(4, "login-b", pr=True, created="2026-11-06T00:00:00Z")],
                              [comment(3, "login-b", "Yes, take them.", 0),
                               comment(3, "stranger", "spam", 5)], OWN_LOGINS)
        lines = out.splitlines()
        self.assertEqual(lines[0], "## o/hub")
        self.assertTrue(lines[1].startswith("- [b] updated PR #4"))
        self.assertTrue(lines[2].startswith("- [b] comment on #3: Yes, take them."))
        self.assertEqual(lines[3], "(1 item(s) of this team's own, not listed)")
        self.assertNotIn("spam", out)
        self.assertIn("ignored 1 item(s)", out)

    def test_shared_login_sorted_by_label_and_signature(self):
        out = self.run_digest([issue(5, "login-a", labels=["team:b"]),
                               issue(6, "login-a", body="text\n\nTeam: a\n")],
                              [comment(5, "login-a", "Done.\n\nTeam: b\n\n---\n_Generated_", 1),
                               comment(5, "login-a", "no signature", 2)], SHARED)
        self.assertIn("- [b] new issue #5", out)
        self.assertIn("- [b] comment on #5: Done.", out)
        self.assertNotIn("no signature", out)
        self.assertNotIn("#6", out.split("(")[0])
        self.assertIn("(2 item(s) of this team's own", out)

    def test_shared_login_seen_from_the_borrowing_team(self):
        out = self.run_digest([issue(5, "login-a", labels=["team:b"])],
                              [comment(5, "login-a", "unsigned, so team a's", 2)], SHARED, team="b")
        self.assertIn("- [a] comment on #5: unsigned, so team a's", out)
        self.assertIn("(1 item(s) of this team's own", out)

    def test_nothing_new(self):
        self.assertEqual(digest.render([("o/hub", [])], "a", OWN_LOGINS), "NOTHING NEW")
        own = [{"at": "t", "login": "login-a", "team": None, "line": "x"}]
        self.assertTrue(digest.render([("o/hub", own)], "a", OWN_LOGINS).startswith("NOTHING NEW\n"))

    def test_roster(self):
        self.assertEqual(digest.parse_roster("a=x, b=x"), {"a": "x", "b": "x"})
        self.assertEqual(digest.parse_roster("login-b"), {"login-b": "login-b"})

    def args(self, *argv):
        import argparse
        a = argparse.Namespace(config=None, team=None, me=None, roster=None)
        for k, v in zip(argv[::2], argv[1::2]):
            setattr(a, k, v)
        return a

    def test_older_form(self):
        a = self.args("config", "/nonexistent.json", "me", "login-a", "roster", "login-b")
        self.assertEqual(digest.settings(a), ("login-a", {"login-b": "login-b", "login-a": "login-a"}, []))

    def test_config_wins(self):
        import json
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"team": "a", "roster": SHARED, "notes": ["n1"]}, f)
        a = self.args("config", f.name, "me", "login-a", "roster", "login-b")
        self.assertEqual(digest.settings(a), ("a", SHARED, ["n1"]))
        os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
