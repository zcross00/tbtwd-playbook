---
name: executor-loop
description: "EXECUTOR LOOP SKILL — Pick up the next backlog item, implement it, and deliver. USE FOR: EXECUTOR starting work on the next item; following the correct branch-implement-verify-merge-communicate sequence. Covers the full EXECUTOR cycle from item selection to completion. DO NOT USE FOR: planning or reviewing (PLANNER work); deciding what goes on the backlog (use backlog-entry skill)."
---

# Executor Loop

Use this skill as an EXECUTOR to implement the next backlog item. Follow every step in order.

---

## Step 1 — Select the Next Item

Open `design/BACKLOG.md`. Find the highest-priority unblocked item:

1. Start with `P1`. If no items exist or all are blocked, move to `P2`, then `P3`, then `P4`.
2. Within a priority level, take the first item in the table.
3. Check the **Dependencies** field — skip items whose dependencies are not yet completed.
4. If no unblocked items exist at any priority, stop and communicate to the user: "Backlog is empty or fully blocked."

Record the `BL-N` you are picking up.

---

## Step 2 — Read the Item Fully

Read the full detail block for the selected `BL-N`:
- Description — what to implement.
- Done-when — the exact completion criteria.
- Design-Ref — the `DESIGN.md` section(s) to consult.
- Dependencies — confirm they are complete.

If the item is ambiguous or missing information needed to implement it, stop and ask the user for clarification before proceeding.

---

## Step 3 — Read Design Context

Open `design/DESIGN.md` and read the section(s) referenced by **Design-Ref**. Understand the intent, components, behaviors, and constraints.

If relevant, also read `design/GOALS.md` to understand the goal the item traces to.

---

## Step 4 — Branch

Use the **git-workflow** skill. Create a branch:

```
git checkout [active-branch]
git pull
git checkout -b work/BL-N
```

Replace `BL-N` with the actual item ID (e.g., `work/BL-23`).

---

## Step 5 — Implement

Write the code. Follow these rules:

1. **Implement exactly what the backlog item says.** Do not add features, refactor unrelated code, or make improvements beyond the scope.
2. Follow `standards/general.md` and the language-specific standards file.
3. If the item includes test requirements in done-when, write the tests. Use the **test-writing** skill for JUnit 5 tests.
4. If you encounter something that works against a goal, note it — you will log it after completing the item.

---

## Step 6 — Build and Verify

Use the **build-verify** skill:

```
mvn clean compile test
```

All tests must pass. If a test fails:
- If it is your code — fix it and re-run.
- If it is a pre-existing failure unrelated to your change — note it and proceed, but communicate it in Step 8.

---

## Step 7 — Commit and Merge

Use the **git-workflow** skill:

```
git add -A
git commit -m "feat(BL-N): [description]"
git checkout [active-branch]
git merge work/BL-N
git branch -d work/BL-N
```

Use the correct commit type prefix:
- `feat` — new capability
- `fix` — bug fix
- `refactor` — internal change, no behavior change
- `test` — adding or updating tests only
- `docs` — documentation only

---

## Step 8 — Communicate

Report to the user:
- Which item you completed (`BL-N`).
- A brief summary of what was done.
- Any observations: drift concerns, follow-up ideas, pre-existing test failures.

Then **wait for the user** before picking up the next item.

---

## Rules

- **One item at a time.** Never work on multiple backlog items simultaneously.
- **No scope expansion.** If you discover related work, note it for the PLANNER — do not implement it.
- **Build must pass.** Never merge with failing tests caused by your changes.
