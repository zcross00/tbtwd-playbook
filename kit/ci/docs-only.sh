#!/usr/bin/env bash
# Whether a PR touches anything but docs (ci.docs_only in .playbook.toml;
# default docs/ and *.md), for CI: writes
# code=true or code=false to $GITHUB_OUTPUT. Needs GH_TOKEN and PR (the PR's
# number; empty outside a PR, which always builds). The project's CI
# workflow runs it first.
set -eo pipefail
source "$(dirname "$0")/../lib/config.sh"
docs=$(cfg ci.docs_only '^docs/|\.md$')
# List the PR's files; when the list can't be read or is cut off at
# 100 files, everything runs.
code=true
if [ -n "$PR" ]; then
  files=$(curl -fsSL -H "Authorization: Bearer $GH_TOKEN" \
    "$GITHUB_API_URL/repos/$GITHUB_REPOSITORY/pulls/$PR/files?per_page=100" |
    grep -o '"filename": *"[^"]*"' | sed 's/.*"\([^"]*\)"$/\1/') || files=""
  echo "$files"
  if [ -n "$files" ] && [ "$(echo "$files" | wc -l)" -lt 100 ] &&
    ! echo "$files" | grep -qvE "$docs"; then
    code=false
  fi
fi
echo "code=$code" | tee -a "$GITHUB_OUTPUT"
