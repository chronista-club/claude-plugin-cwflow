# GitButler CLI コマンド詳細リファレンス

## Table of Contents

1. [but status](#but-status)
2. [but branch](#but-branch)
3. [but commit](#but-commit)
4. [but absorb](#but-absorb)
5. [but rub](#but-rub)
6. [but push / publish](#but-push--publish)
7. [but oplog / undo / restore](#but-oplog--undo--restore)
8. [but config](#but-config)
9. [but pull](#but-pull)
10. [but diff](#but-diff)
11. [but mark / unmark](#but-mark--unmark)

---

## but status

ワークスペースの全体像を表示する。デフォルトコマンド（`but`だけで実行される）。

```bash
but status            # ブランチ + 未コミットファイル
but status -f         # ファイル変更も含む詳細表示
but status --files    # -f と同じ
but status -j         # JSON出力
```

出力の読み方：
- ショートコード（例: `u1`, `h4`）でブランチやファイルを参照可能
- `●` はコミット、`├╯` はブランチの接続点
- `(common base)` はtargetブランチとの分岐点

## but branch

### new — ブランチ作成

```bash
but branch new my-feature         # 並行ブランチ
but branch new -a base-branch dep # スタックブランチ（base-branchの上に）
```

`-a`/`--anchor`には、ブランチ名またはコミットIDを指定。

### list — 一覧

```bash
but branch list                 # active + 最近の20件
but branch list --all           # 全ブランチ
but branch list --local         # ローカルのみ
but branch list --remote        # リモートのみ
but branch list --review        # PR/MR情報付き（遅い）
but branch list --no-check      # マージチェックをスキップ（速い）
but branch list feature         # 名前フィルタ
```

### delete — 削除

```bash
but branch delete my-feature       # 削除（未pushコミットがあれば確認）
but branch delete my-feature -f    # 強制削除
```

### apply / unapply — ワークスペース管理

```bash
but apply my-feature      # ブランチをワークスペースに適用
but unapply my-feature    # ワークスペースから解除（コミットは保持）
```

## but commit

```bash
but commit -m "feat: add auth"                # 全未割当変更をコミット
but commit -m "fix: typo" -b my-branch        # 指定ブランチに
but commit --files AB -m "partial"            # ファイルID ABのみ
but commit --ai                               # AIメッセージ生成
but commit --ai -b my-branch                  # AI + ブランチ指定
but commit empty --before <commit-id>         # 空コミット挿入
but commit empty --after <commit-id>          # 空コミット挿入（後に）
but commit --file msg.txt                     # ファイルからメッセージ
```

複数ブランチが存在し、ブランチを指定しない場合はインタラクティブにプロンプトされる。

## but absorb

未コミットの変更を、各hunkが最も論理的に属するコミットに自動吸収する。
GitButlerの最も強力な機能の一つ。

```bash
but absorb           # 全未コミット変更を自動吸収
but absorb -j        # JSON出力で吸収先を確認
```

動作：各hunkの変更を分析し、過去のコミット履歴から「このhunkが最も自然に入るべきコミット」を判定して自動的にamendする。上位コミットは自動rebase。

## but rub

2つのエンティティを「こすり合わせる」ことで結合操作を行う。
amend、squash、ファイルのブランチ間移動などの統一インターフェース。

```bash
but rub <file-id> <commit-id>    # ファイルをコミットにamend
but rub <file-id> <branch-id>    # ファイルをブランチに割り当て
but rub <commit> <commit>        # コミット同士をsquash
```

ショートID（`but status`や`but diff`で表示される2文字コード）が使える。

## but push / publish

### push

```bash
but push                    # 全applied branchをpush
but push my-branch          # 特定ブランチをpush
but push --dry-run          # プレビュー
but push --force             # 強制push（rebase後など）
```

### publish

PR/MRの作成・更新。

```bash
but publish                 # 未公開ブランチのPR/MRを作成
but publish my-branch       # 特定ブランチ
```

PRが既にあるブランチは自動更新。ないブランチはインタラクティブに作成。

## but oplog / undo / restore

### oplog — 操作履歴

```bash
but oplog                   # 操作履歴一覧
but oplog -n 20             # 最新20件
```

### undo — 直前操作の取消

```bash
but undo                    # 1つ前のスナップショットに復元
```

### restore — 特定スナップショットに復元

```bash
but restore <snapshot-id>   # 指定スナップショットに復元
```

### snapshot — 手動スナップショット

```bash
but snapshot                    # スナップショット作成
but snapshot -m "before merge"  # メッセージ付き
```

## but config

```bash
but config                      # 全設定表示
but config user                 # ユーザー設定
but config forge                # Forge設定
but config target               # ターゲットブランチ設定
but config target main          # ターゲットブランチを変更
but config metrics              # メトリクス設定
but config ui                   # UI設定
```

## but pull

upstream変更を取り込み、ローカルブランチをrebase。

```bash
but pull                # 取り込み + rebase
but pull --check        # 何が起こるかプレビュー
```

`--check`は非常に便利。rebase後の状態を事前確認できる。
コンフリクトするブランチがある場合も事前に表示される。

## but diff

ファイル変更、ブランチ、コミットのdiffプレビュー。

```bash
but diff                    # 全未コミット変更
but diff <file-id>          # 特定ファイル
but diff <branch>           # ブランチの全diff
but diff <commit>           # コミットのdiff
```

## but mark / unmark

ファイルパターンの自動割り当てルール。

```bash
but mark <file-id> <branch>     # ファイルを常にこのブランチに割り当て
but unmark                       # 全マーク解除
```

特定のファイルパスが常に特定ブランチに属すべき場合に有用。
例：`tests/auth/*` は常に `feature-auth` ブランチへ。
