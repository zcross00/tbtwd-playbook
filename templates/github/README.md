# GitHub kit

Drop-in files for a project that follows the playbook. Copy into the project's `.github/` keeping the layout:

| File | Copy to | Does |
|------|---------|------|
| `pull_request_template.md` | `.github/pull_request_template.md` | The Refs + evidence layout every PR fills |
| `ISSUE_TEMPLATE/*.yml` | `.github/ISSUE_TEMPLATE/` | Work, decision, deferred gate, and parked issue forms |
| `workflows/playbook-lint.yml` | `.github/workflows/` | Fails a PR whose body or commits would close an issue, or a code PR with no `Refs #N` |
| `scripts/playbook_lint.py` | `.github/scripts/` | The lint itself (stdlib Python 3) |

Then, in branch protection, make `playbook-lint` a required check alongside the merge gate (`full`).

Test the lint locally: `python3 scripts/test_playbook_lint.py`.
