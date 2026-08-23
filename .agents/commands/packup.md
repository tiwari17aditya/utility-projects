# Command: /packup

End-of-session automated packup workflow: runs all slash commands defined in `.agents/commands/`, stages all changes, creates a detailed git commit, and pushes to remote.

## Instructions for Agent
1. Execute `/irrelevant-files-deleter` to clean temporary and cache files.
2. Execute `/docs-manager` to synchronize all READMEs and project documentation.
3. Execute `/development-tracker` to write the hierarchical session log under `docs/logs/`.
4. Execute any other slash commands in `.agents/commands/`.
5. Run `git status` and `git add .`.
6. Commit changes with a descriptive commit message (`git commit -m "..."`).
7. Push changes to git remote (`git push`).
8. Present a summary report of the packup completion.
