# 12. Roles and GitHub identities

Every thread has one of three roles, and the role decides what it may do on GitHub. The rule is written here, stamped on every post, and checked by a workflow, so it works the same in any AI account that follows this playbook. GitHub itself enforces the one wall it can: no PR merges without an approval from a different login than its author's.

---

## Three roles

A thread is given its role when it starts, on the first line of its instructions (`Role: overseer`, `Role: architect` or `Role: inquisitor`), and keeps it for its life. If nobody said, it is an architect.

| Role | Playbook roles ([Roles](02-roles.md)) | May do on GitHub | Never does |
|---|---|---|---|
| **Overseer** (planner) | Coordinator, daily backlog review, grooming, retro, Dev process's planning | Create, edit, label, milestone, move and park issues and milestones; the board | Write code, approve, close issues |
| **Architect** (developer) | Work threads, Dev process's tooling changes | Push branches, open and update PRs, comment, set `board: status=` on its own issues | Create or move work items, approve, close issues |
| **Inquisitor** (reviewer, verifier) | Code review, Verification | Review, approve, merge, close issues and milestones, file correction issues | Write code, groom, move work items |

- **An architect who finds new work** writes it into the grooming requests file (or a PR comment); an overseer files the issue.
- **Every GitHub post an agent makes starts with its role line,** `Role: <role>`, above the text. It is what the guard and the retro read.

---

## The guard

The `kit-role-guard` workflow (`kit/roles/guard.py`, public in this repository) runs on every issue opened or closed, every PR push and every review submitted. It touches only agent actions (made through the AI tool's app, or carrying its footer); the owner's own actions and workflow bots are left alone.

| Agent action | Allowed when | Otherwise |
|---|---|---|
| Approving review | Stamped `Role: inquisitor` | Dismissed |
| PR head | An inquisitor (or the owner by hand) approved that commit | `role-guard` status stays pending, and the ruleset blocks the merge |
| Closing an issue | An inquisitor comment (the verification note) came first | Reopened |
| Opening an issue | Stamped `Role: overseer` or `Role: inquisitor` | Kept, labelled |

Every correction labels the item `role-violation` with the reason, and the retro reviews the label weekly. Merges are blocked outright: both the `Verifiers` approval and `role-guard` show in every PR's merge box. Work items are corrected after the fact, because GitHub's fixed permission levels give every pushing account issue rights too. Board moves and milestone changes can't be stamped, so they are reviewed at retro from the issue history.

---

## GitHub identities

**An AI account connects to exactly one GitHub login, and every thread in it acts as that login.** In cloud sessions the egress proxy replaces any token a thread supplies with the account's own connection, so a thread can't switch logins. Roles are therefore a process rule plus the guard, not separate GitHub permissions.

| AI account | GitHub login |
|---|---|
| The owner's | The owner's own account |
| A second one | A machine account (Write), created and owned by the owner, with two-factor authentication, on a paid plan if it isn't the owner's one free machine account |

- Both logins are in team `Verifiers`. The ruleset on `main` requires 1 approval from `Verifiers`, dismisses stale approvals, requires the train's CI check and the `role-guard` status, blocks force pushes and deletion, and has **no bypass list** (agents act as the owner, so an owner bypass would be theirs too).
- GitHub never lets an author approve their own PR, so **every PR needs an inquisitor in the other AI account** to approve it: cross-review. Each AI account runs at least one inquisitor.
- When one AI account can't review (out of budget, not connected yet), Code review turns the ruleset off under a `deferred gate` issue ([Tests and gates](07-gates.md)) and back on when both review again. Code review owns these settings under its gate authority.
- A third login (one per role) helps only where threads run on a machine with their own credentials, such as Remote Control sessions on a CI server with one `gh` login per role. That is optional and slow; adopt it only if the retro shows the guard isn't enough.
- Decision answers keep telling the owner apart from agents by the app marker and footer, as before ([Tracking work](03-tracking.md)).

---

## How this sits with two crews

Each crew of [Two crews](11-crews.md) may run threads of any role. Each crew runs an inquisitor that reviews the other crew's PRs. What is single in the home crew stays single.

---

## Moving a personal repository into the organization

Do it in one window, between trains, in this order:

1. The owner creates the org, installs the AI tool's GitHub app on it, creates the machine account as a Member (not an owner, who could turn the ruleset off), sets the base permission to Write, and creates team `Verifiers` with both logins.
2. Process changes that name the new identities merge first (the Saturday window).
3. The owner transfers the repositories. GitHub moves issues, PRs, wiki, secrets and deploy keys, and redirects old links and git remotes.
4. Code review merges one PR that rewrites every `owner/repo` the project names itself: reusable workflow `uses:` lines, checkouts of the playbook, `.playbook.toml`, and script defaults. Redirects aren't documented for Actions `uses:`, so nothing relies on them. The same PR adds the `kit-role-guard` caller.
5. Dev process re-registers self-hosted runners at the org level and watches the first train.
6. The owner swaps the workspace's repository list to the new names.
7. When the second AI account connects and each account's inquisitor has approved one of the other's PRs, Code review turns the ruleset on.
