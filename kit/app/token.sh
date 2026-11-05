#!/usr/bin/env bash
# Prints a one-hour installation token for a GitHub App (playbook/12-identities.md).
# Usage: token.sh <app-id> <org-or-user> [key-env-var]
# The app's PEM private key is read from the environment variable named by the
# third argument (default GITHUB_APP_KEY), never from a file in the repo.
set -euo pipefail

app_id=${1:?app id}
owner=${2:?installation owner}
key_var=${3:-GITHUB_APP_KEY}
key=${!key_var:?"$key_var is empty"}
api=${GITHUB_API_URL:-https://api.github.com}

b64url() { openssl base64 -A | tr '+/' '-_' | tr -d '='; }

now=$(date +%s)
header=$(printf '{"alg":"RS256","typ":"JWT"}' | b64url)
payload=$(printf '{"iat":%d,"exp":%d,"iss":"%s"}' $((now - 60)) $((now + 540)) "$app_id" | b64url)
signature=$(printf '%s.%s' "$header" "$payload" |
  openssl dgst -sha256 -sign <(printf '%s\n' "$key") | b64url)
jwt="$header.$payload.$signature"

call() {
  curl -fsS -X "$1" "$api$2" \
    -H "Authorization: Bearer $jwt" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28"
}

installation=$(call GET /app/installations |
  python3 -c 'import json,sys; o=sys.argv[1].lower(); print(next(i["id"] for i in json.load(sys.stdin) if i["account"]["login"].lower()==o))' "$owner")

call POST "/app/installations/$installation/access_tokens" |
  python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])'
