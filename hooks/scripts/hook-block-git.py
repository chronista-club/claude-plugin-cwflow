#!/usr/bin/env python3
"""
GitButler Workflow Hook: git コマンドをブロックし but への誘導を行う
PreToolUse (Bash matcher) 用

stdinからJSON受信 → tool_input.command を検査 → git操作ならブロック
"""
import json
import sys
import re

# ブロック対象: git の書き込み系・状態変更系コマンド
BLOCKED_GIT_COMMANDS = re.compile(
    r'^\s*git\s+'
    r'(checkout|switch|stash|branch|add|commit|push|pull|merge|rebase|reset|cherry-pick|revert|tag|init)'
    r'(\s|$)'
)

# 許可: 読み取り専用の git コマンド（log, diff, show, blame 等）
# → ブロックしない（but にない機能もあるため）

# 許可: git を内部的に使うツール（gh, git-cz 等）
# → コマンドが 'git' で始まらないので自然に通過

def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # パース失敗時はブロックしない（安全側に倒す）
        sys.exit(0)

    # tool_input.command を取得
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        sys.exit(0)

    # パイプやセミコロンで連結されたコマンドも検査
    # "ls && git commit -m 'test'" のようなケースをキャッチ
    segments = re.split(r'[;&|]+', command)

    for segment in segments:
        segment = segment.strip()
        if BLOCKED_GIT_COMMANDS.match(segment):
            # ブロック: exit code 2 + stderr にメッセージ
            msg = (
                f"Blocked: '{segment.split()[0]} {segment.split()[1]}' — "
                f"This project uses GitButler. Use 'but' instead of 'git'.\n"
                f"Run: but {segment.split()[1]} ...\n"
                f"Details: .claude/skills/gitbutler-workflow/SKILL.md"
            )
            print(msg, file=sys.stderr)
            sys.exit(2)

    # 許可
    sys.exit(0)

if __name__ == "__main__":
    main()
