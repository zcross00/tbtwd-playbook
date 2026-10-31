# Changelog

## 2.2 (merges in the Saturday window)

Rules the reference project kept in its own process file, brought into the playbook:

- A new system gets a spec before its code (Tracking work).
- Acceptance feedback is kept as a verbatim transcript that its issues link (Tracking work).
- Work that turns out bigger mid-build is split and re-planned (Tracking work).
- A PR with no issue opens one first, unless docs-only (Lifecycle, rule 1).
- Reopening an issue in a closed milestone reopens the milestone (Lifecycle, rule 12).
- A train re-runs when `main` moved under it in overlapping files (Working in parallel).

## 2.0 (2026-10-31)

- Rebranded as the **TBTWD Playbook**, repository renamed from `ProcessDocumentation` to `tbtwd-playbook`.
- New baseline extracted from a live multi-agent project: roles (owner, coordinator, work threads, Code review, Verification, Dev process, retro), tracking and grooming, the lifecycle and definition of done, parallel work and merge trains, CI tiers from one laptop to enterprise, tests and gates, estimating and forecasting, cadences, adoption and the enforcement kit.
- New templates: project PROCESS.md, milestone, issue, decision, and a GitHub kit (PR template, issue forms, `playbook-lint` workflow).
- Version 1 (Planner/Executor roles, direct merges, agent and skill files) moved to `archive/v1/`. Standards, style and design-artifact templates carried over unchanged.

## 1.0 (2026-04)

- Planner/Executor model, coding standards (general, Java, C#), documentation style, design-artifact templates.
