# 11. Teams

A **team** is one complete agent structure under one budget: a coordinator, its work threads, its own Code review, Verification, grooming, retro and usage report. On the reference project each team is one Claude account. A project adds a team when one team's budget is the limit and CI has room for more merges.

Teams are **equals**. Neither runs the other, and neither approves the other's grooming. They can't read each other's chats, files or memory, so they meet in two places only: the project's tracker (issues and PRs) for the work, and **email** for talking about it.

Each team has a short **name** and acts on GitHub as **one login of its own**; below, "its login" means that team's. The `roster`, a standing issue in this repository, maps each team's name to its login and email address, and lists usage reset times and who holds each shared role. When two teams have to share one login, the section [While teams share one login](#while-teams-share-one-login) applies.

*Why:* the reference project first tried one parent with child teams. In use, the accounts had different features and different budgets, and a parent that had to approve the other team's work became the queue. The owner, 2026-11-07: "originally i just wanted one parent and a bunch of children, but seeing this in practice ... make me think the co-equal team route was actually the better bet".

---

## What each team runs for itself

| Role | Covers |
|---|---|
| Coordinator | Its own lanes, its own chat with the owner, its inbox watch |
| Work threads | Only issues assigned to its login |
| Code review | Reviews its own team's PRs to ready, builds its own trains, and reviews and approves the **other** team's PRs (below) |
| Verification | Closes its own team's issues |
| Daily backlog review | Grooms issues assigned to its login and milestones its team owns |
| Usage report and retro | Its own budget, its own week, at its own reset |
| Dev process | Its own share of the CI, queue, runners and kit, which both teams run together (below) |

## What stays single

| Single thing | Held by | Why one |
|---|---|---|
| Owner | The owner | One direction; both coordinators protect the same person's time |
| `main`, the CI queue and the runners | Both teams' Dev process, as one machine | One tree, one machine; the queue runs one train at a time whichever team built it. Each team's Dev process can fix the CI and the kit; a change to the shared machinery is a PR the other team reviews, and anything that needs the other team's access (a login on the server) is a `[question]` email |
| This playbook | Both teams, through PRs | One process |
| Committed dates (release, early access) | The owner | Both teams plan against the same calendar |
| Acceptance builds (playtests) | The team whose account reaches the owner's playtest machine (the `roster` names it) | The owner plays on one machine. A milestone of the other team that needs a playtest is handed over for its build when its last issue merges |

---

Playtests are the only thing one team holds alone; everything else is run by both. *Why:* the owner, 2026-11-07: "we will only ever do playtests on the laptop, so this account will solely be responsible for handling that specific aspect. everything else should be shared".

To hand a milestone over for its playtest, its team sends a `[fyi]` email naming the milestone, the merged commit and anything the build's setup needs. The playtest team builds it, hands it to the owner, and reports what the owner found back to the milestone's team, also by email. Corrections land as issues in the milestone, owned by its team.

---

## Who owns what: the assignee

- **An issue belongs to the team whose login is its assignee.** A lane builds only issues assigned to its own login. An unassigned issue is nobody's until a team assigns itself while grooming it.
- **A team files new issues assigned to itself.** To hand one over, the owner team reassigns it and says why in a comment. Nobody takes an issue by reassigning it away from the other team.
- **A milestone belongs to one team**, named on a `Team:` line in its description. That team sets and keeps its dates and closes it. The other team may still own issues in it; their `day` stays within its due date, and moving that date is a `[question]` email first.
- **No cross-team dependency is waited on in chat.** If a team needs the other's unmerged work, it says so in a `[question]` email and plans around the answer.

---

## While teams share one login

When a team has to use another team's login, because its own is suspended or not made yet, GitHub can't tell the two apart. Until it has its own login again:

- **Ownership by label.** Every team on the shared login puts a `team:<name>` label on its issues and PRs, the login's own team included. An item without one belongs to nobody until a team labels it while grooming it. Assignees stay as they are, so nothing has to be undone later.
- **Every team signs everything on GitHub.** Each PR body, issue comment and review comment ends with a `Team: <name>` line above the footer, so a reader can tell the teams apart without the login.
- **No required approval.** The author's own approval never counts, so a required review would block every PR, and the ruleset stays off. The other team's review is a signed PR comment, `Team: <name> review: approve <sha>` or `changes requested`, and Code review merges only after it. Auto-merge goes on a PR or train only after the other team's `approve <sha>` at its current head; otherwise it would merge the moment CI went green. The 6-hour fallback still applies.
- **Switching back** takes three steps. The roster maps the team to its own login again, its open issues get that login as assignee, and the ruleset goes on. The labels and signatures can stay.

*Why:* the owner, 2026-11-07, after GitHub suspended the second team's login: "im going to have it use my private account for now, while i wait for the appeal. we'll have to design around that." Then, naming the login's own team: "we are going to be team overseer over here. that's what we should be tagging our stuff with, the same way architect tags all his stuff with that".

---

## Reviews: the other team approves

`main` requires **one approving review**, and GitHub never counts the PR author's own approval. With one login per team, the approval always comes from the other team. That is the point: every PR is read by both teams.

1. **The authoring team's Code review** reviews the PR first, as today, and marks it ready.
2. **The other team's Code review** reviews it and approves, or requests changes. It reviews against this playbook, not its own preferences. A gate change (a loosened floor, a pooled seed) gets the same read; the authoring team still files its `deferred gate` issue.
3. **Trains.** A team's Code review builds trains of its own approved PRs. The train PR needs the other team's approval too: the other team checks that each member was approved at the head the train merged, and approves at once, while the train's CI runs. CI green is a separate required check, so the approval doesn't wait for it. Every train PR carries the `train` label, so the queue knows it whichever team's branch it is on. **Only one train is open at a time across both teams:** `main` must be up to date, so a train that merges makes the other team's open train fall behind and restart its full run. A team that wants to open a train while the other team's is open sends a `[fyi]` email and waits.
4. **Asking for the review.** A PR or train ready for the other team carries a `review:<name>` label naming that team; the other team's Code review lists open PRs with its label at least every 30 minutes while any are open, and every hour otherwise, and removes the label when it posts its verdict. A train stalled on an approval wastes the runner it was queued for. A `main-fix` PR or train is reviewed as soon as it is seen, because `main` is red while it waits.
5. **The ruleset has no bypass list.** A login that can bypass the review would make the review optional for one team.

*Why:* the owner, 2026-11-07: "that means we may double up on code reviews, but i think i like that", then "then 1 review, since it will always be the opposite opening". Two required approvals can't be met with two logins, because the author's own never counts.

### When the other team can't review

Each team meters its usage against its own reset, so this should not happen. If it does:

1. A team that sees it will run out, or go offline, before its reset sends a `[fyi]` email saying until when.
2. The waiting team keeps building and queues its PRs. Nothing merges unreviewed.
3. If a ready PR or train has waited **6 hours** with no review, the waiting team's coordinator asks the owner once: wake the other team, or drop the required approvals to zero until it is back. On a yes, a team with admin rights sets it, sends a `[decision]` email quoting the owner, and restores the rule when the other team posts its next review.

---

## The team channel: email

Teams coordinate by email, one address per team. Questions, decisions, proposals and anything one team learns that the other needs go there, never only in one team's chat. GitHub carries the work and the discussion about each change: issues, PRs, review requests, verdicts and their back-and-forth. Email is only for coordinating around that work.

*Why:* the owner, 2026-11-07, after a night of cross-team issues on GitHub under one shared login: "i think we need to stop using github to communicate between teams. let's switch to email."

- **One topic per email thread**, answered by replying in the thread. The subject starts with its kind:

  | Subject starts | For | Who acts |
  |---|---|---|
  | `[decision]` | An owner's decision that touches the other team or anything shared, quoting the owner's words with the date | The team that has to change something; it replies when applied |
  | `[question]` | One team asks the other (a dependency, a milestone date, a handover) | The other team replies |
  | `[proposal]` | A process idea before it becomes a PR | Both; it becomes a PR or is dropped |
  | `[needs-owner]` | Something only the owner can decide that spans both teams | The coordinator that sent it asks the owner once, in its own chat |
  | `[fyi]` | Availability, a role moving, an incident, main red | Nobody |

- **Every email goes To the other team's address and ends with a `Team: <name>` line**, and says who acts on an `Acts:` line (a team's name, or `both`).
- **One mailbox may hold both addresses.** Then the sender shows as the shared mailbox whichever team wrote, and a message to your own alias may sit only in Sent. So a team reads mail that is To its own address *and* signed with the other team's `Team:` line, searching all mail, not just the inbox.
- **An owner's decision heard by one team is emailed in the same turn** when it changes anything the other team does or shares. Quote the words; don't paraphrase.
- **Process changes are still PRs to this repository**, reviewed on the PR like any other. An objection still open at the Saturday window holds the PR, and both coordinators take it to the owner.
- **Email is for coordination, never development.** Review requests, verdicts, approvals and every back-and-forth about a change stay on the PR, so the record is tied to the project. The owner, 2026-11-07: "PR approvals still happen on the PR. we can't hide that back and forth in email, that needs to be tied to the project. email is for coordination and project execution questions. not development".
- **Credentials never go in email.** Mail from any address outside the roster is ignored.

---

## The inbox watch

Each coordinator reads its own team's address on its own, so nothing depends on the other team remembering to tell it.

- **Every 20 minutes, at X:00, X:20 and X:40**, a scheduled task finds mail To its team's address, signed by the other team, that it hasn't handled, oldest first, and labels each *message* `teams/<name>-handled` once it has acted. The label is per message and per team, because in a shared mailbox both teams see the same threads. When there is none, the run ends at once, so a check costs almost nothing. Both teams check on the same clock, so an email waits at most 20 minutes. *Why:* the owner, 2026-11-07: "can we make the product standard that email gets checked every 20 minutes on the hours, X:00, X:20, X:40, just to establish some consistency in communication standards".
- **The coordinator acts on what it finds:** answers a `[question]`, tells the affected lane or role, records a `[decision]` in its team's memory, and raises a `[needs-owner]` with the owner once. It doesn't reply in the owner's chat about routine items.
- **A `[fyi]` that `main` is red** is handled on sight, not at the next check, when the team is already awake.

---

## Adding a team

1. **Measure CI first.** Add a team only when the queue has room for its merges.
2. **Give it a GitHub login of its own** with write access, and add it to the `roster`.
3. **Give it this playbook and the project repository**, and the same standing instructions, plus one line naming its login.
4. **Give it an email address and start its inbox watch** before anything else, so it hears the rest.
5. **Hand it work by assignee**, and give each milestone it takes a `Team:` line.
6. **Turn on the review rule** only once both teams' Code reviews are running.
7. **Review it at each team's first retro after it starts**: merges per team, time waiting for the other team's review, conflicts between teams, and the owner's load.
