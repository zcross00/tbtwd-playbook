# 8. Estimating and forecasting

Due dates are **accurate, honest and realistic: not overly ambitious, not overly padded.** They come from measured pace, not hope.

---

## The unit

For AI-built work, the unit is **thousands of output tokens** (Estimate and Actual fields). Output tokens track session cost closely; input and cache tokens follow them. For human work, use ideal hours or points; the rules below don't change.

| Size | k output tokens | Typical work |
|---|---|---|
| S | 20 | rough edge, small spec change, docs |
| M | 60 | a normal one-PR piece of work |
| L | 100 | one PR with a new system, or a spec |
| XL | split it | anything bigger is more than one issue |

- The thread that will build it estimates when it goes to Ready. Pick the closest size; adjust only with a reason.
- **Nobody re-estimates midway.** A bad estimate is the data we want.
- **Actual** is read from the session's running totals at the start and end of the work. If it can't be read, give it from the table by what the work turned out to be, and say so. Never leave it out.
- Weekly, Dev process compares Estimate against Actual per team and adjusts the table if a team is off by more than half.

---

## The daily plan

The board plans in **iterations of one day**, grouped by week. The week is the planning unit: the owner sets the week's budget (tokens, money or hours), and the week's issues fit under it. Each team (area) has at most one issue in progress; the coordinator fills days so no team sits empty while another has more than a day queued, and moves unfinished work to the next day rather than starting more.

---

## Burn-down and re-forecast

- **Daily burn-down.** One line per open milestone: estimate left, PRs merged and issues added since grooming, open corrections, its dates, and ON TRACK / AT RISK / NOT DATED. AT RISK on a committed milestone goes to the owner the same day.
- **Daily re-forecast.** A milestone's due date becomes *today + estimate left ÷ pace*, where pace is the estimate closed in the last 3 days over 3, plus a fixed allowance for verification and acceptance. A milestone with too little recent closing keeps its date; one with a `Date fixed:` line (an outside commitment) keeps it too.
- **Calibrate against history.** A milestone closed in the last 14 days records its last due date against its actual close.
- **Early is a miss too.** A due date is a commitment the owner plans around, so closing early counts as a miss, the same as closing late. Dev process keeps a table of every closed milestone: last due date, actual close, and the signed error (close minus due). The weekly retro reads two numbers from it: the mean signed error (target within ±0.5 days) and the share of milestones that closed on their due date (target at least half). A mean that drifts early means allowances are stacked: shorten the pace window, drop buffer days, or raise the rate to the measured throughput. A mean that drifts late means the opposite. Don't patch individual dates to hide the drift; the retro changes the forecast's settings instead.

*Why:* on the reference project, every one of the first 16 milestones closed before its padded 90% date, because allowances stacked up. Forecasting from measured pace fixed it.

---

## Committed dates

A date becomes a commitment only when the owner commits it. Until then it is a forecast. A committed milestone's done-when may include a sustained measure (e.g. "7 green nightly runs in a row"); a miss restarts the count.
