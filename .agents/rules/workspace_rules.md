# Workspace Rules & Slash Commands Guidelines

This workspace contains automated agent slash commands and skills under `.agents/`.

## Active Slash Commands

- **`/irrelevant-files-deleter`**: Cleans temporary files, cache directories (`__pycache__`, `.pytest_cache`), and orphan log files.
- **`/docs-manager`**: Keeps project documentation, README files, and CLI parameters up to date across all project modules.
- **`/development-tracker`**: Logs session activity, bug fixes, modified files, and test results in a hierarchical structure under `docs/logs/`.
- **`/packup`**: Executes all `.agents/commands/` tasks, stages all changes (`git add .`), commits with a descriptive message, and pushes to git (`git push`).

## Execution Policy
- When `/packup` or a packup request is triggered, always execute the full pipeline: clean irrelevant files -> update docs -> log development activity -> git add -> git commit -> git push.
