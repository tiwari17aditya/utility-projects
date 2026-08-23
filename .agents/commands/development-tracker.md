# Command: /development-tracker

Autonomously create and update hierarchical development logs under `docs/logs/` detailing current work, modified files, bug fixes, and testing results.

## Instructions for Agent
1. Inspect git status and workspace edits.
2. Update/create today's session summary in `docs/logs/session_logs/session_summary_YYYY-MM-DD.md`.
3. Update `docs/logs/development_tracker.md` master log index.
4. Output the path to the recorded session log.
