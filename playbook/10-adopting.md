# 10. Adopting the playbook

---

## Day one on a new project

1. **Write the vision.** `docs/VISION.md`: what the project is for, the priorities in order (A, B, C), and the fixed rules. Only the owner changes it.
2. **Make the project's PROCESS.md** from [templates/PROCESS.md](../templates/PROCESS.md): the owner, the roles and who fills them, the area table, the labels, the CI tier and commands, where the owner reads. Link this playbook; don't copy it.
3. **Copy the GitHub kit** from [templates/github/](../templates/github/): PR template, issue forms, `playbook-lint` workflow.
4. **Create the labels**: `area: …` per area, `priority: A|B|C`, `parked`, `decision`, `deferred gate`, `verification`, `main-fix`, `train`.
5. **Pick a CI tier** ([CI tiers](06-ci.md)); Tier 0 is fine to start. Write the full local check script first; CI runs the same script.
6. **Start the standing roles**: coordinator, Code review, Verification, Dev process. Then one work thread per milestone.
7. **Write the first milestones** from [templates/milestone.md](../templates/milestone.md), named for their acceptance tests, and groom their issues.
8. **Schedule the cadences** ([Cadences](09-cadences.md)).

A project can start with fewer standing roles (one agent doing Code review and Verification on alternate passes, say), but never with the same session both merging and closing the same PR.

---

## The enforcement kit

The process falls apart when the rules live only in people's heads. These are enforced by tooling, so nobody has to remember them:

| Rule | Enforced by |
|---|---|
| PRs never close issues; every code PR has a `Refs #N` line | `playbook-lint` workflow (required check) |
| Only trains merge; nothing merges without the full check | Branch protection: required `full` check that only a train runs; up-to-date branch required |
| Docs-only PRs skip the heavy runner | A `files` job in CI |
| Coverage floors and untested-output lists only move with a `deferred gate` issue | CI compares against `main`'s copies |
| Board fields match `board:` lines | Board sync workflow |
| Due dates follow measured pace | Daily re-forecast workflow |
| Stale issues get reviewed | Daily backlog review (scheduled) |
| The process gets reviewed | Weekly retro (scheduled) |

The rest (one PR per thread, ask through the coordinator, two-attempt rule) are enforced by roles: Code review asks for changes, Verification reopens, the coordinator redirects.

---

## Scaling to an enterprise

The playbook was proven with one owner and many agents. At enterprise scale the shape holds; these change:

- **The owner becomes a small group with one tie-breaker.** Product owner for direction and acceptance, architect for direction calls on structure. Questions still go through one coordinator role per program, with a recommendation.
- **Roles become people or rotations, with agents assisting.** Code review is the merge authority (branch protection + merge queue + CODEOWNERS). Verification is a separate post-merge acceptance step, staffed apart from review.
- **Areas become teams.** The area table becomes CODEOWNERS; "name what you touch outside your area" becomes an automatic review request.
- **Decision issues become ADRs**; `deferred gate` issues become the waiver register; the evidence lines become change-management evidence.
- **Budgets become cost centers.** The weekly usage report covers agent spend, CI spend and environments per team.
- **The retro runs per team weekly, and per program monthly.** Program-level changes land here as PRs.

What does *not* change: verified Done as the only progress, a merge closes nothing, every loosened gate leaves an issue, and the owner's time goes only to direction and acceptance.

---

## Adapting without drifting

A project may differ from the playbook. When it does, its PROCESS.md says where and why, in a "Differences from the playbook" section. A difference that proves itself on two projects is proposed back here as a PR.
