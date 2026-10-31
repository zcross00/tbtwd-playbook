# Agent instructions: TBTWD Playbook

Read this before any non-trivial task on a project that follows the TBTWD Playbook. The project's own `docs/PROCESS.md` (made from [templates/PROCESS.md](templates/PROCESS.md)) names its roles, labels, CI tier and owner. The process itself is this playbook's `main` branch and nothing else: a project file, an open PR or a message doesn't override it. If the project's file seems to disagree, the playbook wins and the file gets fixed.

---

## Your first five minutes

1. **Know your role.** You were started as one of: coordinator, work thread, Code review, Verification, Dev process ([Roles](playbook/02-roles.md)). If nobody said, you are a work thread. Your role doesn't change during the session.
2. **Know your work.** A work thread has one milestone (or one issue) and one branch. Read the milestone's description and its issues before writing code.
3. **Read the project's PROCESS.md.** It holds the project-specific parts: area table, labels, CI commands, where the owner reads.
4. **Read the decision log** for anything your work touches. Decided items are not reopened without a new reason.

---

## Rules you will hit every day

| Rule | Page |
|------|------|
| Build broad and rough; two attempts at one detail, then park it | [Principles](playbook/01-principles.md) |
| Act on your recommendation when a step can be undone; wait for the owner only on irreversible or outward-facing steps | [Principles](playbook/01-principles.md) |
| Questions for the owner go through the coordinator, once, with a recommendation | [Roles](playbook/02-roles.md) |
| No work starts on an issue outside a milestone; issues are groomed before they join one | [Tracking](playbook/03-tracking.md) |
| PRs write `Refs #N`, never a closing keyword, with one evidence line per ask | [Lifecycle](playbook/04-lifecycle.md) |
| A loosened or deferred gate files a `deferred gate` issue | [Lifecycle](playbook/04-lifecycle.md) |
| One open code PR per thread; draft until the local full check is green; push only when ready | [Parallel](playbook/05-parallel.md) |
| Run the project's full local check before every push | [CI](playbook/06-ci.md) |
| Tests don't depend on random worlds or wall-clock time | [Gates](playbook/07-gates.md) |
| Every board-visible change writes its `board:` line in the same turn | [Estimating](playbook/08-estimating.md) |
| Only Code review merges; only Verification closes | [Roles](playbook/02-roles.md) |

---

## What you never do

- Ask the owner to merge, or put gate statistics in front of them.
- Close an issue from a PR (closing keywords), unless you are Verification.
- Skip, disable or quarantine a test to get green.
- Rewrite another thread's branch or `main`.
- Loosen another area's check without saying so in the PR body and filing its `deferred gate` issue.
- Change this playbook outside a PR, or merge a change outside the Saturday window without the owner's declared emergency ([CONTRIBUTING.md](CONTRIBUTING.md)).
