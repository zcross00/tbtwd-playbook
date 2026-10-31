#!/usr/bin/env bash
# Warns when main moved while full ran, for Code review: the run then tested
# an older main than the one the PR would merge onto (playbook/05-parallel.md).
set -eo pipefail
tested=$(cat "${RUNNER_TEMP:-/tmp}/tested-main" 2>/dev/null) || exit 0
main=$(git ls-remote origin refs/heads/main | cut -f1)
if [ -n "$main" ] && [ "$main" != "$tested" ]; then
  msg="main moved from $tested to $main while this ran: check what merged since before merging this PR"
  echo "::warning::$msg"
  echo "$msg." >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
fi
