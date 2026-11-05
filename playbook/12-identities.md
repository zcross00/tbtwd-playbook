# 12. GitHub identities

When every agent acts on GitHub as the owner, through the owner's AI tool, every gate is a promise: GitHub can't tell Code review from a work thread. This page gives each AI account its own GitHub login and makes every PR need an approval from the *other* login, so GitHub itself enforces review.

---

## Two logins, cross-review

The project lives in an organization that the owner's personal account owns, on a plan that enforces rulesets on private repositories (GitHub Team or above).

| AI account | GitHub login | Org role |
|---|---|---|
| The owner's | The **owner's** account, as today | Owner; member of team `Verifiers` |
| A second one | A **developer** machine account | Member, Write; member of team `Verifiers` |

- **Each AI account connects to exactly one GitHub account.** Either can build: branches, PRs, comments, and creating, moving and editing issues, labels, milestones and the board. Work can tilt either way mid-project without changing anything here.
- **GitHub never lets an author approve their own PR.** With both logins in `Verifiers` and one approval required, a PR built in one AI account merges only after the other approves it.
- **Each AI account runs a Code review thread that reviews only the other's PRs.** The home crew's Code review keeps gate authority and owns the ruleset; the other applies this playbook as written.
- The owner creates and owns the developer account, with an address on the company domain and two-factor authentication on. It is the owner's one free machine account under GitHub's terms.
- The owner can approve the developer's PRs by hand. PRs posted as the owner need the other AI account's approval.
- Decision answers keep telling the owner apart from agents by the AI tool's app marker, as before ([Tracking work](03-tracking.md)).

---

## The gate on `main`

A ruleset on the default branch:

- Requires a pull request, with 1 approval from team `Verifiers` (the Required reviewers rule).
- Dismisses stale approvals when new commits are pushed.
- Requires the train's CI check.
- Blocks force pushes and deletion.
- Has **no bypass list**. Agents act as the owner, so an owner bypass would be theirs too.

**When one AI account can't review** (out of budget, or not connected yet), the other's PRs can't merge. Code review then turns the ruleset off and files a `deferred gate` issue ([Tests and gates](07-gates.md)), and turns it back on when both accounts review again. Code review owns these settings under its gate authority and may change them without asking the owner, like any other gate.

---

## How this sits with two crews

The two crews of [Two crews](11-crews.md) are the two AI accounts. Either crew may build; each crew's Code review thread reviews the other crew's PRs; everything else that is single in the home crew stays single. The crews still talk only through the tracker.

---

## Moving a personal repository into the organization

Do it in one window, between trains, in this order:

1. The owner creates the org, installs the AI tool's GitHub app on it, creates the developer account, sets the members' base permission to Write, and creates team `Verifiers` with both logins.
2. Process changes that name the new identities merge first (the Saturday window).
3. The owner transfers the repositories. GitHub moves issues, PRs, wiki, secrets and deploy keys, and redirects old links and git remotes.
4. Code review merges one PR that rewrites every `owner/repo` the project names itself: reusable workflow `uses:` lines, checkouts of the playbook, `.playbook.toml`, and script defaults. Redirects aren't documented for Actions `uses:`, so nothing relies on them.
5. Dev process re-registers self-hosted runners at the org level and watches the first train.
6. The owner swaps the workspace's repository list to the new names.
7. When the second AI account connects as the developer and both Code review threads have approved one of the other's PRs, Code review turns the ruleset on.
