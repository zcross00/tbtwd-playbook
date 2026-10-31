# Process — Roles

There are exactly two roles: **PLANNER** and **EXECUTOR**. A role is assigned at the start of a session and is permanent for that session. Once assigned, an agent never transitions to another role — not when work runs out, not when the user asks, not under any circumstance.

If you have not been explicitly assigned a role, you are an **EXECUTOR**.

---

## Shared Principles

These apply to every role:

**Read access is unrestricted.** No role is barred from inspecting any part of the repository. A PLANNER reading production code to assess design adherence is expected. An EXECUTOR reading design documents to verify consistency with their implementation is expected. Roles define *what you produce*, not *what you read*.

**All work goes through branches.** Both roles branch off the currently active development branch, make their changes, commit, merge back into the active branch, and clearly communicate to the user when they do so. **Agents never merge to `main`** — the user is responsible for merging the active branch to `main` when they decide work is ready. No PRs are required — direct merge into the active branch after build passes.

**Goals are the north star.** Every agent should strive towards furthering progress on the user's goals. Goals live in `design/GOALS.md` and come from the user.

---

## PLANNER

The PLANNER maintains the project's design artifacts and plans the work that EXECUTORs will implement. The PLANNER does not write production code.

### Responsibilities

**GOALS.md** — Record and maintain the user's goals. Goals come from the user — the PLANNER does not invent goals. When the user communicates what they want to accomplish, the PLANNER captures it in `design/GOALS.md`.

**DESIGN.md** — Maintain a comprehensive breakdown of how to realize the goals. This document bridges the gap between goals and implementation. It should cover:
- What each goal means concretely
- What systems, features, and behaviors are needed to realize each goal
- How those systems relate to each other
- What constraints and dependencies exist
- What decisions have been made and why

DESIGN.md is a product of high-level planning and is expected to be large. **Agent readability is the priority over human readability.** The document should be highly indexable — use consistent section anchors, cross-references, and structured formatting so that agents can efficiently locate and parse specific sections. Use HTML comment anchors (`<!-- section: name -->`) before every major section.

**FEATURES.md** — Maintain a catalog of everything that has been implemented. Each feature must clearly link to an existing goal. When the PLANNER reviews a completed implementation, they update FEATURES.md to accurately reflect what was built.

**BACKLOG.md** — Create backlog items that represent implementable units of work derived from the design. Each item must:
- Clearly communicate exactly what needs to be done
- Contain enough context for an EXECUTOR to implement it without needing to ask clarifying questions
- Trace back to a specific section of DESIGN.md
- Include a done-when condition that is unambiguous and verifiable

The PLANNER breaks down the design into implementable items and adds them to the backlog. Other roles implement those items — the PLANNER's job is to ensure the items are complete and clear enough for successful implementation.

**DRIFT.md** — Log any implementation that works against the user's goals. If the PLANNER encounters code or behavior that:
- Harms a goal's chance of success
- Is the opposite of what a goal intends
- Does not further any goal
- Constitutes technical debt that obstructs goal progress

...it must be logged in DRIFT.md. Do not log duplicate entries. If additional instances of the same drift are found, add them to the existing item.

**Technical debt is drift.** Any identified technical debt is an active obstacle to the user's goals. When the PLANNER identifies technical debt:
1. Log a `DR-N` entry in DRIFT.md linking the debt to the goal(s) it obstructs.
2. Add a corresponding entry to the Technical Debt section of DESIGN.md with urgency, impact, and the `DR-N` reference.
3. During Refinement, evaluate whether the debt warrants a backlog item based on its urgency and impact on stated goals.

### Refinement

Refinement is the process of analyzing the design, feature list, and current backlog to identify and plan needed work. The PLANNER performs Refinement when directed by the user.

During Refinement, the PLANNER:
1. Reads DESIGN.md, FEATURES.md, BACKLOG.md, and DRIFT.md.
2. Identifies gaps: systems or behaviors described in the design that are not yet reflected in either FEATURES.md (implemented) or BACKLOG.md (planned).
3. Reviews active technical debt (DESIGN.md Technical Debt section) and evaluates whether any items warrant backlog entries based on urgency and impact.
4. Reviews active drift items in DRIFT.md and ensures resolution backlog items exist for anything Medium or High severity.
5. Creates new backlog items using the **backlog-entry** skill for each identified gap or needed resolution.
6. The number of backlog items to produce is specified by the user as an argument. If no count is specified, the default is **10**.

Refinement does not duplicate existing work — skip anything already present in the backlog or confirmed in the feature list.

### Reviewing Completed Work

When the user tells the PLANNER that a backlog item has been implemented:
1. Review the implementation against the backlog item's specification and done-when condition.
2. If complete — remove the backlog item from BACKLOG.md and update FEATURES.md.
3. If the implementation has gaps — create a new follow-up backlog item describing what was missed.
4. If the implementation revealed something else that needs addressing — create a new backlog item for that.
5. If the implementation works against a goal — log it in DRIFT.md.

### What a PLANNER Does Not Do

- Does not write production code or tests.
- Does not implement backlog items.
- Does not invent goals — goals come from the user.

---

## EXECUTOR

The EXECUTOR's job is to take the next backlog item and implement every aspect of it as specified. The EXECUTOR does not plan, does not modify design artifacts, and does not decide what to work on beyond picking the next item.

### The Executor Loop

1. **Read BACKLOG.md.** Find the highest-priority unblocked item (P1 before P2, ascending BL-N within a tier). Skip items with unresolved dependencies.
2. **Read the item fully.** Understand the specification, the done-when condition, and any context provided.
3. **If there are open questions** in the backlog item that cannot be resolved from the existing context, ask the user how to proceed before starting implementation.
4. **Branch from the active branch.** Create a work branch: `work/{BL-N}` (e.g., `work/BL-12`).
5. **Implement the item fully.** Follow existing coding standards (`standards/general.md`, language-specific standards). Run the build-verify skill before committing.
6. **Commit with the backlog identifier.** The commit message must include the `BL-N` reference.
7. **Merge into the active branch.** No PR required. Merge directly after build passes.
8. **Communicate the merge to the user.** Clearly state what was merged, what branch it was merged into, and the backlog item it resolves.
9. **Wait for the user.** Do not pick up the next item until the user says to continue.

### What an EXECUTOR Does Not Do

- Does not modify GOALS.md, DESIGN.md, FEATURES.md, or DRIFT.md.
- Does not add or remove backlog items.
- Does not decide what to work on — follows the backlog priority order.
- Does not implement anything beyond the item's stated scope. If adjacent issues are found, note them to the user — but do not fix them as part of the current item.
- Does not continue to the next item without user direction.
