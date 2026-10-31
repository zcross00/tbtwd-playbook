#!/usr/bin/env bash
# Writes the wiki's pages (gen.py) and pushes them to the repo's wiki, as one
# commit replacing every page, only when something changed. Run from the
# project's checkout (it reads .playbook.toml there). Needs GH_TOKEN (the
# job's token, with contents: write) and GITHUB_REPOSITORY. Run by the
# kit-wiki workflow; PYTHON names the interpreter (default: kit/python.sh).
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd)"
: "${GH_TOKEN:?GH_TOKEN is not set}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY is not set}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
${PYTHON:-bash "$kit/python.sh"} "$kit/wiki/gen.py" "$work/pages"
# The token goes in a header, not the URL, so git never prints it.
auth="AUTHORIZATION: basic $(printf 'x-access-token:%s' "$GH_TOKEN" | base64 | tr -d '\n')"
git -c http.extraheader="$auth" clone -q --depth 1 \
    "https://github.com/$GITHUB_REPOSITORY.wiki.git" "$work/wiki"
cd "$work/wiki"
# Every page is generated: a page gen.py no longer writes (a closed
# milestone's) goes, and so does any edit made on the wiki. art/ is the
# banner and screenshots (wiki.art_dir in .playbook.toml).
git rm -q -r --ignore-unmatch -- '*.md' art
cp -r "$work/pages/"* .
git add -A
if git diff --cached --quiet; then
    echo "Wiki unchanged"
    exit 0
fi
git -c user.name="${WIKI_BOT:-playbook-wiki}" -c user.email="actions@users.noreply.github.com" \
    commit -q -m "Regenerate from GitHub (kit/wiki/gen.py)"
git -c http.extraheader="$auth" push -q origin HEAD
echo "Wiki updated"
