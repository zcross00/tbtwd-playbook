# The kit

The process tooling, so a project following the playbook doesn't carry its own copy. A project keeps one settings file, `.playbook.toml`, at the root of its repository, and thin workflows that call the playbook's. Everything reads the playbook's `main`, which is the process.

Extracted from the reference project, where each tool was built for a failure it had (the docstrings say which).

---

## What's here

| Directory | Tool | What it does |
|---|---|---|
| `board/` | `sync.py` | Copies the `board:` lines threads write on issues into the owner's project board's fields ([Estimating](../playbook/08-estimating.md)) |
| | `milestones.py` | The daily burn-down of the open milestones, for the morning report |
| | `forecast.py` | Re-forecasts each open milestone's due date from its measured pace; closed milestones get a forecast-against-close line |
| | `pr_milestone.py` | Gives each open PR the milestone of the issues it refs |
| | `paperwork.py` | Checks a PR's paperwork: no closing word, a `Refs #N` line on a code PR, each ref'd issue in a milestone and groomed, a `deferred gate` issue for a loosened gate |
| `wiki/` | `gen.py`, `publish.sh` | Generates every wiki page from GitHub (status, milestones, roadmap, decisions, hand pages) and pushes them. `gen.py --check` is a daily backlog review step |
| | `answer.py` | The owner answers a `decision` issue by commenting on it; the comment is quoted in and the issue closes |
| `queue/` | `pc_queue.py` | Orders CI runs waiting for one full runner: `main-fix`, then priority A, then oldest; trains carry their members; overflow to a hosted machine within budget ([CI tiers](../playbook/06-ci.md)) |
| | `newer_run.py` | Stops an older run when a newer run checks the same head |
| | `train.sh` | Builds a merge train from approved PRs ([Working in parallel](../playbook/05-parallel.md)) |
| `ci/` | `live-draft.sh`, `docs-only.sh`, `mergeable.sh`, `fresh-merge.sh`, `main-moved.sh` | The CI workflow's gate steps: draft and train now, docs-only skip, conflict check, merge today's main, warn when main moved |
| `churn/` | `minutes.py` | Hosted Actions minutes and dollars against the month's budget, and board-sync health |
| | `week.sh` | The week's build churn: queue wait, CI wall time, re-merges of main |
| | `replay.py` | Replays merged PRs pairwise and sorts their conflicts by cause |
| `releases/` | `release_notes.py` | Links each playtest pre-release to its milestone, issues and commit; marks older builds superseded |
| `review/` | `scan.py` | Picks and flags the day's backlog review ([Cadences](../playbook/09-cadences.md)) |
| `usage/` | `pace.py`, `pc_hours.py`, `usage_report.py` | The weekly usage report: pace against the reset, self-hosted runner hours, cost by area |
| `lib/` | `playbook_config.py`, `config.sh` | Reads `.playbook.toml` for the Python and shell tools |

Every script runs from the project's checkout. `run.sh` runs one (`kit/run.sh board/sync.py --apply`); `python.sh` finds Python 3.11+, or on a self-hosted Windows runner with none installed, fetches a pinned embeddable one.

---

## Using it on a project

1. **Copy [example.playbook.toml](example.playbook.toml)** to `.playbook.toml` at the project's root and set the values. Every key is optional; one left out takes the default in [lib/playbook_config.py](lib/playbook_config.py).
2. **Call the reusable workflows** from thin workflows in the project. The project keeps the triggers, the `if:` filters, concurrency and permissions; the playbook keeps the steps:

   ```yaml
   # .github/workflows/board.yml in the project
   name: board
   on:
     issue_comment: { types: [created, edited] }
     issues: { types: [closed, reopened] }
     workflow_dispatch:
   permissions:
     contents: read
   jobs:
     sync:
       uses: zcross00/tbtwd-playbook/.github/workflows/kit-board.yml@main
       with:
         runs-on: '["self-hosted", "light"]'
         apply: true
       secrets: inherit
   ```

   | Workflow | Runs |
   |---|---|
   | `kit-board.yml` | `board/sync.py` (secret `BOARD_TOKEN`: a classic PAT with `project` scope) |
   | `kit-forecast.yml` | `board/forecast.py` |
   | `kit-pr-milestone.yml` | `board/pr_milestone.py` |
   | `kit-paperwork.yml` | `board/paperwork.py` on one PR (input `pr`); red on a problem |
   | `kit-wiki.yml` | `wiki/publish.sh` (`paths`: the project files the pages read) |
   | `kit-decision-answer.yml` | `wiki/answer.py`, then the wiki |
   | `kit-release-notes.yml` | `releases/release_notes.py` |
   | `kit-churn.yml` | `churn/week.sh` |
   | `kit-conflicts.yml` | the `conflict` label |

   Self-hosted runners in `runs-on` are the project's own: a called workflow's jobs run on the caller's runners.
3. **In the project's own CI workflow**, check the playbook out at `.playbook` and run the gate steps through the `kit-run` action, so job names (`files`, `queue`, `full`) stay the project's:

   ```yaml
   - uses: actions/checkout@v4
     with:
       repository: zcross00/tbtwd-playbook
       path: .playbook
       sparse-checkout: |
         kit
         .github/actions
       sparse-checkout-cone-mode: false
   - uses: ./.playbook/.github/actions/kit-run
     with:
       script: queue/pc_queue.py
     env:
       GH_TOKEN: ${{ github.token }}
   ```

   Add `.playbook/` to the project's `.gitignore`.
4. **From a session**, clone the playbook and run tools from the project's checkout: `python3 ../tbtwd-playbook/kit/churn/minutes.py --days 7`.

---

## Changing the kit

A kit change is a playbook change: a PR here, merged in the Saturday window ([CONTRIBUTING.md](../CONTRIBUTING.md)), and every project picks it up on its next run. `bash kit/test.sh` runs the tests against `example.playbook.toml`; the `kit-tests` workflow runs them on every PR that touches the kit. Something only one project needs is a setting in `.playbook.toml`, not a fork of the script.
