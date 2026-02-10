---
description: Plan task decomposition for large (L/XL) tasks into stacked branches. Analyzes task scope, identifies phases, and creates a branch structure.
---

Help me plan and decompose a large task into manageable phases using GitButler stacked branches.

Read the gitbutler-workflow skill for scheduling rules, then:

## Step 1: Analyze the task

Ask me to describe the task if $ARGUMENTS is empty. Otherwise, analyze the task description provided.

Determine the task size:
- XS (~1 commit, 5-10min): Just do it, no planning needed
- S (2-5 commits, ~1hr): Just do it
- M (5-15 commits, 2-4hr): Single branch, no decomposition needed
- L (15-30 commits, ~1 day): Consider decomposition
- XL (30+ commits, 2-5 days): **Must decompose**

If XS/S/M, tell me that decomposition isn't needed and suggest the direct approach.

## Step 2: Identify phases (L/XL only)

Break the task into 3-5 phases where each phase:
- Can build and pass tests independently
- Has a clear, bounded scope
- Takes no more than 4 hours (M-equivalent)
- Has minimal coupling to subsequent phases

Recommended phase ordering:
1. Data layer / type definitions (least impact on other phases)
2. Core logic / business rules
3. API / interface layer
4. Integration / wiring
5. Polish / edge cases

## Step 3: Design the branch structure

Output the exact `but` commands to create stacked branches:

```bash
but branch new xl/<task>-phase-1-<description>
but branch new -a xl/<task>-phase-1-<description> xl/<task>-phase-2-<description>
but branch new -a xl/<task>-phase-2-<description> xl/<task>-phase-3-<description>
```

## Step 4: Create a checklist

For each phase, output:
- [ ] Phase N: <description> — estimated commits, estimated time, key files affected

## Step 5: Check for conflicts

Run `but status -f` and identify any active branches that might conflict with the planned phases. Flag overlapping file paths.

Warn if the stack depth exceeds 3 (our recommended maximum).
