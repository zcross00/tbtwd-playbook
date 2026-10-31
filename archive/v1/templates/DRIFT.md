---
updated: "{{date}}"
goals-version: "{{goals version}}"
---

# {{Project Name}} — Drift Log

This document catalogs implementations that work against the user's stated goals. Drift is a measure of how far the project's actual state has diverged from the intended direction.

An implementation qualifies as drift when it:
- **Harms** a goal's chance of success
- **Contradicts** what a goal intends
- **Does not further** any goal while consuming project resources or adding complexity
- **Constitutes technical debt** that actively obstructs progress toward a goal

Drift is not a bug list. Bugs are defects in intended behavior. Drift is correct behavior that moves the project in the wrong direction relative to its goals.

**Technical debt is drift.** Any identified technical debt is an active obstacle to the user's goals — it slows progress, increases risk, or constrains design options. Every piece of identified technical debt must have a corresponding DRIFT entry linking it to the goal(s) it obstructs. The DRIFT entry establishes the record; the DESIGN.md Technical Debt section captures urgency and impact; a BACKLOG item plans the resolution.

---

<!-- section: rules -->
## Rules

- **No duplicate entries.** If additional instances of the same drift are found, add them to the existing item's Instances section.
- **Every entry links to a goal.** Drift is defined relative to goals — if it doesn't affect a goal, it's not drift.
- **Resolution creates a backlog item.** When drift is identified, create a corresponding `BL-N` item in BACKLOG.md to address it.

---

<!-- section: active-drift -->
## Active Drift

Items that have been identified but not yet resolved.

<!-- drift: DR-1 -->
### DR-1: {{Title}}

**Affects goal:** G-{{N}} — {{Goal title}}
**Severity:** {{Minor | Moderate | Severe}} — {{one sentence explaining impact on the goal}}
**Identified:** {{date}}
**Resolution backlog item:** BL-{{N}}

#### Description

{{What was implemented that works against the goal. Be specific about the behavior or code.}}

#### Instances

| # | Location | Description | Date |
|---|----------|-------------|------|
| 1 | {{file or system}} | {{what was observed}} | {{date}} |

---

<!-- section: resolved-drift -->
## Resolved Drift

Items that have been addressed. Moved here after the resolution backlog item is completed.

| ID | Title | Affected Goal | Resolution | Date Resolved |
|----|-------|---------------|------------|---------------|
