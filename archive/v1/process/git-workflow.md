# Process — Git Workflow

Standard branch naming, commit message format, and merge strategy for all projects.

---

## Branch Structure

There is one long-lived branch per active development effort. Everything else is short-lived and deleted after merge.

| Branch | Purpose |
|--------|---------|
| `main` | Always stable. Represents the last shipped release. **Only the user merges to `main`** — agents never merge to or push to `main` directly. |
| Active branch | The current development branch (e.g., `prototype/active`, `develop`, or whatever the project uses). All work targets this branch. |
| `work/{BL-N}` | Short-lived work branch. Each backlog item is implemented here and merged directly into the active branch. Branched from the current head of the active branch. Delete after merge. |

### Branch Lifecycle

```
main                          ← stable; tagged on release
 └── {active branch}          ← long-lived; all development here
      ├── work/BL-1           ← work branch; merged directly
      ├── work/BL-2           ← work branch; merged directly
      └── work/BL-3           ← work branch; merged directly
```

- Work branches are short-lived. Delete after merge.
- Design documents live in the `design/` folder on the active branch.
- `main` is only updated when the user decides work is ready. **Agents never merge to `main` directly** — the user is responsible for promoting work from the active branch to `main`.
- **No PRs required.** Work branches merge directly into the active branch after build passes. The merge commit is the record.

---

## Merge Workflow

Both roles follow the same merge pattern:

1. **Branch from active.** Create a work branch from the current head of the active branch.
   ```bash
   git checkout {active-branch}
   git pull
   git checkout -b work/{BL-N}
   ```

2. **Make changes and commit.** Include the `BL-N` identifier in the commit message.

3. **Build and verify.** Run the build-verify skill. All tests must pass before merging.

4. **Merge into the active branch.**
   ```bash
   git checkout {active-branch}
   git pull
   git merge work/{BL-N}
   git push
   ```

5. **Delete the work branch.**
   ```bash
   git branch -d work/{BL-N}
   git push origin --delete work/{BL-N}
   ```

6. **Communicate to the user.** Clearly state: what was merged, which branch it landed on, and what backlog item it resolves (if applicable).

---

## Commit Message Format

```
{type}(BL-N): {imperative description}

{optional body — explain WHY, not WHAT, if the change is not self-evident}
```

When a commit is not tied to a backlog item, omit the `(BL-N)` scope:

```
{type}: {imperative description}
```

**Types:**

| Type | Use For |
|------|---------|
| `feat` | New functionality |
| `fix` | Bug fix |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or updating tests |
| `chore` | Build config, dependencies, CI, formatting |
| `docs` | Documentation-only changes |

---

## Work-Item ID Rules

Work-item IDs follow the `BL-N` convention defined in `BACKLOG.md`:
- IDs are sequential integers. The next ID is always `(highest BL-N currently in the document) + 1`.
- IDs are never reused. When an item is removed after completion, its ID is retired.
- This ensures IDs don't clash and can be traced in git history after the item is removed.

---

## Tags

Tags mark meaningful states. Use them sparingly.

| Tag | When to Create | Example |
|-----|---------------|---------|
| `v{major}.{minor}.{patch}` | When stable work is merged to `main` for release. | `v1.0.0` |
| `design/v{N.M}` | When a design document version is finalized. | `design/v0.2` |

**Rules:**
- Tags are permanent once pushed.
- Annotated tags are preferred for releases: `git tag -a {tag} -m "{message}"`.
- Lightweight tags are acceptable for design snapshots.
