# ブランチ戦略パターン詳細

## Table of Contents

1. [戦略選択フロー](#戦略選択フロー)
2. [Feature-Parallel 詳細](#feature-parallel-詳細)
3. [Stacked-Feature 詳細](#stacked-feature-詳細)
4. [Hybrid 詳細](#hybrid-詳細)
5. [リリース管理パターン](#リリース管理パターン)
6. [移行ガイド](#移行ガイド)

---

## 戦略選択フロー

プロジェクトの状況に応じて最適なパターンを選択する：

```
機能間に依存関係がある？
├── No → Feature-Parallel
└── Yes → 全部が依存チェーン？
    ├── Yes → Stacked-Feature
    └── No → Hybrid
```

追加の判断基準：
- **リポジトリのサイズ**: 大規模モノレポ → Hybrid（モジュール境界で並行、モジュール内でスタック）
- **PRレビュー体制**: セルフマージ → Feature-Parallel が最も効率的。レビュー待ちがある → Stacked-Feature でレビュー依存を明示
- **Claude Codeセッション数**: 1-2並列 → どれでもOK。3以上 → Feature-Parallel が安全

## Feature-Parallel 詳細

### いつ使う

- 独立した機能・修正を複数同時に進めたい
- 各ブランチのマージ順序を問わない
- Claude Codeセッションごとに完全に独立した作業をさせたい

### ブランチ命名規則

```
<type>/<short-description>
```

typeの例：
- `feat/` — 新機能
- `fix/` — バグ修正
- `refactor/` — リファクタリング
- `perf/` — パフォーマンス改善
- `docs/` — ドキュメント
- `test/` — テスト追加・修正
- `chore/` — ビルド・CI・依存関係

### 並列数の目安

- **2-3並列**: 快適。GitButlerの自動振り分けも正確
- **4-5並列**: 動作するが、ファイル変更が重なると手動割り当てが増える
- **6以上**: `but mark`でファイルパターンを事前設定しておくことを強く推奨

### マージ戦略

各ブランチが独立なので、マージ順序は自由。ただし：

1. `but pull` で base を更新してから push
2. CI が通ったら `but publish` で PR 作成
3. マージ後は `but pull` で base を再更新
4. マージ済みブランチは自動で消える（or `but branch delete`）

## Stacked-Feature 詳細

### いつ使う

- 機能実装に明確な層がある（データ層 → API層 → UI層）
- 下位の変更が上位に影響する
- PRを小さく保ちつつ、論理的な順序でレビューしたい

### スタック作成の実例

```bash
# 1. データ層
but branch new feat/data-model
# Claude Code: "UserモデルとPostモデルを定義"
but commit --ai

# 2. API層（データ層の上に）
but branch new -a feat/data-model feat/api-endpoints
# Claude Code: "User CRUDのRESTful APIを実装"
but commit --ai

# 3. UI層（API層の上に）
but branch new -a feat/api-endpoints feat/ui-components
# Claude Code: "ユーザー管理画面のReactコンポーネントを実装"
but commit --ai
```

### 底のコミットを修正する場合

スタックの最大の恩恵。底の変更を修正しても上が自動restackされる：

```bash
# data-modelのコミットを修正したい
# 普通に変更して...
but absorb  # 自動で正しいコミットに吸収
# → feat/api-endpoints と feat/ui-components は自動rebase
```

コンフリクトが発生した場合、GitButlerはコミットを「conflicted」としてマークする。
解消はいつでも、どの順序でもOK。

### PRフロー

```bash
# 下から順にpublish
but push
but publish
# → feat/data-model のPRが先に作成される
# → feat/api-endpoints のPRはfeat/data-modelがbaseになる
# → レビュアーは各層を独立してレビュー可能
```

GitHub上では各PRが前のPRのマージを待つ形になる。
底のPRがマージされると、次のPRのbaseが自動更新される。

## Hybrid 詳細

### いつ使う

- 実プロジェクトのほとんどがこのパターンに該当
- 独立した修正とスタックが混在する
- 緊急hotfixと計画的な機能開発が並行する

### 典型的な構成例

```
origin/main (base)
├── fix/urgent-security-patch     （独立・緊急）
├── feat/notification-system      （独立・通常）
└── feat/user-profile             （スタックの根）
    └── feat/profile-api          （user-profileに依存）
        └── feat/profile-ui       （profile-apiに依存）
```

### 運用のコツ

1. **緊急修正は常に並行ブランチ** — スタックの中に入れない
2. **スタックは同じ「機能群」で閉じる** — 異なる機能をスタックしない
3. **並行ブランチの数 + スタック数の合計を意識** — 全体で5-6が管理限界の目安

## リリース管理パターン

### Trunk-Based（推奨）

GitButlerはtrunk-basedと相性が良い。mainに直接マージし、タグでリリース管理。

```bash
# 各ブランチをmainにマージ
but pull
but publish
# マージ後
git tag v1.2.0
git push --tags
```

### Release Branch（必要な場合のみ）

複数バージョンの同時メンテナンスが必要な場合：

```bash
# release branchをGit側で作成（GitButlerの外）
git checkout -b release/1.x main
git push origin release/1.x

# GitButlerのtargetを切り替え
but config target release/1.x

# この上でhotfix作業
but branch new fix/backport-security
```

## 移行ガイド

### git-flow からの移行

| git-flow | GitButler |
|---|---|
| `develop` branch | 不要。mainに直接 |
| `feature/*` branches | Virtual Branches（並行） |
| `release/*` branches | `but config target` で切替 or 不要 |
| `hotfix/*` branches | 並行ブランチで即対応 |
| `git flow feature start` | `but branch new feat/xxx` |
| `git flow feature finish` | `but push` → `but publish` → マージ |

### GitHub Flow からの移行

ほぼ同じ考え方。違いは並列作業が遥かに楽になること：

| GitHub Flow | GitButler |
|---|---|
| `git checkout -b feature` | `but branch new feature` |
| `git stash` → `git checkout` | 不要（Virtual Branches） |
| `git rebase -i` | `but absorb` / `but rub` |
| `gh pr create` | `but publish` |

### 注意事項

- GitButlerは`gitbutler/workspace`という特殊ブランチ上で動作する。`git checkout`で他ブランチに切り替えるとGitButlerモードから外れる
- `but switch-back`でGitButlerモードに戻れる
- GitButler管理下では`git commit`を直接使わない
