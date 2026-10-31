---
name: git-workflow
description: "GIT WORKFLOW SKILL — Exact command sequences for all branch lifecycle operations in this project. USE FOR: creating a work branch for a backlog item; committing and merging work; tagging design versions or releases. Eliminates the need to look up git-workflow.md during implementation. DO NOT USE FOR: deciding what to work on (use backlog-entry or agent-orientation)."
---

# Git Workflow

Exact command sequences for every branch lifecycle operation. Copy and substitute `{placeholders}`.

---

## Creating a Work Branch

```bash
# 1. Start from the active branch
git checkout {active-branch}
git pull

# 2. Create the work branch
git checkout -b work/BL-{N}
```

---

## During Implementation

Periodically sync with the active branch to catch conflicts early:

```bash
git fetch origin
git merge origin/{active-branch}
# Resolve any conflicts now; do not wait until merge time.
```

---

## Committing

Include the `BL-N` identifier in the commit message:

```bash
git add .
git commit -m "{type}(BL-{N}): {imperative description}"
```

---

## Build Verify Before Merge

Run the build-verify skill before merging. All tests must pass.

```bash
mvn clean test
# All tests must pass. Zero failures, zero errors.
```

---

## Merging Into the Active Branch

No PRs required. Merge directly after build passes.

```bash
# 1. Switch to the active branch and pull latest
git checkout {active-branch}
git pull

# 2. Merge the work branch
git merge work/BL-{N}

# 3. Push
git push

# 4. Delete the work branch (local and remote if pushed)
git branch -d work/BL-{N}
git push origin --delete work/BL-{N}  # only if branch was pushed to remote
```

---

## After Merge — Communicate

Always communicate to the user after merging:
- What was merged
- Which branch it landed on
- What backlog item it resolves (if applicable)

---

## Tagging

```bash
# Design version tag
git tag design/v{N.M}
git push origin design/v{N.M}

# Release tag (annotated)
git tag -a v{N.M.P} -m "{release description}"
git push origin v{N.M.P}
```

---

## Commit Message Format

```
{type}(BL-N): {imperative description}
```

When not tied to a backlog item:

```
{type}: {imperative description}
```

| Type | Use For |
|------|---------|
| `feat` | New functionality |
| `fix` | Bug fix |
| `refactor` | Code restructuring |
