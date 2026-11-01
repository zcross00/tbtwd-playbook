# Changelog

## 2.5 (merges in the Saturday window)

- Grooming checks dependency order before it sets a due date. A milestone names the milestones it waits on with `After: m<N>` and is due no earlier than the day after the latest of them. Dependents move together (Estimating, Burn-down and re-forecast). The daily re-forecast learning `After:` is kit issue #10.

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
