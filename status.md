---
description: Show GitButler workspace status with branch summary, active changes, and PR state
---

Show the current GitButler workspace status. Run these commands in order:

1. `but status -f` — full workspace status with file-level detail
2. `but branch list` — all virtual branches and their state
3. `but oplog` — recent operations history (last 5)

Present the results as a concise summary:
- Which branches are active and what they contain
- Any uncommitted changes and which branch they belong to
- Any branches that need push/publish
- Any potential conflicts between active branches

If `but` is not available, inform the user that GitButler CLI is not installed and link to https://docs.gitbutler.com/cli
