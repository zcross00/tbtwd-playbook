# {Project}: development process

This project follows the [TBTWD Playbook](https://github.com/zcross00/tbtwd-playbook) as it stands on its `main` branch. The playbook is the only source of process rules. This file holds only facts specific to this project (who fills the roles, the areas, labels, CI commands, times) and engineering rules about its code. It never restates or overrides a process rule; a gap or a disagreement is a PR to the playbook.

---

## Owner and channel

- **Owner:** {name}. Decides direction, accepts milestones, approves retro picks and irreversible steps.
- **Where the owner reads:** {project chat / channel}. Questions go there, through the coordinator, with a recommendation.
- **Where status lives:** {issue tracker + board link}.

## Roles

| Role | Filled by |
|------|-----------|
| Coordinator | {agent / person} |
| Code review (merges, gate calls) | {…} |
| Verification (closes) | {…} |
| Dev process (CI, tooling, usage report) | {…} |
| Retro | {…} |
| Work threads | One per milestone |

## Areas

| Area | Owns (paths) |
|------|--------------|
| {area} | {paths} |

A file not listed belongs to whichever area last built it.

## Labels

`area: …` (one per area above), `priority: A|B|C`, `parked`, `decision`, `deferred gate`, `verification`, `main-fix`, `train`.

Priorities: A = {…}, B = {…}, C = {…}.

## CI

- **Tier:** {0 laptop / 1 build server / 2 hosted overflow / 3 enterprise}
- **Full local check (ready gate):** `{scripts/ci.sh}`
- **Merge gate:** `{full}` job on `{runner labels}`, run by merge trains
- **Nightly:** `{time UTC}`
- **Hosted budget:** {amount}/month; warn at {…}, stop at {…}

## Cadences

| Cadence | Time | Thread / schedule |
|---|---|---|
| Morning report | {…} | {…} |
| Daily backlog review | {…} | {…} |
| Weekly usage report + retro | {1 h before reset} | {…} |

## Engineering rules specific to this project

- {e.g. the core library has no UI-framework dependency}
- {e.g. saved data migrates from release N on}
