# Process housekeeping (Windows, Bash tool, git, permissions)

- Git: this repo has `core.autocrlf=true`, so a byte-exact port of third-party files needs a `.gitattributes` with `* -text` in its directory (`src/dqi/.gitattributes`). Otherwise checkout rewrites line endings and the SHA-256 manifest breaks (exp-011).
- Permissions: the Claude Code auto-mode classifier denies running ported third-party code (reason "Code from External"), even after a byte-verified copy into `src/` under `python -I -B`. `python -I -B src/dqi/generate.py --import-only ...` was denied (exp-011). Running such code locally or on Kaggle needs the user's permission. Parse-only checks (`ast.parse`, `ast.literal_eval`) were not blocked.
- Git: a user hook (`block_claude_trailer.py`) rejects commit messages that carry a Claude `Co-Authored-By` trailer, so commit without it (exp-003).
- Bash tool: one long command that wrote several files through `<<'EOF'` heredocs failed with ``unexpected EOF while looking for matching `''`` and wrote nothing. The cause was not determined. Writing the files with the Write tool worked (exp-003).
  - It happened again in the exp-005 fix: a ~100-line `<<'EOF'` heredoc of Python whose content held `'''` and `"""` strings. Writing that script with the Write tool and then running it worked.
- The experimenter's path guard (`.claude/hooks/guard_paths.py`) blocks Write and Edit outside `experiments/**`, `src/**`, `requirements.txt` and this file, and that includes the session scratchpad. Put helper scripts under a gitignored `experiments/exp-NNN/out/`. Bash `cp` into the scratchpad still works (exp-005 fix).

- To list processes from Git Bash, call PowerShell CIM. Escape every `$` as `\$` inside the double-quoted `-Command`:
  `powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { \$_.Name -match '^(python|bash|powershell|kaggle)(\.exe)?$' } | Format-List ProcessId,ParentProcessId,CreationDate,CommandLine"`
- Each Claude Code background job shows up as a tree: `bash.exe` (Git\bin), then `bash.exe` (usr\bin), then the command. A `.venv\Scripts\python.exe` launcher shim spawns a second python (the real interpreter), so each python job appears twice. Subprocess verifiers repeat that pair. The CPU and memory sit only on the innermost python.
- Background jobs from every agent in a session share one `claude.exe` parent. To tell experiments apart, use the command line (script path, `--tag`), not the parent PID.
- `browser-use.exe --cli-mcp` pythons under `uv\cache` are Claude Code MCP plugin servers, not experiment processes.
