"""Tests for pc_queue.py: python3 -m unittest discover -s kit/queue (kit/test.sh)"""
import base64
import unittest

import pc_queue as q


def t(hhmm):
    """10-24 at hh:mm, as the API writes it."""
    return f"2026-10-24T{hhmm}:00Z"


def run(rid, started, pr=None, created=None, branch=None):
    return {
        "id": rid,
        "run_started_at": t(started),
        "created_at": t(created or started),
        "head_branch": branch or (f"b{pr}" if pr else "main"),
        "event": "pull_request" if pr else "workflow_dispatch",
        "pull_requests": [{"number": pr}] if pr else [],
    }


def job(name, status, conclusion=None, labels=()):
    return {"name": name, "status": status, "conclusion": conclusion, "labels": list(labels)}


PC = ("self-hosted", "windows", "rust")
LIGHT = ("self-hosted", "light")
WAITING = [job("queue", "in_progress"), job("full", "queued")]
ON_PC = [job("queue", "completed", "success"), job("full", "in_progress", labels=PC)]


class Fake:
    """The API: runs in progress, each run's jobs (waiting unless given),
    issues (with when each opened), each PR's ready-for-review times and each
    branch's CI runs."""

    def __init__(self, runs, jobs=None, issues=None, queued=(), ready=None, history=None, opened=None):
        self.runs, self.jobs, self.issues = runs, jobs or {}, issues or {}
        self.queued = list(queued)
        self.ready, self.history, self.opened = ready or {}, history or {}, opened or {}
        self.closed, self.drafts, self.labelled = set(), set(), {}
        self.heads, self.forks, self.lagging = {}, set(), {}
        # The hosted-full artifacts (None: unreadable) and each paid workflow's runs.
        self.artifacts, self.paid = None, {}
        self.calls = []

    def get(self, path):
        self.calls.append(path)
        if "branch=" in path:
            runs = self.history.get(path.split("branch=")[1].split("&")[0], [])
            page = int(path.split("&page=")[1].split("&")[0])
            return {"workflow_runs": runs[(page - 1) * 100:page * 100]}
        if path.startswith("actions/artifacts?"):
            if self.artifacts is None:
                raise KeyError("artifacts")
            return {"artifacts": [{"workflow_run": {"id": rid}, "created_at": t(h)} for rid, h in self.artifacts]}
        if path.startswith(("actions/workflows/hosted.yml/", "actions/workflows/playtest.yml/")):
            return {"workflow_runs": [{}] * self.paid.get(path.split("/")[2], 0)}
        if "/timeline" in path:
            n = int(path.split("/")[1])
            return [{"event": "ready_for_review", "created_at": t(h)} for h in self.ready.get(n, [])] + [
                {"event": "labeled", "label": {"name": "main-fix"}, "created_at": t(h)} for h in self.labelled.get(n, [])]
        if path.startswith("actions/workflows/"):
            return {"workflow_runs": self.queued if "status=queued" in path else self.runs}
        if path.startswith("actions/runs/") and path.count("/") == 2:
            # A run the in-progress list hasn't caught up with yet.
            return self.lagging.get(int(path.split("/")[2]), {"status": "completed"})
        if path.startswith("actions/runs/"):
            return {"jobs": self.jobs.get(int(path.split("/")[2]), WAITING)}
        if path.startswith("issues?labels="):
            # Every numbered issue here is a PR, open, unless listed as closed.
            label = path.split("labels=")[1].split("&")[0]
            return [{"number": n, "pull_request": {}, "draft": n in self.drafts, "body": body}
                    for n, (labels, body) in sorted(self.issues.items()) if label in labels and n not in self.closed]
        if path.startswith("pulls?state=open"):
            # Open PRs from this repo, on b<n> unless heads names a branch.
            here = {"full_name": "o/r"}
            return [{"number": n, "labels": [{"name": l} for l in labels], "body": body, "base": {"repo": here},
                     "head": {"ref": self.heads.get(n, f"b{n}"), "repo": None if n in self.forks else here}}
                    for n, (labels, body) in sorted(self.issues.items()) if n not in self.closed]
        if path.startswith("pulls/"):
            return {"head": {"ref": f"b{int(path.split('/')[1])}"}}
        number = int(path.split("/")[1])
        labels, body = self.issues.get(number, ([], ""))
        return {"labels": [{"name": n} for n in labels], "body": body, "created_at": t(self.opened[number]) if number in self.opened else ""}


def poll(fake, me, now="10:30"):
    return q.Queue(fake.get, me, now=lambda: q.seconds(t(now))).poll()


class HoldsPc(unittest.TestCase):
    def test_released_run_on_the_pc(self):
        self.assertTrue(q.holds_pc(ON_PC))

    def test_released_run_queued_for_the_pc_before_labels_show(self):
        self.assertTrue(q.holds_pc([job("queue", "completed", "success"), job("full", "queued")]))

    def test_waiting_run(self):
        self.assertFalse(q.holds_pc(WAITING))

    def test_full_on_the_light_runner(self):
        self.assertFalse(q.holds_pc([job("queue", "completed", "success"), job("full", "in_progress", labels=LIGHT)]))
        self.assertFalse(q.holds_pc([job("queue", "completed", "skipped"), job("full", "in_progress", labels=LIGHT)]))

    def test_failed_queue(self):
        self.assertFalse(q.holds_pc([job("queue", "completed", "failure"), job("full", "queued")]))

    def test_run_from_before_the_queue(self):
        self.assertTrue(q.holds_pc([job("full", "queued", labels=PC)]))
        self.assertFalse(q.holds_pc([job("full", "completed", "success", labels=PC)]))

    def test_no_full_job(self):
        self.assertFalse(q.holds_pc([job("queue", "in_progress")]))


    def test_full_on_a_hosted_machine(self):
        self.assertFalse(q.holds_pc([job("queue", "completed", "success"), job("full", "queued", labels=("windows-latest",))]))


class Refs(unittest.TestCase):
    def test_refs_lines_only(self):
        self.assertEqual(q.refs("Refs #470, #12\nFixes nothing #9\nref #3"), [470, 12, 3])

    def test_empty_body(self):
        self.assertEqual(q.refs(None), [])


class MainFix(unittest.TestCase):
    """#818: while main is red, its fix goes first and other runs wait."""

    def test_a_main_fix_goes_ahead_of_an_older_priority_a_run(self):
        fake = Fake([run(1, "10:00", 5), run(2, "10:05", 6)], jobs={1: WAITING},
                    issues={5: (["priority: A"], ""), 6: (["main-fix"], "")})
        self.assertTrue(poll(fake, 2)[0])
        go, why = poll(fake, 1)
        self.assertFalse(go)
        self.assertIn("1 ahead, first PR #6", why)

    def test_a_plain_run_at_the_front_waits_while_a_fix_is_open(self):
        # The fix's own run hasn't started (still in its container CI).
        fake = Fake([run(1, "10:00", 5)], issues={9: (["main-fix"], "")})
        fake.labelled[9] = ["10:25"]
        go, why = poll(fake, 1)
        self.assertFalse(go)
        self.assertIn("main is red: waiting for #9", why)
        fake.closed.add(9)
        self.assertTrue(poll(fake, 1)[0])

    def test_a_fix_still_waiting_for_a_runner_doesnt_pause_anything(self):
        # 10-27 04:45-05:38: all 8 queue runners held runs waiting for #881,
        # whose own run sat queued for a runner. The front run goes instead.
        fake = Fake([run(1, "10:00", 5)], issues={9: (["main-fix"], "")},
                    jobs={3: [job("queue", "queued")]}, queued=[run(3, "10:26", 9)])
        fake.labelled[9] = ["10:25"]
        go, why = poll(fake, 1)
        self.assertTrue(go)
        self.assertIn("first in line", why)

    def test_a_draft_fix_doesnt_pause_anything(self):
        fake = Fake([run(1, "10:00", 5)], issues={9: (["main-fix"], "")})
        fake.labelled[9] = ["10:25"]
        fake.drafts.add(9)
        self.assertTrue(poll(fake, 1)[0])

    def test_a_stale_label_doesnt_pause_anything(self):
        # Labelled at 08:00; at 09:59 it still pauses, from 10:00 it's stale.
        fake = Fake([run(1, "08:30", 5)], issues={9: (["main-fix"], "")})
        fake.labelled[9] = ["08:00"]
        self.assertFalse(poll(fake, 1, now="09:59")[0])
        self.assertTrue(poll(fake, 1, now="10:00")[0])

    def test_a_label_with_no_time_found_doesnt_pause_anything(self):
        fake = Fake([run(1, "10:00", 5)], issues={9: (["main-fix"], "")})
        self.assertTrue(poll(fake, 1)[0])

    def test_main_fix_runs_go_oldest_first(self):
        fake = Fake([run(1, "10:00", 5), run(2, "10:05", 6)], jobs={1: WAITING},
                    issues={5: (["main-fix"], ""), 6: (["main-fix", "priority: A"], "")})
        self.assertTrue(poll(fake, 1)[0])
        self.assertFalse(poll(fake, 2)[0])

    def test_a_fix_doesnt_wait_for_itself(self):
        fake = Fake([run(1, "10:00", 5)], issues={5: (["main-fix"], "")})
        self.assertTrue(poll(fake, 1)[0])

    def test_key_keeps_its_three_argument_form(self):
        # Older runs call main's module through key(run, first, joined).
        r = {"id": 1}
        self.assertLess(q.key(r, True, "a"), q.key(r, False, "a"))
        self.assertLess(q.key(r, False, "b", True), q.key(r, True, "a"))


class Train(unittest.TestCase):
    """#880: one PC run checks a train of approved PRs merged together."""

    def test_members_from_the_train_line(self):
        self.assertEqual(q.members("Refs #1\nTrain: #839, #838 and #828\n#5"), [839, 838, 828])
        self.assertEqual(q.members(None), [])

    def test_a_train_keeps_its_oldest_members_place(self):
        # Train PR 20 opened at 10:20; member 6 joined at 09:00, before run 1.
        # It's built on Code review's own branch, which carried train 15 before.
        train = run(3, "10:20", 20, branch="cr")
        fake = Fake([run(1, "09:30", 5), train], jobs={1: WAITING},
                    issues={20: (["train"], "Train: #6 #7"), 6: ([], ""), 7: ([], "")},
                    history={"cr": [train, run(4, "08:00", 15, branch="cr")],
                             "b6": [run(9, "09:00", 6)], "b7": [run(8, "09:40", 7)]})
        self.assertTrue(poll(fake, 3)[0])
        go, why = poll(fake, 1)
        self.assertFalse(go)
        self.assertIn("PR #20", why)

    def test_a_train_seen_late_takes_its_oldest_members_place(self):
        # #951: on 10-27 the label listing lagged a fresh train, and its own
        # run kept the place it cached on that first poll.
        train = run(3, "10:20", 20, branch="cr")
        fake = Fake([run(1, "09:30", 5), train], jobs={1: WAITING},
                    issues={20: ([], "Train: #6"), 6: ([], "")},
                    history={"cr": [train], "b6": [run(9, "09:00", 6)]})
        queue = q.Queue(fake.get, 3, now=lambda: q.seconds(t("10:30")))
        self.assertFalse(queue.poll()[0])
        fake.issues[20] = (["train"], "Train: #6")
        self.assertTrue(queue.poll()[0])

    def test_a_pr_without_the_label_isnt_a_train(self):
        # A "Train:" line on another branch doesn't make a train: PR 20 waits its own turn.
        fake = Fake([run(1, "09:30", 5), run(3, "10:20", 20)], jobs={1: WAITING},
                    issues={20: ([], "Train: #6"), 6: ([], "")}, history={"b6": [run(9, "09:00", 6)]})
        self.assertFalse(poll(fake, 3)[0])
        self.assertTrue(poll(Fake([run(1, "09:00", 6)], issues={20: ([], "Train: #6")}), 1)[0])

    def test_a_run_the_list_hasnt_caught_up_with_still_waits(self):
        # #913: on 10-27 the list missed #906's run for 15 s, and it went past a train.
        fake = Fake([run(3, "10:20", 20)], jobs={3: WAITING},
                    issues={20: (["train"], "Train: #6"), 6: ([], "")}, history={"b6": [run(9, "09:00", 6)]})
        fake.lagging[1] = dict(run(1, "10:25", 5), status="in_progress")
        go, why = poll(fake, 1)
        self.assertFalse(go)
        self.assertIn("PR #20", why)

    def test_a_run_thats_really_not_in_progress_goes(self):
        self.assertEqual(poll(Fake([]), 1), (True, "this run isn't listed in progress; going"))

    def test_a_train_on_code_reviews_branch_needs_no_label(self):
        # #913: Code review can't set labels; its branch and a "Train:" line are enough.
        fake = Fake([run(1, "09:00", 6), run(3, "10:20", 20, branch=q.TRAIN_BRANCH)], jobs={3: WAITING},
                    issues={20: ([], "Train: #6 #7"), 6: ([], "")})
        fake.heads[20] = q.TRAIN_BRANCH
        go, why = poll(fake, 1)
        self.assertIsNone(go)
        self.assertIn("rides train #20", why)

    def test_code_reviews_branch_without_a_train_line_isnt_a_train(self):
        fake = Fake([run(1, "09:00", 6)], issues={20: ([], "Refs #6"), 6: ([], "")})
        fake.heads[20] = q.TRAIN_BRANCH
        self.assertTrue(poll(fake, 1)[0])

    def test_a_fork_with_code_reviews_branch_name_isnt_a_train(self):
        fake = Fake([run(1, "09:00", 6)], issues={20: ([], "Train: #6"), 6: ([], "")})
        fake.heads[20] = q.TRAIN_BRANCH
        fake.forks.add(20)
        self.assertTrue(poll(fake, 1)[0])

    def test_trains_are_read_once_a_poll(self):
        fake = Fake([run(1, "09:00", 5), run(2, "09:10", 6), run(3, "09:20", 7)], jobs={1: WAITING, 2: WAITING})
        poll(fake, 3)
        self.assertEqual(sum(c.startswith("pulls?state=open") for c in fake.calls), 1)

    def test_a_member_stops_and_leaves_the_line(self):
        fake = Fake([run(1, "09:00", 6), run(3, "10:20", 20)], jobs={3: WAITING},
                    issues={20: (["train"], "Train: #6 #7"), 6: ([], "")})
        go, why = poll(fake, 1)
        self.assertIsNone(go)
        self.assertIn("rides train #20", why)

    def test_a_closed_train_lets_its_members_queue_again(self):
        # A red train is closed; its members go back in line in their places.
        fake = Fake([run(1, "09:00", 6)], issues={20: (["train"], "Train: #6"), 6: ([], "")})
        fake.closed.add(20)
        self.assertTrue(poll(fake, 1)[0])

    def test_the_train_itself_doesnt_stop(self):
        fake = Fake([run(3, "10:20", 20)], issues={20: (["train"], "Train: #20 #6")})
        self.assertTrue(poll(fake, 3)[0])

    def test_a_run_already_on_the_pc_stops_once_a_train_takes_its_pr(self):
        # #1235: on 10-30 #1229's run took the PC at 17:33 and train #1234
        # opened the same minute; full asks again before its long steps.
        from unittest import mock
        fake = Fake([], issues={20: (["train"], "Train: #6"), 6: ([], "")})
        fake.lagging[1] = dict(run(1, "10:20", 6), status="in_progress")
        cancelled, slept = [], []
        with mock.patch("builtins.print") as said:
            self.assertEqual(q.aboard(fake.get, 1, slept.append, cancel=lambda: cancelled.append(1)), 1)
        self.assertEqual((cancelled, slept), ([1], [q.CANCEL_SECS]))
        self.assertTrue(any("train #20" in str(c) for c in said.call_args_list))

    def test_a_run_on_the_pc_with_no_train_goes_on(self):
        from unittest import mock
        cancelled = []
        for trains in ({}, {20: (["train"], "Train: #7")}):
            fake = Fake([], issues={**trains, 6: ([], "")})
            fake.lagging[1] = dict(run(1, "10:20", 6), status="in_progress")
            with mock.patch("builtins.print"):
                self.assertEqual(q.aboard(fake.get, 1, self.fail, cancel=lambda: cancelled.append(1)), 0)
        # The train's own run doesn't stop either.
        fake = Fake([], issues={20: (["train"], "Train: #20 #6")})
        fake.lagging[3] = dict(run(3, "10:20", 20), status="in_progress")
        with mock.patch("builtins.print"):
            self.assertEqual(q.aboard(fake.get, 3, self.fail, cancel=lambda: cancelled.append(1)), 0)
        self.assertEqual(cancelled, [])

    def test_a_run_that_cant_read_the_trains_goes_on(self):
        from unittest import mock

        def broken(path):
            raise OSError("down")
        with mock.patch("builtins.print"):
            self.assertEqual(q.aboard(broken, 1, cancel=lambda: self.fail("cancelled")), 0)

    def test_wait_ends_the_run_when_told_to_stop(self):
        from unittest import mock
        with mock.patch("builtins.print"):
            # One poll says stop; any further poll errors, and ten errors let the run go.
            it = iter([(None, "stop")])
            self.assertEqual(q.wait(lambda: next(it), lambda s: None), 1)

    def test_a_stop_cancels_the_run_and_fails_only_if_that_doesnt_land(self):
        from unittest import mock
        cancelled, slept = [], []
        with mock.patch("builtins.print"):
            it = iter([(None, "this PR rides train #20, whose run checks it; stopping")])
            self.assertEqual(q.wait(lambda: next(it), slept.append, cancel=lambda: cancelled.append(1)), 1)
        self.assertEqual(cancelled, [1])
        self.assertEqual(slept, [q.CANCEL_SECS])

    def test_a_stop_whose_cancel_fails_fails_at_once(self):
        from unittest import mock
        slept = []

        def refuse():
            raise OSError("403")

        with mock.patch("builtins.print"):
            it = iter([(None, "stop")])
            self.assertEqual(q.wait(lambda: next(it), slept.append, cancel=refuse), 1)
        self.assertEqual(slept, [])

    def test_a_stop_names_the_train_on_the_job_summary(self):
        import os, tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "summary.md")
            with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": path}), mock.patch("builtins.print"):
                it = iter([(None, "this PR rides train #20, whose run checks it; stopping")])
                q.wait(lambda: next(it), lambda s: None)
            with open(path) as f:
                self.assertIn("rides train #20", f.read())


class Poll(unittest.TestCase):
    def test_alone(self):
        go, why = poll(Fake([run(1, "10:00", 5)], issues={5: ([], "")}), 1)
        self.assertTrue(go)
        self.assertIn("first in line, 0 behind", why)

    def test_older_run_goes_first(self):
        fake = Fake([run(1, "10:00", 5), run(2, "10:05", 6)])
        self.assertTrue(poll(fake, 1)[0])
        go, why = poll(fake, 2)
        self.assertFalse(go)
        self.assertIn("1 ahead, first PR #5", why)

    def test_priority_a_label_on_the_pr_goes_first(self):
        fake = Fake([run(1, "10:00", 5), run(2, "10:05", 6)], jobs={1: WAITING},
                    issues={6: (["priority: A"], "")})
        self.assertTrue(poll(fake, 2)[0])
        self.assertFalse(poll(fake, 1)[0])

    def test_priority_a_from_a_referenced_issue(self):
        fake = Fake([run(1, "10:00", 5), run(2, "10:05", 6)], jobs={1: WAITING},
                    issues={6: ([], "Refs #40"), 40: (["priority: A", "area: x"], "")})
        self.assertTrue(poll(fake, 2)[0])

    def test_waits_while_a_run_behind_holds_the_pc(self):
        # Run 2 is priority A and arrived after run 1 was already on the PC.
        fake = Fake([run(1, "10:00", 5), run(2, "10:05", 6)], jobs={1: ON_PC},
                    issues={6: (["priority: A"], "")})
        go, why = poll(fake, 2)
        self.assertFalse(go)
        self.assertIn("the PC is running PR #5", why)

    def test_waits_while_a_run_listed_as_queued_holds_the_pc(self):
        fake = Fake([run(2, "10:05", 6)], jobs={1: ON_PC}, queued=[run(1, "10:00", 5)])
        go, why = poll(fake, 2)
        self.assertFalse(go)
        self.assertIn("PR #5", why)

    def test_runs_queued_for_a_queue_runner_dont_hold_it_up(self):
        fake = Fake([run(2, "10:05", 6)], jobs={1: [job("queue", "queued"), job("full", "queued")]},
                    queued=[run(1, "10:00", 5)])
        self.assertTrue(poll(fake, 2)[0])

    def test_dispatch_runs_queue_too(self):
        fake = Fake([run(1, "09:00"), run(2, "10:00", 6)])
        self.assertFalse(poll(fake, 2)[0])
        self.assertTrue(poll(fake, 1)[0])

    def test_a_push_keeps_the_prs_place(self):
        # #555 (#653): PR 6 joined at 09:00; a push since started run 2 at 10:05.
        joined = run(9, "09:00", 6)
        fake = Fake([run(1, "10:00", 5), run(2, "10:05", 6)], jobs={1: WAITING},
                    ready={6: ["08:00"]}, history={"b6": [run(2, "10:05", 6), joined]})
        self.assertTrue(poll(fake, 2)[0])
        go, why = poll(fake, 1)
        self.assertFalse(go)
        self.assertIn("PR #6", why)

    def test_a_rerun_keeps_its_place(self):
        fake = Fake([run(1, "10:30", 5, created="10:00"), run(2, "10:05", 6)], jobs={2: WAITING},
                    history={"b5": [run(1, "10:30", 5, created="10:00")]})
        self.assertTrue(poll(fake, 1)[0])
        self.assertFalse(poll(fake, 2)[0])

    def test_draft_and_ready_again_joins_the_back(self):
        fake = Fake([run(1, "10:00", 5), run(2, "10:05", 6)], jobs={2: WAITING},
                    ready={6: ["08:00", "10:04"]}, history={"b6": [run(2, "10:05", 6), run(9, "09:00", 6)]})
        self.assertTrue(poll(fake, 1)[0])
        self.assertFalse(poll(fake, 2)[0])

    def test_an_earlier_pr_on_the_same_branch_doesnt_count(self):
        fake = Fake([run(1, "10:00", 5), run(2, "10:05", 6)], jobs={2: WAITING},
                    history={"b6": [run(2, "10:05", 6), run(9, "07:00", 4, branch="b6")]})
        self.assertTrue(poll(fake, 1)[0])

    def test_runs_from_before_the_pr_opened_dont_count(self):
        # GitHub lists a branch's open PR on its older runs too (#635 showed 10-21).
        fake = Fake([run(1, "10:00", 5), run(2, "10:05", 6)], jobs={2: WAITING}, opened={6: "10:04"},
                    history={"b6": [run(2, "10:05", 6), run(9, "07:00", 6)]})
        self.assertTrue(poll(fake, 1)[0])
        self.assertFalse(poll(fake, 2)[0])

    def test_a_run_waiting_two_hours_lines_up_with_priority_a(self):
        # Run 1 (no A) joined at 08:00; run 2 is A but joined at 10:05.
        fake = Fake([run(1, "08:00", 5), run(2, "10:05", 6)], jobs={1: WAITING, 2: WAITING},
                    issues={6: (["priority: A"], "")})
        self.assertTrue(poll(fake, 2, now="09:59")[0])
        self.assertFalse(poll(fake, 1, now="09:59")[0])
        self.assertTrue(poll(fake, 1, now="10:00")[0])
        go, why = poll(fake, 2, now="10:00")
        self.assertFalse(go)
        self.assertIn("PR #5", why)

    def test_priority_a_runs_go_oldest_first(self):
        fake = Fake([run(1, "10:00", 5), run(2, "09:00", 6)], jobs={1: WAITING, 2: WAITING},
                    issues={5: (["priority: A"], ""), 6: (["priority: A"], "")})
        self.assertTrue(poll(fake, 2)[0])
        self.assertFalse(poll(fake, 1)[0])

    def test_the_first_run_on_a_later_page_counts(self):
        # A reused branch lists over 100 runs, newest first (Code review, #659).
        newer = [run(100 + i, "10:05", 6) for i in range(120)]
        fake = Fake([run(1, "10:00", 5), run(2, "10:05", 6)], jobs={1: WAITING},
                    history={"b6": newer + [run(9, "09:00", 6)]})
        self.assertTrue(poll(fake, 2)[0])
        self.assertEqual(sum("branch=b6&" in c for c in fake.calls), 2)

    def test_when_a_run_joined_is_read_once(self):
        fake = Fake([run(1, "10:00", 5)])
        queue = q.Queue(fake.get, 1, now=lambda: q.seconds(t("10:30")))
        queue.poll()
        queue.poll()
        self.assertEqual(sum("branch=" in c for c in fake.calls), 1)
        self.assertEqual(sum("/timeline" in c for c in fake.calls), 1)

    def test_tie_on_time_breaks_by_id(self):
        fake = Fake([run(1, "10:00", 5), run(2, "10:00", 6)], jobs={2: WAITING})
        self.assertTrue(poll(fake, 1)[0])
        self.assertFalse(poll(fake, 2)[0])

    def test_not_listed(self):
        self.assertTrue(poll(Fake([]), 1)[0])

    def test_waiting_runs_behind_are_read_once(self):
        fake = Fake([run(1, "10:00", 5), run(2, "10:05", 6)], jobs={2: WAITING})
        queue = q.Queue(fake.get, 1, now=lambda: q.seconds(t("10:30")))
        queue.poll()
        queue.poll()
        self.assertEqual(sum(c.startswith("actions/runs/2/") for c in fake.calls), 1)

    def test_priority_is_read_again_after_its_ttl(self):
        clock = [0]
        fake = Fake([run(1, "10:00", 5)])
        queue = q.Queue(fake.get, 1, now=lambda: clock[0])
        queue.poll()
        queue.poll()
        # Once for the priority, once for when the PR opened (read once a run).
        self.assertEqual(fake.calls.count("issues/5"), 2)
        clock[0] = q.PRIORITY_TTL_SECS
        queue.poll()
        self.assertEqual(fake.calls.count("issues/5"), 3)


class Overflow(unittest.TestCase):
    """#1124: two or more runs ahead sends a PR's run to a hosted machine."""

    def fake(self, ahead=2):
        runs = [run(i, f"09:0{i}", 10 + i) for i in range(1, ahead + 1)] + [run(9, "10:00", 5)]
        fake = Fake(runs)
        fake.artifacts = []
        return fake

    def test_two_ahead_goes_hosted(self):
        go, why = poll(self.fake(), 9)
        self.assertEqual(go, "hosted")
        self.assertIn("2 ahead on the PC", why)

    def test_one_ahead_waits_for_the_pc(self):
        self.assertFalse(poll(self.fake(ahead=1), 9)[0])

    def test_a_run_pushed_under_30_minutes_ago_waits_for_the_pc(self):
        # Run 41072772477 went hosted 3 minutes after its push, and the next
        # push cancelled it 97 minutes in.
        fake = self.fake()
        fake.runs[-1] = run(9, "10:10", 5)
        go, why = poll(fake, 9, now="10:39")
        self.assertFalse(go)
        self.assertIn("2 ahead, first", why)
        self.assertEqual(poll(fake, 9, now="10:40")[0], "hosted")

    def test_a_dispatch_never_goes_hosted(self):
        fake = self.fake()
        fake.runs[-1] = run(9, "10:00")
        self.assertFalse(poll(fake, 9)[0])

    def test_only_the_third_in_line_goes_hosted(self):
        # Code review on #1144: five waiting, polling the same snapshot.
        fake = Fake([run(i, f"09:0{i}", 10 + i) for i in range(1, 6)])
        fake.artifacts = []
        self.assertEqual([poll(fake, i)[0] for i in range(1, 6)], [True, False, "hosted", False, False])

    def test_once_marked_the_next_waits_for_it(self):
        fake = Fake([run(i, f"09:0{i}", 10 + i) for i in range(1, 6)])
        fake.artifacts = [(3, "10:10")]
        fake.lagging[3] = {"status": "in_progress"}
        go, why = poll(fake, 4)
        self.assertFalse(go)
        self.assertIn("2 ahead, first", why)

    def test_one_hosted_run_at_a_time(self):
        fake = self.fake(ahead=3)
        fake.artifacts = [(3, "10:10")]
        fake.lagging[3] = {"status": "in_progress"}
        go, why = poll(fake, 9)
        self.assertFalse(go)
        self.assertIn("2 ahead, first", why)

    def test_a_finished_hosted_run_doesnt_hold_the_next(self):
        fake = self.fake(ahead=3)
        fake.artifacts = [(3, "10:10")]
        self.assertEqual(poll(fake, 9)[0], "hosted")

    def test_three_ahead_waits(self):
        self.assertFalse(poll(self.fake(ahead=3), 9)[0])

    def test_a_run_sent_hosted_isnt_ahead_on_the_pc(self):
        fake = self.fake(ahead=1)
        fake.artifacts = [(1, "09:30")]
        fake.lagging[1] = {"status": "in_progress"}
        go, why = poll(fake, 9)
        self.assertTrue(go)
        self.assertIn("first in line", why)

    def test_a_run_sent_hosted_doesnt_hold_the_pc_from_behind(self):
        fake = Fake([run(1, "10:00", 5), run(2, "10:05", 6)], jobs={2: ON_PC})
        fake.artifacts = [(2, "10:20")]
        self.assertTrue(poll(fake, 1)[0])

    def test_no_room_in_the_months_spend_waits(self):
        fake = self.fake()
        fake.paid = {"hosted.yml": 5, "playtest.yml": 10}
        self.assertEqual(q.COST["hosted.yml"] * 5 + q.COST["playtest.yml"] * 10 + q.COST["overflow"], 37.0)
        self.assertFalse(poll(fake, 9)[0])
        fake.paid = {"hosted.yml": 4, "playtest.yml": 10}
        self.assertEqual(poll(fake, 9)[0], "hosted")

    def test_the_measured_overflow_cost_holds_the_cap(self):
        # #1217: run 40998436045 cost $4.65. With five such runs this month a
        # sixth still fits, and real spend after it ($27.90) is under the $34
        # cap; with six, a seventh is refused.
        measured = 4.65
        self.assertGreaterEqual(q.COST["overflow"], measured)
        fake = self.fake()
        fake.artifacts = [(70 + i, "09:00") for i in range(5)]
        self.assertEqual(poll(fake, 9)[0], "hosted")
        self.assertLess(measured * 6, q.OVERFLOW_UNDER)
        fake = self.fake()
        fake.artifacts = [(70 + i, "09:00") for i in range(6)]
        self.assertFalse(poll(fake, 9)[0])

    def test_last_months_runs_dont_count(self):
        fake = self.fake()
        fake.artifacts = [(70 + i, "09:00") for i in range(20)]
        self.assertFalse(poll(fake, 9)[0])
        queue = q.Queue(fake.get, 9, now=lambda: q.seconds("2026-11-02T10:30:00Z"))
        self.assertEqual(queue.poll()[0], "hosted")

    def test_main_red_waits_for_the_pc(self):
        fake = self.fake()
        fake.issues = {7: (["main-fix"], "")}
        fake.labelled = {7: ["10:00"]}
        self.assertFalse(poll(fake, 9)[0])

    def test_unreadable_marks_never_go_hosted(self):
        fake = self.fake()
        fake.artifacts = None
        go, why = poll(fake, 9)
        self.assertFalse(go)
        self.assertIn("2 ahead, first", why)

    def test_wait_sets_the_output_once_confirmed(self):
        import os
        import tempfile
        from unittest import mock
        with tempfile.NamedTemporaryFile("r", delete=False) as f, \
                mock.patch.dict(os.environ, {"GITHUB_OUTPUT": f.name}), mock.patch("builtins.print"):
            answers = iter([("hosted", "h"), (True, "go"), ("hosted", "h"), ("hosted", "h")])
            self.assertEqual(q.wait(lambda: next(answers), lambda s: None), 0)
            self.assertEqual(f.read(), "where=hosted\n")
        os.unlink(f.name)


class Main(unittest.TestCase):
    def test_api_errors_let_the_run_go_after_max_errors(self):
        import os
        from unittest import mock

        env = {"GITHUB_REPOSITORY": "o/r", "GH_TOKEN": "t", "GITHUB_RUN_ID": "1"}
        with mock.patch.dict(os.environ, env), \
                mock.patch.object(q.urllib.request, "urlopen", side_effect=OSError("down")), \
                mock.patch.object(q.time, "sleep") as sleep, \
                mock.patch("builtins.print"):
            self.assertEqual(q.main(), 0)
        self.assertEqual(sleep.call_count, q.MAX_ERRORS - 1)


def polls(*answers):
    """A poll that gives these answers in turn (True goes) and counts its calls."""
    it = iter(answers)
    calls = []

    def poll():
        calls.append(1)
        go = next(it)
        return go, "go" if go else "wait"
    return poll, calls


class Wait(unittest.TestCase):
    def setUp(self):
        from unittest import mock
        patch = mock.patch("builtins.print")
        patch.start()
        self.addCleanup(patch.stop)

    def test_a_go_is_confirmed_by_a_second_poll(self):
        poll, calls = polls(True, True)
        slept = []
        self.assertEqual(q.wait(poll, slept.append), 0)
        self.assertEqual((len(calls), slept), (2, [q.CONFIRM_SECS]))

    def test_a_run_that_starts_on_the_pc_in_between_holds_it(self):
        # #614: the other run was in neither list at the first poll.
        poll, calls = polls(True, False, False, True, True)
        slept = []
        self.assertEqual(q.wait(poll, slept.append), 0)
        self.assertEqual(slept, [q.CONFIRM_SECS, q.POLL_SECS, q.POLL_SECS, q.CONFIRM_SECS])

    def test_a_vanished_run_on_the_pc_is_seen_by_the_confirming_poll(self):
        other = run(2, "09:00", 6)
        fake = Fake([run(1, "10:00", 5)], jobs={2: ON_PC})
        queue = q.Queue(fake.get, 1)
        self.assertTrue(queue.poll()[0])
        fake.runs.append(other)
        self.assertFalse(queue.poll()[0])


if __name__ == "__main__":
    unittest.main()


def copy(source, sha):
    return {"sha": sha, "content": base64.b64encode(source.encode()).decode()}


MAIN = """
class Queue:
    def __init__(self, get, me, now):
        self.me = me
    def poll(self):
        return False, f"main's order for {self.me}"
"""


class FollowMain(unittest.TestCase):
    """Every run sorts by main's copy, not its own (#659's deadlock)."""

    def follow(self, answers):
        calls = []

        def get(path):
            calls.append(path)
            if path == q.MAIN_COPY:
                answer = answers.pop(0) if len(answers) > 1 else answers[0]
                if isinstance(answer, Exception):
                    raise answer
                return answer
            return {"workflow_runs": []}

        return q.Follow(get, 7), calls

    def test_polls_with_mains_copy(self):
        f, _ = self.follow([copy(MAIN, "a1")])
        self.assertEqual(f.poll(), (False, "main's order for 7"))

    def test_reads_main_again_every_sync_polls(self):
        f, calls = self.follow([copy(MAIN, "a1")])
        for _ in range(q.SYNC_POLLS + 1):
            f.poll()
        self.assertEqual(calls.count(q.MAIN_COPY), 2)

    def test_a_new_main_copy_takes_over(self):
        new = MAIN.replace("main's order", "new order")
        f, _ = self.follow([copy(MAIN, "a1"), copy(new, "b2")])
        f.poll()
        for _ in range(q.SYNC_POLLS):
            last = f.poll()
        self.assertEqual(last, (False, "new order for 7"))

    def test_unreadable_main_keeps_its_own_copy(self):
        f, _ = self.follow([OSError("down")])
        self.assertEqual(f.poll(), (True, "this run isn't listed in progress; going"))

    def test_a_copy_that_doesnt_load_is_skipped(self):
        f, _ = self.follow([copy("this isn't python(", "c3")])
        self.assertEqual(f.poll(), (True, "this run isn't listed in progress; going"))
