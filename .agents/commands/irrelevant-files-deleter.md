# Command: /irrelevant-files-deleter

Autonomously scan the project for temporary files, cache directories, orphan logs, and scratch scripts, then safely delete them.

## Instructions for Agent
1. Scan for `__pycache__`, `*.pyc`, `.pytest_cache`, `Thumbs.db`, `.DS_Store`, and temporary `.tmp`/`.bak` files.
2. Remove matched temporary files using shell commands or clean-up logic.
3. Print a list of deleted items and confirm the workspace is clean.
