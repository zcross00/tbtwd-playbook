# TBTWD Playbook

How to run a software project where one owner sets direction and a team of AI agents (or people, or both) does the building, without the process falling apart as it grows.

This playbook was extracted from a live project: a single-player game built end to end by parallel Claude threads, with one person setting direction, one laptop running CI, and more than a thousand issues and PRs through the same rules. It is written to be reused as-is on the next project, and adapted on purpose (not by drift) for a larger one, such as an enterprise application with human teams.

**Version 2.1.** The baseline is frozen, and `main` is the process: projects follow it as it stands, with no overrides of their own. Changes come as PRs ([CONTRIBUTING.md](CONTRIBUTING.md)), normally out of a weekly retro, and merge on Saturday at 11:00 America/Chicago unless the owner declares an emergency.

---

## The idea in five lines

1. **The owner's attention is the scarcest resource.** Everything else is built to protect it: the owner decides direction and accepts the result; nobody asks them to merge, review statistics, or babysit.
2. **Breadth first.** Build every system broad and rough, park details, and stop after two attempts at the same detail.
3. **A closed issue means done.** A merge closes nothing. A separate verifier closes work after checking it against what merged.
4. **Gates are explicit and owned.** Every check that blocks a merge has an owner, and every loosened gate leaves a tracking issue behind.
5. **The process changes only through its own loop.** A weekly retro proposes changes, the owner approves them, and they land here as PRs on Saturday.

---

## Read in this order

| # | Page | What it answers |
|---|------|-----------------|
| 1 | [Principles](playbook/01-principles.md) | Why the rules exist; the few that matter most |
| 2 | [Roles](playbook/02-roles.md) | Who does what: owner, coordinator, work threads, Code review, Verification, Dev process |
| 3 | [Tracking work](playbook/03-tracking.md) | Issues, milestones, grooming, decisions, the board |
| 4 | [Lifecycle and definition of done](playbook/04-lifecycle.md) | The stages from idea to verified Done, and the rule behind each gate |
| 5 | [Working in parallel](playbook/05-parallel.md) | Branches, one PR per thread, shared files, merge trains |
| 6 | [CI tiers](playbook/06-ci.md) | From one laptop runner to enterprise CI, and when to move up |
| 7 | [Tests and gates](playbook/07-gates.md) | Deterministic tests, statistical gates, deferred gates |
| 8 | [Estimating and forecasting](playbook/08-estimating.md) | Sizes, units, honest due dates |
| 9 | [Cadences](playbook/09-cadences.md) | Daily review, morning report, nightly main, weekly usage report and retro |
| 10 | [Adopting the playbook](playbook/10-adopting.md) | Day-one setup, the enforcement kit, scaling to an enterprise |

Agents start at [AGENTS.md](AGENTS.md).

---

## What else is here

| Directory | Purpose |
|-----------|---------|
| [`templates/`](templates/) | Issue, milestone, decision and project-process templates, plus the design-artifact templates |
| [`templates/github/`](templates/github/) | Drop-in GitHub files: PR template, issue forms, and the `playbook-lint` workflow that enforces the PR rules |
| [`standards/`](standards/) | Coding conventions: general, Java, C# |
| [`style/`](style/) | How documentation is written |
| [`archive/v1/`](archive/v1/) | Version 1 (the Planner/Executor model), kept for reference and superseded by this playbook |

---

## License

[CC BY 4.0](LICENSE). Use it, adapt it, credit it.
