"""PreToolUse hook: allow only Bash commands that start with one of the given prefixes.

Usage in agent frontmatter:
  python "$CLAUDE_PROJECT_DIR/.claude/hooks/guard_bash.py" "kaggle competitions leaderboard" ...
Command chaining (; && || | ` $( ) and redirects are rejected so a prefix can't smuggle a second command.
"""
import json
import re
import sys

try:
    command = json.load(sys.stdin).get("tool_input", {}).get("command", "").strip()
except ValueError:
    print("Blocked: could not parse hook input.", file=sys.stderr)
    sys.exit(2)

if re.search(r"[;&|`<>]|\$\(", command):
    print("Blocked: chaining, pipes and redirects are not allowed for this agent.", file=sys.stderr)
    sys.exit(2)

if any(command == p or command.startswith(p + " ") for p in sys.argv[1:]):
    sys.exit(0)

print(f"Blocked: allowed commands start with: {'; '.join(sys.argv[1:])}", file=sys.stderr)
sys.exit(2)
