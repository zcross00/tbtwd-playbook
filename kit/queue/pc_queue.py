#!/usr/bin/env python3
"""Hold a CI run until it's its turn on the PC's full runner.

GitHub hands queued jobs to a runner in no particular order, so with one
full runner and several ready PRs a run could wait behind ones queued after
it. ci.yml's `queue` job runs this on one of the PC's queue runners
(label `queue`) before `full` is queued. It returns once:

- no run that sorts ahead of this one is still in progress, and
- no run behind it holds the PC (its `full` job queued or running there).

Runs sort by priority, then by when they joined the line: a PR labelled
`main-fix` goes first, then a PR labelled `priority: A`, or one whose body
says "Refs" an issue labelled `priority: A`, then the one waiting longest.

While main is red (#818), the PR that turns it green carries `main-fix`, and
every other run waits at the front of the line while an open, ready PR has
the label: a run merges main as it is when `full` starts, so a run on a red
main would fail and hold the PC while the fix waited behind it (#813 waited
fourth on 2026-10-26). Nothing is cancelled and no run loses its place. A
draft doesn't pause anything, and a label older than MAIN_FIX_SECS is stale
and doesn't either, so a label left on by mistake can't halt the PC. A PR joins the line with its first
CI run since it was last marked ready for review, and a push or a re-run keeps
its place; on 2026-10-24 #555, approved at 00:58, was sent to the back by each
re-merge of a moving main (#653). Marking it draft and ready again joins the
back. A run with no PR (a dispatch) joins when it starts.

A merge train (#880) is an open PR that kit/queue/train.sh built by merging
several approved PRs onto main; its "Train:" line names them. An open PR from
Code review's own branch (TRAIN_BRANCH) with a "Train:" line is a train, and so
is any open PR labelled `train`, so a train doesn't wait for someone who can
set labels (#913). A branch may carry several trains over time. It joins the line when its earliest member did, so
it takes the place of the PR that waited longest. While it's open, each
member's own run stops in its queue job, since the train's run checks it and
merging the train merges it. A train that is closed red lets its members'
next runs queue again, in their old places. A run started before #880 merged
keeps waiting instead of stopping, since its own wait() can't stop it.
A train can also open just after a member's run has left the queue: on
2026-10-30 #1229's run took the PC at 17:33 and train #1234 opened the same
minute, so the train waited an hour (#1235). So `full` asks again (`pc_queue.py
aboard`) before its long steps, and a run whose PR has joined an open train
since cancels itself there and frees the PC.

No run waits for ever (#636). One that has waited AGE_SECS since it joined
counts as priority A, and priority A runs go oldest first, so a fresh A run
only overtakes runs younger than AGE_SECS. Zac, 2026-10-24: runs without A
mustn't starve behind a stream of A runs, and A runs mustn't stall either
(#511, priority A, took 20 hours from ready to merged). Nothing is ever
cancelled.

Only runs holding a queue runner are in progress, so a run still waiting for
one is passed over until it gets one; there are enough queue runners for
that to be rare (PROCESS, The CI runner).

A run missing from the in-progress list is read on its own, since the list can
lag a run that just started: on 2026-10-27 #906 went that way past a train
waiting since 13:45 (#913).

A run goes only once two polls CONFIRM_SECS apart both say so. While a
released run moves from its `queue` job to its `full`, GitHub can list it under
neither status for a moment; on 2026-10-24 a run polled in that gap and went
while another's `full` was starting on the PC (#614).

Every waiting run decides by main's copy of this script, read again every
SYNC_POLLS polls, not by its own checkout's: on 2026-10-24 #659 changed the
order, and its run, sorting by the new order, waited for #576 while every
other run, sorting by main's, waited for #659. Nothing ran for half an hour.

The PR's run with exactly OVERFLOW_AHEAD runs ahead of it goes to one of
GitHub's Windows machines instead (#1124), when no other run is there, main
isn't red, its push is OVERFLOW_SETTLED_SECS old, and the month's hosted spend
leaves room under OVERFLOW_UNDER (Zac,
2026-10-29: "where ever we can farm out builds to github that would ease
bottlenecks, let's start doing it", "46 a month"). A hosted full run takes
110 to 140 minutes against the PC's 40 to 55 (#1103, #1124), so it only beats
a wait of two runs or more. ci.yml marks such a run with a `hosted-full` artifact, which is
how every waiting run, and kit/churn/minutes.py, tell it's not on the PC and
count the month's runs; its `full` is the same job, on `windows-latest`.

Needs GH_TOKEN (actions, issues and pull-requests read), GITHUB_REPOSITORY
and GITHUB_RUN_ID. When the API can't be read for ten polls in a row, it lets
the run go rather than hold it: the order is lost, not the run.
"""
import base64
import datetime
import json
import os
import re
import sys
import time
import types
import urllib.parse
import urllib.request

# The kit's settings. Main's copy, run with exec() (Follow), has no __file__,
# but the copy that loaded it has put kit/lib on the path already.
if "__file__" in globals():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import playbook_config  # noqa: E402

CFG = playbook_config.load()
PRIORITY_LABEL = "priority: A"
MAIN_FIX_LABEL = "main-fix"
TRAIN_LABEL = "train"
# Code review's branch, where it builds every train (PROCESS, Merge order rule 7).
TRAIN_BRANCH = CFG["queue"]["train_branch"]
# The project's CI workflow, whose runs this orders.
CI = CFG["queue"]["ci_workflow"]
# How long a main-fix label pauses other runs; a fix runs in about 30 min.
MAIN_FIX_SECS = 2 * 60 * 60
POLL_SECS = 60
CONFIRM_SECS = 15
# How long a run's priority is trusted before it's read again.
PRIORITY_TTL_SECS = 15 * 60
MAX_ERRORS = 10
# Polls between reads of main's copy of this script.
SYNC_POLLS = 10
# How long a stopped run waits to be cancelled before it fails instead (#1007).
CANCEL_SECS = 120
# The playbook's main (public, so any token reads it).
MAIN_COPY = (os.environ.get("GITHUB_API_URL", "https://api.github.com") + "/repos/"
             + CFG["project"]["playbook_repo"] + "/contents/kit/queue/pc_queue.py?ref=main")
# How long a run waits in line before it counts as priority A.
AGE_SECS = 2 * 60 * 60
# Runs ahead on the PC when a run goes to a hosted machine instead (#1124).
# Exactly this many: every run sorts the same way, so only one run in line
# has it, and the rest wait for that one's mark (Code review on #1144: with
# "or more", every run past the second went at once, before any was marked).
OVERFLOW_AHEAD = 2
# The artifact ci.yml's queue job uploads on a run it sends there.
OVERFLOW_ARTIFACT = "hosted-full"
# Dollars a run, measured and rounded up, for the month's spend. Windows bills
# 2x at $0.008 a minute: the first overflow, run 40998436045, ran 141.5 minutes,
# billed 291 and cost $4.65 (#1124, #1217); hosted.yml is the same job, 107-125
# minutes (#1103), so about $4; a playtest build cost $1.01 (#1123). At $2 an
# overflow the cap let real spend reach about $70 (#1217).
# queue.cost in .playbook.toml: "overflow", and each hosted workflow's file.
COST = CFG["queue"]["cost"]
# No run goes hosted past this much of the month's budget (minutes.py's WARN);
# 0 never sends a run hosted.
OVERFLOW_UNDER = CFG["queue"]["overflow_under"]
# How long after its mark a hosted run can still be going (its timeout is 150).
OVERFLOW_SECS = 4 * 60 * 60
# A run this new waits for the PC rather than go hosted: a branch pushed this
# recently is often pushed again, and a push cancels the run. On 2026-10-30
# run 41072772477 went hosted 3 minutes after its push and was cancelled by
# the next one 97 minutes in, about $3 for nothing.
OVERFLOW_SETTLED_SECS = 30 * 60


def key(run, first, joined, fix=False):
    """Sort key: main-fix first, then priority A (or aged), then the longest
    waiting, then the run id."""
    return (0 if fix else 1 if first else 2, joined, run["id"])


def seconds(at):
    """An API time ("2026-10-24T10:00:00Z") in seconds since the epoch."""
    return datetime.datetime.fromisoformat(at.replace("Z", "+00:00")).timestamp()


def holds_pc(jobs):
    """Whether a run's `full` job is queued or running on the PC's full runner.

    A run with a `queue` job holds the PC only once that job has succeeded;
    one from before the queue existed holds it whenever its `full` job isn't
    done. A `full` on the light runner (a draft, a docs-only PR, a failed
    queue) never does.
    """
    by_name = {j["name"]: j for j in jobs}
    full = by_name.get("full")
    if full is None or full["status"] == "completed":
        return False
    if "light" in full.get("labels", []) or "windows-latest" in full.get("labels", []):
        return False
    queue = by_name.get("queue")
    return queue is None or queue.get("conclusion") == "success"


def waiting(jobs):
    """Whether a run is itself still waiting in this script."""
    queue = next((j for j in jobs if j["name"] == "queue"), None)
    return queue is not None and queue["status"] == "in_progress"


def members(body):
    """PR numbers on a train PR's "Train:" line (#880)."""
    for line in (body or "").splitlines():
        if line.startswith("Train:"):
            return [int(n) for n in re.findall(r"#(\d+)", line)]
    return []


def is_train(pr):
    """Whether an open PR is a train: labelled, or on Code review's branch in
    this repo with a "Train:" line."""
    if any(label["name"] == TRAIN_LABEL for label in pr.get("labels", [])):
        return True
    head = pr.get("head") or {}
    ours = (head.get("repo") or {}).get("full_name") == ((pr.get("base") or {}).get("repo") or {}).get("full_name")
    return ours and head.get("ref") == TRAIN_BRANCH and bool(members(pr.get("body")))


def refs(body):
    """Issue numbers on the body's "Refs" lines."""
    nums = []
    for line in (body or "").splitlines():
        if re.match(r"\s*refs?\b", line, re.I):
            nums += [int(n) for n in re.findall(r"#(\d+)", line)]
    return nums


class Queue:
    """One poll's decision, with caches kept between polls.

    `get(path)` returns the decoded JSON for an API path, or raises.
    """

    def __init__(self, get, me, now=time.time):
        self.get = get
        self.me = me
        self.now = now
        self.polled = now()
        self.priority_cache = {}
        # When each run's PR joined the line, by run and train members (#951).
        self.joined_cache = {}
        # Runs behind this one seen waiting: they can't overtake it, so they
        # needn't be read again.
        self.seen_waiting = set()
        # Open trains, {number: members}, read once a poll.
        self.trains = None
        # Runs sent to a hosted machine this month, {run id: when}, read once a poll.
        self.sent = None

    def labels(self, number):
        issue = self.get(f"issues/{number}")
        return [l["name"] for l in issue.get("labels", [])], issue.get("body")

    def priority_a(self, run):
        return self.priority(run)[0]

    def main_fix(self, run):
        return self.priority(run)[1]

    def priority(self, run):
        """(priority A, main-fix) for a run's PR, cached for PRIORITY_TTL_SECS."""
        cached = self.priority_cache.get(run["id"])
        if cached and self.now() - cached[1] < PRIORITY_TTL_SECS:
            return cached[0]
        a = fix = False
        for pr in run.get("pull_requests", []):
            names, body = self.labels(pr["number"])
            fix = fix or MAIN_FIX_LABEL in names
            if PRIORITY_LABEL in names or any(
                PRIORITY_LABEL in self.labels(n)[0] for n in refs(body)
            ):
                a = True
        self.priority_cache[run["id"]] = ((a, fix), self.now())
        return a, fix

    def main_fixes(self):
        """Open, ready PRs labelled main-fix, as (number, when labelled), oldest
        label first."""
        found = self.get(f"issues?labels={MAIN_FIX_LABEL}&state=open&per_page=100")
        prs = [i["number"] for i in found if "pull_request" in i and not i.get("draft")]
        return sorted(((n, self.labelled_at(n)) for n in prs), key=lambda f: (f[1], f[0]))

    def labelled_at(self, number):
        """When PR `number` was last labelled main-fix ("" if not found)."""
        at, page = "", 1
        while True:
            events = self.get(f"issues/{number}/timeline?per_page=100&page={page}")
            at = max([at] + [
                e["created_at"] for e in events
                if e.get("event") == "labeled" and e.get("label", {}).get("name") == MAIN_FIX_LABEL
            ])
            if len(events) < 100:
                return at
            page += 1

    def ready_at(self, number):
        """When PR `number` was last marked ready for review ("" if never)."""
        ready, page = "", 1
        while True:
            events = self.get(f"issues/{number}/timeline?per_page=100&page={page}")
            ready = max([ready] + [e["created_at"] for e in events if e.get("event") == "ready_for_review"])
            if len(events) < 100:
                return ready
            page += 1

    def joined(self, run):
        """When the run's PR joined the line: the creation of its earliest CI
        run since it was opened or last marked ready, whichever is later. A
        train (#880) joined when its earliest member did, so it keeps the
        place of the PR that waited longest. A run with no PR, or none found,
        joined when it started.

        The cache is keyed on the train's members too, so a run first seen
        before it counted as a train takes its oldest member's place once it
        does: on 10-27 train #938's own run cached its place from before its
        label showed, while every other run put it first, and the line
        deadlocked for an hour and a half (#951)."""
        prs = run.get("pull_requests") or []
        number = prs[0]["number"] if prs else None
        members = tuple(self.open_trains().get(number, [])) if number else ()
        cache_key = (run["id"], members)
        if cache_key in self.joined_cache:
            return self.joined_cache[cache_key]
        at = run["run_started_at"]
        if prs and run.get("head_branch"):
            at = self.pr_joined(number, run["head_branch"], at)
            for n in members:
                if n != number:
                    pr = self.get(f"pulls/{n}")
                    at = self.pr_joined(n, pr["head"]["ref"], at)
        self.joined_cache[cache_key] = at
        return at

    def pr_joined(self, number, head_branch, at):
        """The earlier of `at` and when PR `number` joined the line."""
        # Runs list the branch's open PR even from before it was opened.
        since = max(self.ready_at(number), self.get(f"issues/{number}")["created_at"])
        branch = urllib.parse.quote(head_branch, safe="")
        # Only runs since then, every page: a reused branch has over 100.
        created = f"&created={urllib.parse.quote('>=' + since, safe='')}" if since else ""
        history, page = [], 1
        while True:
            runs = self.get(
                f"actions/workflows/{CI}/runs?branch={branch}&event=pull_request"
                f"{created}&per_page=100&page={page}"
            )["workflow_runs"]
            history += runs
            if len(runs) < 100:
                break
            page += 1
        # The branch may have carried an earlier, merged PR.
        return min(
            [at]
            + [
                r["created_at"]
                for r in history
                if r["created_at"] >= since and any(p["number"] == number for p in r.get("pull_requests", []))
            ]
        )

    def open_trains(self):
        """Open train PRs and their members, {number: [members]}, read once a poll."""
        if self.trains is None:
            found = self.get("pulls?state=open&per_page=100")
            self.trains = {pr["number"]: members(pr.get("body")) for pr in found if is_train(pr)}
        return self.trains

    def train_of(self, run):
        """The open train PR that carries this run's PR, or None."""
        mine = {pr["number"] for pr in run.get("pull_requests", [])}
        for number, carried in self.open_trains().items():
            if number not in mine and mine & set(carried):
                return number
        return None

    def month(self):
        return time.strftime("%Y-%m-01T00:00:00Z", time.gmtime(self.polled))

    def overflowed(self):
        """Runs ci.yml sent to a hosted machine this month, {run id: marked at}.
        Raises while unreadable: the line reads that as none, and no run goes
        hosted on it."""
        if self.sent is None:
            try:
                found = self.get(f"actions/artifacts?name={OVERFLOW_ARTIFACT}&per_page=100")["artifacts"]
                self.sent = {a["workflow_run"]["id"]: a["created_at"] for a in found if a["created_at"] >= self.month()}
            except Exception:  # noqa: BLE001 - asked once a poll
                self.sent = False
        if self.sent is False:
            raise RuntimeError(f"the {OVERFLOW_ARTIFACT} artifacts can't be read")
        return self.sent

    def spent(self):
        """The month's hosted spend, estimated from its runs at COST each.
        One page of each list: at COST, 100 runs is far past OVERFLOW_UNDER,
        so a longer list can't be undercounted below the cap."""
        total = COST["overflow"] * len(self.overflowed())
        since = urllib.parse.quote(">=" + self.month()[:10], safe="")
        for wf in (w for w in COST if w != "overflow"):
            runs = self.get(f"actions/workflows/{wf}/runs?created={since}&per_page=100")["workflow_runs"]
            total += COST[wf] * len(runs)
        return total

    def overflow(self, mine, ahead):
        """Why this run goes to a hosted machine, or None (#1124)."""
        if len(ahead) != OVERFLOW_AHEAD or mine.get("event") != "pull_request":
            return None
        if self.polled - seconds(mine["created_at"]) < OVERFLOW_SETTLED_SECS:
            return None
        try:
            sent = self.overflowed()
            for rid, at in sent.items():
                if rid != self.me and self.polled - seconds(at) < OVERFLOW_SECS:
                    if self.get(f"actions/runs/{rid}").get("status") != "completed":
                        return None
            if any(at and self.polled - seconds(at) < MAIN_FIX_SECS for _, at in self.main_fixes()):
                return None
            spent = self.spent()
        except Exception:  # noqa: BLE001 - unread spend never goes hosted
            return None
        if spent + COST["overflow"] > OVERFLOW_UNDER:
            return None
        return f"{len(ahead)} ahead on the PC; sending full to a hosted machine (about ${spent:.0f} of hosted spend this month)"

    def key(self, run):
        joined = self.joined(run)
        aged = self.polled - seconds(joined) >= AGE_SECS
        a, fix = self.priority(run)
        return key(run, aged or a, joined, fix)

    def poll(self):
        """Returns (go, why); go is None when the run should stop."""
        # One clock for the whole poll, so no run turns aged mid-sort.
        self.polled = self.now()
        self.trains = None
        self.sent = None
        runs = self.get(
            f"actions/workflows/{CI}/runs?status=in_progress&per_page=100"
        )["workflow_runs"]
        mine = next((r for r in runs if r["id"] == self.me), None)
        if mine is None:
            # The list can lag a run that just started for a minute or more:
            # on 10-27 #906 went at 13:57 past a train waiting since 13:45 (#913).
            # So ask about this run itself before going.
            mine = self.get(f"actions/runs/{self.me}")
            if mine.get("status") != "in_progress":
                return True, "this run isn't listed in progress; going"
            runs = runs + [mine]
        train = self.train_of(mine)
        if train:
            return None, f"this PR rides train #{train}, whose run checks it; stopping"
        my_key = self.key(mine)
        try:
            hosted = self.overflowed()
        except Exception:  # noqa: BLE001 - read as none
            hosted = {}
        ahead, behind = [], []
        for r in runs:
            # A run sent to a hosted machine doesn't hold the PC.
            if r["id"] == self.me or r["id"] in hosted:
                continue
            (ahead if self.key(r) < my_key else behind).append(r)
        if ahead:
            ahead.sort(key=self.key)
            why = self.overflow(mine, ahead)
            if why:
                return "hosted", why
            return False, f"{len(ahead)} ahead, first {describe(ahead[0])}"
        # A released run is in progress once its queue job has run, but a run
        # GitHub still lists as queued is read too, in case it holds the PC.
        queued = self.get(
            f"actions/workflows/{CI}/runs?status=queued&per_page=100"
        )["workflow_runs"]
        if not self.main_fix(mine):
            mine_prs = {pr["number"] for pr in mine.get("pull_requests", [])}
            # A fix whose run is queued for a runner can't start while every
            # queue runner holds a run waiting for it (10-27 04:45-05:38,
            # #881): going frees a runner, and once its run is in progress it
            # sorts ahead anyway.
            starved = {pr["number"] for r in queued for pr in r.get("pull_requests", [])}
            fixes = [(n, at) for n, at in self.main_fixes() if n not in mine_prs and n not in starved]
            # A label whose time can't be found counts as stale, so nothing
            # halts the PC without a limit.
            live = [n for n, at in fixes if at and self.polled - seconds(at) < MAIN_FIX_SECS]
            if live:
                return False, f"main is red: waiting for #{live[0]} ({MAIN_FIX_LABEL})"
            if fixes:
                n, at = fixes[0]
                print(time.strftime("%H:%M:%S"), f"#{n}'s {MAIN_FIX_LABEL} label is stale (since {at}); not waiting for it", flush=True)
        behind += queued
        for r in behind:
            if r["id"] in self.seen_waiting:
                continue
            jobs = self.get(f"actions/runs/{r['id']}/jobs?per_page=100")["jobs"]
            if holds_pc(jobs):
                return False, f"the PC is running {describe(r)}"
            if waiting(jobs):
                self.seen_waiting.add(r["id"])
        return True, f"first in line, {len(behind)} behind"


def describe(run):
    prs = run.get("pull_requests", [])
    what = f"PR #{prs[0]['number']}" if prs else run.get("event", "run")
    return f"{what} (run {run['id']}, started {run['run_started_at']})"


def main():
    api = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    repo = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GH_TOKEN"]

    def request(path, method="GET"):
        return urllib.request.Request(
            path if path.startswith("https://") else f"{api}/repos/{repo}/{path}",
            method=method,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )

    def get(path):
        with urllib.request.urlopen(request(path), timeout=30) as resp:
            return json.load(resp)

    me = int(os.environ["GITHUB_RUN_ID"])

    def cancel():
        urllib.request.urlopen(request(f"actions/runs/{me}/cancel", "POST"), timeout=30).close()

    if sys.argv[1:] == ["aboard"]:
        return aboard(get, me, cancel=cancel)
    return wait(Follow(get, me).poll, cancel=cancel)


def aboard(get, me, sleep=None, cancel=None):
    """Asked from `full` once its run has left the queue (#1235): a run whose
    PR an open train has taken on since stops, as it would have in the queue.
    Any other run, or one whose API read fails, goes on."""
    try:
        train = Queue(get, me).train_of(get(f"actions/runs/{me}"))
    except Exception as e:  # noqa: BLE001 - a run that can't tell goes on
        print(time.strftime("%H:%M:%S"), f"couldn't read the trains: {e}; going on", flush=True)
        return 0
    if not train:
        print(time.strftime("%H:%M:%S"), "no open train carries this PR; going on", flush=True)
        return 0
    why = f"this PR joined train #{train} after its run left the queue, and the train's run checks it; stopping"
    print(time.strftime("%H:%M:%S"), why, flush=True)
    return stop(why, sleep or time.sleep, cancel)


class Follow:
    """Polls with main's copy of this script's Queue, read every SYNC_POLLS
    polls, so every waiting run sorts the same way. Until main's copy can be
    read, or if it doesn't load, the copy that's loaded goes on."""

    def __init__(self, get, me, now=time.time):
        self.get, self.me, self.now = get, me, now
        self.sha, self.queue = None, Queue(get, me, now)
        self.polls = 0

    def sync(self):
        try:
            copy = self.get(MAIN_COPY)
            if copy["sha"] == self.sha:
                return
            module = types.ModuleType("pc_queue_main")
            exec(compile(base64.b64decode(copy["content"]), "main:pc_queue.py", "exec"), module.__dict__)
            self.queue = module.Queue(self.get, self.me, self.now)
            self.sha = copy["sha"]
            print(time.strftime("%H:%M:%S"), f"sorting by main's copy ({self.sha[:7]})", flush=True)
        except Exception as e:  # noqa: BLE001 - keep the loaded copy
            print(time.strftime("%H:%M:%S"), f"main's copy not loaded: {e}", flush=True)

    def poll(self):
        if self.polls % SYNC_POLLS == 0:
            self.sync()
        self.polls += 1
        return self.queue.poll()


def summary(why):
    """Puts why the run stopped on its job summary (GITHUB_STEP_SUMMARY), so a
    member's stopped run, which shows red, names the train that checks it."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"Queue: {why}. Not a failure: the train's run checks this PR (PROCESS, Merge order rule 7).\n")


def output(name, value):
    """Sets a step output (GITHUB_OUTPUT), which ci.yml's full job reads."""
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")


def wait(poll, sleep=None, cancel=None):
    """Polls until the run may go. A "go" from a poll is checked by a second
    poll CONFIRM_SECS later, and so is "hosted", which sets the step output
    where=hosted (#1124); ten API errors in a row let the run go at once, to the PC.
    A run told to stop cancels itself, so it shows grey rather than a red X
    that reads as broken CI (#1007; Zac saw #990's and asked to fix CI). If
    the cancel fails or hasn't landed after CANCEL_SECS, the run fails."""
    sleep = sleep or time.sleep
    errors, last, confirming = 0, None, False
    while True:
        try:
            go, why = poll()
            errors = 0
        except Exception as e:  # noqa: BLE001 - any API failure counts
            errors += 1
            if errors >= MAX_ERRORS:
                print(time.strftime("%H:%M:%S"), f"API error {errors} in a row: {e}; letting the run go", flush=True)
                return 0
            go, why = False, f"API error {errors} in a row: {e}"
        if why != last:
            print(time.strftime("%H:%M:%S"), why, flush=True)
            last = why
        if go is None:
            return stop(why, sleep, cancel)
        if go and confirming == go:
            if go == "hosted":
                output("where", "hosted")
            return 0
        confirming = go
        sleep(CONFIRM_SECS if go else POLL_SECS)


def stop(why, sleep, cancel):
    """Ends a run told to stop: cancels it, or fails it if that can't land."""
    summary(why)
    if cancel:
        try:
            cancel()
            print(time.strftime("%H:%M:%S"), "cancelling this run", flush=True)
            sleep(CANCEL_SECS)
        except Exception as e:  # noqa: BLE001 - fail instead
            print(time.strftime("%H:%M:%S"), f"couldn't cancel this run: {e}", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
