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

if rel is not None and any(fnmatch.fnmatch(rel, pattern) for pattern in sys.argv[1:]):
    sys.exit(0)

print(f"Blocked: this agent may only write to {', '.join(sys.argv[1:])}; got {target}", file=sys.stderr)
sys.exit(2)
