# 12. GitHub identities

When every agent acts on GitHub as the owner, through the owner's AI tool, every gate is a promise: GitHub can't tell Code review from a work thread, or either of them from the owner. This page gives the review side its own GitHub account, held by a separate AI account, so GitHub itself enforces the review gate. The build side keeps acting as the owner.

---

## Two identities

The project lives in an organization that the owner's personal account owns, on a plan that enforces rulesets on private repositories (GitHub Team or above).

| Account | Driven by | Org role | Does |
|---|---|---|---|
| **Owner** (the owner's own account) | The owner, and the build side's AI account acting for the owner: coordinator, work threads, Dev process | Owner | Direction and decisions (the owner); branches, PRs, issues, milestones, the board and grooming (the build side) |
| **Verifier** (machine account) | The review side's AI account: Code review, Verification | Member, Write, sole member of team `Verifiers` | Reviews, approves, merges, closes issues and milestones |

- The owner creates and owns the verifier account, with an address on the company domain and two-factor authentication on. It is the owner's one free machine account under GitHub's terms; a second one would need a paid personal plan.
- **Each AI account connects to exactly one GitHub account.** The build side never holds the verifier's login. That separation is what makes the gate real; a shared credential would make it a convention again.
- The owner is not in `Verifiers`, so a PR the build side opens as the owner still needs the verifier's approval. Decision answers keep telling the owner apart from agents by the AI tool's app marker, as before ([Tracking work](03-tracking.md)).
- A project that wants code authorship apart from the owner can add a developer machine account for the build side; nothing else on this page changes.

*Why accounts, not GitHub Apps:* GitHub documents that approvals from accounts with write access count toward required reviews. It doesn't document app approvals, and an app's key would sit in a workspace every thread can read.

---

## The gate on `main`

A ruleset on the default branch:

- Requires a pull request, with 1 approval from team `Verifiers` (the Required reviewers rule).
- Dismisses stale approvals when new commits are pushed.
- Requires the train's CI check.
- Blocks force pushes and deletion.
- Has **no bypass list**. The build side acts as the owner, so an owner bypass would be the build side's bypass. In an emergency the owner turns the ruleset off by hand and back on after.

Only an approval from `Verifiers` satisfies the rule, and only the review side's AI account holds that login. Code review owns these settings under its gate authority ([Tests and gates](07-gates.md)) and may change them without asking the owner, like any other gate.

---

## How this sits with two crews

With this page, the second AI account in [Two crews](11-crews.md) is the **review side**: it runs Code review and Verification and nothing else. A build crew in the same AI account would hold the verifier's login. The crews still talk only through the tracker.

Until the review side's AI account is connected, Code review works as before and the ruleset stays off: in the build side's account it acts as the owner, who isn't in `Verifiers`.

---

## Moving a personal repository into the organization

Do it in one window, between trains, in this order:

1. The owner creates the org, installs the AI tool's GitHub app on it, and creates the verifier account and the `Verifiers` team.
2. Process changes that name the new identities merge first (the Saturday window).
3. The owner transfers the repositories. GitHub moves issues, PRs, wiki, secrets and deploy keys, and redirects old links and git remotes.
4. Code review merges one PR that rewrites every `owner/repo` the project names itself: reusable workflow `uses:` lines, checkouts of the playbook, `.playbook.toml`, and script defaults. Redirects aren't documented for Actions `uses:`, so nothing relies on them.
5. Dev process re-registers self-hosted runners at the org level and watches the first train.
6. The owner swaps the workspace's repository list to the new names.
7. When the review side's AI account connects as the verifier, Code review turns the ruleset on after the first verifier approval lands.
