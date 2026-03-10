#!/bin/bash
# SessionStart hook: Claude Code Workspaceの状態をセッション開始時にコンテキスト注入
# ccws CLIが使えない場合は静かに終了する

set -euo pipefail

# ccws コマンドの存在チェック
CCWS_CMD=""
if command -v ccws &>/dev/null; then
  CCWS_CMD="ccws"
elif [ -x /opt/homebrew/bin/ccws ]; then
  CCWS_CMD="/opt/homebrew/bin/ccws"
elif [ -x "$HOME/.cargo/bin/ccws" ]; then
  CCWS_CMD="$HOME/.cargo/bin/ccws"
else
  exit 0
fi

# ワーカー一覧を取得
WORKER_LIST=$($CCWS_CMD ls 2>/dev/null || echo "")

# ワーカーが0件なら何もしない
if [ -z "$WORKER_LIST" ]; then
  exit 0
fi

# 現在のディレクトリがワーカー環境内かどうか判定
CURRENT_DIR=$(pwd)
IN_WORKER=""
if echo "$CURRENT_DIR" | grep -q "/.local/share/ccws/"; then
  IN_WORKER="true"
fi

# コンテキストを構築
if [ -n "$IN_WORKER" ]; then
  CONTEXT="## Claude Code Workspace 環境\n\n現在ワーカー環境内で作業中です。\nパス: ${CURRENT_DIR}\n\n### 全ワーカー一覧\n\`\`\`\n${WORKER_LIST}\n\`\`\`\n\nワーカーの管理: ccws ls / ccws rm <name>"
else
  CONTEXT="## Claude Code Workspace 環境\n\nアクティブなワーカーがあります。\n\n### ワーカー一覧\n\`\`\`\n${WORKER_LIST}\n\`\`\`\n\nワーカーの管理: ccws ls / ccws new <name> <branch> / ccws rm <name>"
fi

cat <<EOF
{
  "additionalContext": "${CONTEXT}"
}
EOF
