# Command: /docs-manager

Autonomously update and synchronize all project documentation files (`README.md`, sub-module docs, session notes) based on current workspace code changes.

## Instructions for Agent
1. Review `git status` and recent file modifications.
2. Update root `README.md` and module `README.md` files with new CLI parameters, file paths, or structural updates.
3. Validate Markdown links and code block syntax across documentation.
4. Report all documentation files updated.
