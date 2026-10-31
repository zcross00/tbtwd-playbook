# 1. Principles

The goal of the process is that everyone always knows what is being built now, why, and how they will know it is done, and that new ideas don't quietly derail the current work.

Every rule in this playbook carries a *Why*. Most of them were added after skipping them cost something real on the reference project. A rule whose *Why* no longer holds is a candidate for the retro, not for quiet removal.

---

## Breadth first (the rule that matters most)

Projects die by correcting one detail forever. So:

- **Build every system broad and rough first.** Each milestone builds the simplest version that meets its done-when. "Works, ugly, numbers made up" is a valid finished state.
- **Numbers, art and wording are placeholders** until a milestone's done-when depends on them.
- **Two-attempt rule.** If one detail has taken two attempts (two PRs, or one PR reworked twice) and still isn't right, stop. It becomes a parked issue with a note on what's wrong, a placeholder stays, and work moves on. It is revisited at a milestone boundary, not before.
- **"Is this blocking the done-when?"** If not, it becomes a parked issue, not part of the current work.
- **Agents call it out.** When a detail starts eating a milestone, the agent says so and proposes parking it, even mid-conversation, even when the owner raised it.
- **Feedback doesn't jump the queue.** Owner feedback that isn't a blocker or a yes/no on a gate becomes a parked issue with a one-line acknowledgement, and is triaged at the boundary. Acceptance tests are pass/fail. Agents don't invite open-ended tuning ("tell me what feels off").

*Why:* on the reference project the owner named this, in advance, as the way their earlier projects had died. Writing it down as a rule lets agents push back without it being personal.

---

## Protect the owner's attention

- **The owner decides direction and accepts results.** Everything else (merging, reviewing, gate statistics, scheduling, routine fixes) is delegated to a role that owns it ([Roles](02-roles.md)).
- **Act, then report, when a step can be undone.** Branches, PRs, issue edits, queries and reversible config go ahead on the agent's recommendation. Only irreversible or outward-facing steps (production, deletes, public posts, money) wait for the owner's typed yes.
- **Ask once, in one place, with a recommendation.** Questions go through the coordinator into the owner's main channel, never into PR bodies, issue comments or labels, where they get missed. The asker keeps working on the recommendation while waiting.
- **Never ask the owner to merge.** A merge button is not a decision.

*Why:* every time the owner became a bottleneck on something they mostly agreed with, work stalled for hours.

---

## Record the owner's words, not a paraphrase

Every decision is recorded with the owner's own words quoted, the question they answered, the date, and a link to where they said it. Paraphrases drift; quotes don't.

*Why:* months later, "the owner approved X" is worthless unless you can see what they were actually asked and what they actually said.

---

## Docs win

If the code and the process docs disagree, the docs win, or the docs change in the same PR. Decided items aren't reopened without a new reason.

---

## One source of status

Status lives in one place (the issue tracker and its board), and nowhere else. Docs say how things work, not how far along they are. No markdown copies of the board.

*Why:* every copy of status is a copy that goes stale.

---

## The process is under the same rules

The process itself, the owner included, is subject to the weekly retro ([Cadences](09-cadences.md)). It changes through a PR, not through drift. A change to the process mid-week, outside the retro, needs a blocker to justify it.
