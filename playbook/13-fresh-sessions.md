# 13. Fresh sessions for long-running roles

A coordinator, or any standing role that runs for days, must not live in one ever-growing session. Every turn re-sends the whole history, so a session that never resets gets slower, costs more per turn, and starts deciding from a blurred memory of old messages. A role stays continuous through a **state file** and a **handoff**, not through one session.

Some hosts swap the session for you behind the scenes (Claude projects do: the coordinator restarts from memory, recent chat and the thread list). A team on plain Claude Code does it by hand, as below. The outcome is the same: the owner keeps talking to one coordinator; the coordinator is quietly a new session each day.

*Why:* the owner, 2026-11-07, about a coordinator on plain Claude Code: "his context window is slowly growing and filling up, every message sends his whole history. i've already seen this happen before. he's going to start getting 1) stupid ... 2) it's going to get expensive".

---

## The state file

One Markdown file per role, kept where it outlives any session (a folder on the machine that runs the role, outside the project's `main`, so updating it never opens a PR or starts CI). It holds **only what GitHub and email don't already record**:

- Standing rules the owner gave, each as quoted words with the date.
- What is in flight: lanes or threads running and what each is on, trains open, PRs or issues waiting on the other team.
- Open questions: asked of whom, when, and what was recommended.
- Dates and decisions that aren't on the tracker yet.
- Pointers (the roster issue, the playbook page, the inbox search), not copies of them.

Rewrite it, don't append: anything finished or now on GitHub comes out. Keep it under about 4 KB; a bigger file is a sign it is copying the tracker. Update it in the same turn a decision lands, not at the end of the day.

## When to start a fresh session

Whichever comes first:

1. **Daily**, at a fixed quiet time (for example just after the morning report).
2. **At the sprint reset**, after the retro and plan are written.
3. **When context passes half the window** (check with `/context`), or the session has compacted twice.
4. **After any long investigation**, once its result is in the state file.

The steps: the old session brings the state file up to date and says so; then start a new session (or `/clear` in the same one); the new session reads the handoff prompt below before anything else.

## The handoff prompt

Put this in the project's `CLAUDE.md` (or a `SessionStart` hook that prints the state file), so every new session reads it without being told:

> You are the coordinator for team `<name>`. Before anything else: read `<path>/STATE.md`; read this playbook's `main` pages 02, 09 and 11; list open PRs and issues labelled `team:<name>`, `review:<name>` and `verify:<name>`; and read team email from the last 24 hours. Then post one line: what you're picking up and anything that needs action now. Trust the state file and GitHub over anything you remember; if they disagree, GitHub wins and you fix the state file.

## Keeping a session small between resets

- **Scheduled checks run in their own session**, not inside the coordinator's. An hourly inbox watch or label poll started from the coordinator's session adds a turn every hour. Run it headless (`claude -p "<the check>"` from cron or Task Scheduler), have it write a short digest file, and let the coordinator read only the digest.
- **Heavy reads go to a subagent** (logs, diffs, long threads, many issues). The subagent reads; the coordinator keeps the conclusion.
- **`/compact <what to keep>`** when context is high mid-day, naming what must survive (open decisions, the state file path). Leave auto-compact on as a backstop, but don't rely on it: it summarises on its own terms.
- **`/clear`** after the state file is current is the cheapest reset of all.
- **Don't `--resume` an old session** to pick up yesterday's work; start fresh and read the state file.
