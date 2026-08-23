---
name: irrelevant-files-deleter
description: >-
  Autonomously scans, identifies, and safely removes temporary, orphan, cache,
  and junk files across the project workspace.
---

# Irrelevant Files Deleter Skill

Use this skill to scan and clean up temporary files, build artifacts, Python cache directories, and orphan log files across the codebase.

## Workflow

### 1. Scan Workspace
Scan the workspace for known temporary and disposable file patterns:
- Python cache: `**/__pycache__`, `**/*.pyc`, `**/*.pyo`, `**/*.pyd`, `.pytest_cache`, `.coverage`
- OS junk: `.DS_Store`, `Thumbs.db`, `desktop.ini`
- Log/scratch files: `*.tmp`, `*.bak`, `*.swp`, `scratch/` (temporary scripts no longer needed)
- Old/orphan build outputs or duplicate logs.

### 2. Safeguard Check
- Verify that no source code (`.py`, `.js`, `.bat`, etc.) or persistent documentation files are marked for deletion.
- Preserve configuration files (`config.json`, `.gitignore`, `README.md`).

### 3. Cleanup Action
Run clean commands or shell instructions to remove matched temporary directories and files safely.

### 4. Verification & Reporting
Output a list of removed files/directories and report reclaimed disk space.
