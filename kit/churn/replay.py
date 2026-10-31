#!/usr/bin/env python3
"""Replay merged PRs pairwise and sort their conflicts by cause (coupling.md).

Threads rebase rather than merge, so git keeps almost no record of conflicts.
This puts each merged PR's change on main as it was without each of the PRs
merged just before it, asks `git merge-tree` whether the two collide, and
sorts every conflicting hunk by the item it sits in.

    python3 kit/churn/replay.py                 # every merge, window 6
    python3 kit/churn/replay.py --since 2026-10-22 --window 6

Pairs where a later PR built on the earlier one can't be replayed and are
skipped, so the counts are a floor. Needs full history (git fetch --unshallow).
"""

import argparse
import collections
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import playbook_config  # noqa: E402

CFG = playbook_config.load()
# The project's causes ([replay] in .playbook.toml). Items every PR appends
# to: a conflict in one is a "keep both lines" merge.
CHECK_PATHS = set(CFG["replay"]["check_paths"])
CHECK_LISTS = set(CFG["replay"]["check_lists"])
CODE_LISTS = set(CFG["replay"]["code_lists"])
SAVE_PATHS = set(CFG["replay"]["save_paths"])
ITEM = re.compile(r"\s*(?:pub(?:\([a-z]+\))? )?(fn|const|static|struct|enum|impl|mod)\s+(\w+)")


def git(*args):
    p = subprocess.run(["git", *args], capture_output=True, text=True)
    return p.returncode, p.stdout


def merge_tree(base, ours, theirs):
    rc, out = git("merge-tree", "--write-tree", "--name-only", "--no-messages", "--merge-base=" + base, ours, theirs)
    parts = out.split()
    return rc, (parts[0] if parts else None), parts[1:]


def cause(path, item):
    if path in SAVE_PATHS:
        return "save version"
    if path in CHECK_PATHS or item in CHECK_LISTS:
        return "check list"
    if path.endswith(".md"):
        return "docs"
    if item in CODE_LISTS or (item is None and path.endswith(".rs")):
        return "code list"
    return "code body"


def merges(since):
    _, out = git("log", "--first-parent", "--merges", "--format=%H|%P|%s|%cI", "HEAD")
    found = []
    for line in reversed(out.splitlines()):
        h, parents, subject, when = line.split("|", 3)
        parents, pr = parents.split(), re.search(r"#(\d+)", subject)
        if len(parents) == 2 and pr and when >= since:
            found.append(dict(h=h, p1=parents[0], p2=parents[1], pr=int(pr.group(1)), when=when))
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="")
    ap.add_argument("--window", type=int, default=6)
    a = ap.parse_args()
    ms = merges(a.since)
    tested = skipped = 0
    pairs, hunks, files = collections.Counter(), collections.Counter(), collections.Counter()
    conflicting = 0
    for i, later in enumerate(ms):
        for earlier in ms[max(0, i - a.window) : i]:
            tested += 1
            # Main just before `later`, with `earlier` taken back out...
            rc, tree, _ = merge_tree(earlier["h"], later["p1"], earlier["p1"])
            if rc != 0:
                skipped += 1
                continue
            _, without = git("commit-tree", tree, "-p", later["p1"], "-m", "replay")
            # ...then `later`'s change on top of it.
            rc, merged, paths = merge_tree(later["p1"], without.strip(), later["p2"])
            if rc != 1:
                skipped += rc > 1
                continue
            conflicting += 1
            causes = set()
            for path in paths:
                files[path] += 1
                _, text = git("cat-file", "-p", f"{merged}:{path}")
                item = None
                for line in text.splitlines():
                    m = ITEM.match(line)
                    if m:
                        item = f"{m.group(1)} {m.group(2)}"
                    if line.startswith("<<<<<<<"):
                        c = cause(path, item)
                        hunks[c] += 1
                        causes.add(c)
            for c in causes:
                pairs[c] += 1
            if "code body" not in causes:
                pairs["(no code-body hunk)"] += 1
    print(f"{len(ms)} merges, {tested} pairs, {skipped} not replayable, {conflicting} conflicting")
    print("pairs by cause:", dict(pairs.most_common()))
    print("hunks by cause:", dict(hunks.most_common()))
    print("files in most conflicting pairs:")
    for path, n in files.most_common(12):
        print(f"  {n:4} {path}")


if __name__ == "__main__":
    main()
