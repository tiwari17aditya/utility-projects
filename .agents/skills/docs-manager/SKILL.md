---
name: docs-manager
description: >-
  Manages and synchronizes project documentation across the workspace, updating
  README files, API surfaces, and architecture docs whenever code changes.
---

# Docs Manager Skill

Use this skill to audit, update, and align documentation across the repository whenever features, CLI flags, configuration schemas, or file structures change.

## Workflow

### 1. Detect Changes
- Check modified files in git (`git status`, `git diff`).
- Identify any new CLI flags, updated function signatures, directory restructure, or configuration changes.

### 2. Update Documentation Files
- **Root README**: [`README.md`](file:///d:/Antigravity-Projects/utility-projects/README.md) — Ensure project overview, utility directory listings, and key files remain 100% accurate.
- **Module READMEs**: e.g., [`gmail_auto_cleaner/README.md`](file:///d:/Antigravity-Projects/utility-projects/gmail_auto_cleaner/README.md), [`system_maintenance/README.md`](file:///d:/Antigravity-Projects/utility-projects/system_maintenance/README.md), [`eye_care_tracker/README.md`](file:///d:/Antigravity-Projects/utility-projects/eye_care_tracker/README.md).
- Update feature lists, command flags, directory layout trees, and JSON examples.

### 3. Verify Links & Markdown Formatting
- Ensure all file paths use proper Markdown link syntax (`file:///...` or relative link syntax).
- Verify headings, code snippets, and table structures.

### 4. Summary Output
Report all updated documentation files with a brief summary of additions/revisions.
