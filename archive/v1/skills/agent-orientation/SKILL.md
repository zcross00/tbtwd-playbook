---
name: agent-orientation
description: "ORIENTATION SKILL — Run at the start of every agent session. Reads project artifacts in the correct order, determines the active role per the waterfall, and produces a session brief. USE FOR: starting a new session; determining which role to assume; fast orientation after a gap; confirming project state before picking up work. DO NOT USE FOR: mid-task context checks (read files directly); orientation when the user has explicitly assigned a role (skip waterfall step)."
---

# Agent Orientation

Use this skill at the beginning of every session before doing any work. It produces a session brief and confirms the active role.

---

## Step 1 — Pull Current State

```bash
git fetch --prune
git checkout {active-branch}
git pull
```

Confirm you are on the active branch and it is up to date before reading any design artifacts.

---

## Step 2 — Read Artifacts in Order

Read these files in sequence. Each one narrows context established by the previous.

| Order | File | Purpose |
|-------|------|---------|
| 1 | `design/GOALS.md` | What success looks like. Understand what the project is optimizing for. |
| 2 | `design/DESIGN.md` | Comprehensive design breakdown. Understand the intended path to those goals. |
| 3 | `design/FEATURES.md` | What has been implemented. Understand the current state. |
| 4 | `design/BACKLOG.md` | All open items: priorities, dependencies. Identify what is unblocked. |
| 5 | `design/DRIFT.md` | Active drift items. Understand where the project has diverged from goals. |

If any of these files do not exist, note the gap — the PLANNER needs to create them.

---

## Step 3 — Determine Active Role

1. **Explicit assignment:** If the user has said "you are a PLANNER" or "you are an EXECUTOR" — use that role. Skip all other conditions.
2. **Default:** You are an **EXECUTOR** unless explicitly told otherwise.

Once assigned, your role is permanent for the session. No transitions.

Refer to `process/roles.md` for the full definition of each role's responsibilities.

---

## Step 4 — Session Brief

After completing Steps 1–3, output a session brief with this structure:

```
ROLE:        [PLANNER | EXECUTOR]

GOALS:       [version] — [count] goals
DESIGN:      [version] — [status]

BACKLOG:
  P1: [count] items ([list BL-N IDs])
  P2: [count] items ([list BL-N IDs])
  P3: [count] items ([list BL-N IDs])
  P4: [count] items ([list BL-N IDs])

DRIFT:       [count active items, or "none"]

NEXT ACTION: [one sentence describing the first thing to do this session]
```

---

## Step 5 — Proceed

After producing the brief, begin the first action without waiting for direction unless the role assignment is ambiguous.

- **EXECUTOR:** Pick the highest-priority unblocked backlog item and begin the executor loop.
- **PLANNER:** Assess what needs attention first — goals update, design update, backlog creation, implementation review, or drift logging.
