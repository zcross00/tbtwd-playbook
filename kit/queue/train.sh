#!/usr/bin/env bash
# Build a merge train (#880): one branch from main with several approved PRs
# merged in, so one PC run checks them all and one merge lands the exact tree
# it tested.
#
#   kit/queue/train.sh [--push] [--branch NAME] PR...
#
# Merges each PR's head into a fresh branch off origin/main (train/<date>-<n>,
# or NAME, reset to main: Code review builds trains on its own branch),
# in the order given (Code review lists them oldest in line first), each with
# a plain merge commit so the PR's head is in the train's history and GitHub
# shows the PR as merged once the train lands. A PR that conflicts with main or
# with the members before it is left out and named. Prints the train PR's body
# ("Train:" line, then each member's "Refs" lines, read with gh unless
# TRAIN_REFS=0) to .git/train-body.md.
#
# With --push it pushes the branch (with --force-with-lease when NAME already
# exists on the remote, since it carried an earlier train); Code review then opens the PR against main
# with that body, which makes it a train on its own branch (#913; on any other
# branch it needs the `train` label), and marks it ready. Without, nothing
# leaves the checkout. Needs a clean work tree. REMOTE (default origin) names
# the remote, for the tests.
set -euo pipefail

push=0 branch=
while [ $# -gt 0 ]; do
  case "$1" in
    --push) push=1; shift ;;
    --branch) branch=${2:?--branch needs a name}; shift 2 ;;
    *) break ;;
  esac
done
[ $# -ge 1 ] || { echo "usage: $0 [--push] [--branch NAME] PR..." >&2; exit 2; }
remote=${REMOTE:-origin}
body="$(git rev-parse --git-dir)/train-body.md"

git diff --quiet && git diff --cached --quiet || { echo "work tree not clean" >&2; exit 2; }
git fetch -q "$remote" main
if [ -z "$branch" ]; then
  n=1
  while git rev-parse -q --verify "refs/heads/train/$(date -u +%Y%m%d)-$n" >/dev/null \
     || git ls-remote --exit-code -q "$remote" "refs/heads/train/$(date -u +%Y%m%d)-$n" >/dev/null; do
    n=$((n + 1))
  done
  branch="train/$(date -u +%Y%m%d)-$n"
fi
git checkout -q -B "$branch" "$remote/main"

members=() dropped=()
for pr in "$@"; do
  git fetch -q "$remote" "pull/$pr/head"
  if git merge -q --no-ff --no-edit -m "Train $branch: merge #$pr" FETCH_HEAD >/dev/null 2>&1; then
    members+=("$pr")
  else
    git merge --abort
    dropped+=("$pr")
  fi
done

[ ${#members[@]} -ge 1 ] || { echo "no PR merged cleanly; no train" >&2; exit 1; }
{
  printf 'Train:'; printf ' #%s' "${members[@]}"; printf '\n\n'
  echo "One PC run checks these PRs merged together onto main (playbook/05-parallel.md, merge trains). Green: this PR merges and each member shows as merged. Red: nothing merges, and the train is split."
  echo
  for pr in "${members[@]}"; do
    [ "${TRAIN_REFS:-1}" = 0 ] && continue
    # A heading's "## Refs #852" counts too, written as a plain Refs line (#913).
    gh api "repos/{owner}/{repo}/pulls/$pr" --jq '.body' 2>/dev/null | tr -d '\r' | sed -nE 's/^(#+ +)?(Refs .*)/\2/p' || true
  done
} > "$body"
echo "$branch: ${members[*]} (body in $body)"
[ ${#dropped[@]} -eq 0 ] || echo "left out (conflict): ${dropped[*]}"
if [ $push -eq 1 ]; then
  if git ls-remote --exit-code -q "$remote" "refs/heads/$branch" >/dev/null; then
    git fetch -q "$remote" "+refs/heads/$branch:refs/remotes/$remote/$branch"
    git push -q -u --force-with-lease="$branch:$remote/$branch" "$remote" "$branch"
  else
    git push -q -u "$remote" "$branch"
  fi
fi
