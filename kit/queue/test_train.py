"""Tests for train.sh (#880): python3 -m unittest discover -s kit/queue (kit/test.sh)"""
import os
import pathlib
import subprocess
import tempfile
import unittest

TRAIN = pathlib.Path(__file__).with_name("train.sh").resolve()


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


@unittest.skipIf(os.name == "nt", "train.sh runs in Code review's Linux container, not on the PC")
class Train(unittest.TestCase):
    """A bare origin with main and three PR heads: 1 and 3 touch their own
    files, 2 changes the line 1 changes."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = pathlib.Path(tmp.name)
        self.origin, self.work = root / "origin.git", root / "work"
        git(root, "init", "-q", "--bare", "-b", "main", str(self.origin))
        git(root, "clone", "-q", str(self.origin), str(self.work))
        w = self.work
        git(w, "config", "user.email", "t@t")
        git(w, "config", "user.name", "t")
        (w / "a.txt").write_text("base\n")
        git(w, "add", ".")
        git(w, "commit", "-qm", "base")
        git(w, "push", "-q", "origin", "HEAD:main")
        for pr, name, text in ((1, "a.txt", "one\n"), (2, "a.txt", "two\n"), (3, "c.txt", "three\n")):
            git(w, "checkout", "-q", "-B", f"pr{pr}", "origin/main")
            (w / name).write_text(text)
            git(w, "add", ".")
            git(w, "commit", "-qm", f"pr {pr}")
            git(w, "push", "-q", "origin", f"HEAD:refs/pull/{pr}/head")
        git(w, "checkout", "-q", "--detach", "origin/main")

    def train(self, *prs, bodies=None):
        env = dict(os.environ, TRAIN_REFS="0")
        if bodies:
            # A gh on PATH that answers each PR's body from bodies.
            bin_ = self.work.parent / "bin"
            bin_.mkdir()
            for pr, text in bodies.items():
                (bin_ / f"body{pr}").write_text(text)
            (bin_ / "gh").write_text(f'#!/bin/sh\ncat "{bin_}/body$(echo "$2" | sed "s|.*/||")"\n')
            (bin_ / "gh").chmod(0o755)
            env.update(TRAIN_REFS="1", PATH=f"{bin_}:{env['PATH']}")
        return subprocess.run(["bash", str(TRAIN), *map(str, prs)], cwd=self.work, env=env, capture_output=True, text=True)

    def test_refs_lines_carry_over_even_under_a_heading(self):
        out = self.train(1, 3, bodies={1: "Fixes things.\r\nRefs #852\r\n", 3: "## Refs #870, #871\nnot Refs #9\n"})
        self.assertEqual(out.returncode, 0, out.stderr)
        body = (self.work / ".git" / "train-body.md").read_text()
        self.assertTrue(body.endswith("\nRefs #852\nRefs #870, #871\n"), body)

    def test_members_merge_in_order_and_a_conflict_is_left_out(self):
        out = self.train(1, 2, 3)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("left out (conflict): 2", out.stdout)
        body = (self.work / ".git" / "train-body.md").read_text()
        self.assertTrue(body.startswith("Train: #1 #3\n"))
        log = git(self.work, "log", "--format=%s", "--first-parent", "origin/main..HEAD").splitlines()
        self.assertEqual([l.split(": ")[1] for l in log], ["merge #3", "merge #1"])
        # Each member's head is in the train, so GitHub shows it merged.
        for pr in (1, 3):
            head = git(self.work, "rev-parse", f"pr{pr}").strip()
            subprocess.run(["git", "merge-base", "--is-ancestor", head, "HEAD"], cwd=self.work, check=True)

    def test_a_second_train_today_gets_the_next_number(self):
        first = self.train(1).stdout.split(":")[0]
        git(self.work, "checkout", "-q", "--detach", "origin/main")
        second = self.train(3).stdout.split(":")[0]
        self.assertEqual((first[-2:], second[-2:]), ("-1", "-2"))

    def test_a_named_branch_carries_one_train_after_another(self):
        # Code review can push only its own branch, so each train reuses it.
        for prs in ((1,), (3,)):
            out = self.train("--push", "--branch", "cr", *prs)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertTrue(out.stdout.startswith("cr: "))
        pushed = git(self.work, "ls-remote", "origin", "refs/heads/cr").split()[0]
        self.assertEqual(pushed, git(self.work, "rev-parse", "HEAD").strip())
        # The second train starts from main again: #1 isn't in it.
        log = git(self.work, "log", "--format=%s", "--first-parent", "origin/main..cr").splitlines()
        self.assertEqual([l.split(": ")[1] for l in log], ["merge #3"])

    def test_no_clean_member_means_no_train(self):
        git(self.work, "checkout", "-q", "-B", "base", "origin/main")
        (self.work / "a.txt").write_text("moved\n")
        git(self.work, "commit", "-qam", "main moved")
        git(self.work, "push", "-q", "origin", "HEAD:main")
        out = self.train(1, 2)
        self.assertEqual(out.returncode, 1)
        self.assertIn("no PR merged cleanly", out.stderr)

    def test_a_dirty_tree_is_refused(self):
        (self.work / "a.txt").write_text("dirty\n")
        out = self.train(1)
        self.assertEqual(out.returncode, 2)


if __name__ == "__main__":
    unittest.main()
