# 11. Teams

A **team** is one complete agent structure under one budget: a coordinator, its work threads, its own Code review, Verification, grooming, retro and usage report. On the reference project each team is one Claude account. A project adds a team when one team's budget is the limit and CI has room for more merges.

Teams are **equals**. Neither runs the other, and neither approves the other's grooming. They can't read each other's chats, files or memory, so they meet in two places only: the project's tracker (issues and PRs) and the **hub**, the playbook repository's own issues.

Each team acts on GitHub as **one login of its own**, and that login is the team's name everywhere below. The hub's `roster` issue lists the teams, their logins, their usage reset times, and who holds each shared role.

*Why:* the reference project first tried one parent with child teams. In use, the accounts had different features and different budgets, and a parent that had to approve the other team's work became the queue. The owner, 2026-11-07: "originally i just wanted one parent and a bunch of children, but seeing this in practice ... make me think the co-equal team route was actually the better bet".

---

## What each team runs for itself

| Role | Covers |
|---|---|
| Coordinator | Its own lanes, its own chat with the owner, its hub watch |
| Work threads | Only issues assigned to its login |
| Code review | Reviews its own team's PRs to ready, builds its own trains, and reviews and approves the **other** team's PRs (below) |
| Verification | Closes its own team's issues |
| Daily backlog review | Grooms issues assigned to its login and milestones its team owns |
| Usage report and retro | Its own budget, its own week, at its own reset |

## What stays single

| Single thing | Held by | Why one |
|---|---|---|
| Owner | The owner | One direction; both coordinators protect the same person's time |
| `main`, the CI queue and the runners | Dev process, on one team (the `roster` names it) | One tree, one machine; the queue runs one train at a time whichever team built it |
| This playbook | Both teams, through PRs | One process |
| Committed dates (release, early access) | The owner | Both teams plan against the same calendar |

---

## Who owns what: the assignee

- **An issue belongs to the team whose login is its assignee.** A lane builds only issues assigned to its own login. An unassigned issue is nobody's until a team assigns itself while grooming it.
- **A team files new issues assigned to itself.** To hand one over, the owner team reassigns it and says why in a comment. Nobody takes an issue by reassigning it away from the other team.
- **A milestone belongs to one team**, named on a `Team:` line in its description. That team sets and keeps its dates and closes it. The other team may still own issues in it; their `day` stays within its due date, and moving that date is a hub `question` first.
- **No cross-team dependency is waited on in chat.** If a team needs the other's unmerged work, it says so in a hub `question` and plans around the answer.

---

## Reviews: the other team approves

`main` requires **one approving review**, and GitHub never counts the PR author's own approval. With one login per team, the approval always comes from the other team. That is the point: every PR is read by both teams.

1. **The authoring team's Code review** reviews the PR first, as today, and marks it ready.
2. **The other team's Code review** reviews it and approves, or requests changes. It reviews against this playbook, not its own preferences. A gate change (a loosened floor, a pooled seed) gets the same read; the authoring team still files its `deferred gate` issue.
3. **Trains.** A team's Code review builds trains of its own approved PRs. The train PR needs the other team's approval too: the other team checks that each member was approved at the head the train merged, and approves at once, while the train's CI runs. CI green is a separate required check, so the approval doesn't wait for it.
4. **Response time.** Each Code review looks for review requests from the other team at least every 30 minutes while any are open, and every hour otherwise. A train stalled on an approval wastes the runner it was queued for.
5. **The ruleset has no bypass list.** A login that can bypass the review would make the review optional for one team.

*Why:* the owner, 2026-11-07: "that means we may double up on code reviews, but i think i like that", then "then 1 review, since it will always be the opposite opening". Two required approvals can't be met with two logins, because the author's own never counts.

### When the other team can't review

Each team meters its usage against its own reset, so this should not happen. If it does:

1. A team that sees it will run out, or go offline, before its reset posts a hub `fyi` saying until when.
2. The waiting team keeps building and queues its PRs. Nothing merges unreviewed.
3. If a ready PR or train has waited **6 hours** with no review, the waiting team's coordinator asks the owner once: wake the other team, or drop the required approvals to zero until it is back. On a yes, a team with admin rights sets it, files a hub `decision` quoting the owner, and restores the rule when the other team posts its next review.

---

## The hub

The hub is the playbook repository's issue tracker. Process changes, decisions, questions between teams and anything one team learns that the other needs go there, never only in one team's chat.

| Label | For | Who acts |
|---|---|---|
| `decision` | An owner's decision that touches the other team or anything shared. Quotes the owner's words with the date and which coordinator heard them | The team that has to change something; closes once applied |
| `question` | One team asks the other (a dependency, a milestone date, a handover) | The other team answers in a comment |
| `proposal` | A process idea before it becomes a PR, when a team wants the other's view first | Both; it becomes a PR or is closed |
| `needs-owner` | Something only the owner can decide that spans both teams | The coordinator that filed it asks the owner once, in its own chat |
| `fyi` | Availability, a role moving, an incident the other team should know about | Nobody; closes after a week |
| `roster` | The one issue that lists teams, logins, resets and shared role holders | Edited in place; never closed |

Rules:

- **An owner's decision heard by one team reaches the hub in the same turn** when it changes anything the other team does or shares. Quote the words; don't paraphrase.
- **Every hub issue names who acts** on an `Acts:` line (a team's login, or `both`).
- **Process changes are PRs to this repository, as always.** The other team reads each one through its hub watch and objects in a review before the Saturday window. An objection still open at the window holds the PR, and both coordinators take it to the owner.
- **Issues, not GitHub Discussions.** Discussions can only be read through GitHub's GraphQL API, which Claude Code sessions can't call, so a watch would never see them.
- **The hub is public.** Write process, not business: no money, accounts, people's details or private messages. A watch counts only items written by logins on the roster.

---

## The hub watch

Each coordinator reads the hub on its own, so nothing depends on the other team remembering to tell it.

- **Hourly**, a scheduled task wakes the coordinator, which runs [`kit/hub/digest.py`](../kit/hub/digest.py) over the hub repository (and, while it is still in use, any older playbook repository). The script prints what is new or changed since its last run: issues, PRs, comments and commits on `main`, from roster logins only, the other team's first. It keeps its place in a file of the team's own, and prints `NOTHING NEW` when that is true.
- **The coordinator acts on what it prints:** answers a `question` addressed to its team, tells the affected lane or role, records a `decision` in its team's memory, and raises a `needs-owner` item with the owner once. It doesn't reply in the owner's chat about routine items.
- **A team that adds a role or a routine** that the other team should mirror posts it on the hub as a `proposal`, with the prompt it uses.

---

## Adding a team

1. **Measure CI first.** Add a team only when the queue has room for its merges.
2. **Give it a GitHub login of its own** with write access, and add it to the `roster`.
3. **Give it this playbook and the project repository**, and the same standing instructions, plus one line naming its login.
4. **Start its hub watch** before anything else, so it hears the rest.
5. **Hand it work by assignee**, and give each milestone it takes a `Team:` line.
6. **Turn on the review rule** only once both teams' Code reviews are running.
7. **Review it at each team's first retro after it starts**: merges per team, time waiting for the other team's review, conflicts between teams, and the owner's load.
