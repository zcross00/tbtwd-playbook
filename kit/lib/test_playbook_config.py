"""Tests for playbook_config.py: kit/test.sh"""
import os
import subprocess
import sys
import tempfile
import unittest

import playbook_config as pc

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLE = os.path.join(HERE, "..", "example.playbook.toml")


class Load(unittest.TestCase):
    def test_a_missing_file_gives_the_defaults(self):
        cfg = pc.load("/nonexistent/.playbook.toml")
        self.assertEqual(cfg["board"]["iteration_fields"], ["Day", "Week"])
        self.assertEqual(cfg["queue"]["cost"], {"overflow": 5.0})

    def test_the_file_wins_and_keeps_the_defaults_it_leaves_out(self):
        with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
            f.write('[project]\nrepo = "o/r"\n[queue.cost]\n"hosted.yml" = 4.0\n')
        try:
            cfg = pc.load(f.name)
        finally:
            os.unlink(f.name)
        self.assertEqual(pc.owner_repo(cfg), ("o", "r"))
        self.assertEqual(cfg["queue"]["cost"], {"overflow": 5.0, "hosted.yml": 4.0})
        self.assertEqual(cfg["forecast"]["days"], 3)

    def test_the_repo_falls_back_to_github_repository(self):
        old = os.environ.get("GITHUB_REPOSITORY")
        os.environ["GITHUB_REPOSITORY"] = "a/b"
        try:
            self.assertEqual(pc.owner_repo(pc.load("/nonexistent")), ("a", "b"))
        finally:
            if old is None:
                del os.environ["GITHUB_REPOSITORY"]
            else:
                os.environ["GITHUB_REPOSITORY"] = old

    def test_the_example_reads(self):
        cfg = pc.load(EXAMPLE)
        self.assertEqual(cfg["hosted"]["workflows"][-1], ["board.yml", "schedule"])

    def test_one_setting_for_the_shell_scripts(self):
        r = subprocess.run([sys.executable, os.path.join(HERE, "playbook_config.py"), "ci.docs_only"],
                           capture_output=True, text=True, env={**os.environ, "PLAYBOOK_CONFIG": EXAMPLE})
        self.assertEqual(r.stdout, r"^docs/|\.md$")


if __name__ == "__main__":
    unittest.main()
