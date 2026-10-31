#!/usr/bin/env python3
"""Weekly usage attribution report (Zac, 2026-10-31 15:05Z, cmsg_01MBd7bh7crCqMYZ8YdP7oShPMnh9uzyb5vHgj9ci2MTq2:
"every reset, 1 hour before, i want to collect a report of our usage, and try to attribute what parts of the
project consumed resources ... for now i just want to consistently capture the information").

Input: weekly/costs-YYYY-MM-DD.json, each session's cost_usd from get_session, with `prev` = its cost at the
previous 23:20 per-session snapshot, plus its area. Output: weekly/report-YYYY-MM-DD.md.
Usage: python3 usage_report.py weekly/costs-2026-10-31.json --week-start-total 1700 --reading 90
"""
import argparse, collections, json, os, sys

ap = argparse.ArgumentParser()
ap.add_argument("costs")
ap.add_argument("--week-start-total", type=float, required=True, help="project cost at the week's reset")
ap.add_argument("--carried", type=float, default=0, help="cost of finished sessions not listed (carried in totals)")
ap.add_argument("--reading", type=float, help="the owner's latest usage reading, percent")
a = ap.parse_args()
d = json.load(open(a.costs))
s = d["sessions"]
start = d["week_start"][:10]
listed = sum(v["cost"] for v in s.values())
total = listed + a.carried
week = total - a.week_start_total
new = {k: v for k, v in s.items() if v["created"] >= start}
old = {k: v for k, v in s.items() if v["created"] < start}
old_week = week - sum(v["cost"] for v in new.values())

area = collections.defaultdict(float)
for v in new.values():
    area[v["area"]] += v["cost"]
area["Older sessions (created before the reset; their split is unknown this week)"] += old_week

out = [f"# Usage report, week ending {d['taken'][:10]}", "",
       f"Taken {d['taken']}, one hour before the reset. Week started {d['week_start']}.", "",
       f"- **Spent this week: about ${week:,.0f}** (project total ${total:,.0f}, about ${a.week_start_total:,.0f} at the reset)."]
if a.reading:
    out.append(f"- The owner's latest reading: {a.reading:.0f}%, so about ${week / a.reading:,.0f} per 1%.")
out += ["", "## By area (this week)", "", "| Area | $ | Share |", "|---|---|---|"]
for k, v in sorted(area.items(), key=lambda kv: -kv[1]):
    out.append(f"| {k} | {v:,.0f} | {v / week:.0%} |")
out += ["", "## By session", "", "Lifetime cost, cost in the last ~16 h (since the 10-30 23:20 snapshot), and this week's cost where the session started this week.", "",
        "| Session | Area | Lifetime $ | Last 16 h $ | This week $ |", "|---|---|---|---|---|"]
for k, v in sorted(s.items(), key=lambda kv: -kv[1]["cost"]):
    wk = f"{v['cost']:,.0f}" if k in new else "?"
    out.append(f"| {v['title']} ({k}) | {v['area']} | {v['cost']:,.0f} | {v['cost'] - v['prev']:,.0f} | {wk} |")
out += ["", "## Gaps to close next week", "",
        "- The older sessions' share of this week isn't known per session: there was no per-session snapshot at the 10-24 reset. From now on each report saves its costs file, so next week's split is exact.",
        "- Cost is per thread session, not per milestone. A thread that serves two milestones (rich mines did m15 and m9) can't be split yet.",
        "- PC runner time and hosted Actions ($13.59 in October) aren't part of the usage budget and are left out."]
path = os.path.join(os.path.dirname(a.costs), f"report-{d['taken'][:10]}.md")
open(path, "w").write("\n".join(out) + "\n")
print("\n".join(out[:20]))
