---
name: backlog-entry
description: "BACKLOG ENTRY SKILL — Produce a correctly formatted BL-N backlog entry with all required fields. USE FOR: adding new items to design/BACKLOG.md (features, rework, tech debt, drift items); any role that needs to create a backlog entry. Enforces ID uniqueness and required field completeness. DO NOT USE FOR: updating or removing existing entries (edit directly)."
---

# Backlog Entry

Use this skill whenever a new item must be added to `design/BACKLOG.md`. It enforces correct format and prevents ID collisions.

---

## Step 1 — Determine the Next ID

Open `design/BACKLOG.md`. Find the highest `BL-N` number currently present anywhere in the file. The new item's ID is `(highest found) + 1`.

IDs are never reused. If the previous highest was `BL-19`, the new item is `BL-20` regardless of how many items were removed.

---

## Step 2 — Classify the Item

Choose exactly one Type and one Priority.

**Type:**

| Type | When to use |
|------|-------------|
| `Feature` | New capability or behavior described in the design |
| `Rework` | Existing behavior needs to change |
| `TechDebt` | Internal quality improvement with no user-visible change |
| `Bug` | Defect — something is broken or incorrect |

**Priority:**

| Priority | Meaning |
|----------|---------|
| `P1` | Must address next — correctness-blocking or goal-critical |
| `P2` | Important; schedule soon |
| `P3` | Valuable but deferrable |
| `P4` | Low urgency or speculative |

---

## Step 3 — Write the Entry

Produce both a table row and a detail block. Both are required.

**Table row** (place in the correct priority section):
```
| BL-N | [Type] | [One-line synopsis] | [Source] |
```

- **Synopsis:** One sentence, imperative, describing what needs to happen.
- **Source:** Where this item came from — a design section reference (e.g., `S-1`), a review finding, or a direct observation.

**Detail block** (inserted after the table in the same priority section):
```
<!-- item: BL-N -->
**BL-N Detail:**
[Describe what needs to happen and any constraints or context that would help an EXECUTOR implement it. Be specific — vague items stall. Include enough detail that the EXECUTOR does not need to ask clarifying questions.]

**Done-when:** [Unambiguous, verifiable completion criteria.]
**Design-Ref:** [DESIGN.md section reference, e.g., S-1, S-3]
**Dependencies:** [BL-N ID(s) that must be completed first, or None]
**Branch:** —
```

---

## Step 4 — Placement Rules

- Items go in the section matching their priority (`### P1`, `### P2`, etc.).
- Within a priority section, new items append to the end of the table and end of the detail blocks.
- Do not sort or renumber existing items.
