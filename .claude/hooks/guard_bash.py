"""PreToolUse hook: allow only Bash commands that start with one of the given prefixes.

Usage in agent frontmatter:
  python "$CLAUDE_PROJECT_DIR/.claude/hooks/guard_bash.py" "kaggle competitions leaderboard" ...
Command chaining (; && || | ` $( ) and redirects are rejected so a prefix can't smuggle a second command.
An optional leading "--agent NAME" makes the guard apply only to that agent's own calls (a main-session
agent's hooks also fire for its subagents' calls; those defer to the subagent's own guard).
"""
import json
import re
import sys

try:
    event = json.load(sys.stdin)
except ValueError:
    print("Blocked: could not parse hook input.", file=sys.stderr)
    sys.exit(2)
command = event.get("tool_input", {}).get("command", "").strip()

prefixes = sys.argv[1:]
if len(prefixes) >= 2 and prefixes[0] == "--agent":
    owner, prefixes = prefixes[1], prefixes[2:]
    if event.get("agent_type") not in (None, owner):
        sys.exit(0)

if re.search(r"[;&|`<>]|\$\(", command):
    print("Blocked: chaining, pipes and redirects are not allowed for this agent.", file=sys.stderr)
    sys.exit(2)

if any(command == p or command.startswith(p + " ") for p in prefixes):
    sys.exit(0)

print(f"Blocked: allowed commands start with: {'; '.join(prefixes)}", file=sys.stderr)
sys.exit(2)
