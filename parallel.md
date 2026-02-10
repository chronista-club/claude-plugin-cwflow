---
description: Design and validate parallel development sessions. Checks file overlap between tasks, suggests tmux layout, and creates branches for each session slot.
---

Help me set up parallel development sessions using GitButler virtual branches.

Read the gitbutler-workflow skill (especially scheduling and tmux-integration references), then:

## Step 1: Gather tasks

If $ARGUMENTS is empty, ask me to list the tasks I want to run in parallel.
Otherwise, parse the task descriptions from $ARGUMENTS.

## Step 2: Size each task

Classify each task as XS/S/M/L/XL.

## Step 3: Validate the combination

Check these rules:
- ❌ L+L, L+XL, XL+XL in parallel → too risky, suggest serializing
- ✅ L + M + XS/S batch → recommended pattern
- ✅ M + M + XS/S batch → safe
- ⚠️ Maximum 3 concurrent sessions

## Step 4: File overlap analysis

For each task pair, identify potentially overlapping files/directories.
If overlap exists:
- Suggest `but mark` to pre-assign file patterns to branches
- Or recommend serializing the overlapping tasks

## Step 5: Create branches and assign slots

```bash
# Slot A: Large task (deep focus)
but branch new feat/<task-a>

# Slot B: Medium task
but branch new feat/<task-b>

# Slot C: Small batch
but branch new fix/<batch-name>
```

## Step 6: Suggest tmux layout

Output the tmux commands to set up the session:

```bash
tmux new-session -s dev -n slot-a
tmux split-window -h
tmux split-window -v -t 0
# Slot A: left pane (large), Slot B: top-right, Slot C: bottom-right
```

Remind me that each pane should run its own `claude` session targeting its assigned branch.
