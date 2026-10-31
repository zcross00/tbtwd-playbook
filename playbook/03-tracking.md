# 3. Tracking work

Status lives in the issue tracker (GitHub issues plus a Projects board on the reference project) and nowhere else. The owner reads the board; the docs say how things work.

---

## Issues

- **One issue per piece of work:** each planned piece, each owed acceptance test, each spec approval, each rough edge, each idea.
- **Labels** give its area (`area: …`), its priority (`priority: A`, `B`, `C`), and `parked` for rough edges and ideas that aren't planned yet. Other standing labels: `decision`, `deferred gate`, `verification` (a correction), `main-fix`, `train`.
- **New rough edges and ideas are new issues**, labelled `parked`, never rows in a file. Updates are comments on the issue.
- **Every issue links its spec**, when it has one. Specs, the process and the decision log stay in the repo, since they change with the code.

---

## Milestones

- **No issue is worked until it's in a milestone.** A parked issue has no milestone until it's pulled into one, at a boundary.
- **A milestone is named for what its acceptance test proves**, as a statement the owner can check: "Rich mines pay big, and the shelves never run dry", not "Economy 2". Internal milestones (CI health, coverage, refactors) are named `Internal: …`, have no owner acceptance test, and close on a measured done-when.
- **Its description** holds the goal, the spec link, the done-when, its dates line, and ends with the acceptance test: setup, what to try, what passes ([templates/milestone.md](../templates/milestone.md)).
- **A milestone closes only on the owner's acceptance pass.** Every issue verified isn't enough on its own. The owner may pass without playing; that is their call. The acceptance build is prepared ahead of time, so the owner never waits on a build or CI.
- **Acceptance fails only where the team didn't build what was asked.** New opinions formed by seeing the result become new issues outside the milestone, each quoting the owner's words. A fail files a priority A correction in the same milestone for each thing that failed.

*Why:* a milestone exists so the owner can use the result; each issue passing its own check doesn't prove the whole works.

---

## Grooming: the gate into a milestone

An issue joins a milestone only once it's groomed and the coordinator approves. Groomed means:

1. its asks, and a **Check** line, which is its done-when;
2. a `board: estimate=N` line from the thread that will build it;
3. a size of one PR, L or smaller ([Estimating](08-estimating.md)), or else it's split;
4. every unknown filed as its own time-boxed investigation issue, giving the question, a capped estimate, and an answer as a comment plus any issues it turns up.

The thread comments `groomed: approved (coordinator)` and sets the milestone. A change to a milestone's scope or date after its thread has started goes to the owner. Verification corrections skip approval and join the original issue's milestone straight away.

*Why:* without a scope lock, milestones grow until they never close.

---

## The board

Board fields (Status, Estimate, Actual, Day, Week, Team) are set from `board:` lines in issue comments, copied by a sync job, because agents often can't edit board fields directly:

```
board: estimate=60 status=Ready
board: status=In progress
board: actual=72
board: status=In review
board: status=Done
board: day=2026-11-03
```

The newest line wins per key. A line holds only `key=value` pairs. Whoever changes an issue's stage writes the line in the same turn. An open issue is never shown as Done.

---

## Decisions

- **Every decision is an issue labelled `decision`.** Whoever asks the owner files it in the same turn: the title is the question, the body has the options and the recommendation. It stays open while pending.
- **When the owner answers**, the asker adds their words to the body as a quote (`> their words`) with the date and a link, and closes it as completed. A decision made unasked (in chat, in an acceptance test) is filed and closed the same way.
- **The decision log** (`docs/DECISIONS.md`, or the wiki generated from decision issues) is append-only. Decided items aren't reopened without a new reason.

---

## The owner's read: a generated wiki

The reference project generated its wiki every 30 minutes from milestones, issues and decision issues, so nobody edits it and nothing on it drifts. Hand-written pages (the vision) carry a `Last reviewed:` line and get re-read when it passes 30 days. The owner gets up to speed there; the chat is for ad hoc requests.
