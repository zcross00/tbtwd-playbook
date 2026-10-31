#!/usr/bin/env bash
# Build churn, always watched (playbook/09-cadences.md): the week's queue
# wait for the full runner, CI wall time per tier, and how often PRs merged
# main again before merging. Writes a table to the job summary. Needs GH_TOKEN
# and REPO (owner/name); the CI workflow is queue.ci_workflow in .playbook.toml
# and its tiers are the jobs named `quick` and `full`. The kit-churn
# workflow runs it weekly on a hosted runner, about a minute.
set -euo pipefail
source "$(dirname "$0")/../lib/config.sh"
: "${REPO:?REPO is not set}"
ci=$(cfg queue.ci_workflow ci.yml)
since=$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
# Every CI job of the week: its tier, queue wait and wall time, in minutes.
gh api --paginate "repos/$REPO/actions/workflows/$ci/runs?created=%3E$since&per_page=100" \
  --jq '.workflow_runs[].id' > "$work/runs.txt"
: > "$work/jobs.tsv"
while read -r run; do
  gh api "repos/$REPO/actions/runs/$run/jobs" --jq '.jobs[]
    | select(.conclusion == "success" or .conclusion == "failure")
    | select(.name == "quick" or .name == "full")
    | [.name,
       (((.started_at | fromdate) - (.created_at | fromdate)) / 60),
       (((.completed_at | fromdate) - (.started_at | fromdate)) / 60)]
    | @tsv' >> "$work/jobs.tsv"
done < "$work/runs.txt"
# PRs merged this week, and how many times each merged main again.
gh api --paginate "repos/$REPO/pulls?state=closed&per_page=100" \
  --jq ".[] | select(.merged_at != null and .merged_at > \"$since\") | .number" > "$work/prs.txt"
: > "$work/remerges.txt"
while read -r pr; do
  gh api --paginate "repos/$REPO/pulls/$pr/commits?per_page=100" \
    --jq '[.[] | select(.commit.message | test("^Merge (remote-tracking )?branch .*main|^Merge origin/main"))] | length' \
    | awk '{s += $1} END {print s + 0}' >> "$work/remerges.txt"
done < "$work/prs.txt"
stats() { sort -n | awk '{a[NR]=$1} END {if (NR) printf "median %.1f, worst %.1f (n=%d)", a[int((NR+1)/2)], a[NR], NR; else printf "none"}'; }
{
  echo "## Build churn since $since"
  echo
  echo "| Number | This week |"
  echo "|---|---|"
  echo "| full runner queue wait (min) | $(awk -F'\t' '$1=="full"{print $2}' "$work/jobs.tsv" | stats) |"
  echo "| full wall time (min) | $(awk -F'\t' '$1=="full"{print $3}' "$work/jobs.tsv" | stats) |"
  echo "| quick wall time (min) | $(awk -F'\t' '$1=="quick"{print $3}' "$work/jobs.tsv" | stats) |"
  echo "| re-merges of main per merged PR | $(stats < "$work/remerges.txt") |"
} | tee -a "${GITHUB_STEP_SUMMARY:-/dev/null}"
