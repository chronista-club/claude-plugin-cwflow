---
description: ワーカー環境を作成。Issue番号を指定すると自動命名、自由なタスク名でもOK。
---

# CCWS New — ワーカー作成

## 手順

1. ユーザーの指定を判定:

   **A) Issue番号が指定された場合** → Issue 連携モード
   - `gh issue view <number> --json number,title,labels` で情報取得
   - ワーカー名: `issue-<number>` （例: `issue-42`）
   - ブランチ名: `feature/issue-<number>` （bug/fix系なら `fix/issue-<number>`）

   **B) タスク名が直接指定された場合** → フリーモード
   - ワーカー名: そのまま使用（例: `auth-refactor`, `experiment-new-api`）
   - ブランチ名: `feature/<name>` （例: `feature/auth-refactor`）

   **C) 何も指定されない場合** → 選択を促す
   - `gh issue list -l next --json number,title,labels --limit 10` で Issue 候補を表示
   - 「Issue番号を選ぶか、自由なタスク名を入力してください」と案内

2. 実行前に確認を表示:
   ```
   Worker: auth-refactor  (リポ名自動prefix: nexus-auth-refactor)
   Branch: feature/auth-refactor
   Path:   ~/.local/share/ccws/nexus-auth-refactor/

   作成しますか？
   ```

3. `ccws new <name> <branch>` を実行
   - ccws が自動的にリポ名を prefix する（例: `auth-refactor` → `nexus-auth-refactor`）

4. 成功したら:
   - ワーカーのパスを表示
   - 「`cd $(ccws path <name>) && claude` でセッションを開始できます」と案内

## 引数

- `<issue-number>`: GitHub Issue番号（省略可）
- `<task-name>`: 自由なタスク名（省略可、Issue番号と排他）

## 使用例

```bash
# Issue連携
/cwflow:new 42

# フリーモード
/cwflow:new auth-refactor
/cwflow:new experiment-streaming

# 対話選択
/cwflow:new
```

## 注意

- カレントディレクトリがgitリポジトリのルートであることを確認
- 同名のワーカーが既に存在する場合はエラーを出す（`ccws ls` で確認）
