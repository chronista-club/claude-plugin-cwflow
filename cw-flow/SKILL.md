---
name: cw-flow
description: >
  Claude Workers（cwコマンド）を使った並行開発ワークフロー。
  Gitクローンベースのワークスペース分離で、複数のClaude Codeセッションを
  安全に並列実行するためのスキル。

  このスキルは以下のような場面で使う：
  - 「並行開発したい」「複数Issueを同時に進めたい」
  - 「cwコマンドの使い方」「ワーカー環境の作り方」
  - 「worker-files.kdlの設定方法」
  - 「Claude Codeで安全に並列セッションを走らせたい」
  - Issue単位の作業環境分離
---

# CW Flow — Claude Workers 並行開発ワークフロー

`cw`（Claude Workers）はGitクローンベースのワークスペースマネージャー。
メインリポジトリを汚さず、Issue単位で完全に独立した作業環境を作成する。

## コンセプト

```
メインリポ (~/repos/my-project)
│  ← 安定。直接作業しない or リーダーのみ
│
├── cw new issue-42 feature/issue-42
│   → ~/.cache/creo-workers/issue-42/    ← Agent A が作業
│
├── cw new issue-43 feature/issue-43
│   → ~/.cache/creo-workers/issue-43/    ← Agent B が作業
│
└── cw new hotfix-1 fix/urgent-bug
    → ~/.cache/creo-workers/hotfix-1/    ← Agent C が作業
```

各ワーカーは:
- **完全なgitクローン** — ブランチ、コミット、pushが完全に独立
- **secretsはsymlink共有** — `.env`, `.mcp.json` 等は元リポと同期
- **使い捨て** — 作業完了・マージ後に `cw rm` で削除

## コマンドリファレンス

| コマンド | 説明 |
|---|---|
| `cw new <name> <branch>` | ワーカー環境を作成（clone + symlink + setup） |
| `cw ls` | 全ワーカー一覧（名前、ブランチ、パス） |
| `cw path <name>` | ワーカーのパスを出力 |
| `cw rm <name>` | ワーカーを削除 |
| `cw rm --all` | 全ワーカーを削除 |

### 使用例

```bash
# Issue単位でワーカーを作成
cw new issue-42 feature/issue-42

# パスを取得（スクリプト連携用）
cd $(cw path issue-42)

# そのディレクトリでClaude Codeセッションを起動
cd $(cw path issue-42) && claude

# 作業完了後に削除
cw rm issue-42
```

## worker-files.kdl 設定

各プロジェクトの `.claude/worker-files.kdl` に、ワーカー環境へ配置するファイルを定義する。
`cw` はクローン後にこのファイルを読み、シンボリックリンクやコピーを自動で配置する。

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
cd $(cw path issue-42) && claude

# ペイン2: Issue #43
cd $(cw path issue-43) && claude

# ペイン3: hotfix
cd $(cw path hotfix-1) && claude
```

### パターン2: Leader-Worker（Claude Code Teams）

リーダーAgentがワーカーを作成し、Taskツールでサブエージェントを並列起動。

```
Leader (メインリポ)
├── cw new worker-a feature/issue-42
├── cw new worker-b feature/issue-43
├── TeamCreate → TaskCreate × 2
├── Task(CWD=worker-a) → Agent A 起動
├── Task(CWD=worker-b) → Agent B 起動
└── TaskList で進捗監視 → PR作成
```

### パターン3: Issue消化マラソン

GitHub Issuesから直接ワーカーを作成して一気に消化。

```bash
# nextラベルのIssueを取得
gh issue list -l next --json number,title

# 各IssueをワーカーとClaude Codeで処理
cw new issue-42 feature/issue-42
cd $(cw path issue-42) && claude "Issue #42 を実装して"
```

## PRフロー

各ワーカーは独立したgitクローンなので、通常のgit + gh操作でPRを作成。

```bash
cd $(cw path issue-42)

# 作業内容をコミット・プッシュ
git add . && git commit -m "feat: ..."
git push -u origin feature/issue-42

# PR作成
gh pr create --title "..." --body "..."
```

マージ後はワーカーを削除:
```bash
cw rm issue-42
```

## 内部動作

`cw new <name> <branch>` の実行手順:

1. カレントディレクトリのgitリポを検出（`git rev-parse --show-toplevel`）
2. `origin` URLを取得（`git remote get-url origin`）
3. `~/.cache/creo-workers/<name>/` に shallow clone（`--depth 1`）
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

ワーカー環境は `~/.cache/creo-workers/` に配置される。

```bash
~/.cache/creo-workers/
├── issue-42/     # feature/issue-42 ブランチ
├── issue-43/     # feature/issue-43 ブランチ
└── hotfix-1/     # fix/urgent-bug ブランチ
```

ディスク使用量が気になる場合は `cw rm --all` で一括削除。
