#!/usr/bin/env bash
# Brings main up to date in a PR's run, for CI on the PC, so full tests what
# the PR would merge onto now. A pull_request run checks out the merge
# commit GitHub made when the run was queued, a run can wait an hour behind
# others, and GitHub remakes refs/pull/N/merge only when it gets round to it
# (on 2026-10-23 #491's was still on the old main 15 minutes after a merge).
# #455's run tested a merge that predated #453, which is how main went red.
# This fetches main and merges it into that merge commit, which gives the
# PR's head on today's main. It writes what was tested to the run's summary,
# and saves main's head for main-moved.sh.
set -eo pipefail
source "$(dirname "$0")/../lib/config.sh"
check=$(cfg ci.local_check "the full local check")
head=$(git rev-parse HEAD^2)
git fetch -q origin main
main=$(git rev-parse FETCH_HEAD)
if ! git -c user.name=ci -c user.email=ci@localhost merge -q --no-edit FETCH_HEAD; then
  git merge --abort || true
  echo "This PR conflicts with main ($main): merge main, run $check and push (playbook/05-parallel.md, merge trains)."
  exit 1
fi
echo "Tested PR head $head merged onto main $main." | tee -a "${GITHUB_STEP_SUMMARY:-/dev/null}"
echo "$main" > "${RUNNER_TEMP:-/tmp}/tested-main"
