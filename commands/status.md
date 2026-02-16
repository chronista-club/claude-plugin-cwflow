---
description: 全ワーカー環境の状態を一覧表示。ブランチ、変更ファイル数、PR状態を確認。
---

# CW Status — ワーカー環境の状態確認

## 手順

1. `cw ls` で全ワーカー一覧を取得
2. 各ワーカーディレクトリで以下を収集:
   - 現在のブランチ名
   - 未コミットの変更ファイル数（`git status --short | wc -l`）
   - 最新コミットメッセージ（`git log --oneline -1`）
   - リモートとの差分（`git rev-list --left-right --count HEAD...@{upstream} 2>/dev/null`）
   - 対応するPR状態（`gh pr list --head <branch> --json state,url` ）

3. 結果を表形式で表示:

```
Worker          Branch                  Changes  Last Commit         PR
─────────────────────────────────────────────────────────────────────────
issue-42        feature/issue-42        3 files  feat: add auth      Draft
issue-43        feature/issue-43        0 files  fix: typo           Merged
hotfix-1        fix/urgent-bug          1 file   wip                 None
```

4. ワーカーが0件の場合: 「ワーカーはありません。`cw new <name> <branch>` で作成できます。」と表示

## 注意

- `cw` コマンドが見つからない場合は `/opt/homebrew/bin/cw` を試す
- ワーカーディレクトリが存在しない場合はスキップして警告を出す
