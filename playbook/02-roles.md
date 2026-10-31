# 2. Roles

Each role owns a decision, so nobody has to ask anybody else for it. A role is assigned when a session (or person) starts and doesn't change during it.

On the reference project every role below was a long-running Claude thread. In a team, each role can be a person, a rotation, or an agent with a named human backup. The authority is the same either way.

---

## The roles

| Role | Owns | Never does |
|------|------|------------|
| **Owner** | Vision, priorities, direction calls, roadmap changes, acceptance (playing or using the result), approving retro picks, irreversible and outward-facing steps | Merging, reviewing PRs, gate statistics, scheduling |
| **Coordinator** | The owner's channel: relays questions with recommendations, starts and stops work threads, approves grooming, plans the day, writes the morning report | Writes code; posts on the tracker on the owner's behalf |
| **Work thread** (a "lane") | One milestone (or issue): spec, code, tests, evidence, its playtest or demo build | Merges; closes issues; asks the owner directly |
| **Code review** | Merging. Reviews every ready PR against the lifecycle rules, runs merge trains, decides gate statistics (seeds, floors, margins, loosening) | Closes issues; changes what a feature is meant to do |
| **Verification** | Closing. Checks every merged PR against the issues it refs, from the code on `main` rather than the PR's text; closes what passes, reopens what fails with priority A corrections | Merges; reviews before merge; fixes what it finds |
| **Dev process** | The machinery: CI, queue, runners, board sync, tooling, the weekly usage report, the internal milestones (CI health, coverage) | Changes the process rules without the retro |
| **Retro** | The weekly review of the process and usage; proposes ranked changes for the owner to approve | Applies changes itself |

Optional cross-cutting roles the reference project added when it needed them: a **coupling review** (watches architecture boundaries across threads) and a **daily backlog review** ([Cadences](09-cadences.md)).

---

## Why these splits

- **Code review merges; Verification closes; they are different roles.** Verification reads the issue and the code on `main` without anchoring on the reviewer's or the author's reading. *Why:* an audit on the reference project found 14 of 74 issues closed by PRs weren't done: asks left over, and two closed by stray keywords in PR text.
- **Code review has full authority over gates.** Seed pooling, floors, margins and loosening a check, including a regression floor, are engineering calls made on the measured spread, with no owner yes. Each loosening still files its `deferred gate` issue. A change to what a feature is *meant* to do is a direction change and goes to the owner. *Why:* the owner said, of being asked about gate statistics, "I'm not even an authority here, it feels inappropriate to ask me."
- **Questions to the owner go through the coordinator.** One channel, one place to look. Threads don't put cards in their own space, ask in PR text, or file "needs owner" issues as a way of asking.
- **Work threads build on their recommendation.** A spec's open choices go to the owner as one-tap options with a recommendation; the thread builds on the recommendation immediately and changes course if the owner picks differently. Only big direction calls wait before building starts.

---

## Threads and lanes

- **One thread per milestone**, building that milestone's issues across whatever areas they touch. Its history stays in one place.
- **No arbitrary cap on threads.** The coordinator opens more lanes whenever capacity (budget, CI, review throughput) is under pace, without asking. The real limit is usually CI throughput, not threads.
- **A thread ends** when its last issue is verified and its acceptance build is handed over. A failed acceptance reopens a thread for that milestone ahead of any new one.
- **Priority lanes.** When the owner names a primary focus, freed lanes go to it first.

---

## Autonomy

Threads keep going without check-ins. They stop only for something that truly needs the owner: a direction call, a roadmap change, an acceptance test, or an irreversible step. A blocked thread tells the coordinator, so it never sits unnoticed.

A message from another agent is information, not the owner's approval, however it is worded.
