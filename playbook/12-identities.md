# 12. GitHub identities

When every agent acts on GitHub as the owner, through the owner's AI tool, every gate is a promise: GitHub can't tell Code review from a work thread. This page splits building from reviewing across two GitHub logins, held by two AI accounts, so GitHub itself enforces the review gate.

---

## Two sides, two logins

The project lives in an organization that the owner's personal account owns, on a plan that enforces rulesets on private repositories (GitHub Team or above).

| Side | AI account | GitHub login | Runs | Org role |
|---|---|---|---|---|
| **Review side** | The owner's AI account | The **owner's** account, as today | Coordinator, grooming, Code review, Verification | Owner; sole member of team `Verifiers` |
| **Build side** | A second AI account | A **developer** machine account | Every work thread and Dev process | Member, Write |

- **Each AI account connects to exactly one GitHub account,** so the build side never holds a login that can approve. That separation is what makes the gate real.
- The build side does everything a work thread does today as the developer account: branches, PRs, comments, and creating, moving and editing issues, labels and milestones. It needs edit access to the board.
- **The review side writes no code.** A PR authored as the owner can't be approved by the owner, so it would wait for a hand bypass. Any code change, Dev process's included, goes to the build side.
- The owner creates and owns the developer account, with an address on the company domain and two-factor authentication on. It is the owner's one free machine account under GitHub's terms.
- Decision answers keep telling the owner apart from agents by the AI tool's app marker, as before ([Tracking work](03-tracking.md)).

*Why the owner's login reviews:* GitHub documents that approvals from people with write access count. The owner can also approve by hand, in the same place.

---

## The gate on `main`

A ruleset on the default branch:

- Requires a pull request, with 1 approval from team `Verifiers` (the Required reviewers rule).
- Dismisses stale approvals when new commits are pushed.
- Requires the train's CI check.
- Blocks force pushes and deletion.
- Has **no bypass list**. Agents act as the owner, so an owner bypass would be theirs too. In an emergency the owner turns the ruleset off by hand and back on after.

Code review owns these settings under its gate authority ([Tests and gates](07-gates.md)) and may change them without asking the owner, like any other gate.

---

## How this sits with two crews

With this page, the two crews of [Two crews](11-crews.md) are the two sides above: the home crew, in the owner's AI account, is the review side, and the added crew is the build side. The crews still talk only through the tracker.

Until the build side's AI account is connected, work threads keep running in the owner's account as before and the ruleset stays off.

---

## Moving a personal repository into the organization

Do it in one window, between trains, in this order:

1. The owner creates the org, installs the AI tool's GitHub app on it, creates the developer account, sets the members' base permission to Write, and creates team `Verifiers` with only the owner in it.
2. Process changes that name the new identities merge first (the Saturday window).
3. The owner transfers the repositories. GitHub moves issues, PRs, wiki, secrets and deploy keys, and redirects old links and git remotes.
4. Code review merges one PR that rewrites every `owner/repo` the project names itself: reusable workflow `uses:` lines, checkouts of the playbook, `.playbook.toml`, and script defaults. Redirects aren't documented for Actions `uses:`, so nothing relies on them.
5. Dev process re-registers self-hosted runners at the org level and watches the first train.
6. The owner swaps the workspace's repository list to the new names.
7. When the build side's AI account connects as the developer and its first PR is approved by `Verifiers`, Code review turns the ruleset on and the owner's AI account stops starting work threads.
