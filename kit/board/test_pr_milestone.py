import unittest

import pr_milestone as pm


def pr(number, body, milestone=None, labels=()):
    return {"number": number, "body": body, "milestone": {"number": milestone} if milestone else None,
            "labels": [{"name": n} for n in labels]}


ISSUES = {1: 17, 2: 17, 3: 23, 4: None}


class Plan(unittest.TestCase):
    def test_a_pr_gets_its_issues_milestone(self):
        self.assertEqual(pm.plan([pr(10, "x\n\nRefs #1")], ISSUES.get), [(10, 17)])

    def test_the_milestone_most_refs_are_in_wins(self):
        self.assertEqual(pm.plan([pr(10, "Refs #1, #2\nRefs #3")], ISSUES.get), [(10, 17)])

    def test_a_tie_or_no_milestone_sets_nothing(self):
        self.assertEqual(pm.plan([pr(10, "Refs #1 #3"), pr(11, "Refs #4"), pr(12, "no refs")], ISSUES.get), [])

    def test_a_pr_with_a_milestone_keeps_it(self):
        self.assertEqual(pm.plan([pr(10, "Refs #1", milestone=23)], ISSUES.get), [])

    def test_a_train_is_left_out(self):
        self.assertEqual(pm.plan([pr(10, "Train: #5 #6\n\nRefs #1"), pr(11, "Refs #1", labels=["train"])], ISSUES.get), [])

    def test_only_refs_lines_count(self):
        # "Closes"/"see #1" in prose isn't a ref; one issue ref'd twice counts once.
        self.assertEqual(pm.plan([pr(10, "see #3 and #3\nRefs #1")], ISSUES.get), [(10, 17)])
        self.assertEqual(pm.plan([pr(10, "Refs #3\nRefs #3 #1 #2")], ISSUES.get), [(10, 17)])


if __name__ == "__main__":
    unittest.main()
