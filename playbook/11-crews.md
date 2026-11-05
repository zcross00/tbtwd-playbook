# 11. Two crews on one repository

A **crew** is one complete agent structure: a coordinator and its work threads, in one workspace, under one budget. A project adds a second crew when one crew's budget is the limit and CI has room for more merges. The crews can't read each other's chats, files or memory, so the repository's tracker is the only place they meet. Every rule below works through it.

The **home crew** is the one the project started with. The second crew is the **added crew**. Both follow this playbook's `main`, and nothing else.

---

## What stays single

These exist once for the whole project, in the home crew, whatever the number of crews:

| Single thing | Why one |
|---|---|
| **Owner** | One direction. Both coordinators protect the same person's time |
| **Roadmap and grooming approval** | The home coordinator approves grooming and gives each milestone to a crew. Two approvers would grow two roadmaps |
| **Code review** | One merge queue, one train at a time, one gate authority. Both crews' PRs ride the same trains |
| **Verification** | Closing reads `main`, which is one tree |
| **Dev process** | One CI, one queue, one board, one weekly usage report covering both budgets |
| **Daily backlog review and retro** | One backlog, one process |

The added crew has a coordinator and work threads only. It never merges, closes, or approves grooming.

*Why:* every single gate above already ran at its limit with one crew. Copying a gate into the second crew would give two answers to the same PR.

---

## Splitting the work: by milestone

- **A milestone belongs to one crew.** Its description carries a `Crew:` line (`home` or `added`), set by the home coordinator when it approves the grooming. A crew starts work only on milestones that name it.
- **Split by milestone, not by file.** Two crews can touch the same file; [Working in parallel](05-parallel.md) already makes that mechanical. A file split would block features that cross areas.
- **The owner's primary focus stays with the home crew**, and the added crew takes whole milestones beside it: a release milestone, an internal milestone, or the next milestone in the roadmap that doesn't depend on open work.
- **Moving a milestone between crews** is a `Crew:` line change by the home coordinator, at a boundary (before its thread starts, or after its last PR merges). Never mid-PR.
- **No crew-to-crew dependency inside a milestone.** If a milestone needs another crew's unmerged work, it waits or moves crews. Dependency order is a roadmap rule, not a chat.

---

## Claiming an issue

An issue is claimed by its milestone's crew. Within that crew, its thread claims it with a `board: status=In progress` line, as today. A thread that finds an issue in progress under another milestone, or in a milestone that doesn't name its crew, leaves it alone.

New issues found mid-build are filed with no milestone and go through the home crew's grooming, like any other.

---

## Talking across crews

The crews can't message each other. Everything they say to each other goes on the tracker, where both can read it:

- **A PR is the added crew's request to merge.** Ready means not a draft, rebased, green on the full local check, and mergeable ([Lifecycle](04-lifecycle.md)). Code review picks ready PRs from the tracker; it doesn't wait for a message.
- **Code review talks back on the PR.** The added crew's thread follows its own PR's activity, so a review comment or a train failure reaches it.
- **Corrections from Verification** are issues in the original milestone, so they land with the crew that owns it.
- **A blocker for the home crew** (a broken check, a needed dependency) is an issue with `priority: A`, mentioned in the PR, never a message.

---

## The owner's channel

The owner reads two chats, so each one stays small:

- **The home coordinator** is the channel for direction, roadmap, scope, dates and anything that crosses crews.
- **The added coordinator** asks the owner only about its own milestones (spec choices, and the acceptance build when one is ready), with a recommendation, once.
- **Acceptance builds go through one queue**, with the home coordinator, so the owner sees one list of what's waiting to be played, oldest first.

*Why:* the owner's attention is the scarcest resource ([Principles](01-principles.md)). A second crew doubles the work arriving at it; it must not double the places to look.

---

## Budgets

Each crew paces against its own budget with the same pace tool and the same reset. Each coordinator opens or idles its own lanes. The added crew posts its readings where Dev process can read them (a standing internal issue, one comment per reading), and the weekly usage report covers both crews.

Opening more lanes than CI can merge spends budget on work that waits in the queue. Before the added crew opens a lane, its coordinator checks the queue wait; Dev process gives both coordinators the same number.

---

## CI with two crews

Both crews share one merge queue on the shared runners ([CI tiers](06-ci.md)). A second crew is worth adding only when CI can take its merges: in practice, a Tier 1 server with a measured full run, not a Tier 0 laptop that is already the limit.

---

## Starting the added crew

1. **Measure CI first.** Start the added crew only after the shared runners' first measured full run shows room in the queue.
2. **Give it the same repositories and instructions.** Its workspace connects the project repository and this playbook; its standing instructions are the home crew's, word for word, plus one line saying it is the added crew.
3. **Give it GitHub access** with permission to push branches and open PRs, nothing more. Merging stays with Code review's access.
4. **Hand it its first milestones** by setting their `Crew: added` lines, and start one thread per milestone.
5. **Create the standing internal issue** for its budget readings.
6. **Review it at the first retro** after it starts: merges per crew, queue wait, conflicts between crews, and the owner's load.
