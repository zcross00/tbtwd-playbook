# 4. Lifecycle and the definition of done

A closed issue means the work is done, and the board is only worth reading if that holds. So a merge closes nothing: an issue moves to **In review** when its PR merges, and only **Verification** closes it.

---

## Stages

| Stage | Who acts | Gate to leave it | Evidence | Board status |
|---|---|---|---|---|
| 1. Planned | Coordinator places it; owning thread estimates | Groomed and approved, with area, priority, milestone | `board: estimate=N status=Ready` | Todo → Ready |
| 2. Building | Owning thread, own branch, draft PR | Every ask built, or marked "not in this PR" with its own issue | `board: status=In progress` | In progress |
| 3. PR ready | Owning thread | Full local check green on the head, merged with `main`; `Refs #N` with one evidence line per ask; marked ready | PR body; `board: actual=N` | In progress |
| 4. Code review | Code review | Green merge-gate run on the current head (or its train), no conflict, rules 1–4 met | Its review | In progress |
| 5. Merge | Code review | Same as stage 4 | `board: status=In review` on each ref'd issue | In review |
| 6. Verification | Verification, after merge | Every ask covered by what merged, with real evidence | One checked line per ask | In review |
| 7a. Done | Verification | Passed | Closes as completed; `board: status=Done` | Done |
| 7b. Back to work | Verification, then the owning thread | Failed: back to stage 2, a priority A correction per failure | `board: status=In progress` | In progress |

---

## Before merge: the PR

1. **PRs never close issues.** A PR names each issue as `Refs #N`, on its own line. It never writes `close(s|d)`, `fix(es|ed)` or `resolve(s|d)` directly before `#N`, in the body or a commit message. To mention one, write "the fix in #N". A PR with no issue opens one first; only a docs-only PR may have none. *Why:* closing keywords moved cards to Done with nobody checking, and a stray "fix #N" closed an issue nothing had touched. The `playbook-lint` workflow enforces this ([templates/github/](../templates/github/)).
2. **Every ask has a line of evidence.** Under each `Refs #N`, one line per ask in the issue, including its Check line, naming what proves it: a test by name, a check and its gate, a measurement, a screenshot path. An ask not finished says "not in this PR". An ask the owner changed links where they did. *Why:* a PR summary says what was built, not what was asked.
3. **Attestations are tied to their issue.** A capability or acceptance file says `Owner:` (the area) and `Covers: #N, #M`, not a milestone name or a sentence.
4. **A loosened or deferred gate gets a tracking issue.** A PR that loosens, reports instead of gates, or defers any check or target files an issue labelled `deferred gate`: what changed, why, and what would restore it. It links it from the PR and related issues. Code review decides gate changes without the owner ([Roles](02-roles.md)). *Why:* a gate loosened in a PR body is forgotten once the PR merges.
5. **Ready means the full local check is green** on the head you mark ready, merged with `main`. *Why:* the merge-gate runner is everyone's queue; a red run costs everyone a slot.
6. **Push only when ready.** Work in draft, squash fix-ups locally. Each push to a ready PR restarts its merge-gate run.
7. **Only Code review merges**, after a green merge-gate run on the tree that lands (in practice, the merge train's head). It asks for changes when rules 1–4 aren't met, or when a ref'd issue isn't groomed into a milestone. Nobody asks the owner to merge.
8. **A PR handed over for merging is frozen.** Follow-ups go in the next PR. The one exception is a rebase to resolve a conflict, after which the full local check runs again.

---

## After merge: verification

9. **What Verification checks.** For each issue a merged PR refs, it reads the asks from the issue itself (plus any change the owner agreed to in its comments), and checks that:
   - what merged on `main` covers each ask, judged from the diff and code, not the PR's text;
   - the evidence named exists on `main` and proves that ask;
   - each attestation names this issue and the right owner;
   - any loosened gate has its `deferred gate` issue.
10. **Pass:** one comment with a checked line per ask, close as completed, `board: status=Done`. If a stated ask was split off unbuilt, the parent stays open and the split-off becomes its priority A correction. If only a check was loosened, the parent passes and the `deferred gate` issue tracks the rest.
11. **Fail:** the issue stays open (or reopens) at `In progress`, with a comment saying which asks failed. Each fix is a new issue labelled `verification`, priority A, in the same milestone, linked to the original and the PR. *Why:* a violation means the board was wrong, which is the most expensive kind of wrong, so its correction goes first.
12. **Nothing else closes work.** An issue is closed only by Verification, or as not planned / duplicate with a comment saying why. Anyone who finds a closed issue with an ask still open reopens it. Reopening an issue in a closed milestone reopens the milestone too.

---

## Measuring progress

**Progress is verified Done, nothing else.** The morning report gives, per area: issues verified Done yesterday, In review, In progress, blocked, sent back with their corrections, and estimate against actual. A merge isn't progress until Verification passes it.
