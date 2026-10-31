<!--
TBTWD Playbook PR rules (playbook/04-lifecycle.md):
- Name each issue as "Refs #N" on its own line. Never put close/fix/resolve
  words right before "#N" (here or in commits): a merge must not close issues.
- Under each Refs line, one evidence line per ask in the issue, Check line included.
- A loosened or deferred gate links its `deferred gate` issue.
- Name files touched outside your issues' areas.
-->

## What this does

{one paragraph}

## Evidence

Refs #N
- Ask 1: {test name / check and gate / measurement / screenshot path}
- Check: {…}
- Ask 3: not in this PR, split to #M

## Gates

- [ ] No gate loosened or deferred
- [ ] Gate changed: `deferred gate` issue #…

## Outside my area

- {path}: {why}

## Ready gate

Full local check green on {commit}, merged with main at {commit}.
