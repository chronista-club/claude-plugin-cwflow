# cwflow

Claude Workers（`cw`コマンド）を使った並行開発ワークフローのClaude Codeプラグイン。
Gitクローンベースのワークスペース分離で、複数セッションを安全に並列実行。

## インストール

```bash
/plugin install chronista-club/claude-plugin-cwflow
```

## 概要

```
メインリポ (~/repos/my-project)    <-- 安定。汚さない
|
+-- cw new issue-42 feature/issue-42
|   -> ~/.cache/cw/issue-42/    <-- Agent A
|
+-- cw new issue-43 feature/issue-43
    -> ~/.cache/cw/issue-43/    <-- Agent B
```

## `cw` CLI コマンド

`cw` はシステムにインストールするCLIツール（`~/.cargo/bin/cw`）。プラグインのコマンドではない。

| コマンド | 説明 |
|---|---|
| `cw new <name> <branch>` | ワーカー環境を作成（clone + symlink + setup） |
| `cw ls` | 全ワーカー一覧 |
| `cw path <name>` | ワーカーのパスを出力 |
| `cw rm <name>` | ワーカーを削除 |

## Claude Code コマンド

プラグインが提供するスラッシュコマンド:

| コマンド | 説明 |
|---|---|
| `/cwflow:new [issue番号 or タスク名]` | ワーカー環境を作成。Issue番号指定で自動命名、フリーモードも可 |
| `/cwflow:parallel [worker-names...]` | tmuxで複数ワーカーのClaude Codeセッションを並列起動（ccwire自動登録付き） |
| `/cwflow:dashboard` | Vantage Pointに並列開発ダッシュボードを表示（Agent一覧/タスク/メッセージの3ペイン） |
| `/cwflow:status` | 全ワーカーの状態一覧（ブランチ、変更数、PR状態） |
| `/cwflow:cleanup` | マージ済み・不要なワーカーを検出して一括削除 |
| `/cwflow:conflict-check` | 並列ワーカーの変更ファイル重複を検知し、コンフリクトを早期警告 |

## Leader-Worker パターン

リーダーがワーカーを作成し、tmuxペインで並列起動。ccwireで相互通信する:

```
Leader (メインリポ, ccwire: "lead")
+-- /cwflow:new 42
+-- /cwflow:new 43
+-- /cwflow:parallel issue-42 issue-43
|   +-- tmux pane 0: CCWIRE_SESSION_NAME=worker-issue-42 claude
|   +-- tmux pane 1: CCWIRE_SESSION_NAME=worker-issue-43 claude
+-- wire_status で進捗監視
+-- wire_receive でワーカーからの質問に回答
```

ワーカーは `AskUserQuestion` を使わず、質問は ccwire でリーダーに送信する（PreToolUse フックでブロック済み）。

## ワークフロー

```bash
# 1. ワーカー作成
cw new issue-42 feature/issue-42

# 2. Claude Codeセッション起動
cd $(cw path issue-42) && claude

# 3. 作業完了 -> PR -> マージ
gh pr create ...

# 4. 削除
cw rm issue-42
```

## worker-files.kdl

各プロジェクトの `.claude/worker-files.kdl` でワーカー環境の設定を定義:

```kdl
symlink ".env"
symlink ".mcp.json"
symlink ".claude/settings.local.json"
symlink-pattern "**/*.local.*"
post-setup "bun install"
```

## フック

| フック | 動作 |
|--------|------|
| SessionStart | ワーカー環境を検出し、コンテキストを注入 |
| PreToolUse | ワーカー環境での `AskUserQuestion` をブロック |

## 前提

- `cw` コマンド（`~/.cargo/bin/cw`）
- [Claude Code](https://claude.ai/code)

## License

MIT
