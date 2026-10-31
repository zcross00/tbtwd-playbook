---
name: refinement
description: "REFINEMENT SKILL — Analyze design, features, backlog, and drift to identify and plan needed work. USE FOR: PLANNER producing new backlog items from gaps between design and current state; evaluating tech debt and drift for resolution; structured backlog growth when the user asks the PLANNER to refine or plan more work. DO NOT USE FOR: implementing backlog items (EXECUTOR work); reviewing completed work (use planner-review skill)."
---

# Refinement

Use this skill when the PLANNER is directed to refine — that is, to analyze the current project state and produce new backlog items for work not yet planned.

---

## Arguments

| Argument | Default | Meaning |
|----------|---------|---------|
| count | 10 | Number of backlog items to produce |

If the user specifies a count (e.g., "refine 5 items"), use that number. Otherwise, produce **10** items.

---

## Step 1 — Read Project State

Read these files in order:

1. `design/GOALS.md` — Understand what success looks like.
2. `design/DESIGN.md` — Understand the full system design, including the Technical Debt section.
3. `design/FEATURES.md` — Understand what has already been implemented.
4. `design/BACKLOG.md` — Understand what is already planned.
5. `design/DRIFT.md` — Understand what is working against the goals.

---

## Step 2 — Identify Gaps

Compare the design against the feature list and backlog to find work that is:

- **Described in the design but not yet implemented** (no matching feature) **and not yet planned** (no matching backlog item).
- **Technical debt** listed in the Technical Debt section of DESIGN.md that has no corresponding backlog item and whose urgency/impact warrants resolution.
- **Active drift** in DRIFT.md that has no corresponding backlog item for resolution and is Medium or High severity.
- **Missing infrastructure** implied by the design but not explicitly called out — e.g., a system references a concept that has no supporting code, or a feature depends on a mechanism that doesn't exist yet.

Skip anything that is already in the backlog or confirmed in the feature list.

---

## Step 3 — Prioritize

Rank identified gaps by:

1. **Goal impact** — Items that unblock or directly advance a goal rank higher.
2. **Dependency order** — Items that other items depend on rank higher.
3. **Urgency** — High-urgency tech debt and high-severity drift rank higher.
4. **Breadth** — Items that advance multiple goals rank higher than single-goal items.

Select the top N items (where N is the count argument).

---

## Step 4 — Create Backlog Items

For each selected gap, use the **backlog-entry** skill to create a properly formatted `BL-N` entry.

Each entry must:
- Trace to a specific section in DESIGN.md (Design-Ref field).
- Link to the goal(s) it serves.
- Have clear Done-when criteria.
- If the item resolves tech debt, reference the `TD-N` and `DR-N` entries.
- If the item resolves drift, reference the `DR-N` entry.

---

## Step 5 — Communicate

Report to the user:
- How many items were created and their IDs (e.g., BL-80 through BL-89).
- A brief summary of the themes covered (e.g., "3 items for resource system gaps, 2 for tech debt resolution, 5 for missing AI behaviors").
- Any notable gaps that were identified but deferred (beyond the count limit).
