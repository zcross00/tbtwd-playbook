# Project Instructions — Sovereign

## Start Here

Before doing any non-trivial work in this project, read:

**[AGENTS.md](https://github.com/zcross00/ProcessDocumentation/blob/main/AGENTS.md)**

That file is the primary entry point for all process, coding standards, and workflow rules. It tells you what to read next based on what you are doing.

---

## Role Assignment

If you have not been explicitly told your role, you are an **EXECUTOR**. Read [`process/roles.md`](https://github.com/zcross00/ProcessDocumentation/blob/main/process/roles.md) for role definitions. Once assigned, your role is permanent for the session — no transitions.

---

## Process Documentation Reference

The **[ProcessDocumentation](https://github.com/zcross00/ProcessDocumentation)** repository is the source of truth for:

| File | Contains |
|------|----------|
| [AGENTS.md](https://github.com/zcross00/ProcessDocumentation/blob/main/AGENTS.md) | Primary agent entry point — start here |
| [process/roles.md](https://github.com/zcross00/ProcessDocumentation/blob/main/process/roles.md) | PLANNER and EXECUTOR role definitions and workflows |
| [process/git-workflow.md](https://github.com/zcross00/ProcessDocumentation/blob/main/process/git-workflow.md) | Branch naming, commit format, merge workflow |
| [standards/general.md](https://github.com/zcross00/ProcessDocumentation/blob/main/standards/general.md) | Language-agnostic coding rules (apply always) |
| [standards/java.md](https://github.com/zcross00/ProcessDocumentation/blob/main/standards/java.md) | Java-specific conventions |
| [style/documentation.md](https://github.com/zcross00/ProcessDocumentation/blob/main/style/documentation.md) | Tone, headings, table formatting for all docs |
| [templates/](https://github.com/zcross00/ProcessDocumentation/tree/main/templates) | Templates for GOALS, DESIGN, FEATURES, BACKLOG, DRIFT |

Follow these conventions over ad-hoc decisions. If a project file conflicts with a ProcessDocumentation standard, note the divergence — don't silently resolve it.

---

## Design Artifacts

All design documents for this project live in the `design/` folder on the active branch:

- `design/GOALS.md` — project goals; read first to understand what success looks like
- `design/DESIGN.md` — comprehensive design breakdown; agent-optimized, highly indexable
- `design/FEATURES.md` — catalog of implemented features linked to goals
- `design/BACKLOG.md` — all open work items with priorities
- `design/DRIFT.md` — implementations that work against the user's goals

---

## Agent Skills

Skills are pre-packaged, task-specific instructions for common workflows. Before starting any of the tasks below, read the corresponding skill file — it contains exact steps, commands, and rules that supersede ad-hoc reasoning.

| Skill | When to use | File |
|---|---|---|
| `agent-orientation` | Start of every session — read project state, determine active role | `.github/skills/agent-orientation/SKILL.md` |
| `git-workflow` | Branch creation, merging, tagging | `.github/skills/git-workflow/SKILL.md` |
| `build-verify` | Before committing any code changes — compile and run all tests | `.github/skills/build-verify/SKILL.md` |
| `backlog-entry` | Adding a new item to `design/BACKLOG.md` | `.github/skills/backlog-entry/SKILL.md` |
| `drift-entry` | Logging a counter-goal implementation to `design/DRIFT.md` | `.github/skills/drift-entry/SKILL.md` |
| `planner-review` | PLANNER reviewing a completed backlog item | `.github/skills/planner-review/SKILL.md` |
| `executor-loop` | EXECUTOR picking up and implementing the next backlog item | `.github/skills/executor-loop/SKILL.md` |
| `test-writing` | Writing new JUnit 5 tests for engine or domain logic | `.github/skills/test-writing/SKILL.md` |
| `domain-model` | Deciding the correct Java construct (JavaBean vs. record vs. enum) for a new type | `.github/skills/domain-model/SKILL.md` |
| `standards-check-java` | Standards compliance check on a Java file or diff | `.github/skills/standards-check-java/SKILL.md` |
| `refinement` | PLANNER analyzing design/features/backlog to identify and plan needed work | `.github/skills/refinement/SKILL.md` |
