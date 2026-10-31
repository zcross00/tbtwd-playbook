#!/usr/bin/env bash
# Runs one kit script from the project's checkout: `kit/run.sh board/sync.py
# --apply`. A .py runs on the kit's Python (python.sh), anything else on bash.
# The kit-run action calls it, on Windows through Git's bash.
set -euo pipefail
kit="$(cd "$(dirname "$0")" && pwd)"
script=${1:?usage: kit/run.sh SCRIPT [ARGS...]}
shift
case $script in
  *.py) exec bash "$kit/python.sh" "$kit/$script" "$@" ;;
  *) exec bash "$kit/$script" "$@" ;;
esac
