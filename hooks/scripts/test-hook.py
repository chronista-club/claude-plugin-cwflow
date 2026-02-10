#!/usr/bin/env python3
"""
hook-block-git.py のテストスイート
実行: python3 test-hook.py
"""
import subprocess
import json
import sys
import os

HOOK_SCRIPT = os.path.join(os.path.dirname(__file__), "hook-block-git.py")

def run_hook(command: str) -> tuple[int, str, str]:
    """hookにコマンドを渡して実行し、(exit_code, stdout, stderr) を返す"""
    input_data = json.dumps({
        "session_id": "test-session",
        "tool_name": "Bash",
        "tool_input": {
            "command": command,
            "description": "test"
        }
    })
    result = subprocess.run(
        [sys.executable, HOOK_SCRIPT],
        input=input_data,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr

def test(name: str, command: str, expect_blocked: bool):
    code, stdout, stderr = run_hook(command)
    blocked = code == 2
    status = "✓" if blocked == expect_blocked else "✗"
    if blocked != expect_blocked:
        print(f"  {status} FAIL: {name}")
        print(f"    command: {command}")
        print(f"    expected: {'blocked' if expect_blocked else 'allowed'}")
        print(f"    got:      {'blocked' if blocked else 'allowed'} (exit {code})")
        if stderr:
            print(f"    stderr:   {stderr.strip()}")
        return False
    else:
        print(f"  {status} {name}")
        return True

def main():
    print("=== hook-block-git.py テスト ===\n")
    results = []

    print("-- ブロックされるべきコマンド --")
    results.append(test("git checkout main", "git checkout main", True))
    results.append(test("git switch feature", "git switch feature", True))
    results.append(test("git stash", "git stash", True))
    results.append(test("git stash pop", "git stash pop", True))
    results.append(test("git branch new-branch", "git branch new-branch", True))
    results.append(test("git add .", "git add .", True))
    results.append(test("git add -A", "git add -A", True))
    results.append(test("git commit -m 'msg'", "git commit -m 'test'", True))
    results.append(test("git push origin main", "git push origin main", True))
    results.append(test("git pull", "git pull", True))
    results.append(test("git merge feature", "git merge feature", True))
    results.append(test("git rebase main", "git rebase main", True))
    results.append(test("git reset --hard", "git reset --hard HEAD~1", True))
    results.append(test("git cherry-pick abc", "git cherry-pick abc123", True))
    results.append(test("git revert HEAD", "git revert HEAD", True))
    results.append(test("git tag v1.0", "git tag v1.0", True))
    results.append(test("git init", "git init", True))

    print("\n-- パイプ/連結内のgitもブロック --")
    results.append(test("ls && git commit", "ls && git commit -m 'test'", True))
    results.append(test("echo ok; git push", "echo ok; git push origin main", True))
    results.append(test("test || git add .", "test || git add .", True))

    print("\n-- 許可されるべきコマンド --")
    results.append(test("git log", "git log --oneline -20", False))
    results.append(test("git diff", "git diff HEAD", False))
    results.append(test("git show", "git show abc123", False))
    results.append(test("git blame", "git blame src/main.rs", False))
    results.append(test("git status", "git status", False))
    results.append(test("git remote -v", "git remote -v", False))

    print("\n-- but コマンドは許可 --")
    results.append(test("but status", "but status", False))
    results.append(test("but commit", "but commit -m 'test'", False))
    results.append(test("but push", "but push", False))
    results.append(test("but branch new x", "but branch new feature", False))
    results.append(test("but absorb", "but absorb", False))

    print("\n-- ツール経由のgitは許可（gitで始まらない） --")
    results.append(test("gh pr create", "gh pr create --fill", False))
    results.append(test("cargo build", "cargo build", False))
    results.append(test("npm test", "npm test", False))

    print("\n-- エッジケース --")
    results.append(test("空コマンド", "", False))
    results.append(test("先頭スペース付きgit commit", "  git commit -m 'x'", True))

    passed = sum(results)
    total = len(results)
    print(f"\n=== 結果: {passed}/{total} passed ===")
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
