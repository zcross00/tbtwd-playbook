# Changing the playbook

The playbook's `main` branch is the process. A project that follows the playbook is driven only by what is on `main`: not by a PR still open, not by a rule in the project's own files, not by a message. The baseline changes only like this:

1. **A reason from use.** A retro pick, a blocker, or a difference that proved itself on a project. "It could be better" is not a reason; that is how processes fall apart.
2. **One PR per change.** The PR says the problem, the evidence (what happened, where), and the change. It keeps the *Why* style: a new rule carries the incident behind it.
3. **The owner approves the change, not the merge.** The owner's yes on the retro pick (or their own ask) is the approval, quoted in the PR. Code review merges, as everywhere else; nobody asks the owner to press the button.
4. **Version and log it.** A wording fix is a patch (2.0.1); a changed or added rule is a minor version (2.1); a changed role or lifecycle stage is a major version (3.0). Add a line to [CHANGELOG.md](CHANGELOG.md).

## When changes merge

**Changes merge on Saturday, from 11:00 America/Chicago until the end of that Saturday.** Not before, however long the PR has been approved. Until it merges, a change isn't in force.

**Except in an emergency.** An emergency PR carries the `emergency` label and a line in its body starting `Emergency:` that quotes the owner's words declaring it, with the date and a link. It may merge at once. The emergency is the owner's call, not a thread's or the coordinator's.

The `merge-window` workflow enforces both: it sets a `merge-window` status on every open PR, green inside the window or for an emergency, red otherwise, and `main` requires it.

*Why:* the owner (2026-10-31): "the repo becomes the bible, any changes to it do not merge until saturday at 11AM, and the process can only be driven off of what is in that repo's main, unless there is an emergency situation (in which we would circumvent the 11AM merge time)". A process that changes mid-week, a rule at a time, is a process nobody can keep up with.
