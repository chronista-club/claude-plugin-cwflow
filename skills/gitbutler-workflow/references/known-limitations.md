# 既知の制限事項と未検証事項

このスキルの記述には「検証済み」と「理論上の想定」が混在している。
本ドキュメントでは、その区別を正直に記載する。

## ✅ 検証済み

### but CLI 単体の動作
- `but status`, `but branch`, `but commit`, `but absorb`, `but push`, `but publish`
  → 公式ドキュメントおよびCLIチュートリアルで確認済み
- `but undo`, `but oplog`, `but restore`
  → Operations Log機能として公式サポート
- `but mark` によるファイル→ブランチの固定割り当て
  → 公式ドキュメントに記載あり

### cc + GitButler Hooks方式
- Edit/Write時にhooksが発火する
  → GitButler公式ブログ（2025/02）で記載
- セッションIDベースのブランチ自動振り分け
  → 公式ドキュメントで動作原理が説明されている

### cc + tmux
- ccはtmux内で動作する（公式サポート）
- Agent Teamsのsplit-paneモードにtmuxが必要（公式ドキュメント明記）
- セッション永続化（detach/reattach）
- 別ペインの内容参照（tmux N.M 記法）

### hook-block-git.py
- 36テストケース全パス（本スキルに付属のテスト）
- PreToolUse の stdin JSON形式は公式ドキュメントで確認済み

---

## ⚠️ 未検証（理論上の想定）

### 複数ccセッションの同時書き込み

**想定**: 2-3個のccセッションが同一ワーキングディレクトリで同時に
ファイルを編集しても、GitButlerが正しくブランチに振り分ける。

**リスク**:
- GitButlerのファイルシステムwatcherがリアルタイムに追従できるか不明
- 2セッションが同じファイルの異なるhunkを同時に編集した場合の挙動
- `but absorb` が2セッションから同時に呼ばれた場合のロック機構の有無

**既知のGitHub Issue**:
- [#2671](https://github.com/gitbutlerapp/gitbutler/issues/2671):
  ファイル変更が意図しないブランチに入る問題（Desktop UIで報告）
- [#3136](https://github.com/gitbutlerapp/gitbutler/issues/3136):
  ロックされたファイルのdiscardができない問題

**緩和策**:
- `but mark` で事前にファイルパターンを割り当てる
- 同時セッションの変更ファイルが重ならないよう設計する
- 並行度を2に抑える（3はリスクが高い）

### Agent Teams + GitButler の併用

**想定**: ccのteammate機能で3 teammateがspawnされ、
各teammateの変更がGitButlerで自動的に別ブランチになる。

**リスク**:
- teammateが同じファイルに触れる可能性がある
- leadがタスク分配する際、ファイル重複を回避する保証はない
- teammateのセッションIDがGitButler Hooksに正しく伝播するか未確認

**緩和策**:
- leadへの指示で「ファイルが重ならないようにタスクを分割」と明示
- teammate数を2以下に抑える
- 事前に `but mark` でファイルパターンを設定

### XL分解のphase独立性

**想定**: XLタスクをstacked branchesで3-5 phaseに分解すると、
各phaseが独立してビルド・テスト・PR可能。

**リスク**:
- 実際のXLタスク（例: フレームワーク移行）では
  phase-1のAPI変更がphase-2以降の全コードに影響し、
  「独立してビルド可能」にならないケースがある
- stacked branchesの自動rebaseがコンフリクトする場合、
  phase-1のPR修正時にphase-2, 3が連鎖的に壊れる

**緩和策**:
- phase-1を「データ層」「型定義」等、影響範囲が明確なものにする
- 3段を超えるスタックは避ける（スキルの設計原則に記載済み）
- phase完了後は速やかにマージし、スタックを短く保つ

### スケジューリングのスループット見積もり

**想定**: 1日あたりの処理能力として
XS:8-10個, S:4-5個, M:2-3個, L:1個, XL:0.3-0.5個 を記載。

**実態**:
- これはccの処理速度 × 並行度 × 人間のレビュー速度から概算した値
- 実際のスループットはプロジェクトの複雑さ、テスト時間、
  CI/CDの速度、コードレビューの待ち時間に大きく依存
- 見積もりは楽観的な可能性がある

### hookの網羅性

**想定**: `git (checkout|switch|stash|...)` の正規表現で
主要なgit書き込みコマンドをブロック。

**限界**:
- `git` のエイリアス（`g`, `gco` 等のシェルエイリアス）は捕捉できない
- サブシェルやスクリプトファイル経由の `git` 呼び出し
  （例: `bash deploy.sh` 内の `git push`）は捕捉できない
- ccが `Bash` ツールではなく `Write` ツールでシェルスクリプトを書き、
  後で実行する場合は間に合わない

**緩和策**:
- CLAUDE.md と rules で「gitを使うな」と明示的に指示
- hookは最後の防衛線であり、唯一の手段ではない

---

## 📋 検証TODO

以下は実機で検証すべき項目のリスト：

- [ ] but CLI: 2つのターミナルから同時に `but commit` した場合の挙動
- [ ] but CLI: 2つのターミナルから同時に `but absorb` した場合の挙動
- [ ] but mark: CLI経由での設定と、並列セッションでの動作確認
- [ ] Agent Teams: teammateのセッションIDがhooksに渡るか
- [ ] Agent Teams: 3 teammate同時実行時のGitButlerブランチ振り分け
- [ ] stacked branches: 3段スタックでphase-1修正時のrebase動作
- [ ] Hooks + Plugin: 両方有効にした場合の干渉
- [ ] パフォーマンス: Virtual Branch 6本同時applyでの `but status` 応答時間
