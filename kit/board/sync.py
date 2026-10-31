#!/usr/bin/env python3
"""Copy what threads write on issues into the project board's fields.

Cloud sessions can't reach GitHub Projects, so threads record planning on the
issue itself and this script, run by the kit-board workflow, copies it
onto the board. Threads write lines like these in the issue body or any comment:

    board: estimate=60
    board: status=In progress
    board: actual=72 status=In review
    board: day=2026-10-23

`day` sets both iteration fields, Day and Week. For each key the newest line wins (the body counts as oldest). Team always comes from the `area:` label.
Status falls back to Done for closed issues, and an open issue is never set
to Done (PROCESS, The lifecycle and the definition of done). Values are thousands of output
tokens; see PROCESS "Estimating and the daily plan".

Needs BOARD_TOKEN (classic PAT, `project` scope). Dry run unless --apply.
Safe to re-run: it only sets values that differ.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import playbook_config  # noqa: E402

CFG = playbook_config.load()
OWNER, REPO = playbook_config.owner_repo(CFG)
PROJECT = CFG["board"]["project"]
LOOKBACK_DAYS = CFG["board"]["lookback_days"]
# The title of the annotation for a board: line the sync skips.
SKIP_TITLE = "board line skipped"
# Iteration fields set from `day=`: the 1-day one and the week it falls in.
ITERATION_FIELDS = tuple(CFG["board"]["iteration_fields"])

AREA_TO_TEAM = CFG["board"]["teams"]
BOARD_LINE = re.compile(r"^\s*board:(.*)$", re.MULTILINE | re.IGNORECASE)
PAIR = re.compile(r"(\w+)=(.+?)(?=\s+\w+=|$)")


def gql(query, **variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {os.environ['BOARD_TOKEN']}"},
    )
    with urllib.request.urlopen(req) as r:
        out = json.load(r)
    if out.get("errors"):
        sys.exit(f"GraphQL error: {out['errors']}")
    return out["data"]


def pages(query, path, **variables):
    cursor = None
    while True:
        node = gql(query, after=cursor, **variables)
        for key in path:
            node = node[key]
        yield from node["nodes"]
        if not node["pageInfo"]["hasNextPage"]:
            return
        cursor = node["pageInfo"]["endCursor"]


# The board's Status options, and PROCESS's lifecycle stages that show as one
# of them (The lifecycle and the definition of done, the Board Status column).
STATUSES = ("Todo", "Ready", "In progress", "In review", "Done")
STAGE_STATUS = {"planned": "Todo", "building": "In progress", "pr ready": "In progress",
                "code review": "In progress", "merge": "In review", "verification": "In review"}
NUMBER = re.compile(r"\d+(?:\.\d+)?")
DAY = re.compile(r"\d{4}-\d{2}-\d{2}")


def clean(key, value):
    """The value a board: line means, without prose after it ("actual=30 (final)"
    is 30). A value that doesn't start with a valid one comes back as written,
    and the sync skips it with a warning."""
    if key == "status":
        low = value.lower()
        names = {s.lower(): s for s in STATUSES} | STAGE_STATUS
        for name in sorted(names, key=len, reverse=True):
            if low == name or (low.startswith(name) and not low[len(name)].isalnum()):
                return names[name]
        return value
    if key in ("estimate", "actual"):
        m = NUMBER.match(value)
        return m.group() if m else value
    if key == "day":
        m = DAY.match(value)
        return m.group() if m else value
    return value


def board_values(comments):
    """Newest value per key from `board:` lines, oldest comment first."""
    vals = {}
    for c in comments:
        for line in BOARD_LINE.findall(c["body"]):
            for key, value in PAIR.findall(line.strip()):
                vals[key.lower()] = clean(key.lower(), value.strip())
    return vals


def project():
    d = gql("""query($login: String!) { user(login: $login) {
        projectsV2(first: 50) { nodes { id title } } } }""", login=OWNER)
    return next((p["id"] for p in d["user"]["projectsV2"]["nodes"] if p["title"] == PROJECT), None) \
        or sys.exit(f"no project named {PROJECT!r}")


def fields(pid):
    d = gql("""query($id: ID!) { node(id: $id) { ... on ProjectV2 {
        fields(first: 50) { nodes {
          ... on ProjectV2Field { id name dataType }
          ... on ProjectV2SingleSelectField { id name options { id name } }
          ... on ProjectV2IterationField { id name
            configuration { iterations { id startDate duration } completedIterations { id startDate duration } } } } } } } }""", id=pid)
    return {f["name"]: f for f in d["node"]["fields"]["nodes"] if f}


ITEMS = """query($id: ID!, $after: String) { node(id: $id) { ... on ProjectV2 {
    items(first: 100, after: $after) { pageInfo { hasNextPage endCursor }
      nodes { id
        content { ... on Issue { number repository { nameWithOwner } } }
        fieldValues(first: 30) { nodes {
          ... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2Field { name } } }
          ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2SingleSelectField { name } } }
          ... on ProjectV2ItemFieldIterationValue { iterationId field { ... on ProjectV2IterationField { name } } }
        } } } } } } }"""

ISSUES = """query($o: String!, $r: String!, $since: DateTime!, $after: String) { repository(owner: $o, name: $r) {
    issues(first: 50, after: $after, filterBy: {since: $since}) { pageInfo { hasNextPage endCursor }
      nodes { id number state body labels(first: 20) { nodes { name } }
        comments(last: 50) { nodes { body } } } } } }"""


def main():
    apply = "--apply" in sys.argv
    if not os.environ.get("BOARD_TOKEN"):
        sys.exit("BOARD_TOKEN isn't set (a classic PAT with `project` scope)")
    pid = project()
    f = fields(pid)
    option = lambda field, name: next((o["id"] for o in f.get(field, {}).get("options", [])
                                       if o["name"].lower() == name.lower()), None)

    def iteration_on(field, day):
        """The id of the field's iteration that contains the date, if any."""
        conf = f[field].get("configuration", {})
        day = dt.date.fromisoformat(day)
        for i in conf.get("iterations", []) + conf.get("completedIterations", []):
            start = dt.date.fromisoformat(i["startDate"])
            if start <= day < start + dt.timedelta(days=i["duration"]):
                return i["id"]
        return None

    # Start dates of the Day field's iterations, for items given a Day on the
    # board itself rather than by a `day=` line.
    day_conf = f.get("Day", {}).get("configuration", {})
    day_start = {i["id"]: i["startDate"] for i in day_conf.get("iterations", []) + day_conf.get("completedIterations", [])}

    have = {}
    for n in pages(ITEMS, ["node", "items"], id=pid):
        c = n["content"] or {}
        if c.get("repository", {}).get("nameWithOwner") == f"{OWNER}/{REPO}":
            vals = {v["field"]["name"]: v.get("number", v.get("name", v.get("iterationId")))
                    for v in n["fieldValues"]["nodes"] if v and v.get("field")}
            have[c["number"]] = (n["id"], vals)

    skipped = 0

    def skip(num, why):
        # A board: line the board can't take. In Actions it's also a warning
        # annotation, which kit/churn/minutes.py counts (#560).
        nonlocal skipped
        skipped += 1
        print(f"#{num}: {why}")
        if os.environ.get("GITHUB_ACTIONS"):
            print(f"::warning title={SKIP_TITLE}::#{num}: {why}")

    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=LOOKBACK_DAYS)).isoformat()
    changes = 0
    for issue in pages(ISSUES, ["repository", "issues"], o=OWNER, r=REPO, since=since):
        num = issue["number"]
        if num not in have:
            if issue["state"] != "OPEN":
                continue
            print(f"#{num}: add to project")
            changes += 1
            if not apply:
                continue
            d = gql("""mutation($p: ID!, $c: ID!) { addProjectV2ItemById(input: {projectId: $p, contentId: $c}) {
                item { id } } }""", p=pid, c=issue["id"])
            have[num] = (d["addProjectV2ItemById"]["item"]["id"], {})
        item, current = have[num]
        labels = {l["name"] for l in issue["labels"]["nodes"]}
        said = board_values([issue] + issue["comments"]["nodes"])

        wanted = {}
        team = next((AREA_TO_TEAM[l] for l in sorted(labels) if l in AREA_TO_TEAM), None)
        if team:
            wanted["Team"] = ("select", team)
        for key, field in (("estimate", "Estimate"), ("actual", "Actual")):
            if key in said:
                try:
                    wanted[field] = ("number", float(said[key]))
                except ValueError:
                    skip(num, f"{key}={said[key]!r} isn't a number")
        status = "Done" if issue["state"] != "OPEN" else said.get("status")
        if issue["state"] == "OPEN" and (status or "").lower() == "done":
            # Reopened without a new line: it goes back to work (PROCESS rule 11).
            print(f"#{num}: open, but its newest status line says Done; In progress")
            status = "In progress"
        if status:
            wanted["Status"] = ("select", status)
        if "day" in said:
            for field in ITERATION_FIELDS:
                wanted[field] = ("iteration", said["day"])
        elif current.get("Day") in day_start:
            # A Day set on the board: keep the Week in step with it.
            wanted["Week"] = ("iteration", day_start[current["Day"]])

        for field, (kind, value) in wanted.items():
            if field not in f:
                print(f"#{num}: the project has no {field} field")
                continue
            if kind == "number":
                if current.get(field) == value:
                    continue
                payload = {"number": value}
            elif kind == "select":
                oid = option(field, value)
                if not oid:
                    skip(num, f"{field} has no option {value!r}")
                    continue
                if (current.get(field) or "").lower() == value.lower():
                    continue
                payload = {"singleSelectOptionId": oid}
            else:
                try:
                    iid = iteration_on(field, value)
                except ValueError:
                    skip(num, f"day={value!r} isn't a date (YYYY-MM-DD)")
                    continue
                if not iid:
                    skip(num, f"no {field} iteration covers {value}")
                    continue
                if current.get(field) == iid:
                    continue
                payload = {"iterationId": iid}
            changes += 1
            print(f"#{num}: {field} -> {value}")
            if apply:
                gql("""mutation($p: ID!, $i: ID!, $f: ID!, $v: ProjectV2FieldValue!) {
                    updateProjectV2ItemFieldValue(input: {projectId: $p, itemId: $i, fieldId: $f, value: $v}) {
                      projectV2Item { id } } }""", p=pid, i=item, f=f[field]["id"], v=payload)

    print(f"{changes} change(s){'' if apply else ' (dry run; pass --apply)'}")
    if skipped:
        print(f"{skipped} board: line(s) skipped")


if __name__ == "__main__":
    main()
