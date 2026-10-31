#!/usr/bin/env python3
"""Daily burn-down of the open GitHub milestones (#716, PROCESS "Estimating").

One line per open milestone: issues open and closed, the estimate left (the
newest `board: estimate=N` on each open issue, read the same way as sync.py),
PRs merged since grooming that ref its issues, issues filed after the
grooming day (scope growth), open `verification` corrections, the 50% and
90% planning dates from the description's Dates paragraph, the committed due
date, and ON TRACK, AT RISK or NOT DATED. An open milestone past its 50%
date, or whose estimate left at its rate runs past it, says so as well,
unless its "Signed off:" line has the date of the owner's pass and it only waits
on merges. A committed milestone also shows
its run of green nightly main runs (#414) since its last issue closed.

Reads the GitHub API through `gh api` (authenticated) where it's installed;
the public API's 60 calls an hour are too few for a full run.
Dev process runs it daily and posts the output in the morning report.
"""
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sync import board_values, CFG, OWNER, REPO  # noqa: E402

API = f"https://api.github.com/repos/{OWNER}/{REPO}"
# #414's nightly run of the full checks on main: ci.yml's schedule.
NIGHTLY = f"/actions/workflows/{CFG['milestones']['nightly_workflow']}/runs?branch=main&event=schedule&per_page=30"
# Thousands of output tokens one milestone thread burns a day, used until a
# milestone has a day of its own history: about 4 PRs a day at about 40k each
# (the four milestone groomings of 2026-10-25).
PLANNED_RATE = CFG["milestones"]["planned_rate"]
MONTHS = {m: i for i, m in enumerate(
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
DATE = r"([A-Z][a-z]{2})[a-z]*\.? (\d{1,2})"
# The sign-off line milestone descriptions end with ("Signed off: not yet"),
# once it carries the date of the owner's pass.
SIGNED_OFF = re.compile(r"^Signed off: \d{4}-\d{2}-\d{2}", re.M)
REFS = re.compile(r"\bRefs?\b([^\n]*)", re.I)


def planning_dates(description, today):
    """The 50% and 90% dates in a description, as dates in today's year
    (or next year's for a month already well past), or None."""
    out = []
    for pct in ("50", "90"):
        m = re.search(pct + r"%:?\s*" + DATE, description or "")
        if not m or m.group(1) not in MONTHS:
            out.append(None)
            continue
        d = dt.date(today.year, MONTHS[m.group(1)], int(m.group(2)))
        out.append(d.replace(year=d.year + 1) if (today - d).days > 180 else d)
    return tuple(out)


def groomed_on(description, created):
    """The date in the Dates paragraph (the grooming), else the milestone's
    creation date."""
    i = (description or "").find("Dates")
    m = re.search(r"\d{4}-\d{2}-\d{2}", description[i:]) if i >= 0 else None
    return dt.date.fromisoformat(m.group(0)) if m else created


def estimate(comments):
    """The newest estimate from an issue's body and comments, or None."""
    v = board_values(comments).get("estimate")
    return int(v) if v and v.isdigit() else None


def refs(body):
    """Issue numbers a PR body refs (`Refs #1, #2`)."""
    return {int(n) for line in REFS.findall(body or "") for n in re.findall(r"#(\d+)", line)}


def at_risk(left, rate, today, d90):
    """True when the estimate left, at `rate` a day, runs past the 90% date."""
    if d90 is None:
        return False
    return today + dt.timedelta(days=left / max(rate, 1)) > d90


def green_streak(runs, since):
    """Successful nightly runs in a row, newest first, completed after `since`
    (a datetime); stops at the first failure."""
    n = 0
    for r in runs:
        if r["conclusion"] == "success" and r["updated_at"] >= since:
            n += 1
        elif r["conclusion"] in (None, "cancelled", "skipped"):
            continue
        else:
            break
    return n


def fetch(path):
    """One GET of a repo API path, through `gh api` when it's installed (it's
    authenticated on the PC and in the containers), else the public API."""
    if shutil.which("gh"):
        r = subprocess.run(["gh", "api", f"repos/{OWNER}/{REPO}{path}"], capture_output=True,
                           text=True, encoding="utf-8")
        if r.returncode:
            raise LookupError(r.stderr.strip() or r.stdout.strip())
        return json.loads(r.stdout)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "playbook-milestones"}
    # Self-hosted runners may have no gh; the job's token is enough.
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"bearer {os.environ['GH_TOKEN']}"
    req = urllib.request.Request(API + path, headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise LookupError(f"{e.code} {path}") from e


def nightly(runs):
    """One line on the nightly main run: the last night and the green run."""
    done = [r for r in runs or [] if r["status"] == "completed"]
    if not done:
        return "Nightly main run: none yet (#414)"
    last = done[0]
    return (f"Nightly main run: last {last['created_at'][:10]} {last['conclusion']}, "
            f"{green_streak(done, '')} green in a row")


def get(path):
    """Every page of a list (`&page=N` until a short page; GitHub's own next
    links name the repo by id, which the containers' proxy refuses)."""
    out, n = [], 1
    while True:
        page = fetch(f"{path}&page={n}")
        if isinstance(page, dict):
            return page
        out += page
        if len(page) < 100:
            return out
        n += 1


def parts(ms, issues, comments, prs, runs, today):
    """The burn-down line's parts: the title and counts first, the 50%/90%
    dates sixth, then the due date and the verdicts (kit/wiki reads them)."""
    desc = ms["description"] or ""
    start = groomed_on(desc, dt.date.fromisoformat(ms["created_at"][:10]))
    d50, d90 = planning_dates(desc, today)
    open_ = [i for i in issues if i["state"] == "open"]
    ests = {i["number"]: estimate(comments.get(i["number"], [])) for i in open_}
    left = sum(e for e in ests.values() if e)
    unest = sum(e is None for e in ests.values())
    nums = {i["number"] for i in issues}
    merged = sum(1 for p in prs if p["merged_at"] and p["merged_at"][:10] >= start.isoformat()
                 and refs(p["body"]) & nums)
    added = sum(i["created_at"][:10] > start.isoformat() for i in issues)
    fixes = sum(any(l["name"] == "verification" for l in i["labels"]) for i in open_)
    done = sum(estimate(comments.get(i["number"], [])) or 0 for i in issues if i["state"] == "closed")
    days = (today - start).days
    rate = done / days if days >= 1 and done else PLANNED_RATE
    due = ms.get("due_on")
    parts = [f"#{ms['number']} {ms['title']}: {len(open_)} open, {len(issues) - len(open_)} closed",
             f"{left}k left" + (f" (+{unest} unestimated)" if unest else ""),
             f"{merged} PRs merged since {start:%b %d}", f"{added} added", f"{fixes} corrections open",
             "50% " + (f"{d50:%b %d}" if d50 else "?") + " / 90% " + (f"{d90:%b %d}" if d90 else "?")]
    if due:
        parts.append(f"COMMITTED {due[:10]}")
        if not open_:
            last = max(i["closed_at"] for i in issues)
            parts.append(f"{green_streak(runs, last)} green nights" if runs is not None
                         else "no nightly run yet (#414)")
    parts.append("NOT DATED" if d90 is None else "AT RISK" if at_risk(left, rate, today, d90) else "ON TRACK")
    # The due date is the 90% date, so it mustn't become slack (Zac, 2026-10-30
    # 00:11: "just want to make sure we're not giving ourselves too much time
    # if it's not efficient"): an open milestone is held to its 50% date too.
    if open_ and d50 is not None:
        if SIGNED_OFF.search(desc):
            parts.append("PLAYTEST PASSED, WAITING ON MERGE")
        elif today > d50:
            parts.append(f"PAST ITS 50% DATE by {(today - d50).days} days")
        elif at_risk(left, rate, today, d50):
            parts.append("BEHIND ITS 50% DATE")
    return parts


def line(ms, issues, comments, prs, runs, today):
    return ", ".join(parts(ms, issues, comments, prs, runs, today))


def main():
    today = dt.date.today()
    mss = get("/milestones?state=open&per_page=100")
    prs = get("/pulls?state=closed&sort=updated&direction=desc&per_page=100")
    try:
        runs = get(NIGHTLY)["workflow_runs"]
    except LookupError:
        runs = None
    print(nightly(runs))
    for ms in sorted(mss, key=lambda m: m["number"]):
        issues = [i for i in get(f"/issues?milestone={ms['number']}&state=all&per_page=100")
                  if "pull_request" not in i]
        comments = {i["number"]: [{"body": i["body"] or ""}] + get(f"/issues/{i['number']}/comments?per_page=100")
                    for i in issues}
        print(line(ms, issues, comments, prs, runs, today))


if __name__ == "__main__":
    sys.exit(main())
