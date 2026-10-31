#!/usr/bin/env python3
"""Hosted Actions minutes and dollars, billed, for today and the month so far.

    python3 kit/churn/minutes.py            # today and this month
    python3 kit/churn/minutes.py --days 7   # also each of the last 7 days

The repo is private, so every job on GitHub's machines is billed, rounded up
to a whole minute; jobs on the self-hosted PC runner cost nothing. On
2026-10-22 hosted jobs billed about 3,100 minutes in one day, against 3,000 a
month, and nobody saw it until the budget was gone. This reads it back from
the API with `gh` and costs no hosted minutes itself: run it from a session,
never from a workflow. It exits 1 when any day in the window is over the
limit (--limit, default 500: about four hosted full runs), so a session can
watch it.

Hosted minutes are paid for out of a monthly budget (hosted.budget in
.playbook.toml), once the plan's included minutes are spent. Dollars are counted
at the rates in RATE, per minute and rounded up per job as GitHub bills. Past
WARN of the budget it warns and exits 1; past STOP it says to start no new
hosted work. It also exits 1 when
the latest board sync failed, and counts today's failed syncs: on 2026-10-23
every sync failed for 8 hours and nothing said so (#560). And it exits 1 when
the latest sync skipped a board: line the board can't take, naming each.
"""
import argparse
import collections
import concurrent.futures
import datetime as dt
import json
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import playbook_config  # noqa: E402

CFG = playbook_config.load()
REPO = "/".join(playbook_config.owner_repo(CFG))
# Dollars a minute on a 2-core hosted runner. GitHub's list prices, at the
# higher figure until a bill shows lower.
RATE = {"windows": 0.016, "macos": 0.08, "linux": 0.008}
# hosted.budget, warn and stop in .playbook.toml, in dollars a month.
BUDGET = CFG["hosted"]["budget"]
WARN, STOP = CFG["hosted"]["warn"], CFG["hosted"]["stop"]
# GitHub returns at most this many runs for a filtered search, and says
# nothing when it stops: in October a month's query (2,500 runs) came back as
# the newest 1,000, about a day and a half.
CAP = 1000
# The workflows that run jobs on GitHub's machines, and the event that sends
# them there (board.yml runs on the PC's light runner except its schedule).
# The month's spend is read from these; every run of the last --days days is
# read too, one day at a time, so a hosted job anywhere else still shows.
HOSTED = tuple((wf, event or None) for wf, event in CFG["hosted"]["workflows"])
# ci.yml runs its full checks on a hosted machine when the PC's line is long
# (#1124), and marks each such run with this artifact (kit/queue/pc_queue.py).
OVERFLOW_ARTIFACT = "hosted-full"


def gh(path):
    out = subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def when(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def runs(path, query):
    """Every run the query matches. Exits rather than count a capped list."""
    try:
        first = gh(f"{path}?per_page=100&{query}")
    except subprocess.CalledProcessError as e:
        if "404" in e.stderr:  # a workflow not on main yet has no runs
            return []
        raise
    total = first["total_count"]
    if total >= CAP:
        sys.exit(f"RUN QUERY CAPPED: {path}?{query} matches {total} runs, and GitHub lists {CAP} at most")
    out, page = first["workflow_runs"], 1
    while len(out) < total:
        page += 1
        batch = gh(f"{path}?per_page=100&page={page}&{query}")["workflow_runs"]
        if not batch:
            break
        out += batch
    return out


def overflow_runs(since):
    """ci.yml's runs sent to a hosted machine since `since`, by their artifact."""
    found = gh(f"repos/{REPO}/actions/artifacts?name={OVERFLOW_ARTIFACT}&per_page=100")["artifacts"]
    ids = {a["workflow_run"]["id"] for a in found if a["created_at"][:10] >= since}
    return [gh(f"repos/{REPO}/actions/runs/{i}") for i in sorted(ids)]


def source(run):
    """The HOSTED entry a run belongs to, or None."""
    for wf, event in HOSTED:
        if run["path"].endswith("/" + wf) and event in (None, run["event"]):
            return wf, event
    return None


def skipped_lines(run_id):
    """The board: lines a sync skipped, from its warning annotations (kit/board/sync.py)."""
    out = []
    for j in gh(f"repos/{REPO}/actions/runs/{run_id}/jobs?per_page=100")["jobs"]:
        for n in gh(f"repos/{REPO}/check-runs/{j['id']}/annotations?per_page=100"):
            if n.get("title") == "board line skipped":
                out.append(n["message"])
    return out


def hosted_jobs(run):
    jobs = gh(f"repos/{REPO}/actions/runs/{run['id']}/jobs?per_page=100")["jobs"]
    out = []
    for j in jobs:
        # Hosted jobs run in the "GitHub Actions" runner group. A job cancelled
        # before a runner took it has no group; it's hosted only if it asked
        # for a hosted image. `self-hosted` can't tell: the PC's queue runners
        # carry only `queue`.
        group = j.get("runner_group_name")
        if group:
            self_hosted = group != "GitHub Actions"
        else:
            self_hosted = not any(l.startswith(("ubuntu-", "windows-", "macos-")) for l in j.get("labels", []))
        if self_hosted or not j.get("started_at") or not j.get("completed_at"):
            continue
        secs = (when(j["completed_at"]) - when(j["started_at"])).total_seconds()
        if secs > 0:
            out.append((j["started_at"][:10], f"{run['name']}/{j['name']}", math.ceil(secs / 60), os_of(j)))
    return out


def os_of(job):
    """windows, macos or linux, from the image the job asked for or ran on."""
    names = " ".join(job.get("labels", []) + [job.get("runner_name") or ""]).lower()
    for os_ in ("windows", "macos"):
        if os_ in names:
            return os_
    return "linux"


def dollars(jobs, since):
    return sum(m * RATE[o] for d, _, m, o in jobs if d >= since)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--days", type=int, default=1)
    ap.add_argument("--limit", type=int, default=500, help="billed minutes a day that count as a runaway")
    a = ap.parse_args()
    today = dt.datetime.now(dt.timezone.utc).date()
    first = min(today.replace(day=1), today - dt.timedelta(days=a.days - 1))
    days = [str(today - dt.timedelta(days=i)) for i in range(a.days)]
    hosted_runs = [r for wf, event in HOSTED
                   for r in runs(f"repos/{REPO}/actions/workflows/{wf}/runs",
                                 f"created=%3E%3D{first}" + (f"&event={event}" if event else ""))]
    hosted_runs += overflow_runs(str(first))
    sent = {r["id"] for r in hosted_runs}
    day_runs = [r for d in days for r in runs(f"repos/{REPO}/actions/runs", f"created={d}")]
    others = [r for r in day_runs if source(r) is None and r["id"] not in sent]
    with concurrent.futures.ThreadPoolExecutor(16) as pool:
        jobs = [j for js in pool.map(hosted_jobs, hosted_runs) for j in js]
        stray = [j for js in pool.map(hosted_jobs, others) for j in js]
    jobs += stray
    by_day = collections.Counter()
    by_job = collections.Counter()
    for day, name, mins, _ in jobs:
        by_day[day] += mins
        if day == str(today):
            by_job[name] += mins
    month = sum(m for d, m in by_day.items() if d >= str(today.replace(day=1)))
    print(f"hosted minutes billed: today {by_day[str(today)]}, {today:%B} so far {month}")
    spent = dollars(jobs, str(today.replace(day=1)))
    # Only HOSTED's workflows count before the --days window: ci.yml's hosted
    # jobs of 2026-10-22, before the budget, aren't in the month.
    print(f"hosted dollars: today ${dollars(jobs, str(today)):.2f}, {today:%B} so far ${spent:.2f} of ${BUDGET:.0f}")
    if spent >= STOP:
        print(f"HOSTED BUDGET STOP: ${spent:.2f} this month, past ${STOP:.0f}; start no hosted work")
    elif spent >= WARN:
        print(f"HOSTED BUDGET WARNING: ${spent:.2f} this month, past ${WARN:.0f}")
    for d in days[1:]:
        print(f"  {d}: {by_day[d]}")
    if by_job:
        print("today by job: " + ", ".join(f"{n} {m}" for n, m in by_job.most_common(6)))
    if stray:
        print("HOSTED JOBS OUTSIDE HOSTED: " + ", ".join(sorted({n for _, n, _, _ in stray})) + " (add the workflow to HOSTED)")
    board = sorted((r["created_at"], r["conclusion"], r["id"]) for r in day_runs
                   if r["name"] == "board" and r["conclusion"] in ("success", "failure"))
    failed = [t for t, c, _ in board if c == "failure" and t[:10] == str(today)]
    broken = bool(board) and board[-1][1] == "failure"
    if broken:
        print(f"BOARD SYNC FAILED: the latest sync, at {board[-1][0][11:16]} UTC, failed ({len(failed)} failed today)")
    elif failed:
        print(f"board sync: {len(failed)} failed today, the latest at {board[-1][0][11:16]} UTC passed")
    # The latest sync reads every issue changed in 14 days, so its skipped
    # lines are all the board: lines the board can't take right now.
    skipped = skipped_lines(board[-1][2]) if board and not broken else []
    if skipped:
        print(f"BOARD LINES SKIPPED: {len(skipped)} in the latest sync, at {board[-1][0][11:16]} UTC: " + "; ".join(skipped))
    over = [d for d in days if by_day[d] > a.limit]
    if over:
        print(f"OVER {a.limit} a day on {', '.join(over)}")
    return 1 if over or broken or skipped or stray or spent >= WARN else 0


if __name__ == "__main__":
    sys.exit(main())
