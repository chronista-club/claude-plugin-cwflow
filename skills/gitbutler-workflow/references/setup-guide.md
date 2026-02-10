# GitButler Workflow スキル — 確実に読み込ませる設定ガイド

## なぜ多層防御が必要か

ccのスキル検出メカニズムには限界がある：

- **Skillsの自動検出**: descriptionのセマンティックマッチで発火 → **56%スキップ**（Vercel調査）
- **CLAUDE.md**: セッション開始時に1回読まれる → 常に存在するが注意が薄れる
- **Hooks**: 決定論的に毎回実行される → **100%保証**

よって「スキル単体」ではなく「CLAUDE.md + Skills + Hooks」の三層で確実性を担保する。

```
確実性のピラミッド:

  Hooks（100%実行）        ← 決定論的。ブランチ操作時に強制注入
  ────────────────
  CLAUDE.md（常時存在）    ← セッション開始時に読み込み。受動的
  ────────────────
  Skills（自動検出）       ← セマンティックマッチ。最も不確実
```

## ディレクトリ構成

```
your-project/
├── CLAUDE.md                              ← 層1: 常時コンテキスト
├── .claude/
│   ├── settings.json                      ← 層3: Hooks定義
│   ├── rules/
│   │   └── gitbutler.md                   ← 層1.5: ルール（常時読み込み）
│   └── skills/
│       └── gitbutler-workflow/            ← 層2: スキル本体
│           ├── SKILL.md
│           └── references/
│               ├── commands.md
│               ├── strategies.md
│               ├── claude-code-integration.md
│               ├── tmux-integration.md
│               └── scheduling.md
```

---

## 層1: CLAUDE.md

CLAUDE.mdはccの「憲法」。セッション開始時に必ず読まれる。
ここにスキルの存在と使用タイミングを明記する。

**重要**: CLAUDE.mdは簡潔に。詳細はスキルに委譲する。

```markdown
## Branch Strategy

このプロジェクトはGitButler（`but`コマンド）でバージョン管理する。
従来のgitコマンドは使わない。

ブランチ操作・並列開発・PR管理に関するタスクでは、
必ず `.claude/skills/gitbutler-workflow/SKILL.md` を読み込んでから作業すること。

具体的には以下の場面で必ずスキルを参照：
- ブランチの作成・切替・削除
- コミット・absorb・push・publish
- 並列セッションの開始・管理
- PR作成・レビュー
- stacked branchesの構成
- タスクのスケジューリング（XS〜XL混在タスクの並行処理）

### Quick Reference

- `but status -f` — 状態確認
- `but absorb` — 変更を最適コミットに吸収
- `but undo` — 直前の操作を取り消し
- `but push && but publish` — PR作成

### 禁止事項

- `git checkout`, `git switch`, `git stash` は使わない（GitButlerが壊れる）
- `git commit` の代わりに `but commit` を使う
- mainブランチへの直接コミット禁止
```

### なぜこう書くか

1. **「必ず〜を読み込んでから」** — 明示的にスキルファイルのパスを指定。ccはファイルパスが具体的だと読みに行く確率が格段に上がる
2. **具体的な場面の列挙** — セマンティックマッチの精度を上げる。「ブランチ」「PR」「並列」等のキーワードがccの判断材料になる
3. **Quick Reference** — CLAUDE.md内に最低限のコマンドを書くことで、スキルを読まなくても基本操作は回る
4. **禁止事項** — ccが素のgitコマンドに逃げるのを防止

---

## 層1.5: .claude/rules/

rulesはCLAUDE.mdと同等の扱いで常時読み込まれるが、
ファイル分離できるのでメンテしやすい。

```markdown
# .claude/rules/gitbutler.md

# GitButler Rules

## MUST
- Use `but` command instead of `git` for all version control operations
- Read `.claude/skills/gitbutler-workflow/SKILL.md` before any branch operation
- Run `but status` before starting work on any task
- Use `but absorb` instead of manual `git add` + `git commit`
- Keep virtual branches ≤ 6 simultaneously

## MUST NOT
- Never use `git checkout`, `git switch`, `git stash`, `git branch`
- Never commit directly to main
- Never run parallel tasks on overlapping file paths without `but mark`
- Never stack branches deeper than 3 levels

## SHOULD
- Batch XS/S tasks in a single session when possible
- Push and publish PRs same-day for XS/S/M tasks
- Decompose XL tasks into M-sized stacked branches
- Run `but pull` at the start of each work session
```

### CLAUDE.md vs rules の使い分け

| | CLAUDE.md | .claude/rules/ |
|---|---|---|
| 用途 | プロジェクト概要、アーキテクチャ | 具体的なDo/Don'tルール |
| 粒度 | 粗い | 細かい |
| 共有 | git commit | git commit |
| 読み込み | セッション開始時 | セッション開始時 |

両方に書く必要はない。CLAUDE.mdは「何を使うか」、rulesは「どう使うか」で分離。

---

## 層2: Skills（既存のスキル）

`.claude/skills/gitbutler-workflow/` にスキル本体を配置。

descriptionのトリガーワードを充実させることで自動検出の精度を上げる（が、これだけでは不十分）。

SKILL.mdのfrontmatterにある既存のdescriptionは十分トリガーリッチなので、そのまま使える。

---

## 層3: Hooks（決定論的保証）

Hooksは唯一**100%確実に実行される**メカニズム。
「CLAUDE.mdを読み飛ばした」「スキルを検出しなかった」場合でもhooksは発火する。

### 設計思想

- **PreToolUse（Bash）**: `git` コマンドをブロック → `but` を使わせる
- **PreToolUse（Edit|Write）**: ブランチ操作のコンテキスト注入（軽量）
- **Stop**: セッション終了時に `but status` を促す

**重要**: Hooksでスキル全体を注入するのは重すぎる（コンテキスト消費）。
Hooksは「ガードレール」として最小限のルールを注入し、
詳細はスキルに委譲するのが最適。

```json
// .claude/settings.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"$CLAUDE_TOOL_INPUT\" | grep -qE '^git (checkout|switch|stash|branch|add|commit|push|merge|rebase)' && echo '{\"decision\": \"block\", \"reason\": \"Use but (GitButler CLI) instead of git. Read .claude/skills/gitbutler-workflow/SKILL.md for details.\"}' || true",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

このhookは：
1. ccが `Bash` ツールを使おうとするたびに発火
2. コマンドが `git checkout/switch/stash/branch/add/commit/push/merge/rebase` なら**ブロック**
3. 「butを使え、スキルを読め」というメッセージを返す
4. git以外のbashコマンドはそのまま通過

### なぜEdit/Writeのhooksは入れないのか

Vercelのベストプラクティスとも一致するが、
**書き込み中のブロックはccの計画を混乱させる**。
ブロックするなら最終段階（commit時）が効果的。

### 高度な設定: セッション開始時のコンテキスト注入

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo '{\"feedback\": \"Reminder: This project uses GitButler. Use but commands, not git. For branch strategy details, read .claude/skills/gitbutler-workflow/SKILL.md\"}'",
            "timeout": 3
          }
        ]
      }
    ]
  }
}
```

これは**毎プロンプト**でリマインダーを注入する。
コンテキストを消費するのでfeedbackは短く。

---

## 推奨構成: 実用バランス

全部入りではなく、効果/コストのバランスで選ぶ：

### ミニマル構成（まずこれから）

```
✅ CLAUDE.md にスキルパスと基本ルールを記載
✅ .claude/skills/ にスキル本体を配置
✅ PreToolUse hook で git コマンドをブロック
```

これだけで90%以上のケースをカバーできる。

### フル構成（確実性を最大化）

```
✅ CLAUDE.md にスキルパスと基本ルールを記載
✅ .claude/rules/gitbutler.md に詳細ルール
✅ .claude/skills/ にスキル本体を配置
✅ PreToolUse hook で git コマンドをブロック
✅ UserPromptSubmit hook でリマインダー注入
```

### 過剰（やらなくていい）

```
❌ Edit/Write の hook で毎回スキル全文注入 → コンテキスト爆発
❌ PostToolUse で毎回 but status 実行 → 遅くなる
❌ スキル内容をCLAUDE.mdに全部コピー → 二重管理
```
