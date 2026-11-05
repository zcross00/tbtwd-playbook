# 12. GitHub identities

Most agents act on GitHub as the owner, through the owner's AI tool. That makes every gate a promise: GitHub can't tell Code review from a work thread, so a review "approval" is only as strong as everyone's discipline. This page gives the gate roles identities of their own, so GitHub itself enforces the gates that matter.

---

## The shape

- **The project lives in an organization** that the owner's personal account owns, on a plan that enforces rulesets on private repositories (GitHub Team or above).
- **Gate roles are GitHub Apps**, not extra user accounts. Apps are free, need no seat, and don't count against the one free machine account a person may hold.
- **Everyone else acts as the owner**, as before: coordinators and work threads push branches and open PRs through the owner's AI tool.
- **A second crew ([Two crews](11-crews.md)) is one machine account** the owner creates and owns, with the org's Write role. It never holds an app key.

| Role | App | Permissions on the project repo | Acts as the app to |
|---|---|---|---|
| Code review | `<Project> Code Review` | Checks, statuses, pull requests, contents: write | Post the `code-review` check, review, merge |
| Verification | `<Project> Verification` | Issues: write; contents, pull requests: read | Close issues and post verification results |
| Dev process | `<Project> Dev Process` | Actions, issues: write; org self-hosted runners: write | Runner and workflow housekeeping, usage readings |

*Why apps:* GitHub's terms allow one free machine account per person, and a fake user per role would be a paid seat each. An app is the identity GitHub built for automation.

---

## The gate is a check, not an approval

Code review's verdict is a **check run named `code-review`** on the PR's head commit: success when there are no blocking findings, failure listing them when there are. The ruleset on `main` requires that check **with Code review's app as its expected source**, so a check of the same name from anyone else doesn't count.

The ruleset on `main`:

- Require a pull request before merging, with 0 approvals (the check is the approval).
- Require status checks: `code-review` from the Code Review app, and the train's CI check.
- Block force pushes and deletion.
- Bypass: org admins only, used for an owner-declared emergency.

Code review owns these settings under its gate authority ([Tests and gates](07-gates.md)) and may change them without asking the owner, like any other gate.

*Why not an approving review:* GitHub documents that approvals from people with write access count; it doesn't document app approvals. A required check with an expected source is documented and can't be faked by another identity.

---

## Using an app identity

1. Each app's private key is stored as a secret in the crew's cloud environment, entered by the owner. Keys are never pasted into chat, issues or files.
2. The role's thread turns the key into a one-hour installation token with `kit/app/token.sh` and calls the GitHub API with it.
3. **Only the named role uses its key.** Every thread in one workspace can read the same environment, so this is a process rule, checked at retro, not a wall. The wall that GitHub enforces is between crews: the added crew's workspace holds no keys.
4. A new required check leaves open PRs waiting until their next push, so Code review turns a new check on between trains and re-posts it on every open PR.

---

## Moving a personal repository into the organization

Do it in one window, between trains, in this order:

1. The owner creates the org and installs the AI tool's GitHub app on it.
2. Process changes that name the new identities merge first (the Saturday window).
3. The owner transfers the repositories. GitHub moves issues, PRs, wiki, secrets and deploy keys, and redirects old links and git remotes.
4. Dev process merges one PR that rewrites every `owner/repo` the project names itself: reusable workflow `uses:` lines, checkouts of the playbook, `.playbook.toml`, and script defaults. Redirects aren't documented for Actions `uses:`, so nothing relies on them.
5. Dev process re-registers self-hosted runners at the org level and watches the first train.
6. The owner swaps the workspace's repository list to the new names.
7. The owner creates the role apps; Code review posts its check unrequired for a day, then turns the ruleset on.
