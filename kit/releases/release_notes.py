#!/usr/bin/env python3
"""Links every playtest pre-release to its milestone, issues and commit.

    python3 kit/releases/release_notes.py          # every playtest release
    python3 kit/releases/release_notes.py --dry    # print, change nothing
    python3 kit/releases/release_notes.py --delete m14-playtest-1
                                  # remove a release that isn't a playtest, and its tag

A release with only a text blurb doesn't say which milestone or issues it
plays, or whether it's still the build to play.

Each release whose tag matches releases.tag_pattern (default m<N>-playtest-<k>,
the first group the milestone) gets a
header above its notes: the milestone with its state, the commit it was built
from, the milestone's issues, and whether it's the one to play. The newest
release of a milestone is current; older ones are marked superseded by it,
in the header and the title. A header written before is replaced, so this can
run any number of times. The kit-release-notes workflow runs it on every
published release, and a project build workflow can run it after each build, since Claude
sessions can't edit releases themselves.

Needs `gh` signed in with contents write and issues read (GH_TOKEN in CI).
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import playbook_config  # noqa: E402

CFG = playbook_config.load()
REPO = "/".join(playbook_config.owner_repo(CFG))
MARK = "<!-- playtest-links -->"
END = "<!-- /playtest-links -->"
TAG = re.compile(CFG["releases"]["tag_pattern"])
# Tags from before milestones named the build, and the milestone they belong to.
OLD = dict(CFG["releases"]["old_tags"])
SUPERSEDED = " (superseded)"


def gh(*args):
    # UTF-8, not Windows' cp1252: milestone descriptions quote curly quotes.
    out = subprocess.run(["gh", "api", *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout
    return json.loads(out) if out.strip() else None


def milestone_of(tag):
    m = TAG.match(tag)
    return int(m.group(1)) if m else OLD.get(tag)


def strip(body):
    """The notes without a header written before."""
    body = body or ""
    if MARK in body and END in body:
        return body.split(END, 1)[1].lstrip("\n")
    return body


def header(ms, issues, sha, current):
    if current is None:
        status = ("This is the build to play. The milestone is closed: "
                  f"{CFG['project']['owner_name']}'s playtest passed."
                  if ms["state"] == "closed" else "This is the build to play.")
    else:
        status = f"Superseded by [{current}](https://github.com/{REPO}/releases/tag/{current}): play that one instead."
    nums = ", ".join(f"#{n}" for n in issues) or "none yet"
    return "\n".join([
        MARK,
        f"**Milestone:** [{ms['number']}. {ms['title']}]({ms['html_url']}) ({ms['state']})",
        f"**Built from:** [{sha[:7]}](https://github.com/{REPO}/commit/{sha})",
        f"**Status:** {status}",
        f"**Issues in the milestone:** {nums}",
        END,
        "",
    ])


def plan(releases, milestone, issues_of):
    """(release, new name, new body) for each playtest release whose notes change.

    `milestone(n)` and `issues_of(n)` read milestone n and its issue numbers."""
    by_milestone = {}
    for r in releases:
        n = milestone_of(r["tag_name"])
        if n is not None:
            by_milestone.setdefault(n, []).append(r)
    out = []
    for n, rels in sorted(by_milestone.items()):
        rels.sort(key=lambda r: r["created_at"])
        newest = rels[-1]["tag_name"]
        ms, issues = milestone(n), issues_of(n)
        for r in rels:
            current = None if r["tag_name"] == newest else newest
            body = header(ms, issues, r["target_commitish"], current) + strip(r["body"])
            name = r["name"] or r["tag_name"]
            if current and "superseded" not in name.lower() and "retired" not in name.lower():
                name += SUPERSEDED
            if body != (r["body"] or "") or name != r["name"]:
                out.append((r, name, body))
    return out


def main():
    dry = "--dry" in sys.argv
    releases = gh(f"repos/{REPO}/releases?per_page=100")
    if "--delete" in sys.argv:
        tag = sys.argv[sys.argv.index("--delete") + 1]
        doomed = [r for r in releases if r["tag_name"] == tag]
        for r in doomed:
            print(f"{tag}: deleted")
            if not dry:
                gh("-X", "DELETE", f"repos/{REPO}/releases/{r['id']}")
                gh("-X", "DELETE", f"repos/{REPO}/git/refs/tags/{tag}")
        releases = [r for r in releases if r["tag_name"] != tag]
    milestones = {}

    def milestone(n):
        if n not in milestones:
            milestones[n] = gh(f"repos/{REPO}/milestones/{n}")
        return milestones[n]

    def issues_of(n):
        found = gh(f"repos/{REPO}/issues?milestone={n}&state=all&per_page=100")
        return sorted(i["number"] for i in found if "pull_request" not in i)

    changes = plan(releases, milestone, issues_of)
    for r, name, body in changes:
        print(f"{r['tag_name']}: {name}")
        if not dry:
            gh("-X", "PATCH", f"repos/{REPO}/releases/{r['id']}", "-f", f"name={name}", "-f", f"body={body}")
    print(f"{len(changes)} release(s) {'would change' if dry else 'updated'}")


if __name__ == "__main__":
    main()
