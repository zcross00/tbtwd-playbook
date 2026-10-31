# 7. Tests and gates

A gate is any check that can block a merge. Flaky gates cost every thread a slot in the queue, so they get the same care as code.

---

## Tests don't depend on dice or timing

- **Determinism.** All randomness comes from seeded generators owned by the system under test. Wall-clock time never affects results. Any bug can be reproduced from a seed plus a saved state.
- **A test sets up the state it checks** (staged or built directly), instead of searching a seeded world for a case that happens to fit. A test that has to search asserts only what holds for any case it might find.
- **No pass/fail on wall-clock time, thread scheduling or frame rate.** Step the system a fixed count, or wait for the state, with a timeout only as a backstop.
- **Test reactions from a standing start.** A rule that reacts to a change in state also gets a test that starts with the state already true (loading saved state goes from nothing to everything at once).

*Why:* two PRs that each passed together changed which case a searching test found, and turned `main` red.

---

## Checks on rare or noisy outcomes are staged or statistical

A gate that leans on an event a run sees only a few times, or on a number that moves with the seed, does one of two things:

- **Staged:** the check sets the event up itself, so it happens on every run and the gate tests the rule, not the dice.
- **Statistical:** it pools seeds, or compares paired runs with and without the rule on the same seeds, and its threshold sits **at least three spreads** from the measured mean. For a mean pooled over k seeds, the spread is the per-seed standard deviation over √k. A count gate ("at least N events") needs both margins ≥ 3: on the log scale, and (mean − threshold)/√mean. A count that measured 0 on any seed doesn't pass.

The PR that adds or changes such a gate measures it on at least 8 seeds besides CI's and gives the mean, spread, margin, and the CI time the gate adds. A gate that can't reach the margin within affordable CI time is staged instead, or re-gated with a `deferred gate` issue, never loosened quietly.

*Why:* on the reference project, shared-world checks failed 5 of 6 red runs on PRs that didn't touch them; one floor sat a single spread under its mean.

---

## Before a check leans on something, count it

- **Check the system has what a rule leans on.** Before building on an existing mechanic, count how often it happens in a real run.
- **Size the rule against the check.** A spec estimates from its counts how far the proposed change moves the number the check measures. A check the estimate says can't be reached is fixed in the spec, not discovered at the milestone.
- **Walk every check before approval.** Every test a spec promises is named in some milestone's check, and each check is walked step by step against what the milestones build.
- **New user commands run on real data** in the same milestone, and have to reach their effect, not just be accepted.

---

## Deferred gates

A PR that loosens, reports instead of gates, or defers any check, target or floor files an issue labelled `deferred gate`:

- what changed, and in which PR;
- why (the measurement);
- what would restore it.

It links from the PR and every related issue. The daily review keeps them visible. Code review owns the decision; the owner isn't asked.

---

## Coverage and quality

- Lints run with warnings as errors.
- Coverage floors sit one point under what each module measures. A PR that raises coverage two points raises its floor in the same PR. Lowering a floor, dropping a module, or adding a known gap fails CI unless the line names its own `deferred gate` issue.
- A list of untested outputs (enum variants, messages, events) is checked against `main`'s copy, so new outputs can't land untested.

---

## Saved-state compatibility

When users keep data (saves, records, documents), every stored field is named, so stored data outlives layout changes. A new field takes a default; a rename or change of meaning adds a migration. A frozen sample from every released build is loaded and exercised in CI, so a change that needs a migration fails without one. Before the first public release a PR may reset stored data, and says so; after it, never.
