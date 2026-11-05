# 11. Two crews on one repository

A **crew** is one complete agent structure: its sessions, in one workspace, under one AI account and one budget. A project adds a second crew when one account's budget is the limit and CI has room for more merges. The crews can't read each other's chats, files or memory, so the repository's tracker is the only place they meet. Every rule below works through it.

The **home crew** is the one the project started with. The second crew is the **added crew**. Both follow this playbook's `main`, and nothing else.

---

## Who does what

Either crew may build. Each acts on GitHub as its own login ([GitHub identities](12-identities.md)), and each reviews the other's work.

| | Home crew (the owner's AI account) | Added crew (the second AI account) |
|---|---|---|
| GitHub login | The owner's account, as today | A developer machine account |
| Builds | Milestones whose `Crew:` line says `home` | Milestones whose `Crew:` line says `added` |
| Reviews | The added crew's PRs | The home crew's PRs, and every train |
| Also runs | Coordinator, grooming approval, the daily backlog review, Verification, Dev process, the retro | Its coordinator |

- **Cross-review.** Both logins are in the reviewer team, and an author can't approve their own PR, so every PR needs the other crew's approval. Each crew runs a Code review thread (its inquisitor, in [GitHub identities](12-identities.md)) that reviews only the other crew's PRs.
- **One merge queue.** The home crew's Code review runs the trains and merges, one train at a time, and keeps gate authority (seeds, floors, loosening). Because it authors the train PRs, the added crew's Code review approves each train: the members are the approved heads, and nothing else rode along.
- **Everything else stays single, in the home crew**: Verification, Dev process, grooming approval, the backlog review, the retro, and the owner's channel.
- **When one side can't review** (out of budget, or not connected yet), the home crew's Code review turns the ruleset off and files a `deferred gate` issue saying why and until when. It turns the ruleset back on when both sides can review.

*Why:* the owner, 2026-11-05, on which account builds: "im going to need the flexibility to also do development with my personal account as well, depending on how things go down mid project". Cross-review keeps the gate real whichever account builds: no login can pass its own work.

---

## Splitting the work: by milestone

- **A milestone belongs to one crew.** Its description carries a `Crew:` line (`home` or `added`), set by the home coordinator when it approves the grooming. A crew starts work only on milestones that name it, so two crews never claim the same issue.
- **Split by milestone, not by file.** Two crews can touch the same file; [Working in parallel](05-parallel.md) already makes that mechanical.
- **Moving a milestone between crews** is a `Crew:` line change by the home coordinator, at a boundary: before its thread starts, or after its last PR merges. Never mid-PR. This is how the owner shifts building between accounts mid-project.
- **No crew-to-crew dependency inside a milestone.** If a milestone needs another crew's unmerged work, it waits or moves crews.

---

## Talking across crews

The crews can't message each other. Everything they say to each other goes on the tracker, where both can read it:

- **A ready PR is a request for review.** Ready means not a draft, rebased, green on the full local check, and mergeable ([Lifecycle](04-lifecycle.md)). The other crew's Code review picks ready PRs from the tracker; it doesn't wait for a message.
- **Reviews and train results go on the PR.** The thread that owns the PR follows its activity, so the answer reaches it.
- **Verification talks back on the issue**: a close, or a reopen with its priority A correction in the original milestone, which belongs to that milestone's crew.
- **Gate calls** are written on the PR or the `deferred gate` issue.
- **A blocker for the other crew** is an issue with `priority: A`, linked from the PR, never a message.
- **The owner's channel is the home coordinator.** The added crew's questions become `decision` issues, which the home coordinator puts to the owner. Acceptance builds are named on the milestone and handed over by the home coordinator.

---

## Budgets

Each crew paces against its own account's budget with the same pace tool, and each coordinator opens or idles its own lanes.

- **Review comes first.** Each crew keeps enough budget to review the other's PRs; a crew that can't review stalls both.
- **Opening more lanes than CI can merge spends budget on work that waits in the queue.** Before opening a lane, a coordinator checks the queue wait that Dev process reports.
- **The weekly usage report covers both accounts.** The added crew posts its readings where Dev process can read them: a standing internal issue, one comment per reading.

---

## Starting the added crew

1. **Until it connects, nothing changes.** Every milestone is `home`, and the ruleset stays off under its `deferred gate` issue.
2. **Connect it as the developer account.** Its workspace connects the project repository and this playbook, with GitHub access as that machine account only.
3. **Give it the same standing instructions**, word for word, plus one line saying it is the added crew.
4. **Start its Code review thread first**, then hand it milestones by setting their `Crew: added` lines.
5. **Turn on the ruleset** once each side has approved one of the other's PRs ([GitHub identities](12-identities.md)).
6. **Review it at the first retro** after it starts: merges per crew, time from ready to merged, review wait per side, conflicts between crews, and the owner's load.
