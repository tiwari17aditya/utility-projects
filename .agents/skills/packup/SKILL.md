---
name: packup
description: >-
  Executes the automated end-of-session packup workflow: runs all slash commands
  in .agents/commands/ (irrelevant files deleter, docs manager, development tracker),
  stages all changes, commits to git with a descriptive message, and pushes to remote.
---

# Packup Skill

Use this skill whenever the user triggers `/packup` or requests to pack up, wrap up, commit, and push the session's work.

## Automated Packup Workflow

### Step 1: Run All Slash Commands in `.agents/commands/`
Execute all defined commands in sequence:
1. **`/irrelevant-files-deleter`**: Sweep `__pycache__`, `.pytest_cache`, `*.pyc`, `*.tmp`, and orphan temporary files.
2. **`/docs-manager`**: Audit and update root [`README.md`](file:///d:/Antigravity-Projects/utility-projects/README.md) and module documentation.
3. **`/development-tracker`**: Write/update hierarchical session logs under `docs/logs/session_logs/` and update master tracker index.
4. **Other Commands**: Execute any additional commands present in `.agents/commands/`.

### Step 2: Git Stage
Check workspace status:
`git status`
Stage all modified, added, and deleted files:
`git add .`

### Step 3: Git Commit
Generate a detailed, multi-line commit message summarizing key changes made during the session:
`git commit -m "<concise summary line>" -m "<bulleted breakdown of changes>"`

### Step 4: Git Push
Push committed changes to the active branch on the remote repository:
`git push`

### Step 5: Final Session Summary Report
Output a clean final packup summary showing:
- 🧹 Irrelevant files deleted
- 📚 Documentation files updated
- 📝 Hierarchical development log updated
- 🚀 Git commit message, hash, and push status
