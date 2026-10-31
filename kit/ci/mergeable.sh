#!/usr/bin/env bash
# Whether a PR still merges cleanly with main, for CI on the PC: fails a
# conflicted PR before the long build. Needs GH_TOKEN and PR (the PR's number).
# With HEAD_SHA (the head the run was started for) it also fails a run that is
# already stale: a push to a draft seconds before it's marked ready can start
# the ready run on the old head, and the new head's run skipped full as a draft.
# GitHub works out mergeability after a push, so this asks up to 6 times, 10 s
# apart; when it still doesn't know, or the API can't be read, the build runs.
set -eo pipefail
source "$(dirname "$0")/../lib/config.sh"
check=$(cfg ci.local_check "the full local check")
api=${GITHUB_API_URL:-https://api.github.com}
for _ in 1 2 3 4 5 6; do
  pr=$(curl -fsSL -H "Authorization: Bearer $GH_TOKEN" "$api/repos/$GITHUB_REPOSITORY/pulls/$PR") || pr=""
  # The first "sha" in the PR is its head's.
  head=$(echo "$pr" | grep -o '"sha": *"[0-9a-f]*"' | head -1 | sed 's/.*"\([0-9a-f]*\)"$/\1/') || head=""
  if [ -n "$HEAD_SHA" ] && [ -n "$head" ] && [ "$head" != "$HEAD_SHA" ]; then
    echo "This run is for $HEAD_SHA, but the PR's head is now $head, and that push may have"
    echo "had no full run. Mark the PR draft and then ready again to run the head (playbook/05-parallel.md)."
    exit 1
  fi
  mergeable=$(echo "$pr" | grep -o '"mergeable": *[a-z]*' | sed 's/.*: *//') || mergeable=""
  case $mergeable in
    false)
      echo "This PR conflicts with main: merge main, run $check and push (playbook/05-parallel.md, merge trains)."
      exit 1 ;;
    true) echo "mergeable"; exit 0 ;;
  esac
  sleep 10
done
echo "mergeability unknown; building anyway"
exit 0
