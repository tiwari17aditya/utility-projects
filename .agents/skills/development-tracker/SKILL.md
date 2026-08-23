---
name: development-tracker
description: >-
  Generates and maintains hierarchical development logs and session summaries under
  docs/logs/ to track project progress, modifications, and fixes.
---

# Development Tracker Skill

Use this skill to log engineering activity, refactorings, feature additions, and bug fixes in a structured, hierarchical format under `docs/logs/`.

## Hierarchical Log Structure

Logs are cataloged hierarchically by date and task:
```text
docs/logs/
├── session_logs/
│   ├── session_summary_2026-08-16.md
│   ├── session_summary_2026-08-19.md
│   └── session_summary_2026-08-23.md
└── development_tracker.md
```

## Workflow

### 1. Gather Activity Data
- Collect modified file paths (`git status`, `git diff --name-status`).
- Review session actions, bug fixes, refactorings, and test verification outputs.

### 2. Update/Create Hierarchical Log Entry
Create or append to `docs/logs/session_logs/session_summary_YYYY-MM-DD.md` using the standard format:
```markdown
# Session Summary — [YYYY-MM-DD]

## 🎯 Objectives
- Objective 1...

## 🛠️ Files Modified / Added
- `path/to/file` — Summary of change...

## 🐛 Bug Fixes & Refactoring
- Fix description...

## 🧪 Verification & Testing
- Command run: `python ...`
- Result: Passed / Verified.

## 📌 Next Steps
- Pending item 1...
```

### 3. Update Master Index
Maintain `docs/logs/development_tracker.md` with an updated index table of all recorded sessions.
