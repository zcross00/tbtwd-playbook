#!/usr/bin/env python3
"""TBTWD Playbook PR lint (playbook/04-lifecycle.md, rules 1 and 2).

Fails when the PR body or any commit message would close an issue on merge
(a closing keyword right before #N), or when a PR that touches more than
docs has no "Refs #N" line.

Usage: playbook_lint.py BODY_FILE COMMITS_FILE DOCS_ONLY(true|false)
"""
import re
import sys

CLOSING = re.compile(
    r"\b(close[sd]?|fix(e[sd])?|resolve[sd]?)\b[\s:]*"
    r"((\w[\w.-]*/[\w.-]+)?#\d+|https://github\.com/\S+/issues/\d+)",
    re.IGNORECASE,
)
REFS = re.compile(r"^\s*Refs\s+#\d+", re.IGNORECASE | re.MULTILINE)


def check(body: str, commits: str, docs_only: bool) -> list[str]:
    errors = []
    for where, text in (("PR body", body), ("commit messages", commits)):
        for m in CLOSING.finditer(text):
            errors.append(
                f'{where}: "{m.group(0)}" would close the issue on merge. '
                'Write "Refs #N", or "the fix in #N" to mention it.'
            )
    if not docs_only and not REFS.search(body):
        errors.append('PR body: no "Refs #N" line. Open an issue first (only docs-only PRs are exempt).')
    return errors


def main() -> int:
    body = open(sys.argv[1], encoding="utf-8").read()
    commits = open(sys.argv[2], encoding="utf-8").read()
    docs_only = sys.argv[3] == "true"
    errors = check(body, commits, docs_only)
    for e in errors:
        print(f"::error::{e}")
    if not errors:
        print("playbook-lint: ok")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
