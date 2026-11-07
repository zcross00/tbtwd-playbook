# Changelog

## 2.5 (merges in the Saturday window)

- New page [Teams](playbook/11-teams.md): equal agent teams on one project, each with its own coordinator, lanes, Code review, Verification, grooming, retro and usage report. Issues and milestones belong to a team by assignee (or a `team:<name>` label while two teams share one login) and a `Team:` line. `main` requires one approving review, which with one login per team always comes from the other team; while a login is shared the ruleset is off and the review is a signed PR comment. A 6-hour fallback goes to the owner.
- Teams talk by email, one address per team, with `[decision]`, `[question]`, `[proposal]`, `[needs-owner]` and `[fyi]` subjects, and each coordinator watches its own address hourly. GitHub carries the work, reviews included; a PR waiting for the other team carries a `review:<name>` label.
- Supersedes the unmerged "Two crews" page (PR #15).

## 2.3.2 (2026-11-06, emergency: a 3-hour silent queue stall)

- `kit/queue/pc_queue.py`: a run ahead in the queue counts only while it can still take the PC. A run whose `full` has finished, or whose `queue` job was skipped, failed or was cancelled, no longer holds every later run behind it, even when GitHub keeps it listed as in progress.
- `kit/queue/pc_queue.py`: a run that has waited 15 minutes behind others while nothing holds the PC fails as `QUEUE STUCK`, naming the run ahead, so whoever watches the PR hears in 15 minutes and not hours.

## 2.3.1 (2026-11-02, owner declared it urgent)

- License: the whole repository is now MIT (was CC BY 4.0), so the docs and the `kit/` code can be used commercially under one standard software license. No rule changes.

## 2.3 (2026-10-31, initial setup; the owner waived the Saturday window)

- New `kit/`: the process tooling moved here from the reference project, so the project keeps only one `.playbook.toml` and thin workflows. Board sync, milestone burn-down and forecast, PR milestones, the generated wiki and decision answers, the CI queue, newer-run check and merge trains, the CI gate scripts, hosted-minutes and churn reports, conflict replay, release notes, the daily backlog scan and the weekly usage report.
- Reusable workflows `kit-board`, `kit-forecast`, `kit-pr-milestone`, `kit-wiki`, `kit-decision-answer`, `kit-release-notes`, `kit-churn`, `kit-conflicts`, and the `kit-run` action; `kit-tests` runs the kit's tests on every PR.
- The kit names no one: it says "the owner" (`project.owner_name` sets the name the pages use), quotes no private messages, and keeps budget figures only in `.playbook.toml`. `kit-conflicts` pins its third-party action to a commit.

## 2.2 (merges in the Saturday window)

Rules the reference project kept in its own process file, brought into the playbook:

- A new system gets a spec before its code (Tracking work).
- Acceptance feedback is kept as a verbatim transcript that its issues link (Tracking work).
- Work that turns out bigger mid-build is split and re-planned (Tracking work).
- A PR with no issue opens one first, unless docs-only (Lifecycle, rule 1).
- Reopening an issue in a closed milestone reopens the milestone (Lifecycle, rule 12).
- A train re-runs when `main` moved under it in overlapping files (Working in parallel).

## 2.1 (merges in the Saturday window)

- `main` is the only process. Projects follow it as it stands: no version pin, no "Differences from the playbook" section, no project file that wins over it. The PROCESS.md template holds only project facts and engineering rules.
- Changes merge on Saturday from 11:00 America/Chicago, except an emergency the owner declares (`emergency` label plus an `Emergency:` line quoting them). The `merge-window` workflow enforces it as a required status.
- Retro picks land here, not in the project's PROCESS.md.

## 2.0 (2026-10-31)

- Rebranded as the **TBTWD Playbook**, repository renamed from `ProcessDocumentation` to `tbtwd-playbook`.
- New baseline extracted from a live multi-agent project: roles (owner, coordinator, work threads, Code review, Verification, Dev process, retro), tracking and grooming, the lifecycle and definition of done, parallel work and merge trains, CI tiers from one laptop to enterprise, tests and gates, estimating and forecasting, cadences, adoption and the enforcement kit.
- New templates: project PROCESS.md, milestone, issue, decision, and a GitHub kit (PR template, issue forms, `playbook-lint` workflow).
- Version 1 (Planner/Executor roles, direct merges, agent and skill files) moved to `archive/v1/`. Standards, style and design-artifact templates carried over unchanged.

## 1.0 (2026-04)

- Planner/Executor model, coding standards (general, Java, C#), documentation style, design-artifact templates.
