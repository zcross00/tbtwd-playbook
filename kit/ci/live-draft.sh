#!/usr/bin/env bash
# Whether a PR is a draft now, and whether it's a merge train, for CI: writes
# draft=true|false and train=true|false to $GITHUB_OUTPUT. Needs GH_TOKEN, PR (the PR's number; empty outside a PR,
# which is never a draft) and EVENT_DRAFT (what the event said). The project's
# CI workflow runs it.
#
# The event's word is from when the event fired, and GitHub can start a push's
# run after the PR was marked ready: on 2026-10-25 that draft run's failed
# full, newer than the ready run's, blocked #783 and #788 (newer_run.py).
# When the API can't be read, the event's word stands.
#
# A train is a PR whose body has a line starting "Train:", or one labelled
# `train` (playbook/05-parallel.md, merge trains). Only a train runs `full` on the PC (retro pick 3, Zac
# 2026-10-30 23:26Z); outside a PR (the nightly run, a manual run) train=true,
# since those check main. When the API can't be read, train=false: the PR
# waits for its next run rather than taking the PC unasked.
set -eo pipefail
draft=false
train=true
if [ -n "$PR" ]; then
  draft=$EVENT_DRAFT
  pr=$(curl -fsSL -H "Authorization: Bearer $GH_TOKEN" \
    "$GITHUB_API_URL/repos/$GITHUB_REPOSITORY/pulls/$PR") || pr=""
  live=$(echo "$pr" | grep -o '"draft": *[a-z]*' | head -1 | sed 's/.*: *//') || live=""
  case $live in
    true | false) draft=$live ;;
    *) echo "the PR couldn't be read; the event said draft=$EVENT_DRAFT" ;;
  esac
  train=false
  # The body as JSON: a line starts at the string's start or after an escaped \n.
  if echo "$pr" | grep -qE '"body": *"(Train:|([^"\\]|\\.)*\\nTrain:)|"name": *"train"'; then
    train=true
  fi
fi
echo "draft=$draft" | tee -a "$GITHUB_OUTPUT"
echo "train=$train" | tee -a "$GITHUB_OUTPUT"
