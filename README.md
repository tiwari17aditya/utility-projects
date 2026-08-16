# Utility-Items

A curated collection of single-functionality utility scripts, maintenance tools, and automation workflows.

---

## 🛠️ Included Utilities

### 1. 📧 [Gmail Auto-Cleaner](gmail_auto_cleaner/)
- **Description**: Automated multi-user script to clear Spam and Trash folders for Gmail accounts via IMAP SSL and Google App Passwords.
- **Key Files**:
  - [`gmail_cleaner.py`](gmail_auto_cleaner/gmail_cleaner.py) - Main cleaning script with multi-account & `--dry-run` support.
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
