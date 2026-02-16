---
description: tmuxを使って複数ワーカーでClaude Codeセッションを並列起動。
---

# CW Parallel — 並列セッション起動

## 手順

1. 起動対象の決定:
   - 引数でワーカー名が指定された場合 → それらを使用
   - 指定がない場合 → `cw ls` で一覧を表示し、起動するワーカーを選択

2. tmuxセッションの構成を決定:
   - 2ワーカー: 左右2ペイン
   - 3ワーカー: 左 + 右上下
   - 4ワーカー: 2x2グリッド

3. tmuxセッション `cw-parallel` を作成（既存なら確認の上で再作成）:

   ```bash
   # 例: 2ワーカーの場合
   tmux new-session -d -s cw-parallel -c "$(cw path issue-42)"
   tmux split-window -h -t cw-parallel -c "$(cw path issue-43)"

   # 各ペインでClaude Codeを起動
   tmux send-keys -t cw-parallel:0.0 'claude' Enter
   tmux send-keys -t cw-parallel:0.1 'claude' Enter
   ```

4. セッションにアタッチ:
   ```bash
   tmux attach -t cw-parallel
   ```

5. 起動完了メッセージ:
   ```
   並列セッションを起動しました:
     Pane 0: issue-42 (feature/issue-42)
     Pane 1: issue-43 (feature/issue-43)

   tmux attach -t cw-parallel でアクセスできます。
   ```

## 引数

- `<worker-names...>`: 起動するワーカー名（スペース区切り、省略時は対話選択）

## 注意

- tmuxがインストールされていない場合はエラー
- 各ペインは独立したClaude Codeセッション（互いに干渉しない）
