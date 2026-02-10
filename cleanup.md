---
description: Clean up merged branches, check for stale virtual branches, and verify workspace health.
---

Clean up the GitButler workspace.

## Step 1: Identify merged branches

```bash
but branch list
```

Check which branches have been merged upstream (PRs merged). For each merged branch:
```bash
but branch delete <branch-name>
```

## Step 2: Check for stale branches

Identify branches with no commits in the last 7 days. List them and ask me which ones to delete.

## Step 3: Verify workspace health

```bash
but status -f
```

Check for:
- Uncommitted changes that don't belong to any branch
- Branches with unpushed commits
- Virtual branch count (warn if >6)

## Step 4: Pull latest

```bash
but pull
```

Report any conflicts that arise.

## Step 5: Summary

- Branches deleted: N
- Branches remaining: N
- Workspace health: clean / needs attention
