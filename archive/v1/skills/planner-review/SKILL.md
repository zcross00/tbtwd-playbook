---
name: planner-review
description: "PLANNER REVIEW SKILL — Review a completed backlog item and update design artifacts accordingly. USE FOR: PLANNER reviewing an EXECUTOR's completed work; updating FEATURES.md after a feature lands; removing completed items from BACKLOG.md; checking for drift. DO NOT USE FOR: implementing backlog items (EXECUTOR work); initial planning (read GOALS and DESIGN directly)."
---

# Planner Review

Use this skill after an EXECUTOR reports that a backlog item is complete. The PLANNER verifies the work and updates design artifacts.

---

## Step 1 — Read the Backlog Item

Open `design/BACKLOG.md` and find the reported `BL-N`. Read the full detail block, including:
- The description of what was requested.
- The **Done-when** criteria.
- The **Design-Ref**.

---

## Step 2 — Verify Completion

Check each **Done-when** criterion against the actual codebase:

- Read the files mentioned or implied by the criteria.
- Run `build-verify` (or confirm the EXECUTOR already did).
- Confirm all criteria are met. If any criterion is not met, stop and communicate to the user what is incomplete.

**Verdict:** All done-when criteria pass → proceed. Any criterion fails → report the gap; do not update artifacts.

---

## Step 3 — Update FEATURES.md

If the completed item was type `Feature` or `Rework` that adds visible capability:

1. Open `design/FEATURES.md`.
2. Find the goal section matching the item's linked goal.
3. Add a row to the feature table:

```
| [Feature name] | [Brief description] | BL-N | YYYY-MM-DD |
```

If the feature doesn't clearly map to a goal, add it to the **Features Without Goal Link** section and consider logging drift.

---

## Step 4 — Remove from BACKLOG.md

Delete both the table row and the detail block for the completed `BL-N`. Do not renumber other items.

If priority section becomes empty after removal, leave the section header in place.

---

## Step 5 — Check for Follow-Up Work

Review the implementation for:

1. **Drift** — Does anything in the implementation work against a stated goal? If yes, use the **drift-entry** skill.
2. **New backlog items** — Did the implementation reveal needed follow-up work? If yes, use the **backlog-entry** skill.
3. **Design updates** — Does `design/DESIGN.md` need to reflect new decisions, constraints, or changes that emerged during implementation? If yes, update the relevant section.

---

## Step 6 — Communicate

Report the review result to the user:
- Confirmed complete, artifacts updated.
- Or: incomplete, with specific gaps listed.
