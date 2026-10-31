#!/usr/bin/env python3
"""Check a PR's paperwork, the parts the reviewer used to check by hand (the
reference project's retro, 2026-10-30).

Problems it reports, each a playbook rule:
- a closing word ("fixes #N") in the title or body, which closes the issue on
  merge (playbook/04-lifecycle.md, rule 1);
- a code PR with no `Refs #N` line (docs-only PRs exempt);
- a ref'd issue with no milestone, or not groomed: no `groomed` comment
  (`[paperwork] groomed`, default "groomed: approved"), unless it carries one
  of `[paperwork] exempt_labels` (a verification correction, a deferred gate;
  playbook/03-tracking.md);
- a body that says it loosens, defers or reports a gate instead of failing,
  with no `[paperwork] deferred_label` issue among the ones it names
  (playbook/07-gates.md).

The first two overlap templates/github's playbook-lint, which also reads
commit messages; this one adds the issue checks. A draft and a merge train
are skipped: a train's members carry their own paperwork. The
kit-paperwork workflow runs the playbook's main copy on a PR and goes red on
a problem. `kit/run.sh board/paperwork.py N` checks PR N.

Needs GH_TOKEN (read) or `gh`.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import playbook_config  # noqa: E402
from pr_milestone import is_train, refs  # noqa: E402

CFG = playbook_config.load()
REPO = "/".join(playbook_config.owner_repo(CFG))
API = os.environ.get("GITHUB_API_URL", "https://api.github.com")
PAPER = CFG["paperwork"]
# templates/github/scripts/playbook_lint.py's: a closing word before #N, an
# owner/repo#N, or an issue URL closes it on merge.
CLOSING = re.compile(
    r"\b(close[sd]?|fix(e[sd])?|resolve[sd]?)\b[\s:]*"
    r"((\w[\w.-]*/[\w.-]+)?#\d+|https://github\.com/\S+/issues/\d+)", re.I)
# What a body says when it loosens a gate, or the PR template's Gates box
# ticked. Naming the label alone ("a `deferred gate` issue") isn't one.
LOOSENS = re.compile(r"\b(loosen(s|ed|ing)?|report-only|reports? instead of gat|defers? (the|a|its) "
                     r"(gate|check))|^\s*[-*]\s*\[[xX]\]\s*gate changed", re.I | re.M)
# Lines that say nothing was loosened: the template's unticked boxes and its
# "No gate loosened" line, ticked or not.
UNSAID = re.compile(r"^\s*[-*]\s*\[ \].*$|^\s*[-*]\s*(\[[xX]\]\s*)?no gates? (was |were )?loosened.*$",
                    re.I | re.M)
GROOMED = re.compile(re.escape(PAPER["groomed"]), re.I)
EXEMPT = set(PAPER["exempt_labels"])
DEFERRED = PAPER["deferred_label"]


def docs_only(files):
    return bool(files) and all(f.startswith("docs/") or f.endswith(".md") for f in files)


def labels(issue):
    return {l["name"] for l in issue.get("labels", [])}


def problems(pr, files, issue_of, comments_of):
    """The paperwork problems in a PR, as lines. issue_of(n) gives the issue
    (or None when it can't be read), comments_of(n) its comment bodies."""
    if pr.get("draft") or is_train(pr):
        return []
    text = (pr.get("title") or "") + "\n" + (pr.get("body") or "")
    out = [f"closing word: \"{m.group(0)}\" closes the issue on merge; write \"Refs #N\" "
           "(playbook/04-lifecycle.md, rule 1)" for m in CLOSING.finditer(text)]
    nums = [n for n in dict.fromkeys(refs(pr.get("body"))) if n != pr["number"]]
    if not nums and not docs_only(files):
        out.append("no `Refs #N` line: a code PR refs its issue (playbook/04-lifecycle.md)")
    for n in nums:
        issue = issue_of(n)
        if issue is None:
            out.append(f"#{n}: not readable")
            continue
        if "pull_request" in issue:
            continue
        if not issue.get("milestone"):
            out.append(f"#{n}: no milestone")
        if not labels(issue) & EXEMPT and not any(GROOMED.search(c) for c in comments_of(n)):
            out.append(f"#{n}: no `{PAPER['groomed']}` comment (playbook/03-tracking.md)")
    said = UNSAID.sub("", re.sub(r"<!--.*?-->", "", pr.get("body") or "", flags=re.S))
    if LOOSENS.search(said):
        named = set(nums) | {int(n) for n in re.findall(r"#(\d+)", pr.get("body") or "")}
        named.discard(pr["number"])
        if not any(DEFERRED in labels(issue_of(n) or {}) for n in named):
            out.append(f"loosens or defers a gate but names no `{DEFERRED}` issue (playbook/07-gates.md)")
    return out


def call(path):
    if shutil.which("gh"):
        r = subprocess.run(["gh", "api", f"repos/{REPO}/{path}"], capture_output=True, text=True)
        if r.returncode:
            raise LookupError(r.stderr.strip())
        return json.loads(r.stdout)
    req = urllib.request.Request(f"{API}/repos/{REPO}/{path}", headers={
        "Authorization": f"Bearer {os.environ['GH_TOKEN']}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main(argv):
    number = int(argv[0])
    pr = call(f"pulls/{number}")
    files = [f["filename"] for f in call(f"pulls/{number}/files?per_page=100")]
    cache = {}

    def issue_of(n):
        if n not in cache:
            try:
                cache[n] = call(f"issues/{n}")
            except (LookupError, OSError):
                cache[n] = None
        return cache[n]

    def comments_of(n):
        return [(issue_of(n) or {}).get("body") or ""] + [
            c["body"] or "" for c in call(f"issues/{n}/comments?per_page=100")]

    found = problems(pr, files, issue_of, comments_of)
    for line in found:
        print(f"PR #{number}: {line}")
    if not found:
        print(f"PR #{number}: paperwork OK")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
