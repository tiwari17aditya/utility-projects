# Utility-Items

A curated collection of single-functionality utility scripts, maintenance tools, and automation workflows.

---

## 🛠️ Included Utilities

### 1. 📧 [Gmail Auto-Cleaner](gmail_auto_cleaner/)
- **Description**: Automated multi-user script to clean Spam, Trash, and Category labels (`Promotions`, `Updates`, `Social`, `Primary`). Features auto-purging for Promotions/Social and confidence-based interactive review staging for Updates/Primary emails.
- **Key Files**:
  - [`gmail_cleaner.py`](gmail_auto_cleaner/gmail_cleaner.py) - Main cleaning script with multi-account, `--account` filter, and interactive review menu.
  - [`category_classifier.py`](gmail_auto_cleaner/category_classifier.py) - Smart Retain vs Delete recommendation engine with Primary inbox protection heuristics.
  - [`report_generator.py`](gmail_auto_cleaner/report_generator.py) - Interactive visual HTML inspection dashboard generator.
  - [`list_deleted_titles.py`](gmail_auto_cleaner/list_deleted_titles.py) - Interactive viewer for deleted email titles and staged review candidates (`sr no, || Category type || title of mail`).
  - [`config.json.example`](gmail_auto_cleaner/config.json.example) - Multi-account configuration template.
  - [`README.md`](gmail_auto_cleaner/README.md) - Setup guide for App Passwords and Task Scheduler.

---

### 2. 🧹 [System Maintenance](system_maintenance/)
- **Description**: Enterprise Windows maintenance script to purge temporary files, empty Recycle Bin, flush DNS cache, and run SFC integrity scans.
- **Key Files**:
  - [`CleanPC.bat`](system_maintenance/CleanPC.bat) - Self-elevating batch maintenance tool.

---

### 3. 👁️ [Eye Care & Screen Time Tracker](eye_care_tracker/)
- **Description**: Background idle timer and break notification system with interactive 7-day screen time visualization.
- **Key Files**:
  - [`eye_care_alert.pyw`](eye_care_tracker/eye_care_alert.pyw) - Background alert prompt.
  - [`interactive_stats.py`](eye_care_tracker/interactive_stats.py) - Tkinter dashboard GUI.

---

### 4. ⚙️ [Developer Tools](dev_tools/)
- **Description**: Project setup script for initializing Python virtual environments and Jupyter kernels.
- **Key Files**:
  - [`setup_project.sh`](dev_tools/setup_project.sh) - Quick project bootstrapper script.

---

### 5. 🐙 [GitHub Tools](github_tools/)
- **Description**: Utilities for auditing repository artifact storage and purging build artifacts via GitHub REST API.
- **Key Files**:
  - [`audit_storage.py`](github_tools/audit_storage.py) - Audits artifact storage sizes across repositories.
  - [`purge_artifacts.py`](github_tools/purge_artifacts.py) - Purges Actions build artifacts for a repository.

---

## 🚀 Usage & Setup
Navigate to any individual tool directory and check its `README.md` or file documentation for execution instructions.

---

## 📅 Session Logs & Roadmap
- 💡 **Future Enhancements & Roadmap**: [`docs/enhancements.md`](docs/enhancements.md)
- 📝 **Session Summary (2026-08-31)**: [`docs/logs/session_logs/session_summary_2026-08-31.md`](docs/logs/session_logs/session_summary_2026-08-31.md)
- 📝 **Session Summary (2026-08-25)**: [`docs/logs/session_logs/session_summary_2026-08-25.md`](docs/logs/session_logs/session_summary_2026-08-25.md)
- 📝 **Session Summary (2026-08-23)**: [`docs/logs/session_logs/session_summary_2026-08-23.md`](docs/logs/session_logs/session_summary_2026-08-23.md)



