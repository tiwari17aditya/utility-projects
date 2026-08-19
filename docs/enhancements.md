# Future Enhancements & Personal Utility Roadmap

This document outlines proposed future enhancements for existing utilities and ideas for new personal utility tools to expand the `utility-items` workspace.

---

## 🚀 Enhancements for Existing Utilities

### 1. Gmail Auto-Cleaner (`gmail_auto_cleaner/`)
- **Web Dashboard / GUI**: Build a simple local FastAPI/Streamlit interface to view per-user deleted email logs (`deleted_emails/<username>.json`), filter by date/account, and search subjects.
- **Rules Engine / Filters**: Add criteria matching to only auto-purge emails older than `N` days (e.g. `--older-than 30d`) or matching specific keywords.
- **Telegram / Email Notification Digest**: Send a daily summary message (e.g. "Gmail Cleaner: Purged 15 spam & 30 trash emails today") via Telegram Bot or Email.
- **Google OAuth2 Support**: Provide an option for OAuth2 desktop flow as an alternative to App Passwords.

### 2. System Maintenance (`system_maintenance/`)
- **Automated Storage Analyzer**: Add a Python script to scan local drives (`C:\`, `D:\`) for duplicate files, large video/iso files (>500MB), and empty folders.
- **Windows Startup Manager**: Audit and log non-essential startup applications causing slow boot times.

### 3. Eye Care Tracker (`eye_care_tracker/`)
- **System Tray Icon (pystray)**: Minimize `eye_care_alert.pyw` into the Windows system tray with quick options (Pause 1hr, View Stats, Reset Counter).
- **Weekly Email / PDF Report**: Export weekly screen time summaries with charts showing active screen time distribution.

### 4. GitHub Tools (`github_tools/`)
- **Automated Repository Backup Utility**: Clone or fetch ZIP archives of all personal repositories to external storage or cloud drive as a local backup solution.
- **Stale Branch Cleanup**: Detect and report unmerged or abandoned branches across all personal GitHub repositories.

---

## 💡 New Personal Utility Concepts to Build

### 🛠️ 1. Automated Downloads / Desktop Organizer (`desktop_organizer/`)
- **Purpose**: Auto-sort files in `Downloads` or `Desktop` based on extensions (`.pdf` -> `Documents/PDFs`, `.png`/`.jpg` -> `Pictures`, `.zip`/`.exe` -> `Installers`).
- **Trigger**: Run periodically or monitor folder via `watchdog`.

### 📱 2. Whatsapp / SMS Reminder Utility (`quick_reminders/`)
- **Purpose**: A lightweight CLI or web UI to schedule quick reminders sent to personal Telegram or WhatsApp.

### 📊 3. Monthly Expense & Subscriptions Tracker (`expense_tracker/`)
- **Purpose**: Parse bank transaction CSV exports or manual entries to track recurring monthly subscriptions (Netflix, cloud hosting, domain renewals) with upcoming renewal alerts.

### 🔑 4. Local Environment & API Key Auditor (`env_auditor/`)
- **Purpose**: Scan local workspace folders for uncommitted API keys, credentials, or `.env` files exposed outside `.gitignore`.

### 🌐 5. Website Uptime & SSL Monitor (`uptime_checker/`)
- **Purpose**: Periodically ping personal portfolio/app domains and alert if any service goes down or SSL certificates are expiring within 14 days.
