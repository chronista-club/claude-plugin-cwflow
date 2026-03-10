---
name: cwflow
description: >
  Claude Code Workspace（ccwsコマンド）を使った並行開発ワークフロー。
  Gitクローンベースのワークスペース分離で、複数のClaude Codeセッションを
  安全に並列実行するためのスキル。

  このスキルは以下のような場面で使う：
  - 「並行開発したい」「複数Issueを同時に進めたい」
  - 「ccwsコマンドの使い方」「ワーカー環境の作り方」
  - 「worker-files.kdlの設定方法」
  - 「Claude Codeで安全に並列セッションを走らせたい」
  - Issue単位の作業環境分離
---

# CW Flow — Claude Code Workspace 並行開発ワークフロー

`ccws`（Claude Code Workspace）はGitクローンベースのワークスペースマネージャー。
メインリポジトリを汚さず、Issue単位で完全に独立した作業環境を作成する。

## コンセプト

```
メインリポ (~/repos/my-project)
│  ← 安定。直接作業しない or リーダーのみ
│
├── ccws new issue-42 feature/issue-42
│   → ~/.local/share/ccws/issue-42/    ← Agent A が作業
│
├── ccws new issue-43 feature/issue-43
│   → ~/.local/share/ccws/issue-43/    ← Agent B が作業
│
└── ccws new hotfix-1 fix/urgent-bug
    → ~/.local/share/ccws/hotfix-1/    ← Agent C が作業
```

各ワーカーは:
- **完全なgitクローン** — ブランチ、コミット、pushが完全に独立
- **secretsはsymlink共有** — `.env`, `.mcp.json` 等は元リポと同期
- **使い捨て** — 作業完了・マージ後に `ccws rm` で削除

## コマンドリファレンス

| コマンド | 説明 |
|---|---|
| `ccws new <name> <branch>` | ワーカー環境を作成（clone + symlink + setup） |
| `ccws ls` | 全ワーカー一覧（名前、ブランチ、パス） |
| `ccws path <name>` | ワーカーのパスを出力 |
| `ccws rm <name>` | ワーカーを削除 |
| `ccws rm --all` | 全ワーカーを削除 |

### 使用例

```bash
# Issue単位でワーカーを作成
ccws new issue-42 feature/issue-42

# パスを取得（スクリプト連携用）
cd $(ccws path issue-42)

# そのディレクトリでClaude Codeセッションを起動
cd $(ccws path issue-42) && claude

# 作業完了後に削除
ccws rm issue-42
```

## worker-files.kdl 設定

各プロジェクトの `.claude/worker-files.kdl` に、ワーカー環境へ配置するファイルを定義する。
`ccws` はクローン後にこのファイルを読み、シンボリックリンクやコピーを自動で配置する。

### 構文

```kdl
// シンボリックリンク — 元リポと共有（secrets等の変更が即反映）
symlink ".env"
symlink ".mcp.json"
symlink ".claude/settings.local.json"

// globパターンでまとめてsymlink
symlink-pattern "**/*.local.*"
symlink-pattern "**/*.local"

// コピー — ワーカー側で独立して変更可能
copy "config/dev.toml"

// セットアップ後に実行するコマンド
post-setup "bun install"
```

### symlink vs copy の判断基準

| ファイル種類 | 戦略 | 理由 |
|---|---|---|
| secrets・接続情報（`.env`） | symlink | 変更が全ワーカーに即反映 |
| MCP設定（`.mcp.json`） | symlink | 全ワーカーで同じツールを使える |
| ローカル設定（`*.local.*`） | symlink | 通常は共通 |
| ワーカーが独自に変更するファイル | copy | 独立して変更可能 |

### プロジェクト別の設定例

**Rustプロジェクト**:
```kdl
symlink ".env"
symlink ".mcp.json"
symlink ".claude/settings.local.json"
symlink-pattern "**/*.local.*"
```

**Node/Bunプロジェクト**:
```kdl
symlink ".env"
symlink ".mcp.json"
symlink ".claude/settings.local.json"
symlink-pattern "**/*.local.*"
symlink-pattern "**/*.local"
post-setup "bun install"
```

## 並行開発ワークフロー

### パターン1: 手動並列（ターミナル分割）

最もシンプル。各ターミナルペインで独立したClaude Codeセッションを起動。

```bash
# ペイン1: Issue #42
cd $(ccws path issue-42) && claude

# ペイン2: Issue #43
cd $(ccws path issue-43) && claude

# ペイン3: hotfix
cd $(ccws path hotfix-1) && claude
```

### パターン2: Leader-Worker（cwflow + ccwire 統合）

リーダーがワーカーを作成し、tmux ペインで並列起動。ccwire で相互通信。

```
Leader (メインリポ, ccwire: "lead")
├── worker-planner で Wave 計画を策定
├── TaskCreate で依存関係付きタスクを作成
├── ccws new issue-42 feature/issue-42
├── ccws new issue-43 feature/issue-43
├── /cwflow:parallel issue-42 issue-43
│   ├── tmux pane 0: CCWIRE_SESSION_NAME=worker-issue-42 claude
│   └── tmux pane 1: CCWIRE_SESSION_NAME=worker-issue-43 claude
├── wire_status で進捗監視
├── wire_receive でワーカーからの質問に回答
└── TaskList で完了確認 → 次 Wave 起動
```

**通信フロー**:
- ワーカー → リーダー: `wire_send(to: "lead", content: "質問", type: "task_request")`
- リーダー → ワーカー: `wire_send(to: "worker-issue-42", content: "回答")`
- 全体通知: `wire_broadcast(content: "main への push を停止してください")`
- ステータス: `wire_status(status: "busy")` → ダッシュボードに反映

**AskUserQuestion は使わない**: ワーカー環境では PreToolUse フックでブロック済み。

### パターン3: Issue消化マラソン

GitHub Issuesから直接ワーカーを作成して一気に消化。

```bash
# nextラベルのIssueを取得
gh issue list -l next --json number,title

# 各IssueをワーカーとClaude Codeで処理
ccws new issue-42 feature/issue-42
cd $(ccws path issue-42) && claude "Issue #42 を実装して"
```

## PRフロー

各ワーカーは独立したgitクローンなので、通常のgit + gh操作でPRを作成。

```bash
cd $(ccws path issue-42)

# 作業内容をコミット・プッシュ
git add . && git commit -m "feat: ..."
git push -u origin feature/issue-42

# PR作成
gh pr create --title "..." --body "..."
```

マージ後はワーカーを削除:
```bash
ccws rm issue-42
```

## 内部動作

`ccws new <name> <branch>` の実行手順:

1. カレントディレクトリのgitリポを検出（`git rev-parse --show-toplevel`）
2. `origin` URLを取得（`git remote get-url origin`）
3. `~/.local/share/ccws/<name>/` に shallow clone（`--depth 1`）
4. リモートURLをGitHub URLに設定
5. `.claude/worker-files.kdl` を読んでsymlink/copy を配置
6. 指定ブランチを作成
7. `post-setup` コマンドを実行

## 設計の原則

1. **1ワーカー = 1ブランチ = 1タスク** — 責務を混在させない
2. **メインリポは汚さない** — 直接作業はワーカーで行う
3. **使い捨て** — ワーカーは一時的。マージしたら削除
4. **secretsは共有** — symlink で一元管理。更新は全ワーカーに即反映
5. **shallow clone** — `--depth 1` で高速作成。履歴が必要なら `git fetch --unshallow`

## ストレージ

ワーカー環境は `~/.local/share/ccws/` に配置される。

```bash
~/.local/share/ccws/
├── issue-42/     # feature/issue-42 ブランチ
├── issue-43/     # feature/issue-43 ブランチ
└── hotfix-1/     # fix/urgent-bug ブランチ
```

ディスク使用量が気になる場合は `ccws rm --all` で一括削除。

## clone vs worktree の使い分け

Claude Code には2つのワークスペース分離方法がある:

| 方式 | ccws (clone) | EnterWorktree (CC標準) |
|------|-----------|----------------------|
| 仕組み | `git clone --depth 1` | `.claude/worktrees/` に git worktree |
| 容量 | 100-500MB（完全コピー） | 軽量（.git 共有） |
| 独立性 | 完全独立（別 .git） | .git 共有（lock 競合の可能性） |
| secrets | symlink で元リポと共有 | 元リポと完全共有 |
| 適用場面 | 長期並列開発、複数人/agent | 短期的な isolated 作業 |
| 削除 | `ccws rm` | セッション終了時に自動削除 |

### 推奨

- **並列開発（複数 agent）** → `ccws` を使う。完全独立で安全
- **単独の isolated 作業** → `EnterWorktree` で十分。軽量で手軽
- **CI/CD 連携** → `ccws` を使う。ディレクトリパスが予測可能

## コンテキスト制限への対策

長時間タスクでは Claude Code のコンテキストが圧縮され、初期の指示を忘れる可能性がある。

### 対策

1. **タスクを小さく分割**: 1 ワーカー = 1 PR = 短時間で完了
2. **creo-memories に中間記録**: 重要な決定・進捗を `remember()` で記録
3. **CLAUDE.md に指示を記載**: コンテキスト圧縮後も残る永続的な指示
4. **ccwire でリーダーに報告**: 定期的に `wire_send` で進捗報告 → リーダーが全体把握

### 推奨ワーカー作業時間

| 規模 | 目安 | コンテキスト圧縮リスク |
|------|------|---------------------|
| S | ~30分 | 低 |
| M | ~1時間 | 中（中間記録推奨） |
| L | ~2時間 | 高（分割を強く推奨） |
