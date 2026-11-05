# 11. Two crews on one repository

A **crew** is one complete agent structure: its sessions, in one workspace, under one AI account and one budget. A project adds a second crew when one account's budget is the limit and CI has room for more merges, and to put the builders and the gate under different GitHub identities. The crews can't read each other's chats, files or memory, so the repository's tracker is the only place they meet. Every rule below works through it.

The **home crew** is the one the project started with. The second crew is the **build crew**. Both follow this playbook's `main`, and nothing else.

---

## Who does what

| Crew | Runs | GitHub identity ([GitHub identities](12-identities.md)) |
|---|---|---|
| **Home crew** (the owner's AI account) | Coordinator, grooming, the daily backlog review, the retro, Code review, Verification. It writes no code | The owner's account, as today. It is the only member of the reviewer team |
| **Build crew** (the second AI account) | Its coordinator, every work thread, Dev process | A developer machine account with Write access, which also creates and moves work items |

- **Each role exists once.** One owner's channel, one grooming approver, one Code review running one train at a time, one Verification, one Dev process.
- **Builders never hold the approving login.** The build crew's account can't approve its own PRs, and isn't in the reviewer team, so GitHub enforces the review gate ([GitHub identities](12-identities.md)).
- **The home crew writes no code.** A work thread there would author PRs as the owner, which the owner's own approval could then pass, so the gate would be a promise again.
- **The owner's channel is the home coordinator.** It approves grooming and milestones, relays direction calls, and hands over acceptance builds. The build crew's coordinator starts one thread per approved milestone and paces its own lanes. It doesn't ask the owner directly: a question becomes a `decision` issue, which the home coordinator puts to the owner.

*Why:* the owner, 2026-11-05: "i'm hoping to have myself, with a "planner" role, a developer account with a developer role access, and a verifier account with validation/review access", then "i still want agents to still be able to create, move, adjust work items in github, same as today, they can still post on my behalf", then "the llc claude account isn't going to just be doing validation, it'll be doing a majority of the building ideally". The roles that merge and close stay with the owner's identity; the builders get their own.

---

## Talking across crews

The crews can't message each other. Everything they say to each other goes on the tracker, where both can read it:

- **An approved milestone is the build crew's work order.** The home coordinator approves its grooming and sets it; the build crew starts a thread for it.
- **A ready PR is the build crew's request to merge.** Ready means not a draft, rebased, green on the full local check, and mergeable ([Lifecycle](04-lifecycle.md)). Code review picks ready PRs from the tracker; it doesn't wait for a message.
- **Code review talks back on the PR**: a review, a requested change, a train result. The thread that owns the PR follows its activity, so the answer reaches it.
- **Verification talks back on the issue**: a close, or a reopen with its priority A correction in the original milestone, which the build crew picks up.
- **Gate calls** (loosening, seeds, floors) are written on the PR or the `deferred gate` issue, as now.
- **A blocker for the other crew** is an issue with `priority: A`, linked from the PR, never a message.
- **Acceptance builds** are named on the milestone when ready; the home coordinator hands them to the owner.

---

## Budgets

Each crew paces against its own account's budget with the same pace tool. The build crew's coordinator opens or idles lanes against its budget; the home crew's spend is coordination, review and verification.

- **Opening more lanes than CI can merge spends budget on work that waits in the queue.** Before the build crew opens a lane, its coordinator checks the queue wait that Dev process reports.
- **The home crew's spare budget buys depth, not lanes**: review at higher effort, grooming further ahead, and playing the acceptance build's first minutes headless before the owner does.
- **The weekly usage report covers both accounts.** The home crew posts its readings where Dev process can read them: a standing internal issue, one comment per reading.

---

## Starting the build crew

1. **Until it connects, nothing changes.** Work threads run in the home crew as today, and the ruleset stays off.
2. **Connect it as the developer account.** Its workspace connects the project repository and this playbook, with GitHub access as that machine account only ([GitHub identities](12-identities.md)).
3. **Give it the same standing instructions**, word for word, plus one line saying it is the build crew.
4. **Move the building over.** The home crew stops starting work threads; threads already running finish their current PR there. Dev process moves to the build crew.
5. **Turn on the ruleset** after the first approved PR from the developer account lands ([GitHub identities](12-identities.md)).
6. **Review it at the first retro** after it starts: merges per day, time from ready to merged, verification fails, and the owner's load.
