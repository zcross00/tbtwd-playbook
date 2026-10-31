#!/usr/bin/env python3
"""Give each open PR the milestone of the issues it refs, so the PR list and
the board show which milestone each PR serves.

PROCESS keeps milestones on issues, and a PR names its issues on `Refs #N`
lines, so a PR never got a milestone unless its thread set one by hand: on
10-30, 50 of the last 60 merged PRs and 10 of 12 open ones had none. This sets
an open PR's milestone from its refs: the milestone most of its ref'd issues
are in, when exactly one is ahead. A PR that already has a milestone keeps it,
and so does a PR that refs nothing in a milestone (a docs PR, an infra fix
with no issue). A merge train (#880) is left out: its members can be in
several milestones, and each member carries its own.

The kit-pr-milestone workflow runs it on the light runner
when a PR is opened, edited, reopened or marked ready, over every open PR, so
it also catches PRs opened before it. `--closed N` looks at the N most recently
merged PRs as well, once, to backfill. Without `--apply` it only prints.

Needs GH_TOKEN (issues and pull-requests write, to apply).
"""
import argparse
import collections
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import playbook_config  # noqa: E402

CFG = playbook_config.load()
REPO = "/".join(playbook_config.owner_repo(CFG))
API = os.environ.get("GITHUB_API_URL", "https://api.github.com")


def refs(body):
    """Issue numbers on the body's "Refs" lines (the queue's reading, #1235)."""
    nums = []
    for line in (body or "").splitlines():
        if re.match(r"\s*refs?\b", line, re.I):
            nums += [int(n) for n in re.findall(r"#(\d+)", line)]
    return nums


def is_train(pr):
    """A train PR names its members on a "Train:" line (kit/queue/train.sh)."""
    return any(line.startswith("Train:") for line in (pr.get("body") or "").splitlines()) or any(
        label["name"] == "train" for label in pr.get("labels", []))


def pick(milestones):
    """The milestone most of these are in (None ignored), or None on a tie."""
    counts = collections.Counter(m for m in milestones if m is not None).most_common(2)
    if not counts or (len(counts) == 2 and counts[0][1] == counts[1][1]):
        return None
    return counts[0][0]


def plan(prs, milestone_of):
    """(PR number, milestone number) for each PR to set. milestone_of(issue)
    gives an issue's milestone number, or None."""
    out = []
    for pr in prs:
        if pr.get("milestone") or is_train(pr):
            continue
        nums = [n for n in refs(pr.get("body")) if n != pr["number"]]
        m = pick(milestone_of(n) for n in dict.fromkeys(nums))
        if m is not None:
            out.append((pr["number"], m))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--closed", type=int, default=0, help="also the N most recently merged PRs")
    args = ap.parse_args()
    token = os.environ["GH_TOKEN"]

    def call(path, method="GET", data=None):
        req = urllib.request.Request(
            f"{API}/repos/{REPO}/{path}", method=method,
            data=json.dumps(data).encode() if data is not None else None,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)

    prs = call("pulls?state=open&per_page=100")
    if args.closed:
        closed = call(f"pulls?state=closed&sort=updated&direction=desc&per_page={min(args.closed, 100)}")
        prs += [pr for pr in closed if pr.get("merged_at")]
    cache = {}

    def milestone_of(n):
        if n not in cache:
            try:
                cache[n] = (call(f"issues/{n}").get("milestone") or {}).get("number")
            except Exception as e:  # noqa: BLE001 - an unreadable ref counts as none
                print(f"#{n}: not read ({e})", flush=True)
                cache[n] = None
        return cache[n]

    todo = plan(prs, milestone_of)
    for number, m in todo:
        print(f"#{number}: milestone {m}{'' if args.apply else ' (dry run)'}", flush=True)
        if args.apply:
            call(f"issues/{number}", "PATCH", {"milestone": m})
    print(f"{len(todo)} PRs {'set' if args.apply else 'to set'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
