---
description: Batch process multiple XS/S tasks in a single session. Creates a branch, executes tasks sequentially, and publishes as a single PR.
---

Execute multiple small tasks (XS/S) as a batch in a single branch.

Read the gitbutler-workflow skill for batch processing rules, then:

## Step 1: Collect tasks

If $ARGUMENTS is empty, ask me to list the XS/S tasks.
Otherwise, parse the task list from $ARGUMENTS.

Verify each task is genuinely XS or S (≤5 commits each). If any task looks like M or larger, flag it and suggest removing it from the batch.

## Step 2: Create batch branch

```bash
but branch new fix/batch-$(date +%Y%m%d)
```

## Step 3: Execute sequentially

For each task:
1. Implement the change
2. `but commit -m "<conventional-commit-message>"`
3. Verify the change (run tests if applicable)
4. Move to next task

Use conventional commit prefixes: fix:, chore:, docs:, style:, refactor:

## Step 4: Finalize

```bash
but absorb       # clean up any uncommitted fragments
but status -f    # verify everything is clean
but push
but publish      # create PR
```

## Step 5: Summary

Report what was accomplished:
- N tasks completed
- N commits created
- Branch name and PR link
- Any tasks that were skipped or deferred (with reasons)
