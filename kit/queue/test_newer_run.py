"""Tests for newer_run.py: python3 -m unittest discover -s kit/queue (kit/test.sh)"""
import unittest

import newer_run as n

HEAD = "066bca0"
CI, OTHER = 1, 2


def job(name, status, conclusion=None):
    return {"name": name, "status": status, "conclusion": conclusion}


DRAFT = [job("files", "completed", "skipped"), job("queue", "completed", "skipped"), job("full", "completed", "failure")]
DECIDING = [job("files", "in_progress"), job("queue", "queued"), job("full", "queued")]
WAITING = [job("files", "completed", "success"), job("queue", "in_progress"), job("full", "queued")]
PASSED = [job("files", "completed", "success"), job("queue", "completed", "success"), job("full", "in_progress")]
DOCS = [job("files", "completed", "success"), job("queue", "completed", "skipped"), job("full", "completed", "success")]
CONFLICT = [job("files", "completed", "success"), job("queue", "completed", "failure"), job("full", "completed", "failure")]
CANCELLED = [job("files", "completed", "success"), job("queue", "completed", "cancelled"), job("full", "completed", "cancelled")]


class Fake:
    """The API: runs for HEAD as (id, workflow), and each run's jobs, either
    fixed or a list handed out one poll at a time (the last one repeating)."""

    def __init__(self, runs, jobs):
        self.runs = [{"id": rid, "workflow_id": wf} for rid, wf in runs]
        self.jobs = jobs
        self.reads = {}

    def __call__(self, path):
        if path.startswith("actions/runs?"):
            assert f"head_sha={HEAD}" in path
            return {"workflow_runs": self.runs}
        rid = int(path.split("/")[2].split("?")[0])
        if path.endswith(f"actions/runs/{rid}"):
            return next(r for r in self.runs if r["id"] == rid)
        jobs = self.jobs[rid]
        if jobs and isinstance(jobs[0], list):
            i = self.reads.get(rid, 0)
            self.reads[rid] = i + 1
            jobs = jobs[min(i, len(jobs) - 1)]
        return {"jobs": jobs}


def decide(api, me):
    sleeps = []
    run = n.decide(api, me, HEAD, sleep=sleeps.append)
    return (run["id"] if run else None), len(sleeps)


class Decide(unittest.TestCase):
    def test_alone_goes_on(self):
        self.assertEqual(decide(Fake([(10, CI)], {}), 10), (None, 0))

    def test_older_runs_dont_count(self):
        # #776: the draft run came first, so its failure was older than the
        # ready run's full, and the ready run goes on.
        api = Fake([(9, CI), (10, CI)], {9: DRAFT})
        self.assertEqual(decide(api, 10), (None, 0))

    def test_steps_aside_for_a_newer_run_checking_the_head(self):
        # #783: the draft run was made after the ready run; reading the draft
        # state live, it now checks the head, and only its full will count.
        for jobs in (WAITING, PASSED):
            with self.subTest(jobs=jobs[1]):
                self.assertEqual(decide(Fake([(10, CI), (11, CI)], {11: jobs}), 10), (11, 0))

    def test_waits_for_a_newer_run_still_deciding(self):
        api = Fake([(10, CI), (11, CI)], {11: [DECIDING, DECIDING, WAITING]})
        self.assertEqual(decide(api, 10), (11, 2))

    def test_newer_runs_not_checking_leave_it_to_this_one(self):
        # A docs-only head, the PR made a draft again, a conflict, a cancel.
        for jobs in (DRAFT, DOCS, CONFLICT, CANCELLED):
            with self.subTest(jobs=jobs[1]):
                self.assertEqual(decide(Fake([(10, CI), (11, CI)], {11: jobs}), 10), (None, 0))

    def test_gives_up_waiting_and_goes_on(self):
        api = Fake([(10, CI), (11, CI)], {11: DECIDING})
        self.assertEqual(decide(api, 10), (None, n.WAIT_POLLS))

    def test_other_workflows_dont_count(self):
        api = Fake([(10, CI), (11, OTHER)], {11: PASSED})
        self.assertEqual(decide(api, 10), (None, 0))

    def test_a_run_from_before_the_queue_counts_as_checking(self):
        api = Fake([(10, CI), (11, CI)], {11: [job("full", "in_progress")]})
        self.assertEqual(decide(api, 10), (11, 0))


if __name__ == "__main__":
    unittest.main()
