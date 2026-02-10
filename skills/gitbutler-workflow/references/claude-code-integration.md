# Claude Code × GitButler 連携詳細

## Table of Contents

1. [セットアップ](#セットアップ)
2. [Hooks方式の詳細](#hooks方式の詳細)
3. [Plugin方式の詳細](#plugin方式の詳細)
4. [MCP方式の詳細](#mcp方式の詳細)
5. [並列セッションの運用](#並列セッションの運用)
6. [トラブルシューティング](#トラブルシューティング)

---

## セットアップ

### 前提条件

1. GitButler CLI がインストール済み
   ```bash
   brew install gitbutler
   # or GitButler Desktop → General Settings → "Install CLI"
   but --version
   ```

2. プロジェクトがGitButlerで初期化済み
   ```bash
   cd /path/to/project
   but init
   # or 初回 `but` 実行で自動セットアップ
   ```

3. Claude Code がインストール済み
   ```bash
   claude --version
   ```

### GitButler Cloud認証（PR連携に必要）

```bash
but auth login
# ブラウザが開いてGitHub/GitLab認証
```

## Hooks方式の詳細

### 動作原理

Claude CodeのHooksシステムを利用。ファイル編集の前後でGitButlerに通知し、
セッションごとの変更を自動でブランチに振り分ける。

### フック実行フロー

```
Claude Code: ファイル編集を計画
  → PreToolUse: `but claude pre-tool`
    → GitButlerにセッション情報を送信
    → 現在の状態をスナップショット

Claude Code: ファイル編集を実行
  → PostToolUse: `but claude post-tool`
    → 変更をGitButlerに通知
    → セッションIDに基づいてブランチに自動割当

Claude Code: セッション終了
  → Stop: `but claude stop`
    → プロンプトに基づいたコミットメッセージ生成
    → 自動コミット
    → ブランチ更新
```

### 設定ファイルの優先順位

1. `.claude/settings.local.json` — ローカル（gitignore対象）
2. `.claude/settings.json` — プロジェクト固有（チームで共有可）
3. `~/.claude/settings.json` — ユーザーグローバル

推奨：個人プロジェクトは`~/.claude/settings.json`に一括設定。
チームプロジェクトは`.claude/settings.json`に設定して共有。

### 設定テンプレート

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          { "type": "command", "command": "but claude pre-tool" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          { "type": "command", "command": "but claude post-tool" }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "but claude stop" }
        ]
      }
    ]
  }
}
```

## Plugin方式の詳細

### インストール

Claude Code内で：
```
/plugin marketplace add gitbutlerapp/claude
/plugin install gitbutler
```

### 特徴

- Hooks方式より粒度が粗い（タスク完了時にまとめてコミット）
- 将来的に `/absorb`, `/squash` 等のslash commandが追加予定
- 最もセットアップが簡単

## MCP方式の詳細

### セットアップ

```bash
# Claude Code
claude mcp add gitbutler but mcp

# 確認
claude mcp list
# gitbutler: but mcp
```

### 利用可能なツール

- `gitbutler_update_branches` — 変更をGitButlerに送信しブランチ更新

### 自動実行の設定

CLAUDE.mdまたはメモリに追記：
```markdown
## Development Workflow
- When you're done with a task where code was created or files edited,
  run the gitbutler update_branches MCP tool.
```

### Cursor / VSCodeとの併用

```json
// .cursor/mcp.json or VSCode MCP settings
{
  "mcp": {
    "servers": {
      "gitbutler-mcp": {
        "type": "stdio",
        "command": "but",
        "args": ["mcp"]
      }
    }
  }
}
```

## 並列セッションの運用

並列実行には2つのアプローチがある。詳細は `references/tmux-integration.md` も参照。

### 方式A: 手動マルチペイン

tmuxで複数ペインを開き、各ペインで独立したccセッションを走らせる：

```bash
# セッション作成
tmux new-session -d -s dev

# 3ペインレイアウト
tmux split-window -h
tmux split-window -v

# 各ペインでcc起動
tmux send-keys -t dev:0.0 'cd ~/project && cc "feat: implement auth"' Enter
tmux send-keys -t dev:0.1 'cd ~/project && cc "fix: memory leak in api"' Enter
tmux send-keys -t dev:0.2 'cd ~/project && cc "refactor: error handling"' Enter
```

### 方式B: Agent Teams（cc teammate機能）

ccのteammate機能を使い、leadが自動的にタスクを分配する方式。
tmux上ではsplit-paneで各teammateが表示される。

```json
// .claude/settings.json
{
  "teammateMode": "tmux"
}
```

```bash
tmux new-session -s dev -c ~/project
cc "以下を並列で実装: 1) JWT認証 2) メモリリーク修正 3) エラーハンドリング統一"
# → cc leadが自動でteammateをspawn → 各tmuxペインに表示
```

Agent Teams + GitButler Hooksの併用は問題なし。各teammateのEdit/Writeに
hooksが発火し、セッションIDでGitButlerが正しいブランチに振り分ける。

### 並列時の注意点

1. **同一ファイルの競合**: 2つのセッションが同じファイルを編集すると、
   GitButlerが「どちらのブランチ？」と判断に迷う場合がある。
   → `but mark` でファイルパターンを事前に割り当てるか、
   セッションの責務を明確に分離する

2. **ブランチ自動生成**: Hooks/Plugin方式では、
   セッション開始時に自動でブランチが作られる。
   ブランチ名はセッションの内容に基づいて生成される

3. **セッション終了後の整理**: 全セッション終了後に
   `but status -f` で全体を確認し、必要なら手動で調整

### GitButler Desktop との併用

CLIで作業しつつ、GitButler Desktopで視覚的に確認するのが理想的：

- Desktop: ブランチの全体像、ファイル割り当ての確認
- CLI: 実際のコミット、push、PR操作
- Agents Tab: Claude Codeセッションの状態確認

## トラブルシューティング

### 「Stack is uninitialised」エラー

GitButlerの初期化が不完全。
```bash
but init
# または
but  # 初回実行で再セットアップ
```

### ファイルが間違ったブランチに割り当てられた

```bash
but rub <file-id> <correct-branch>  # 正しいブランチに移動
```

### Claude Codeがgit commitを直接実行してしまう

CLAUDE.mdのルールが不足。以下を追記：
```markdown
## IMPORTANT
- NEVER use `git commit`, `git add`, or `git push`.
- All version control is managed by GitButler (`but` commands).
```

### rebase後のコンフリクト

GitButlerではコンフリクトは「解決待ち」としてマークされ、
作業は続行できる。パニックにならなくてOK。

```bash
but status              # conflictedなコミットを確認
# エディタでコンフリクト解決
but absorb              # 解決した変更を自動で正しいコミットに
```

### GitButlerモードから外れた

`git checkout` を直接実行するとGitButlerモードから外れる。

```bash
but switch-back         # GitButlerモードに復帰
```

### Operations Logが肥大化

通常は問題にならないが、気になる場合：
```bash
but oplog -n 5          # 最新5件だけ確認
```

古いスナップショットは自動的にガベージコレクションされる。
