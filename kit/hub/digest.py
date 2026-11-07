#!/usr/bin/env python3
"""What changed on the hub since this team last looked ([Teams](../../playbook/11-teams.md)).

Each team's coordinator runs it hourly from a scheduled task, so neither team
depends on the other remembering to tell it about a decision, a question or a
process PR. Prints new and updated issues and PRs, new comments, and commits on
`main`, written by roster logins only. Each item goes to the team its
`team:<name>` label or `Team: <name>` line names, or else to its login's
own team: the first --roster entry with that login. The other
teams' items are listed and this team's own only counted. Prints NOTHING NEW
when there is nothing.

  kit/hub/digest.py --state FILE --team NAME --roster NAME=LOGIN,NAME=LOGIN REPO...

--config FILE (default: config.json beside this script, when there is one) sets
the team and roster instead, so a scheduled task's command never has to change
when a team's login does: {"team": NAME, "roster": {NAME: LOGIN, ...},
"notes": [LINE, ...], "last_digest": FILE}. Its notes are printed under every digest that lists
something. The older form --me LOGIN --roster LOGIN,LOGIN names each team by
its login.

FILE keeps the time of the last run per repository; it is the team's own.
The first run looks back 24 hours. --dry-run prints without moving FILE on.
Reads the GitHub API through `gh api`.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

SIGNED = re.compile(r"^\s*\**Team:\**\s*`?([\w.-]+)", re.M)


def gh(path):
    r = subprocess.run(["gh", "api", "--paginate", "--slurp", path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        if "409" in r.stderr or "Git Repository is empty" in r.stderr:
            return []
        raise RuntimeError(f"gh api {path}: {r.stderr.strip()}")
    pages = json.loads(r.stdout or "[]")
    return [x for p in pages for x in (p if isinstance(p, list) else [p])]


def one_line(text, n=160):
    t = " ".join((text or "").split())
    return t if len(t) <= n else t[: n - 1] + "…"


def named_team(body, labels=()):
    for l in labels:
        if l.startswith("team:"):
            return l[5:]
    m = SIGNED.search(body or "")
    return m.group(1) if m else None


def collect(repo, since, fetch=gh):
    q = f"since={since}&per_page=100"
    issues = fetch(f"repos/{repo}/issues?state=all&sort=updated&direction=asc&{q}")
    comments = fetch(f"repos/{repo}/issues/comments?sort=updated&direction=asc&{q}")
    commits = fetch(f"repos/{repo}/commits?sha=main&{q}")
    items = []
    for i in issues:
        kind = "PR" if "pull_request" in i else "issue"
        new = i["created_at"] >= since
        labels = [l["name"] for l in i.get("labels", [])]
        what = ("new " if new else "updated ") + kind + (" (closed)" if i["state"] == "closed" else "")
        items.append({"at": i["updated_at"], "login": i["user"]["login"],
                      "team": named_team(i.get("body"), labels),
                      "line": f"{what} #{i['number']} [{','.join(labels)}] {one_line(i['title'], 100)} {i['html_url']}"})
    for c in comments:
        num = c["issue_url"].rsplit("/", 1)[-1]
        items.append({"at": c["updated_at"], "login": c["user"]["login"],
                      "team": named_team(c.get("body")),
                      "line": f"comment on #{num}: {one_line(c['body'])} {c['html_url']}"})
    for c in commits:
        login = (c.get("author") or {}).get("login") or (c.get("committer") or {}).get("login") or ""
        msg = c["commit"]["message"]
        items.append({"at": c["commit"]["committer"]["date"], "login": login,
                      "team": named_team(msg),
                      "line": f"main {c['sha'][:7]}: {one_line(msg.splitlines()[0], 100)}"})
    return items


def team_of(item, roster):
    teams = [t for t, login in roster.items() if login == item["login"]]
    if not teams:
        return None
    if item.get("team") in teams:
        return item["team"]
    return teams[0]


def render(repos_items, team, roster):
    out, outside, own = [], 0, 0
    for repo, items in repos_items:
        theirs = []
        for i in items:
            t = team_of(i, roster)
            if t is None:
                outside += 1
            elif t == team:
                own += 1
            else:
                theirs.append((t, i))
        if theirs:
            out.append(f"## {repo}")
            out += [f"- [{t}] {i['line']}" for t, i in sorted(theirs, key=lambda x: x[1]["at"])]
    if not out:
        out.append("NOTHING NEW")
    if own:
        out.append(f"({own} item(s) of this team's own, not listed)")
    if outside:
        out.append(f"(ignored {outside} item(s) from logins outside the roster)")
    return "\n".join(out)


def parse_roster(text):
    roster = {}
    for pair in (text or "").split(","):
        pair = pair.strip()
        if not pair:
            continue
        name, _, login = pair.partition("=")
        roster[name.strip()] = (login or name).strip()
    return roster


def settings(a):
    cfg_path = a.config or os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    cfg = {}
    if os.path.exists(cfg_path):
        with open(cfg_path) as f:
            cfg = json.load(f)
    team = cfg.get("team") or a.team or a.me
    roster = dict(cfg.get("roster") or parse_roster(a.roster))
    if not cfg.get("roster") and a.me and team == a.me:
        roster.setdefault(a.me, a.me)
    return team, roster, cfg.get("notes") or [], cfg.get("last_digest")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--team")
    ap.add_argument("--me", help="older form: this team's login, used as its name")
    ap.add_argument("--roster", help="NAME=LOGIN,... for every team, a shared login's own team first")
    ap.add_argument("--config")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("repos", nargs="+")
    a = ap.parse_args(argv)
    team, roster, notes, last = settings(a)
    if not team or team not in roster:
        ap.error("no team, or the team is not in the roster")
    state = {}
    if os.path.exists(a.state):
        with open(a.state) as f:
            state = json.load(f)
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    default = (now - dt.timedelta(hours=24)).isoformat().replace("+00:00", "Z")
    stamp = now.isoformat().replace("+00:00", "Z")
    got = [(r, collect(r, state.get(r, default))) for r in a.repos]
    out = render(got, team, roster)
    if notes and not out.startswith("NOTHING NEW"):
        out += "\n" + "\n".join(f"NOTE: {n}" for n in notes)
    print(out)
    if last and not a.dry_run:
        with open(last, "w") as f:
            f.write(f"{stamp}\n{out}\n")
    if not a.dry_run:
        for r in a.repos:
            state[r] = stamp
        os.makedirs(os.path.dirname(os.path.abspath(a.state)), exist_ok=True)
        with open(a.state, "w") as f:
            json.dump(state, f, indent=1)


if __name__ == "__main__":
    sys.exit(main())
