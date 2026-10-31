---
name: drift-entry
description: "DRIFT ENTRY SKILL — Log a counter-goal implementation to design/DRIFT.md. USE FOR: any role that identifies an implementation working against a stated goal; adding a new drift item or a new instance to an existing drift item. Enforces the no-duplicate rule and ensures every entry links to a goal. DO NOT USE FOR: resolving drift (create a backlog item instead)."
---

# Drift Entry

Use this skill whenever you identify an implementation that works against one of the project's stated goals.

---

## Step 1 — Confirm It Is Drift

Drift is an implementation that actively works against a goal in `design/GOALS.md`. It is not:
- A missing feature (that is a backlog item).
- A known limitation (that may be acceptable).
- A style violation (that is a standards issue).

The test: *Does this thing make a stated goal harder to achieve?* If yes, it is drift.

---

## Step 2 — Check for Existing Items

Open `design/DRIFT.md`. Scan the active items for one that describes the same drift pattern.

- **If a matching item exists** — go to Step 4 (add an instance).
- **If no match** — go to Step 3 (create a new item).

**Never create a duplicate.** Two entries about the same underlying problem must be merged into one.

---

## Step 3 — Create a New Drift Item

Determine the next `DR-N` ID: find the highest existing ID and add 1.

Add a new entry in the **Active** section:

```markdown
<!-- drift: DR-N -->
### DR-N — [Short title describing the drift]

**Against Goal:** G-N — [goal title]
**Severity:** [Low | Medium | High]
**First Observed:** [YYYY-MM-DD]

[One paragraph explaining what the implementation does and why it works against the goal.]

**Instances:**
1. [Specific location or behavior — file, class, method, or user-facing description]

**Resolution:** Pending — see BL-N (if a backlog item has been created) or "No backlog item yet."
```

**Severity guide:**
- **High** — Actively prevents the goal from being achieved.
- **Medium** — Partially undermines the goal or creates friction.
- **Low** — Minor tension with the goal; acceptable short-term.

---

## Step 4 — Add an Instance to an Existing Item

Find the matching `DR-N` entry. Add a numbered line to the **Instances** list:

```
N. [Specific location or behavior]
```

If the new instance changes the severity (e.g., the pattern is now more widespread), update the severity.

---

## Step 5 — Create a Backlog Item (If Warranted)

If the drift is Medium or High severity and no `BL-N` exists for it yet:

1. Use the **backlog-entry** skill to create a new backlog item.
2. Set Type to `Rework`.
3. Reference the `DR-N` in the detail block.
4. Update the drift entry's **Resolution** line to `Pending — see BL-N`.
