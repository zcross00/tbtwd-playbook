#!/usr/bin/env bash
# Runs the kit's Python. Arguments go to the interpreter.
#
# Where python3 (3.11 or newer, for tomllib) is on the PATH, that runs.
# Otherwise, on a self-hosted Windows runner with no Python installed (the
# laptop runner of playbook/06-ci.md), it fetches the embeddable Python once
# into the runner's tool cache and reuses it after that.
set -euo pipefail
if [ -z "${KIT_EMBEDDED_PYTHON:-}" ] && command -v python3 >/dev/null 2>&1 &&
   python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
    exec python3 "$@"
fi
command -v cygpath >/dev/null 2>&1 || { echo "kit/python.sh: no python3 3.11+ on the PATH" >&2; exit 1; }
ver=3.12.7
# python.org's published hashes for python-$ver-embed-amd64.zip: the SHA-256
# from its SBOM (python-$ver-embed-amd64.zip.spdx.json), the MD5 from the
# release page. The interpreter runs with tokens (BOARD_TOKEN, the job's
# GH_TOKEN), so a zip that doesn't match is never unpacked.
sha256=0d57bb6cb078b74d23dbfe91f77d6780d45bed328911609f1f7ee2ba1606bf44
md5=4c0a5a44d4ca1d0bc76fe08ea8b76adc
# Named by its hash, so a changed pin fetches afresh.
dir="$(cygpath -u "${RUNNER_TOOL_CACHE:?}")/python-embed-$ver-${sha256:0:12}"
if [ ! -x "$dir/python.exe" ]; then
    rm -rf "$dir.tmp" "$dir.zip"
    curl -fsSL -o "$dir.zip" "https://www.python.org/ftp/python/$ver/python-$ver-embed-amd64.zip"
    echo "$sha256  $dir.zip" | sha256sum -c - || { sha256sum "$dir.zip"; exit 1; }
    echo "$md5  $dir.zip" | md5sum -c -
    # Unpacked whole, then moved into place, so a failed unpack never leaves
    # a python.exe that later runs would trust. Windows' own tar reads zip
    # files; Git's doesn't.
    mkdir -p "$dir.tmp"
    (cd "$dir.tmp" && /c/Windows/System32/tar.exe -xf "$(cygpath -w "$dir.zip")")
    rm -rf "$dir"
    mv "$dir.tmp" "$dir"
    rm -f "$dir.zip"
fi
exec "$dir/python.exe" "$@"
