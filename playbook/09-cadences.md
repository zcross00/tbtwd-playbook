# 9. Cadences

Standing routines that keep the board true without anyone remembering to. Each runs as a scheduled task in its own thread. **If a routine's thread or schedule ends, it is recreated**; these are not optional.

| Cadence | When | Owner | Output |
|---|---|---|---|
| Nightly `main` | Daily, off-hours | CI | Full run on `main`; a red night leads the morning report |
| Board sync | On each `board:` comment, plus a backstop every few hours | CI | Board fields current |
| Morning report | Daily | Coordinator (inputs from Dev process) | Verified Done, In review, blocked, corrections, burn-down, CI numbers |
| Daily backlog review | Daily, before the working day | Its own thread | Stale issues re-checked; routine fixes; one list for the owner |
| Daily re-forecast | Daily | CI | Milestone due dates from measured pace |
| Weekly usage report | Weekly, ~1 h before the budget resets | Dev process | Spend by area and by thread |
| Weekly retro | Same time as the usage report | Retro thread | Ranked process changes for the owner to approve |

---

## Morning report

Leads with anything red (a red night, an AT RISK committed milestone, a blocked thread). Then, per area: verified Done yesterday, In review, In progress, blocked, sent back with corrections, estimate vs actual. Then the burn-down lines and the CI numbers (queue wait, wall time, re-merges, hosted spend). It counts only verified Done as progress.

---

## Daily backlog review

1. **Pick** (by script, so the run is lean): up to 50 open non-parked issues, least recently *reviewed* first; every issue In review for more than 24 hours; every open `decision` issue; every open milestone past its 50% date.
2. **Check each issue** for: its ask against the owner's own quoted words or the approved spec; a Check line, an estimate, and a day no later than its milestone's due date; a status that matches what happened; labels; links that open (on `main`, not a branch); whether it's still wanted or a duplicate.
3. **Fix the routine things** in place (links, labels, missing fields, cross-links). The coordinator approved those in advance.
4. **Record the review quietly.** No comments on the issues (each one fires workflows and notifications). The script stamps the reviewed issues in a file, so the next run takes the next stalest.
5. **Send what needs the owner to the coordinator as one list**, each with a recommendation: scope changes, moving issues between milestones, closes, and status calls that belong to another thread.
6. **Check the manual inputs**: hand-written pages past their review date, and decisions the owner made in chat that have no `decision` issue yet.

*Why:* picking the 50 stalest *by update time* picked only parked issues and fired a comment on each; picking by *review* time and staying quiet fixed both.

---

## Weekly usage report

About an hour before the weekly budget resets, Dev process captures what the week consumed and tries to attribute it:

- totals against plan, and the reading against the budget;
- spend by area (each milestone/lane, standing threads, coordinators);
- a per-thread table (lifetime, this week);
- CI: self-hosted hours, hosted minutes and cost, queue wait;
- any other resource with a bill.

Start by capturing it consistently; refine the attribution week by week. Reports are dated files (`report-YYYY-MM-DD.md`) next to the raw data, so trends can be computed later.

---

## Weekly retro

At the same time, the retro reviews the process, the owner included ("all processes are subject to retro"):

1. Read the week: the usage report, red nights, verification fails, queue incidents, threads that stalled, questions the owner was asked (and whether they should have been).
2. Propose a **ranked pick list** of changes, each with the problem, the evidence, and the change.
3. The owner approves picks (all, some, none) in one reply.
4. Approved picks land as PRs to the project's PROCESS.md, and, if they're general, to this playbook.
5. Record the week's results (picks, approvals with the owner's words).

Outside the retro, the process changes only when something is blocked.
