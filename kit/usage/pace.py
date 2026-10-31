#!/usr/bin/env python3
"""Weekly usage pace (Zac, 2026-10-25): +7% every 12 h from the reset, 91% by the
last 12 h, 9% kept in reserve. Reads USAGE_SNAPSHOTS (default ./snapshots.csv:
taken, cost_usd, zac_reading_pct as the owner's reading).

Nothing we can reach shows the plan's usage %, so it's estimated: the project
sessions' summed cost_usd (get_session's usage), scaled by dollars per 1% from
two of the owner's readings. Until there are two readings, a default scale is used
and the line says so.

    python3 pace.py [--reset 2026-10-24T16:00Z]
"""
import csv, os, sys, datetime as dt, pathlib

RESET = "2026-10-24T16:00Z"   # Fri 11:00 CDT (UTC-5); the next is a week later
STEP, HOURS, RESERVE, DRIFT = 7.0, 12.0, 9.0, 5.0

def t(s): return dt.datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc)

def main():
    reset = t(sys.argv[sys.argv.index("--reset") + 1]) if "--reset" in sys.argv else t(RESET)
    rows = list(csv.DictReader(open(pathlib.Path(os.environ.get("USAGE_SNAPSHOTS") or "snapshots.csv"))))
    readings = [r for r in rows if r["zac_reading_pct"]]
    a = readings[0]
    if len(readings) >= 2:
        b = readings[-1]
        per_pct = (float(b["project_cost_usd"]) - float(a["project_cost_usd"])) / (float(b["zac_reading_pct"]) - float(a["zac_reading_pct"]))
        a = b
        how = f"${per_pct:.0f} per 1% from the owner's readings"
    else:
        per_pct = 25.0
        how = "a guessed $25 per 1% until the owner's second reading"
    last = rows[-1]
    now = t(last["utc"])
    pct = float(a["zac_reading_pct"]) + (float(last["project_cost_usd"]) - float(a["project_cost_usd"])) / per_pct
    hours = (now - reset).total_seconds() / 3600
    plan = min(STEP * hours / HOURS, 100 - RESERVE)
    week = 7 * 24
    rate = None
    if len(rows) >= 2:
        p = rows[-2]
        dh = (now - t(p["utc"])).total_seconds() / 3600
        if dh > 0:
            rate = (float(last["project_cost_usd"]) - float(p["project_cost_usd"])) / per_pct / dh
    if rate is None:
        rate = pct / hours
    at_reset = pct + rate * (week - hours)
    flag = "ON PACE" if abs(pct - plan) <= DRIFT else ("AHEAD BY >5%" if pct > plan else "BEHIND BY >5%")
    print(f"Usage pace {now:%m-%d %H:%M} UTC: {pct:.0f}% used against {plan:.0f}% planned ({pct - plan:+.0f}), "
          f"heading for {at_reset:.0f}% at the reset {reset + dt.timedelta(days=7):%a %m-%d %H:%M} UTC, "
          f"so {100 - at_reset:.0f}% left over (plan: {RESERVE:.0f}%). {flag}. Scale: {how}.")

main()
