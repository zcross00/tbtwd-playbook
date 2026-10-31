"""Tests for paperwork.py's PR paperwork check: kit/test.sh"""
import unittest

import paperwork as p

ISSUES = {
    1: {"number": 1, "milestone": {"number": 13}, "labels": []},
    2: {"number": 2, "milestone": None, "labels": []},
    3: {"number": 3, "milestone": {"number": 13}, "labels": [{"name": "verification"}]},
    4: {"number": 4, "milestone": {"number": 13}, "labels": [{"name": "deferred gate"}]},
    5: {"number": 5, "pull_request": {}},
}
COMMENTS = {1: ["Estimate 60k.", "groomed: approved (coordinator)"], 2: ["groomed: approved (coordinator)"]}
CODE = ["sim/src/lib.rs"]


def pr(body, title="A change", number=10, **kw):
    return {"number": number, "title": title, "body": body, **kw}


def check(body, files=CODE, **kw):
    return p.problems(pr(body, **kw), files, ISSUES.get, lambda n: COMMENTS.get(n, []))


class Paperwork(unittest.TestCase):
    def test_a_groomed_issue_in_a_milestone_is_ok(self):
        self.assertEqual(check("Does x.\n\nRefs #1\n- ask: test_x"), [])

    def test_a_closing_word_is_flagged_in_title_or_body(self):
        self.assertEqual(len(check("Refs #1\nThis fixes #1.")), 1)
        self.assertEqual(len(check("Refs #1", title="Closes #1: x")), 1)
        # "the fix in #N" is the playbook's way to mention one, and isn't flagged.
        self.assertEqual(check("Refs #1\nBuilds on the fix in #1."), [])

    def test_a_code_pr_needs_a_refs_line_and_a_docs_pr_does_not(self):
        self.assertEqual(check("No issue."), ["no `Refs #N` line: a code PR refs its issue (playbook/04-lifecycle.md)"])
        self.assertEqual(check("No issue.", files=["docs/PROCESS.md", "README.md"]), [])

    def test_no_milestone_and_no_grooming(self):
        self.assertEqual(check("Refs #2"), ["#2: no milestone"])
        out = check("Refs #6")
        self.assertIn("#6: not readable", out)

    def test_verification_and_deferred_gate_skip_grooming(self):
        self.assertEqual(check("Refs #3\nRefs #4"), [])

    def test_a_ref_to_a_pr_is_left_alone(self):
        self.assertEqual(check("Refs #1, #5"), [])

    def test_a_loosened_gate_needs_its_deferred_gate_issue(self):
        self.assertEqual(check("Refs #1\nLoosens the f2 floor to 20%."),
                         ["loosens or defers a gate but names no `deferred gate` issue (playbook/07-gates.md)"])
        self.assertEqual(check("Refs #1\nLoosens the f2 floor to 20%, tracked in #4."), [])

    def test_drafts_and_trains_are_skipped(self):
        self.assertEqual(check("fixes #2", draft=True), [])
        self.assertEqual(check("Train: #11 #12\n\nfixes #2"), [])


if __name__ == "__main__":
    unittest.main()
