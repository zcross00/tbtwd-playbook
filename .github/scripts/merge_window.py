#!/usr/bin/env python3
"""TBTWD Playbook merge window (CONTRIBUTING.md, "When changes merge").

Changes to the playbook merge only on Saturday from 11:00 America/Chicago
until the end of that Saturday, unless the PR is an emergency: labelled
`emergency` and with a line in its body starting "Emergency:" that quotes
the owner's words.

Sets a commit status named "merge-window" on each PR's head: success inside
the window or for an emergency, failure otherwise. Make "merge-window" a
required status check on main, and merges outside the window are blocked.

Usage:
  merge_window.py pr <number>   one PR (pull_request events)
  merge_window.py all           every open PR (the scheduled runs)
Needs GITHUB_TOKEN and GITHUB_REPOSITORY.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Chicago")
OPENS = dt.time(11, 0)  # Saturday, local time; open until Saturday ends
CONTEXT = "merge-window"
LABEL = "emergency"
EMERGENCY_LINE = re.compile(r"^\s*Emergency:\s*\S", re.IGNORECASE | re.MULTILINE)


def window_open(now: dt.datetime) -> bool:
    local = now.astimezone(TZ)
    return local.weekday() == 5 and local.time() >= OPENS


def verdict(now: dt.datetime, labels: list[str], body: str) -> tuple[str, str]:
    if LABEL in labels:
        if EMERGENCY_LINE.search(body or ""):
            return "success", "Emergency: may merge now"
        return "failure", 'Label "emergency" needs an "Emergency:" line quoting the owner'
    if window_open(now):
        return "success", "Saturday merge window is open"
    return "failure", "Merges wait for Saturday 11:00 America/Chicago"


def api(method: str, path: str, data=None):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}{path}",
        method=method,
        data=json.dumps(data).encode() if data is not None else None,
        headers={
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read() or b"null")


def mark(pr: dict, now: dt.datetime) -> None:
    labels = [l["name"] for l in pr.get("labels", [])]
    state, text = verdict(now, labels, pr.get("body") or "")
    api("POST", f"/statuses/{pr['head']['sha']}",
        {"state": state, "context": CONTEXT, "description": text[:140]})
    print(f"#{pr['number']}: {state} ({text})")


def main() -> int:
    now = dt.datetime.now(dt.timezone.utc)
    if sys.argv[1] == "pr":
        mark(api("GET", f"/pulls/{int(sys.argv[2])}"), now)
    else:
        for pr in api("GET", "/pulls?state=open&per_page=100"):
            mark(pr, now)
    return 0


if __name__ == "__main__":
    sys.exit(main())
