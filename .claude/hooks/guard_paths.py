"""PreToolUse hook: block Write/Edit outside the agent's allowed paths.

Usage in agent frontmatter:
  python "$CLAUDE_PROJECT_DIR/.claude/hooks/guard_paths.py" "experiments/**" "src/**"
Patterns are fnmatch globs relative to the project root (`*` also matches `/`).
"""
import fnmatch
import json
import os
import sys
from pathlib import Path

root = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
try:
    event = json.load(sys.stdin)
except ValueError:
    print("Blocked: could not parse hook input.", file=sys.stderr)
    sys.exit(2)

# Optional leading "--agent NAME": the guard belongs to that agent. A main-session
# agent's hooks also fire for its subagents' calls; those defer to the subagent's own guard.
patterns = sys.argv[1:]
if len(patterns) >= 2 and patterns[0] == "--agent":
    owner, patterns = patterns[1], patterns[2:]
    if event.get("agent_type") not in (None, owner):
        sys.exit(0)

target = event.get("tool_input", {}).get("file_path") or event.get("tool_input", {}).get("notebook_path")
if not target:
    sys.exit(0)

path = Path(target)
if not path.is_absolute():
    path = Path(event.get("cwd", root)) / path
try:
    rel = path.resolve().relative_to(root).as_posix()
except ValueError:
    rel = None

if rel is not None and any(fnmatch.fnmatch(rel, pattern) for pattern in patterns):
    sys.exit(0)

print(f"Blocked: this agent may only write to {', '.join(patterns)}; got {target}", file=sys.stderr)
sys.exit(2)
