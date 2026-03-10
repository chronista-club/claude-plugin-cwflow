#!/bin/bash
# PreToolUse hook: Block AskUserQuestion in worker environments
# Workers should use ccwire (wire_send) to communicate with the lead agent

CURRENT_DIR=$(pwd)

# Only block if we're in a worker environment
if echo "$CURRENT_DIR" | grep -q "/.local/share/ccws/"; then
  cat <<'EOF'
{
  "decision": "block",
  "reason": "ワーカー環境では AskUserQuestion は使用できません。\n質問はリーダーに ccwire で送信してください:\n  wire_send(to: \"lead\", content: \"質問内容\", type: \"task_request\")"
}
EOF
else
  echo '{}'
fi
