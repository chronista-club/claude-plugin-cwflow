# tmux × Claude Code × GitButler 統合ガイド

## Table of Contents

1. [アーキテクチャ概要](#アーキテクチャ概要)
2. [基本セットアップ](#基本セットアップ)
3. [Agent Teams（teammate機能）](#agent-teams)
4. [別ペイン参照パターン](#別ペイン参照パターン)
5. [セッション永続化と運用](#セッション永続化と運用)
6. [tmux設定の推奨](#tmux設定の推奨)
7. [サードパーティツール](#サードパーティツール)
8. [トラブルシューティング](#トラブルシューティング)

---

## アーキテクチャ概要

3層構成で並列開発を実現する：

```
┌─────────────────────────────────────────────┐
│ tmux                                         │
│  セッション永続化 / ペイン管理 / 画面分割     │
├─────────────────────────────────────────────┤
│ Claude Code                                  │
│  Agent Teams / Subagents / タスク実行         │
├─────────────────────────────────────────────┤
│ GitButler                                    │
│  Virtual Branches / 自動ブランチ振分 / Undo   │
└─────────────────────────────────────────────┘
```

- **tmux**: セッション管理とUI層。永続化とマルチペイン表示を担当
- **Claude Code**: タスク実行層。Agent TeamsまたはSubagentsで並列作業
- **GitButler**: バージョン管理層。ccセッションごとの変更を自動でブランチに分離

## 基本セットアップ

### 前提

```bash
# tmuxインストール（未インストールの場合）
brew install tmux     # macOS
sudo apt install tmux # Ubuntu/Debian

# 確認
tmux -V
```

### ccをtmux内で起動する基本パターン

```bash
# 新規セッション作成 + cc起動
tmux new-session -s myproject -c ~/project
cc "実装を開始"

# detach: Ctrl-b d（ccは走り続ける）
# reattach:
tmux attach -t myproject
```

### 手動マルチペイン構成

```bash
# セッション作成
tmux new-session -s dev -c ~/project

# ペイン分割
tmux split-window -h    # 水平分割
tmux split-window -v    # 垂直分割

# 各ペインでcc起動（ペイン切替: Ctrl-b o）
# pane 0: cc "feat: 認証"
# pane 1: cc "fix: メモリリーク"
# pane 2: but status --watch（状態監視）
```

## Agent Teams

ccのteammate機能はtmux上で最も効果を発揮する。leadが複数teammateにタスクを委譲し、
各teammateが独立したtmuxペインで動作する。

### 設定

```json
// .claude/settings.json or ~/.claude/settings.json
{
  "teammateMode": "tmux"
}
```

モード一覧：
- `"auto"` — tmux内ならsplit-pane、それ以外ならin-process（デフォルト）
- `"tmux"` — 常にsplit-pane。tmux未検出時はエラー
- `"in-process"` — 常にメインターミナル内。Shift+Up/Downで切替

### Agent Teams + GitButlerの動作フロー

```
ユーザー → cc lead に複合タスクを指示
  │
  ├── cc lead: タスクを分解
  │   ├── teammate-1 (tmux pane 1): feat/auth
  │   ├── teammate-2 (tmux pane 2): fix/memory-leak
  │   └── teammate-3 (tmux pane 3): refactor/error-handling
  │
  ├── GitButler Hooks: 各teammateのEdit/Writeを検知
  │   → セッションIDでブランチ自動振り分け
  │
  └── 完了後: but status で3つのブランチが整理された状態
```

### teammateへの介入

split-paneモードでは、teammateのペインをクリックして直接操作可能：

- ペインをクリック → そのteammateのセッションに入る
- 追加指示を送る → teammateが受け取って続行
- Ctrl-b o → ペイン間を順に移動

in-processモードでは：
- Shift+Up/Down → teammate選択
- 入力 → 選択中のteammateにメッセージ送信

### タスク管理

Agent Teamsは共有タスクリストで協調する：

- **lead**: タスク作成・割り当て
- **teammate**: 自動的に未割当タスクをclaim
- **依存関係**: タスクAが完了するまでタスクBはpending

GitButlerのstacked branchesとの相性が良い。
タスクの依存関係 = ブランチのスタック関係として表現できる。

### 権限リクエスト

teammateが権限を必要とする操作（ファイル削除、外部コマンド実行等）を行う場合、
leadに確認が上がる。事前に許可設定をしておくと中断が減る：

```json
// .claude/settings.json
{
  "permissions": {
    "allow": ["Edit", "Write", "Bash(but *)"]
  }
}
```

## 別ペイン参照パターン

ccはtmuxの別ペインの内容を読み取れる。これを活用したパターン：

### サーバーログ参照

```bash
# pane 0: 開発サーバー
cargo run

# pane 1: cc
cc "tmux 0.0のサーバーログを見て、エラーを修正して"
```

ccは`tmux 0.0`（ウィンドウ0、ペイン0）のバッファを読み、
エラーメッセージに基づいてコードを修正できる。

### テスト結果参照

```bash
# pane 0: テストウォッチ
cargo watch -x test

# pane 1: cc
cc "tmux 0.0のテスト結果を確認して、失敗しているテストを修正して"
```

### GitButler状態の参照

```bash
# pane 0: but status を定期実行
watch -n 5 but status -f

# pane 1: cc（作業中）
# → ccが必要に応じてpane 0のGitButler状態を確認
```

## セッション永続化と運用

### detach/reattachパターン

```bash
# 長時間タスクを開始
tmux new-session -s refactor -c ~/project
cc "全テストファイルをVitest v2に移行して"

# detach（ラップトップを閉じてもOK）
# Ctrl-b d

# 後で戻る
tmux attach -t refactor
# → ccの作業状況がそのまま表示される
```

### リモート開発

```bash
# リモートマシンにSSH
ssh dev-server

# tmuxセッションにattach
tmux attach -t project
# → 以前detachしたccセッションがそのまま
```

### セッション一覧と管理

```bash
tmux ls                     # 全セッション一覧
tmux kill-session -t old    # 不要なセッション削除
```

## tmux設定の推奨

### GitButler + cc向けの最小設定

```bash
# ~/.tmux.conf

# マウスサポート（ペインクリックでteammate切替に便利）
set -g mouse on

# ペイン分割のキーバインド
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"

# ペイン間移動（vim風）
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

# 履歴バッファを大きく（ccの長い出力に対応）
set -g history-limit 50000

# 256色サポート
set -g default-terminal "screen-256color"
set -sa terminal-overrides ",xterm-256color:RGB"

# ステータスバーにGitButler情報を表示（オプション）
set -g status-right '#(but status -j 2>/dev/null | jq -r ".branches | length" 2>/dev/null || echo "?") branches'
```

### 推奨レイアウト

```
┌──────────────────────┬──────────────────────┐
│                      │                      │
│   cc session 1       │   cc session 2       │
│   (feat/auth)        │   (fix/leak)         │
│                      │                      │
├──────────────────────┴──────────────────────┤
│                                              │
│   but status -f (監視) or サーバーログ        │
│                                              │
└──────────────────────────────────────────────┘
```

作成コマンド：
```bash
tmux new-session -s dev -c ~/project
tmux split-window -h -c ~/project
tmux split-window -v -t 0 -c ~/project  # 下部に監視ペイン
tmux select-pane -t 0
```

## サードパーティツール

### tmux-cli（cc用tmux自動操作）

ccがtmuxを操作する際のレースコンディションを解決するラッパー。
素のtmux send-keysだとテキストとEnterが同時送信されて失敗することがあるが、
tmux-cliは自動的に遅延を挿入して信頼性を確保する。

```bash
# インストール
pip install tmux-cli

# CLAUDE.mdに追記
# "tmuxペイン操作時は tmux-cli send を使うこと"
```

用途：
- ccからインタラクティブなスクリプトを実行・操作
- ccからデバッガ（pdb, gdb）を制御
- cc間のコミュニケーション（cc-to-cc）

### claude-tmux（セッション管理TUI）

Rust + Ratatui製。複数ccセッションの一元管理。

```bash
# インストール
cargo install claude-tmux

# 起動（tmux内で Ctrl-b Ctrl-c）
# → 全ccセッションの一覧表示
```

機能：
- ccセッションの検出・ステータス表示
- セッションの作成・kill・リネーム
- 最終出力のライブプレビュー（ANSI色対応）
- ファジーフィルタリング
- git worktree / PR連携

## トラブルシューティング

### split-paneモードが動かない

ccがtmuxを検出できていない可能性。確認：

```bash
echo $TMUX  # 値があればtmux内
```

手動で設定：
```json
{
  "teammateMode": "tmux"
}
```

注意：VS Code統合ターミナル、Windows Terminal、Ghosttyではsplit-paneモード非対応。

### teammateのペインが残る

ccセッション終了後にtmuxペインが残ることがある：

```bash
# 手動クリーンアップ
tmux kill-pane -t <pane-id>
```

### ccの出力が見切れる

履歴バッファが小さい場合：

```bash
# ~/.tmux.conf
set -g history-limit 50000
```

コピーモードでスクロール：Ctrl-b [ → ページアップ/ダウンで閲覧

### GitButler HooksとAgent Teamsの併用

Hooks方式とAgent Teamsは問題なく併用可能。
各teammateのEdit/Writeそれぞれに対してhooksが発火し、
セッションIDに基づいてGitButlerが正しいブランチに振り分ける。

Plugin方式の場合も同様に動作する。MCP方式の場合は
各teammateが明示的に`gitbutler_update_branches`を呼ぶ必要がある。
