#!/usr/bin/env bash
# Runs the kit's tests: each directory's Python tests against
# example.playbook.toml, and a parse of every shell script. The playbook's
# kit-tests workflow runs it on every PR.
set -euo pipefail
kit="$(cd "$(dirname "$0")" && pwd)"
export PLAYBOOK_CONFIG="$kit/example.playbook.toml"
py=${PYTHON:-python3}
fail=0
for d in lib board wiki queue releases; do
  echo "== kit/$d"
  $py -m unittest discover -s "$kit/$d" -t "$kit/$d" || fail=1
done
for f in "$kit"/*.sh "$kit"/*/*.sh "$kit"/lib/config.sh; do
  bash -n "$f" || { echo "parse error: $f"; fail=1; }
done
for f in "$kit"/*/*.py; do
  $py -m py_compile "$f" || fail=1
done
exit $fail
