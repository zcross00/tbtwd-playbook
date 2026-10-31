# Changing the playbook

The baseline is frozen. It changes only like this:

1. **A reason from use.** A retro pick, a blocker, or a difference that proved itself on a project. "It could be better" is not a reason; that is how processes fall apart.
2. **One PR per change.** The PR says the problem, the evidence (what happened, where), and the change. It keeps the *Why* style: a new rule carries the incident behind it.
3. **The owner merges.** This repo is the one place where the owner is the merge authority, because it is the process itself.
4. **Version and log it.** A wording fix is a patch (2.0.1); a changed or added rule is a minor version (2.1); a changed role or lifecycle stage is a major version (3.0). Add a line to [CHANGELOG.md](CHANGELOG.md).

Projects pin the version they follow in their PROCESS.md and move up deliberately.
