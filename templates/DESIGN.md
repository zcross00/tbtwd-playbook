---
version: "1.0"
updated: "{{date}}"
goals-version: "{{goals version this design is based on}}"
---

# {{Project Name}} — Design

This document is the comprehensive breakdown of how to realize the project's goals. It bridges the gap between what the user wants to accomplish (GOALS.md) and what needs to be implemented (BACKLOG.md).

**This document is optimized for agent consumption.** It is expected to be large. Every section uses HTML comment anchors for fast indexing. Human readability is secondary to agent navigability.

---

<!-- section: goals-summary -->
## Goals Summary

Reference copy of active goals for inline cross-referencing. The authoritative source is `GOALS.md`.

| ID | Goal | Version |
|----|------|---------|
| G-1 | {{Goal 1 title}} | {{goals version}} |
| G-2 | {{Goal 2 title}} | {{goals version}} |
| G-3 | {{Goal 3 title}} | {{goals version}} |

---

<!-- section: systems -->
## Systems

Each system section describes a coherent area of functionality needed to realize one or more goals. Systems are the primary unit of design decomposition.

<!-- section: system-1 -->
### S-1: {{System Name}}

**Serves goals:** G-1, G-3
**Status:** {{Not Started | In Progress | Implemented | Needs Rework}}

#### Intent

{{What this system is meant to accomplish and why it exists. 2–4 sentences.}}

#### Components

{{List the concrete classes, modules, data structures, or UI elements this system requires. Be specific — a work thread will use this to understand what to build.}}

#### Behaviors

{{Describe the runtime behaviors this system exhibits. What happens when? What triggers what? What are the inputs and outputs?}}

#### Constraints

{{Any rules, limits, or invariants this system must maintain.}}

#### Dependencies

{{Other systems this one depends on. Reference by S-N ID.}}

#### Open Questions

{{Anything not yet decided. These block backlog item creation until resolved.}}

---

<!-- section: system-2 -->
### S-2: {{System Name}}

{{Same structure as S-1. Repeat for each system.}}

---

<!-- section: technical-debt -->
## Technical Debt

Identified technical debt that actively obstructs progress toward the project's goals. Every item here must have a corresponding `DR-N` entry in DRIFT.md — technical debt is drift.

| ID | Description | Affected Goals | Urgency | Impact | DRIFT Ref | BACKLOG Ref |
|----|-------------|----------------|---------|--------|-----------|-------------|
| TD-1 | {{Short description of the debt}} | G-{{N}} | {{Low \| Medium \| High}} | {{How this debt obstructs the goal}} | DR-{{N}} | BL-{{N}} or Pending |

**Urgency guide:**
- **High** — Blocks near-term work or compounds daily.
- **Medium** — Slows progress noticeably; should be scheduled.
- **Low** — Manageable for now; address when convenient.

**Impact guide:** Describe the concrete effect on the linked goal(s) — not the code smell itself, but what the debt *prevents or degrades* in terms of goal progress.

---

<!-- section: decisions -->
## Design Decisions

Log of significant design decisions with rationale. Decisions are permanent records — do not delete them when they become obsolete; mark them as superseded.

| ID | Decision | Rationale | Date | Superseded By |
|----|----------|-----------|------|---------------|
| D-1 | {{What was decided}} | {{Why}} | {{date}} | — |

---

<!-- section: changelog -->
## Changelog

### v1.0 — {{date}}
- Initial design created from Goals v{{goals version}}.
