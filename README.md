# but-flow

A Claude Code plugin for GitButler CLI workflows. Virtual branches, stacked branches, parallel development, task scheduling, and tmux integration.

## Install

```bash
claude /plugin install https://github.com/chronista-club/claude-plugin-but-flow
```

## What it does

**Replaces git with `but`** — blocks raw git write commands and provides GitButler-native workflows.

### Components

| Component | What | Detail |
|---|---|---|
| **Skill** | `gitbutler-workflow` | Auto-loaded when branch/PR/scheduling work is detected. 400+ lines of reference documentation. |
| **Hook: PreToolUse** | git blocker | Intercepts `git checkout/commit/push/...` → forces `but` commands. 36 test cases. |
| **Hook: SessionStart** | status inject | Runs `but status` at session start, injects branch state into context. |
| **Command** | `/but-flow:status` | Workspace overview: branches, changes, PRs |
| **Command** | `/but-flow:plan` | Decompose L/XL tasks into stacked branches |
| **Command** | `/but-flow:parallel` | Design parallel sessions with conflict validation |
| **Command** | `/but-flow:batch` | Batch XS/S tasks into single branch |
| **Command** | `/but-flow:cleanup` | Clean merged branches, health check |
| **Agent** | `branch-planner` | Analyzes tasks → designs optimal branch strategy |
| **Agent** | `conflict-checker` | Detects file overlap between active branches |

### Task Scheduling

Built-in XS-XL task sizing with scheduling rules:

```
XS (~1 commit)  → batch with other XS/S
S  (2-5 commits) → batch or standalone
M  (5-15 commits) → standalone branch
L  (15-30 commits) → consider decomposition
XL (30+ commits) → MUST decompose into stacked branches
```

### Parallel Development

3-slot pattern: Large + Medium + Small-batch, with file overlap detection and `but mark` for ownership assignment.

### tmux Integration

Agent Teams support, split-pane layouts, session persistence, and cross-pane reference.

## Prerequisites

- [GitButler CLI](https://docs.gitbutler.com/cli) (`but` command)
- [Claude Code](https://code.claude.com) v2.0+
- Python 3.8+ (for hook scripts)

## Known Limitations

See `skills/gitbutler-workflow/references/known-limitations.md` for:
- Verified behaviors
- Unverified assumptions (concurrent sessions, Agent Teams + GitButler)
- Verification TODO checklist

## License

MIT
