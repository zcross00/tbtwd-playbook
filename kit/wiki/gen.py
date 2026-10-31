#!/usr/bin/env python3
"""Writes the project wiki's pages from GitHub (Zac, 2026-10-30 18:11: "I
want github to just be where I get up to speed on everything").

Every page is generated, so none can drift: Status and the milestone pages
from the open milestones and their issues (the same burn-down as
kit/board/milestones.py), Roadmap as a Mermaid timeline of the milestones,
Decisions from the issues labeled `decision` (open is pending, closed is
decided), and the few hand-written pages (HAND) copied from their files in
the repo, where they're reviewed like any other doc. publish.sh pushes the
pages to the wiki; the kit-wiki workflow runs it.

    python3 kit/wiki/gen.py OUTDIR     # write the pages
    python3 kit/wiki/gen.py --check    # what the daily backlog review flags

Reads the API through `gh api` where it's installed, else with GH_TOKEN.
"""
import datetime as dt
import json
import os
import shutil
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "board"))
import milestones as ms_  # noqa: E402
from sync import board_values  # noqa: E402

CFG = ms_.CFG["wiki"]
OWNER_NAME = ms_.CFG["project"]["owner_name"]
TITLE = CFG["title"] or ms_.REPO
REPO_URL = f"https://github.com/{ms_.OWNER}/{ms_.REPO}"
# The project's checkout: every kit script runs from its root.
ROOT = os.getcwd()
# The hand-written pages: wiki page name and the repo file it's copied from.
# Each file carries a "Last reviewed: YYYY-MM-DD" line, and --check flags one
# older than REVIEW_DAYS.
HAND = [tuple(p) for p in CFG["hand_pages"]]
# Files the pages summarise, also held to the review date.
REVIEWED_TOO = list(CFG["reviewed_too"])
REVIEW_DAYS = CFG["review_days"]
# The banner and the screenshots (gallery.json: file, caption, milestone).
ART = os.path.join(ROOT, CFG["art_dir"])
REVIEWED = re.compile(r"^Last reviewed: (\d{4}-\d{2}-\d{2})", re.M)
# A decided issue quotes the owner's answer in a blockquote (PROCESS, "Decisions").
QUOTE = re.compile(r"^> ?(.+)$", re.M)
# The day it was decided, when that's not the day the issue closed (the
# decisions moved over from docs/DECISIONS.md on 2026-10-30).
DECIDED = re.compile(r"^Decided: (\d{4}-\d{2}-\d{2})", re.M)
# A pending decision older than this is flagged: it's waiting on the owner.
PENDING_DAYS = CFG["pending_days"]
# How the owner answers (kit/wiki/answer.py records the comment).
ANSWER = ("**To answer a decision, comment on its issue** with your pick (\"1\", \"B\", or in your own "
          "words). Any other comment counts as your answer: it's quoted into the issue, which closes as "
          "decided, and this page updates within minutes. A comment ending in \"?\", or starting \"not "
          "yet\" or \"later\", leaves it open. Reopen an issue to undo. Answering in chat still works too.")
VERDICTS = ("ON TRACK", "AT RISK", "NOT DATED", "PAST", "BEHIND", "PLAYTEST PASSED")


def issue_link(n):
    return f"[#{n}]({REPO_URL}/issues/{n})"


def cell(text):
    """Text safe inside a Markdown table cell."""
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def bar(done, total, width=10):
    filled = round(width * done / total) if total else 0
    return "▰" * filled + "▱" * (width - filled)


def milestone_row(ms, issues, comments, prs, runs, today):
    """One open milestone's Status row, from milestones.py's burn-down."""
    p = ms_.parts(ms, issues, comments, prs, runs, today)
    closed = sum(i["state"] == "closed" for i in issues)
    flags = [x for x in p[6:] if x.startswith(VERDICTS)]
    due = ms.get("due_on")
    return {
        "number": ms["number"], "title": ms["title"],
        "open": len(issues) - closed, "closed": closed,
        "left": p[1], "dates": p[5].replace("50% ", "").replace(" / 90% ", " → "),
        "due": due[:10] if due else "", "flags": flags,
        "playtest_owed": bool(issues) and closed == len(issues),
    }


def status_page(rows, decisions, needs_owner, nightly, today):
    pending = [d for d in decisions if d["state"] == "open"]
    owed = [r for r in rows if r["playtest_owed"]]
    out = ["# Status", "", f"Generated {today:%Y-%m-%d}. {nightly}.", "", "## Needs you", ""]
    if not (pending or owed or needs_owner):
        out.append("Nothing is waiting on you.")
    for d in pending:
        out.append(f"- Decision: {d['title']} ({issue_link(d['number'])})")
    for r in owed:
        out.append(f"- Playtest: [{r['title']}](Milestone-{r['number']}), every issue is closed")
    for i in needs_owner:
        out.append(f"- {i['title']} ({issue_link(i['number'])})")
    if pending:
        out += ["", ANSWER]
    recent = [d for d in decisions if d["state"] == "closed"
              and (today - dt.date.fromisoformat(decided_on(d))).days <= 1]
    if recent:
        out += ["", "## Decided since yesterday", ""]
        out += [f"- {d['title']} ({issue_link(d['number'])}): {quote(d['body'])}" for d in recent]
    out += ["", "## Milestones", "",
            "| Milestone | Done | Estimate left (k tokens) | 50% → 90% | Committed | Verdict |",
            "|---|---|---|---|---|---|"]
    for r in rows:
        total = r["open"] + r["closed"]
        out.append(f"| [{cell(r['title'])}](Milestone-{r['number']}) "
                   f"| {bar(r['closed'], total)} {r['closed']}/{total} | {cell(r['left'])} "
                   f"| {r['dates']} | {r['due']} | {cell(', '.join(r['flags']))} |")
    out += ["", "Estimates are the newest `board: estimate=` on each open issue; the verdict is "
            "`kit/board/milestones.py`'s, against the dates in the milestone's description.", ""]
    return "\n".join(out)


def gantt_name(title):
    """A milestone title Mermaid accepts as a task name."""
    return re.sub(r"[:#;,]", " ", title).strip()[:80]


def roadmap_page(open_ms, closed_ms, rows, today):
    """The milestones as a Mermaid timeline: open ones from their grooming to
    their 90% date (or committed date), closed ones from start to close."""
    flags = {r["number"]: r["flags"] for r in rows}
    out = ["# Roadmap", "", f"Generated {today:%Y-%m-%d}. Each bar runs from the milestone's grooming to "
           "its 90% date (its committed date once there is one). Red is at risk or past its 50% date; "
           "the line is today.", "", "```mermaid", "gantt", "  dateFormat YYYY-MM-DD",
           "  axisFormat %b %d", "  section Open"]
    undated = []
    for ms in sorted(open_ms, key=lambda m: m["number"]):
        desc = ms["description"] or ""
        start = ms_.groomed_on(desc, dt.date.fromisoformat(ms["created_at"][:10]))
        end = ms["due_on"][:10] if ms.get("due_on") else None
        if not end:
            d90 = ms_.planning_dates(desc, today)[1]
            end = d90.isoformat() if d90 else None
        if not end or end <= start.isoformat():
            undated.append(ms)
            continue
        f = flags.get(ms["number"], [])
        tag = "crit, " if any(x.startswith(("AT RISK", "PAST", "BEHIND")) for x in f) else "active, "
        out.append(f"  m{ms['number']} {gantt_name(ms['title'])} :{tag}m{ms['number']}, {start}, {end}")
    recent = [m for m in closed_ms if m.get("closed_at")]
    recent.sort(key=lambda m: m["closed_at"])
    if recent:
        out.append("  section Done")
    for ms in recent[-12:]:
        start, end = ms["created_at"][:10], ms["closed_at"][:10]
        if end <= start:
            end = (dt.date.fromisoformat(start) + dt.timedelta(days=1)).isoformat()
        out.append(f"  m{ms['number']} {gantt_name(ms['title'])} :done, d{ms['number']}, {start}, {end}")
    out += ["```", ""]
    if undated:
        out += ["Not dated yet: " + ", ".join(f"[{m['title']}](Milestone-{m['number']})" for m in undated), ""]
    out += ["## Order", ""]
    for ms in sorted(open_ms, key=lambda m: (m.get("due_on") or "9999", m["number"])):
        due = f", committed {ms['due_on'][:10]}" if ms.get("due_on") else ""
        out.append(f"- [{ms['title']}](Milestone-{ms['number']}){due}")
    out.append("")
    return "\n".join(out)


def milestone_page(ms, issues, comments, today, gallery=()):
    out = [f"# {ms['title']}", "", f"Generated {today:%Y-%m-%d} from "
           f"[milestone {ms['number']}]({REPO_URL}/milestone/{ms['number']}).", ""]
    out += [shot(g, 640) + "\n" for g in gallery if g.get("milestone") == ms["number"]]
    out += [(ms["description"] or "No description.").strip(), "", "## Issues", "",
            "| Issue | Title | State | Board status | Estimate (k) |", "|---|---|---|---|---|"]
    for i in sorted(issues, key=lambda i: (i["state"] != "open", i["number"])):
        v = board_values(comments.get(i["number"], []))
        out.append(f"| {issue_link(i['number'])} | {cell(i['title'])} | {i['state']} "
                   f"| {cell(v.get('status', ''))} | {cell(v.get('estimate', ''))} |")
    out.append("")
    return "\n".join(out)


def quote(body):
    """The owner's words from a decision issue: its first blockquote line."""
    m = QUOTE.search(body or "")
    return m.group(1).strip() if m else ""


def decided_on(d):
    m = DECIDED.search(d["body"] or "")
    return m.group(1) if m else d["closed_at"][:10]


def decisions_page(decisions, today):
    pending = sorted((d for d in decisions if d["state"] == "open"), key=lambda d: d["created_at"])
    decided = sorted((d for d in decisions if d["state"] == "closed"),
                     key=lambda d: (decided_on(d), d["number"]), reverse=True)
    out = ["# Decisions", "", f"Generated {today:%Y-%m-%d} from the issues labeled "
           f"[`decision`]({REPO_URL}/issues?q=label%3Adecision). Open is pending, closed is decided.",
           "", ANSWER, "", "## Pending", ""]
    if not pending:
        out.append("Nothing pending.")
    else:
        out += ["| Decision | Asked | Waiting |", "|---|---|---|"]
        for d in pending:
            days = (today - dt.date.fromisoformat(d["created_at"][:10])).days
            out.append(f"| {issue_link(d['number'])} {cell(d['title'])} | {d['created_at'][:10]} | {days} days |")
    out += ["", "## Decided", "", f"| Decision | Decided | {OWNER_NAME}'s words |", "|---|---|---|"]
    for d in decided:
        out.append(f"| {issue_link(d['number'])} {cell(d['title'])} | {decided_on(d)} "
                   f"| {cell(quote(d['body']))} |")
    out.append("")
    return "\n".join(out)


def verdict_icon(flags):
    if any(f.startswith("PAST") for f in flags):
        return "🔴"
    if any(f.startswith(("AT RISK", "BEHIND")) for f in flags):
        return "🟡"
    if any(f.startswith("NOT DATED") for f in flags):
        return "⚪"
    return "🟢"


def pr_link(p):
    return f"[#{p['number']}]({REPO_URL}/pull/{p['number']}) {cell(p['title'])}"


def merged_since(prs, since):
    # A train (kit/queue/train.sh) merges PRs that are listed on their own.
    return sorted((p for p in prs if p.get("merged_at") and p["merged_at"][:10] >= since.isoformat()
                   and not p["title"].startswith("Train:")),
                  key=lambda p: p["merged_at"], reverse=True)


def banner():
    """The banner, when the art has one."""
    if not os.path.exists(os.path.join(ART, "banner.svg")):
        return []
    return [f'<p align="center"><img src="art/banner.svg" alt="{TITLE}" width="100%"></p>', ""]


def shot(item, width=300):
    return (f'<img src="art/{item["file"]}" width="{width}" alt="{item["caption"]}"><br>'
            f'<sub>{item["caption"]}</sub>')


def home_page(rows, decisions, needs_owner, open_ms, prs, open_prs, gallery, today):
    """Status at a glance (Zac, 2026-10-30 22:15: "would want home to be overall status at a
    glance")."""
    pending = [d for d in decisions if d["state"] == "open"]
    owed = [r for r in rows if r["playtest_owed"]]
    asks = len(pending) + len(owed) + len(needs_owner)
    week = merged_since(prs, today - dt.timedelta(days=7))
    dated = sorted((m for m in open_ms if m.get("due_on")), key=lambda m: m["due_on"])
    nxt = (f"[{dated[0]['title']}](Milestone-{dated[0]['number']}), {dated[0]['due_on'][5:10]}"
           if dated else "nothing committed")
    risky = sum(verdict_icon(r["flags"]) in "🔴🟡" for r in rows)
    out = banner() + ([f'<p align="center"><i>{CFG["tagline"]}</i></p>', ""] if CFG["tagline"] else []) + [
           "| 🙋 Needs you | 🚀 Milestones open | ⚠️ Behind or at risk | ✅ PRs merged, 7 days | 🎯 Next due |",
           "|:-:|:-:|:-:|:-:|:-:|",
           f"| **{asks}** | **{len(rows)}** | **{risky}** | **{len(week)}** | {nxt} |", "",
           f"<sub>Updated {today:%b %d}. Generated from GitHub; edits here are overwritten. "
           "Answer decisions by commenting on their issue.</sub>", "", "## 🙋 Needs you", ""]
    if not asks:
        out.append("Nothing. Go play something.")
    out += [f"- 🗳️ **Decide:** {d['title']} ({issue_link(d['number'])})" for d in pending]
    out += [f"- 🎮 **Playtest:** [{r['title']}](Milestone-{r['number']}), all its work is done" for r in owed]
    out += [f"- 👀 {i['title']} ({issue_link(i['number'])})" for i in needs_owner]
    out += ["", "## 🚀 Milestones", "", "| | Milestone | Progress | Due |", "|:-:|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["due"] or "9999", r["number"])):
        total = r["open"] + r["closed"]
        out.append(f"| {verdict_icon(r['flags'])} | [{cell(r['title'])}](Milestone-{r['number']}) "
                   f"| `{bar(r['closed'], total)}` {r['closed']}/{total} | {r['due'][5:] or '—'} |")
    out += ["", "<sub>🟢 on track · 🟡 behind its 50% date or at risk · 🔴 past it · ⚪ not dated. "
            "Details on [Status](Status), timeline on [Roadmap](Roadmap).</sub>", "",
            "## 🛬 Just landed", ""]
    out += [f"- {pr_link(p)} <sub>{p['merged_at'][5:10]}</sub>" for p in week[:8]] or ["Nothing merged this week."]
    out += ["", "## 🛠️ In the queue", ""]
    ready = [p for p in open_prs if not p.get("draft") and not p["title"].startswith("Train:")]
    out += [f"- {pr_link(p)}" for p in ready[:8]] or ["No PRs waiting."]
    if len(ready) > 8:
        out.append(f"- …and [{len(ready) - 8} more]({REPO_URL}/pulls)")
    if gallery:
        out += ["", "## 📸 From the frontier", "", "<table><tr>"]
        for n, item in enumerate(gallery[:6]):
            if n and n % 3 == 0:
                out.append("</tr><tr>")
            out.append(f'<td align="center">{shot(item)}</td>')
        out += ["</tr></table>"]
    out += ["", "## 📚 Read more", "",
            " · ".join(f"[{label}]({page})" for label, page in nav())
            + f" · [Board](https://github.com/users/{ms_.OWNER}/projects)", ""]
    return "\n".join(out)


def has_vision():
    return bool(CFG["vision"]) and os.path.exists(os.path.join(ROOT, CFG["vision"]))


def nav():
    """(label, page) for the pages every page links to."""
    out = [("Status", "Status"), ("Roadmap", "Roadmap"), ("Decisions", "Decisions")]
    out += [(name.replace("-", " ").capitalize(), name) for name, _ in HAND]
    return out + ([("Vision", "Vision")] if has_vision() else [])


def sidebar(open_ms):
    out = ["**[Home](Home)**", ""] + [f"- [{label}]({page})" for label, page in nav()] + ["", "**Milestones**", ""]
    out += [f"- [{m['title']}](Milestone-{m['number']})" for m in sorted(open_ms, key=lambda m: m["number"])]
    return "\n".join(out) + "\n"


def vision_page(path=None):
    """The vision in brief: its pitch and its priorities' headings, linking the file for the rest
    (Zac, 2026-10-30 22:15: "i don't understand why we're copying things like vision wholesale")."""
    path = path or CFG["vision"]
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"## The one-sentence pitch\n\n(.+?)\n", text)
    heads = re.findall(r"^### (.+)$", text, re.M)
    out = banner() + ["# Vision", "", f"> {m.group(1) if m else ''}", "", "**What matters, in order:**", ""]
    out += [f"1. {h.split('. ', 1)[-1]}" for h in heads[:6]]
    out += ["", f"The whole vision, and why each priority sits where it does: [docs/VISION.md]"
            f"({REPO_URL}/blob/main/{path}).", ""]
    return "\n".join(out)


def hand_page(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        text = f.read()
    return text + f"\n\n---\n_From [{path}]({REPO_URL}/blob/main/{path}); edit it there._\n"


def review_flags(today):
    """Hand-written pages missing a review date or past REVIEW_DAYS."""
    out = []
    for name, path in HAND + [(p.split("/")[-1], p) for p in REVIEWED_TOO]:
        if not os.path.exists(os.path.join(ROOT, path)):
            out.append(f"STALE PAGE {name}: {path} is missing")
            continue
        with open(os.path.join(ROOT, path), encoding="utf-8") as f:
            m = REVIEWED.search(f.read())
        if not m:
            out.append(f"STALE PAGE {name}: {path} has no 'Last reviewed:' line")
        elif (today - dt.date.fromisoformat(m.group(1))).days > REVIEW_DAYS:
            out.append(f"STALE PAGE {name}: {path} last reviewed {m.group(1)}")
    return out


def decision_flags(decisions, today):
    out = []
    for d in decisions:
        if d["state"] == "open":
            days = (today - dt.date.fromisoformat(d["created_at"][:10])).days
            if days > PENDING_DAYS:
                out.append(f"DECISION WAITING #{d['number']} {d['title']}: {days} days")
        elif not quote(d["body"]):
            out.append(f"DECISION UNQUOTED #{d['number']} {d['title']}: no '> ' line with {OWNER_NAME}'s words")
    return out


def fetch_decisions():
    return [i for i in ms_.get("/issues?labels=decision&state=all&per_page=100") if "pull_request" not in i]


def main(argv):
    today = dt.date.today()
    if argv[1:] == ["--check"]:
        flags = review_flags(today) + decision_flags(fetch_decisions(), today)
        print("\n".join(flags) or "Wiki: nothing to flag.")
        return 0
    if len(argv) != 2:
        sys.exit(__doc__)
    outdir = argv[1]
    os.makedirs(outdir, exist_ok=True)
    open_ms = ms_.get("/milestones?state=open&per_page=100")
    closed_ms = ms_.get("/milestones?state=closed&per_page=100")
    prs = ms_.get("/pulls?state=closed&sort=updated&direction=desc&per_page=100")
    try:
        runs = ms_.get(ms_.NIGHTLY)["workflow_runs"]
    except LookupError:
        runs = None
    decisions = fetch_decisions()
    needs_owner = [i for i in ms_.get("/issues?labels=" + urllib.parse.quote(CFG["needs_owner_label"]) + "&state=open&per_page=100")
                 if "pull_request" not in i]
    gallery = []
    if os.path.exists(os.path.join(ART, "gallery.json")):
        with open(os.path.join(ART, "gallery.json"), encoding="utf-8") as f:
            gallery = json.load(f)
    pages, rows = {}, []
    for ms in sorted(open_ms, key=lambda m: m["number"]):
        issues = [i for i in ms_.get(f"/issues?milestone={ms['number']}&state=all&per_page=100")
                  if "pull_request" not in i]
        comments = {i["number"]: [{"body": i["body"] or ""}]
                    + ms_.get(f"/issues/{i['number']}/comments?per_page=100") for i in issues}
        rows.append(milestone_row(ms, issues, comments, prs, runs, today))
        pages[f"Milestone-{ms['number']}"] = milestone_page(ms, issues, comments, today, gallery)
    open_prs = ms_.get("/pulls?state=open&sort=created&direction=asc&per_page=100")
    pages["Home"] = home_page(rows, decisions, needs_owner, open_ms, prs, open_prs, gallery, today)
    pages["Status"] = status_page(rows, decisions, needs_owner, ms_.nightly(runs), today)
    pages["Roadmap"] = roadmap_page(open_ms, closed_ms, rows, today)
    pages["Decisions"] = decisions_page(decisions, today)
    if has_vision():
        pages["Vision"] = vision_page()
    for name, path in HAND:
        pages[name] = hand_page(path)
    if os.path.isdir(ART):
        shutil.copytree(ART, os.path.join(outdir, "art"), dirs_exist_ok=True)
    pages["_Sidebar"] = sidebar(open_ms)
    pages["_Footer"] = ("_Generated by [kit/wiki/gen.py](https://github.com/" + ms_.CFG["project"]["playbook_repo"]
                        + "/blob/main/kit/wiki/gen.py) "
                        f"on {today:%Y-%m-%d}. Edits here are overwritten._\n")
    for name, text in pages.items():
        with open(os.path.join(outdir, name + ".md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    print(f"Wrote {len(pages)} pages to {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
