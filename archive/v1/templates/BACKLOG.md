---
updated: "{{date}}"
---

# {{Project Name}} — Backlog

This is the living work backlog. It tracks every identified item that has not yet been implemented. Items are derived from `DESIGN.md` and represent implementable units of work.

Git history is the log of resolved items. When an item is completed, the PLANNER removes it from here after review. The backlog contains only what's still pending.

---

<!-- section: how-to-read -->
## How to Read This

Each item has:
- **ID** — Sequential `BL-N`, never reused.
- **Priority** — `P1` (must address next), `P2` (important, schedule soon), `P3` (valuable but deferrable), `P4` (low urgency or speculative).
- **Type** — `Feature`, `Rework`, `TechDebt`, `Bug`.
- **Synopsis** — One-line description.
- **Source** — Where the item came from: a design section reference (e.g., `S-1`), a review finding, or a direct observation.
- **Detail** — Full specification of what needs to be implemented. Must contain enough context for an EXECUTOR to implement without clarifying questions.
- **Done-when** — Unambiguous, verifiable completion criteria.
- **Design-Ref** — Which DESIGN.md section this item traces to.
- **Dependencies** — `BL-N` IDs that must be resolved before this item can start. Use `None` if there are no blockers.
- **Branch** — `work/BL-N` when claimed, `—` when unassigned.

---

<!-- section: backlog -->
## Backlog

<!-- section: p1 -->
### P1 - Must Address Next

| ID | Type | Synopsis | Source |
|----|------|----------|--------|

<!-- section: p2 -->
### P2 - Important, Schedule Soon

| ID | Type | Synopsis | Source |
|----|------|----------|--------|

<!-- section: p3 -->
### P3 - Valuable but Deferrable

| ID | Type | Synopsis | Source |
|----|------|----------|--------|

<!-- section: p4 -->
### P4 - Low Urgency / Speculative

| ID | Type | Synopsis | Source |
|----|------|----------|--------|
