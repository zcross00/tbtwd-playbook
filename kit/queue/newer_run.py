#!/usr/bin/env python3
"""Fail a PR's run when a newer run of the same workflow checks the same head.

GitHub reads a head's required `full` from its newest check suite: a failed
`full` in an older run doesn't block a merge, but one in the newest does. On
2026-10-25 a push to a draft and its marking ready, a minute apart, made the
ready run first and the draft run second for #783 and #788. The draft run's
`full` failed ("a draft doesn't run the checks"), and that failure, being
newest, blocked both PRs after their ready runs went green.

ci.yml's `files` job now reads whether the PR is a draft from the API, not
from the event, so a draft run that starts after the PR was marked ready
checks the head like a ready run. Two runs then check one head, and only the
newest one's `full` counts. ci.yml's `queue` job runs this once its wait
(pc_queue.py) is over: when a newer run of this workflow for the same head is
checking it (its `queue` job is waiting or passed), this run fails rather than spend
a PC run on a result GitHub won't read. Its wait wasn't wasted: the newer run
sorts behind this one in pc_queue.py, so it waited behind it and goes next.

A newer run whose `files` job hasn't finished yet hasn't decided whether it
checks the head, so this waits for it, up to WAIT_POLLS polls. A newer run
whose `queue` job was skipped (a docs-only head, or the PR made a draft
again), failed or was cancelled leaves this one to go on.

Needs GH_TOKEN (actions read), GITHUB_REPOSITORY, GITHUB_RUN_ID and HEAD_SHA
(the head the run was started for). When the API can't be read, the run goes
on: a wasted PC run is better than none.
"""
import json
import os
import sys
import time
import urllib.request

POLL_SECS = 15
WAIT_POLLS = 20


def newer_runs(get, me, head):
    """Runs of this run's workflow for `head`, started after this one."""
    mine = get(f"actions/runs/{me}")
    runs = get(f"actions/runs?head_sha={head}&per_page=100")["workflow_runs"]
    return [r for r in runs if r["workflow_id"] == mine["workflow_id"] and r["id"] > me]


def checking(jobs):
    """Whether a run checks its head: True, False, or None while undecided.

    A run's `files` job decides; until it has finished, the run's `queue` job
    can still be skipped. A `queue` job that was skipped, failed or cancelled
    leaves the head to this run. A run with no `queue` job (from before it
    existed) counts as checking.
    """
    by_name = {j["name"]: j for j in jobs}
    files, queue = by_name.get("files"), by_name.get("queue")
    if queue is None:
        return True
    if files is not None and files["status"] != "completed":
        return None
    return queue["status"] != "completed" or queue.get("conclusion") == "success"


def decide(get, me, head, sleep=time.sleep):
    """The newer run checking `head`, or None when this run should go on."""
    for _ in range(WAIT_POLLS):
        undecided = False
        for run in newer_runs(get, me, head):
            jobs = get(f"actions/runs/{run['id']}/jobs?per_page=100")["jobs"]
            state = checking(jobs)
            if state:
                return run
            undecided = undecided or state is None
        if not undecided:
            return None
        sleep(POLL_SECS)
    return None


def main():
    api = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    repo = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GH_TOKEN"]

    def get(path):
        req = urllib.request.Request(
            f"{api}/repos/{repo}/{path}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)

    head = os.environ["HEAD_SHA"]
    try:
        run = decide(get, int(os.environ["GITHUB_RUN_ID"]), head)
    except Exception as e:  # noqa: BLE001 - any API failure lets the run go
        print(f"newer runs not read: {e}; checking the head anyway")
        return 0
    if run is None:
        print(f"no newer run checks {head[:7]}")
        return 0
    print(f"Run {run['id']} started after this one and checks the same head ({head[:7]}).")
    print("GitHub reads only the newest run's full, so that run checks it and this one stops.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
