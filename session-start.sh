#!/bin/bash
# SessionStart hook: GitButler状態をセッション開始時にコンテキスト注入
# but CLIが使えない場合は静かに失敗する

set -euo pipefail

# but コマンドの存在チェック
if ! command -v but &>/dev/null; then
  exit 0
fi

# GitButlerが初期化されているか確認
if ! but status &>/dev/null 2>&1; then
  exit 0
fi

# ブランチ状態を取得
STATUS=$(but status -f 2>/dev/null || echo "unable to get status")
BRANCH_LIST=$(but branch list 2>/dev/null || echo "unable to list branches")

# additionalContext として注入
cat <<EOF
{
  "additionalContext": "## GitButler Workspace State\n\nThis project uses GitButler (but CLI). Never use raw git commands for write operations.\n\n### Current Status\n\`\`\`\n${STATUS}\n\`\`\`\n\n### Active Branches\n\`\`\`\n${BRANCH_LIST}\n\`\`\`\n\nFor workflow details, read the gitbutler-workflow skill."
}
EOF
