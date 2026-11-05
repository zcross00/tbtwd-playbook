# 11. Two crews on one repository

A **crew** is one complete agent structure: its sessions, in one workspace, under one AI account and one budget. A project adds a second crew when it wants the review gate held by a different identity from the builders, or when one account's budget is the limit and CI has room for more merges. The crews can't read each other's chats, files or memory, so the repository's tracker is the only place they meet. Every rule below works through it.

The two crews are the **build side** and the **review side**. Both follow this playbook's `main`, and nothing else.

---

## Who does what

| Crew | Runs | GitHub identity ([GitHub identities](12-identities.md)) |
|---|---|---|
| **Build side** | Coordinator, every work thread, Dev process, the daily backlog review, the retro | The owner's account, which the agents post through as today |
| **Review side** | Code review and Verification, and nothing else | The verifier account |

- **Each role exists once.** One coordinator, one Code review running one train at a time, one Verification, one Dev process. Splitting the roles across two accounts doesn't copy them.
- **Only the review side holds the verifier's login.** The build side keeps creating, moving and adjusting work items and posting as the owner. It can't approve: GitHub doesn't count an author's own approval, and the owner's account isn't in the reviewer team.
- **The review side never builds.** A work thread in the review side's account would hold the verifier's login and could approve its own work, so the gate would be a promise again.
- **The owner's channel is the build side's coordinator.** The review side doesn't ask the owner anything. Its calls are its own (merging, closing, gate statistics), and anything that needs the owner goes on the tracker as an issue for the coordinator to pick up.

*Why:* the owner, 2026-11-05: "i'm hoping to have myself, with a "planner" role, a developer account with a developer role access, and a verifier account with validation/review access". And 2026-11-05: "i still want agents to still be able to create, move, adjust work items in github, same as today, they can still post on my behalf". The roles that merge and close are the ones worth separating, so they get the separate identity.

---

## Talking across crews

The crews can't message each other. Everything they say to each other goes on the tracker, where both can read it:

- **A ready PR is the build side's request to merge.** Ready means not a draft, rebased, green on the full local check, and mergeable ([Lifecycle](04-lifecycle.md)). Code review picks ready PRs from the tracker; it doesn't wait for a message.
- **Code review talks back on the PR**: a review, a requested change, a train result. The thread that owns the PR follows its activity, so the answer reaches it.
- **Verification talks back on the issue**: a close, or a reopen with its priority A correction in the original milestone.
- **Gate calls** (loosening, seeds, floors) are written on the PR or the `deferred gate` issue, as now. The build side reads them there.
- **A blocker for the other crew** is an issue with `priority: A`, linked from the PR, never a message.
- **Morning report and retro inputs** from the review side (trains run, merges, verification fails) are read from the tracker by the build side's coordinator and Dev process, not reported by chat.

---

## Budgets

Each crew paces against its own account's budget with the same pace tool. The review side's coordinator duties are none, so its spend is review and verification only, and most of its budget is spare.

- **Moving review off the build side's account** frees that share of its budget for more work threads.
- **The review side's spare budget buys depth, not more lanes.** It can review at higher effort, run the acceptance build and play its first minutes headless before the owner does, and re-check verified issues against `main` more often. It never builds.
- **The weekly usage report covers both accounts.** The review side posts its readings where Dev process can read them: a standing internal issue, one comment per reading.

---

## Starting the review side

1. **Connect it as the verifier.** Its workspace connects the project repository and this playbook, with GitHub access as the verifier account only ([GitHub identities](12-identities.md)).
2. **Give it the same standing instructions**, word for word, plus one line saying it is the review side and runs only Code review and Verification.
3. **Start Code review and Verification there, then stop them on the build side.** Never both at once: two Code reviews would run two trains.
4. **Turn on the ruleset** after the first verifier approval lands ([GitHub identities](12-identities.md)).
5. **Create the standing internal issue** for its budget readings.
6. **Review it at the first retro** after it starts: merges per day, time from ready to merged, verification fails, and whether the build side opened more lanes with the freed budget.
