#!/bin/bash
# SessionStart hook: Claude Workersの状態をセッション開始時にコンテキスト注入
# cw CLIが使えない場合は静かに終了する

set -euo pipefail

# cw コマンドの存在チェック
CW_CMD=""
if command -v cw &>/dev/null; then
  CW_CMD="cw"
elif [ -x /opt/homebrew/bin/cw ]; then
  CW_CMD="/opt/homebrew/bin/cw"
elif [ -x "$HOME/.cargo/bin/cw" ]; then
  CW_CMD="$HOME/.cargo/bin/cw"
else
  exit 0
fi

# ワーカー一覧を取得
WORKER_LIST=$($CW_CMD ls 2>/dev/null || echo "")

# ワーカーが0件なら何もしない
if [ -z "$WORKER_LIST" ]; then
  exit 0
fi

# 現在のディレクトリがワーカー環境内かどうか判定
CURRENT_DIR=$(pwd)
IN_WORKER=""
if echo "$CURRENT_DIR" | grep -q "creo-workers"; then
  IN_WORKER="true"
fi

# コンテキストを構築
if [ -n "$IN_WORKER" ]; then
  CONTEXT="## Claude Workers 環境\n\n現在ワーカー環境内で作業中です。\nパス: ${CURRENT_DIR}\n\n### 全ワーカー一覧\n\`\`\`\n${WORKER_LIST}\n\`\`\`\n\nワーカーの管理: cw ls / cw rm <name>"
else
  CONTEXT="## Claude Workers 環境\n\nアクティブなワーカーがあります。\n\n### ワーカー一覧\n\`\`\`\n${WORKER_LIST}\n\`\`\`\n\nワーカーの管理: cw ls / cw new <name> <branch> / cw rm <name>"
fi

cat <<EOF
{
  "additionalContext": "${CONTEXT}"
}
EOF
