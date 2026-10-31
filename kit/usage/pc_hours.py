#!/usr/bin/env python3
"""Hours the PC's self-hosted runners spent on jobs, per day and per runner label, from the Actions API.
Part of the weekly usage report (Zac 2026-10-31 15:19Z: "i'd want a complete picture of ALL resource usage").
Lists runs one day at a time (GitHub's run listing stops at 1,000), then each run's jobs.
Usage: python3 pc_hours.py 2026-10-25 2026-10-31   (inclusive, UTC days)"""
import datetime as dt, json, os, subprocess, sys, collections

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import playbook_config  # noqa: E402

REPO = "repos/" + "/".join(playbook_config.owner_repo(playbook_config.load()))

def gh(path):
    r = subprocess.run(["gh", "api", f"{REPO}/{path}"], capture_output=True, text=True)
    if r.returncode:
        raise LookupError(r.stderr.strip()[:200])
    return json.loads(r.stdout)

def secs(j):
    if not j.get("started_at") or not j.get("completed_at"):
        return 0
    a = dt.datetime.fromisoformat(j["started_at"].replace("Z", "+00:00"))
    b = dt.datetime.fromisoformat(j["completed_at"].replace("Z", "+00:00"))
    return max(0, (b - a).total_seconds())

def hosted(j):
    return j.get("runner_group_name") == "GitHub Actions" or any(
        l.startswith(("ubuntu-", "windows-", "macos-")) for l in j.get("labels", []))

def main(a, b):
    day, end = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
    total = collections.Counter()
    while day <= end:
        per = collections.Counter()
        page = 1
        while True:
            runs = gh(f"actions/runs?created={day}&per_page=100&page={page}")["workflow_runs"]
            for r in runs:
                for j in gh(f"actions/runs/{r['id']}/jobs?per_page=100").get("jobs", []):
                    if j.get("runner_name") and not hosted(j):
                        kind = "full" if "full" in " ".join(j.get("labels", [])).lower() else "light"
                        per[kind] += secs(j)
            if len(runs) < 100:
                break
            page += 1
        print(f"{day}: " + ", ".join(f"{k} {v / 3600:.1f} h" for k, v in sorted(per.items())), flush=True)
        total.update(per)
        day += dt.timedelta(days=1)
    print("total: " + ", ".join(f"{k} {v / 3600:.1f} h" for k, v in sorted(total.items())))

if __name__ == "__main__":
    main(*sys.argv[1:3])
