# 5. Working in parallel

Many threads build against one `main` and a limited merge gate. These rules keep conflicts mechanical, so a rebase never needs judgment.

---

## Branches and PRs

- **One branch per thread.** One open code PR per thread at a time; the next starts after the last merges. After a merge the branch restarts from the latest `main` (same name, new PR). No stacked PRs.
- **A spec can wait beside the code.** A thread may keep one docs-only spec PR open on `<branch>-spec`, so a spec in review doesn't hold the code up. Specs merge through Code review like code.
- **Name what you touch outside your area.** The project's area table maps files to areas. A PR names each file it touches outside its issues' areas, so two threads in the same file see it coming.
- **Your PR keeps the whole workspace green.** If your change breaks another area's check, fixing or re-gating it is part of your PR, and you tell the thread whose work leans on it.
- **Pick up `main` early.** Rebase local work whenever another PR merges, so conflicts are found small. Pushing still waits until ready.
- **Rebase only your own branch.** Never rewrite another thread's branch or `main`.
- **Flag drift, don't chase it.** Work that pulls against the vision or another area's spec becomes a parked issue naming the priority it harms. A thread fixes drift only inside its own milestone.

---

## Shared files

Files every PR touches get rules that make conflicts trivial:

- **Roadmap**: holds only order, scope and done-whens. Threads don't edit it; changes are their own PR with the owner's sign-off.
- **Decision log and other logs**: append rows at the end, never reorder. A conflict is resolved by keeping both rows.
- **Version counters are hashes, not numbers.** A layout or schema change adds a file named for its issue (`242-journal-site-claims`) to a directory, and the version is a hash of the file names. Two PRs never edit the same line.
- **Registries are generated.** A new command, check or plugin is a new file in a directory; a build step writes the list. Nobody edits a central list.
- **Central entry points** (`main.rs`, `App.tsx`, `Program.cs`) stay thin: a feature is a module or plugin registered once.
- **Lock files**: on conflict take `main`'s and rebuild. Adding a dependency is its own small PR from Dev process.

*Why:* on the reference project, the central entry points and a version counter were the biggest conflict hotspots in the history until each got one of these rules.

---

## Merge order

1. **Before asking for a merge**, the thread rebases on the latest `main`, runs the full local check, pushes, marks the PR ready, and checks it is still mergeable.
2. **Priority, then first ready.** Priority A goes first; ties go to the PR waiting longest. The queue never reorders the roadmap.
3. **A pure refactor yields to feature PRs for at most 4 hours.** A refactor can be redone on any `main` in minutes (if scripted); a feature merging into moved files is hand surgery. After 4 hours it goes next.
4. **After each merge**, threads with open PRs rebase only if GitHub shows a conflict or the merge changed something they depend on. Rebasing just to re-run CI wastes the runner.

---

## Merge trains

Every code PR merges in a train, a train of one included.

- Code review resets its own branch to `main`, merges 2 to 5 approved PRs' heads into it with plain merge commits (oldest and priority A first, conflicting ones left out), pushes it, and opens it as a PR with a `Train:` line naming the members and their `Refs` lines.
- Only a train runs the full merge-gate check. A member's own `full` check reports "full runs in a train" and passes on a light runner, so members show no red but can't merge alone (the required check is missing, never skipped or neutral, since a skipped required check counts as passing).
- **Green:** merge the train with a merge commit; every member shows as merged; each gets its board lines.
- **Red:** nothing merges and the train closes. If the log names the failing member, it goes back to its thread and the rest ride the next train. If not, split the train in two.
- **A member never changes while it rides.** A push to a member takes it off the train.
- **If `main` moved during the run**, the tree that lands isn't quite the tree that was tested. Code review checks what merged meanwhile, and re-runs the train when any of it touches the same files or a check a member leans on.
- One train is open at a time.

*Why:* with one full run every ~25 minutes, separate runs per PR plus a combined run cost six runs for five merges. A train spends one run on all of them, and the tree that lands is the tree that was tested.

---

## Main stays green

- **Nightly full run on `main`.** Two PRs that are each green can break `main` together. A red night is the first line of the morning report, and fixing it is priority A for whoever owns what broke.
- **`main-fix` label.** Once `main` is declared red, the fixing PR (a revert or a fix) gets `main-fix` and jumps every queue; other runs that reach the front wait in place, since they'd merge a red `main`. The label goes stale after 2 hours, so a forgotten label can't halt the queue.
- **A train that breaks `main` is reverted first, fixed after.** Once a merged train is found to have turned `main` red, Code review's next action is a revert PR of that train, labelled `main-fix`. The fix comes back afterwards as a new PR on a green `main`. A fix-forward is allowed only when it's ready before the revert would be. *Why:* a revert is ready in minutes and known to be green; on 11-07 a fix-forward held every run behind it for 36 minutes while its merge waited.
- **A train that fails twice is split.** After a train's second red `full`, Code review drops it and builds smaller trains from its members (halves, or the suspect alone and the rest together), so the members that are green merge while the failing one is found. *Why:* a re-run of the same train spends a full run to learn nothing new.
