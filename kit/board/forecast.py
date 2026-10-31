#!/usr/bin/env python3
"""Daily re-forecast of the open milestones' due dates (retro pick 9).

Zac agreed to the retro's ten picks on 2026-10-30 ("on the pick list, i agree
with all 10"). Pick 9: re-forecast daily from the last 3 days' measured pace,
not the planned 150k a thread, and have each closed milestone report its
forecast against its actual close. Of the 16 milestones closed by 10-31, all
closed before their 10-25 or 10-30 90% date (median 9 days) and 13 before
their 50% date (median 3 days), so one date from measured pace replaces the
50%/90% pair.

For each open milestone:
- pace: the estimate on its issues closed in the last 3 days, divided by 3;
- left: the estimate on its open issues, 60k for one with no estimate;
- forecast: today + left / pace (whole days, rounded up) + 1 day for
  verification and the playtest.

A milestone with less than MIN_SIGNAL closed in those 3 days has no pace of
its own (it hasn't started, waits on another milestone, or has a date set by
an outside plan, like m32 and m33), so its date is left alone and the line
says why. A description with a "Date fixed:" line is never moved either.

With --apply, an active milestone's due date becomes its forecast, and the
forecast line goes on top of its description, replacing only a line this tool
wrote earlier. A milestone closed in the last 14 days
whose due date isn't its close date gets a "Closed" line comparing the two,
then its due date set to the close date (Zac, 2026-10-30: closed = close
date).

Reads and writes through `gh api` where it's installed, else GH_TOKEN.
Without --apply it only prints what it would change.
"""
import datetime as dt
import json
import math
import os
import re
import shutil
import subprocess
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import milestones as ms_tool  # noqa: E402

CFG = ms_tool.CFG

DAYS = CFG["forecast"]["days"]
# Estimate (k) closed in DAYS before a milestone counts as having a pace:
# about one normal PR's worth (PROCESS sizes) over the window.
MIN_SIGNAL = CFG["forecast"]["min_signal"]
UNESTIMATED = CFG["forecast"]["unestimated"]
PLAYTEST_DAYS = CFG["forecast"]["playtest_days"]
CLOSED_LOOKBACK = CFG["forecast"]["closed_lookback"]
FIXED = re.compile(r"^Date fixed:", re.M)
# Due and close dates are the owner's days (project.utc_offset_hours). A fixed offset, because the PC runner's Windows Python has
# no time-zone database: in summer time it dates a 05:00-06:00 UTC close a
# day early, which only the closed lines show.
ZONE = dt.timezone(dt.timedelta(hours=CFG["project"]["utc_offset_hours"]))
# A `board: estimate=` above this was written in tokens, not thousands
# (#1349 says 100000): read it as thousands.
TOKENS = 5000


def k(est):
    """An estimate in thousands, or UNESTIMATED for none."""
    if not est:
        return UNESTIMATED
    return round(est / 1000) if est > TOKENS else est


def local_date(stamp):
    """The owner's date of a GitHub timestamp."""
    return dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(ZONE).date()


def pace(issues, ests, now):
    """Estimate (k) a day closed in the last DAYS days, or None under MIN_SIGNAL."""
    since = (now - dt.timedelta(days=DAYS)).isoformat(timespec="seconds")
    done = sum(k(ests.get(i["number"])) for i in issues
               if i["state"] == "closed" and i.get("state_reason") != "not_planned"
               and (i["closed_at"] or "") >= since)
    return done / DAYS if done >= MIN_SIGNAL else None


def left(issues, ests):
    return sum(k(ests.get(i["number"])) for i in issues if i["state"] == "open")


def forecast(left_k, rate, today):
    """The date the work left finishes at `rate`, plus the playtest day."""
    return today + dt.timedelta(days=math.ceil(left_k / rate) + PLAYTEST_DAYS)


# The line this tool writes; only such a line is ever replaced, so a thread's
# own lines (the groomings' "Forecast dates (...)", which can quote Zac) stay.
OWN_LINE = re.compile(r"^Forecast \(\d{4}-\d{2}-\d{2}, (?:kit|tools)/board/forecast\.py\)")


def forecast_line(today, d, left_k, rate):
    """The forecast line. It carries the date as "50% ... 90% ..." as well, so
    milestones.py's planning_dates reads it (the line is on top, so its dates
    are the first it finds)."""
    day = f"{d:%b} {d.day}"
    return (f"Forecast ({today.isoformat()}, kit/board/forecast.py): due {day} "
            f"(50% {day}, 90% {day}: one date, from measured pace). "
            f"{left_k}k left at {round(rate)}k a day, its pace over the last {DAYS} days, "
            f"plus {PLAYTEST_DAYS} day for verification and the playtest.")


def with_line(description, line):
    """The description with its first line replaced by `line` when this tool
    wrote that line, else with `line` on top."""
    desc = description or ""
    first, sep, rest = desc.partition("\n")
    if OWN_LINE.match(first):
        return line + sep + rest
    return line + ("\n\n" + desc if desc else "")


def closed_line(closed, due):
    days = (due - closed).days
    when = "on its due date" if days == 0 else (
        f"{abs(days)} day{'s' if abs(days) != 1 else ''} {'early' if days > 0 else 'late'}")
    return f"Closed {closed.isoformat()}, {when}: its last due date was {due:%b} {due.day}."


def plan_open(ms, issues, ests, now, today):
    """(new due date or None, new description or None, report line); `now`
    is a naive UTC datetime, `today` the owner's date."""
    desc = ms["description"] or ""
    due = dt.date.fromisoformat(ms["due_on"][:10]) if ms.get("due_on") else None
    head = f"#{ms['number']} {ms['title'][:50]}"
    todo = left(issues, ests)
    rate = pace(issues, ests, now)
    if FIXED.search(desc):
        return None, None, f"{head}: date fixed, kept {due}"
    if rate is None:
        return None, None, f"{head}: {todo}k left, under {MIN_SIGNAL}k closed in {DAYS} days, kept {due}"
    d = forecast(todo, rate, today)
    new_desc = with_line(desc, forecast_line(today, d, todo, rate))
    move = "" if d == due else f" (was {due})"
    return (d if d != due else None, new_desc if new_desc != desc else None,
            f"{head}: {todo}k left at {round(rate)}k a day, due {d}{move}")


def plan_closed(ms, today):
    """(new due date or None, new description or None, report line) for a
    recently closed milestone whose due date isn't its close date."""
    if not ms.get("closed_at") or not ms.get("due_on"):
        return None, None, None
    closed = local_date(ms["closed_at"])
    due = dt.date.fromisoformat(ms["due_on"][:10])
    if closed == due or (today - closed).days > CLOSED_LOOKBACK:
        return None, None, None
    line = closed_line(closed, due)
    desc = ms["description"] or ""
    return closed, desc.rstrip() + "\n\n" + line, f"#{ms['number']} {ms['title'][:50]}: {line}"


def send(path, data):
    """One PATCH of a repo API path."""
    if shutil.which("gh"):
        r = subprocess.run(["gh", "api", "-X", "PATCH", f"repos/{ms_tool.OWNER}/{ms_tool.REPO}{path}",
                            "--input", "-"], input=json.dumps(data), capture_output=True, text=True)
        if r.returncode:
            raise LookupError(r.stderr.strip() or r.stdout.strip())
        return
    req = urllib.request.Request(ms_tool.API + path, data=json.dumps(data).encode(), method="PATCH",
                                 headers={"Accept": "application/vnd.github+json",
                                          "Authorization": f"bearer {os.environ['GH_TOKEN']}",
                                          "User-Agent": "playbook-forecast"})
    with urllib.request.urlopen(req, timeout=30):
        pass


def due_on(d):
    return f"{d.isoformat()}T12:00:00Z"


def main(argv):
    apply = "--apply" in argv
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    today = dt.datetime.now(ZONE).date()
    changes = []
    for ms in sorted(ms_tool.get("/milestones?state=open&per_page=100"), key=lambda m: m["number"]):
        issues = [i for i in ms_tool.get(f"/issues?milestone={ms['number']}&state=all&per_page=100")
                  if "pull_request" not in i]
        ests = {i["number"]: ms_tool.estimate(
            [{"body": i["body"] or ""}] + ms_tool.get(f"/issues/{i['number']}/comments?per_page=100"))
            for i in issues}
        d, desc, report = plan_open(ms, issues, ests, now, today)
        print(report)
        changes.append((ms["number"], d, desc))
    for ms in ms_tool.get("/milestones?state=closed&sort=due_on&direction=desc&per_page=100"):
        d, desc, report = plan_closed(ms, today)
        if report:
            print(report)
            changes.append((ms["number"], d, desc))
    if not apply:
        print("(dry run: --apply writes these)")
        return 0
    for number, d, desc in changes:
        data = {}
        if d:
            data["due_on"] = due_on(d)
        if desc:
            data["description"] = desc
        if data:
            send(f"/milestones/{number}", data)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
