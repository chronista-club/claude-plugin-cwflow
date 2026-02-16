---
description: GitHub Issueからワーカー環境を作成。Issue番号を指定すると、名前とブランチを自動決定。
---

# CW New — Issue連携ワーカー作成

## 手順

1. ユーザーに確認:
   - Issue番号が指定されている場合 → そのIssueの情報を取得
   - 指定がない場合 → `gh issue list -l next --json number,title,labels --limit 10` で候補を表示し選択を促す

2. Issueの情報から名前とブランチを自動生成:
   - ワーカー名: `issue-<number>` （例: `issue-42`）
   - ブランチ名: `feature/issue-<number>` （例: `feature/issue-42`）
   - Issueタイトルにbug/fixが含まれる場合: `fix/issue-<number>`

3. 実行前に確認を表示:
   ```
   Issue:  #42 - ユーザー認証の追加
   Worker: issue-42
   Branch: feature/issue-42
   Path:   ~/.cache/creo-workers/issue-42/

   作成しますか？
   ```

4. `cw new <name> <branch>` を実行

5. 成功したら:
   - ワーカーのパスを表示
   - 「`cd $(cw path issue-42) && claude` でセッションを開始できます」と案内

## 引数

- `<issue-number>`: GitHub Issue番号（省略時は一覧から選択）

## 注意

- カレントディレクトリがgitリポジトリのルートであることを確認
- 同名のワーカーが既に存在する場合はエラーを出す（`cw ls` で確認）
