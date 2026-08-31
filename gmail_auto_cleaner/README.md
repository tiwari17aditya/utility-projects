# Multi-User Gmail Spam & Trash Auto-Cleaner

An automated tool to clean the **Spam** and **Trash** (Bin) folders across multiple Gmail accounts securely using standard IMAP SSL protocol and Google App Passwords.

---

## Features

- **Multi-User Support**: Clean multiple family or personal Gmail accounts in a single run.
- **Smart Category Classifier**: Inspects `Promotions`, `Updates`, `Social`, and `Forums` tab labels and automatically recommends what to **Retain** (bank statements, receipts, orders, OTPs, security alerts) vs. what can be **Deleted** (promotional newsletters, marketing blasts).
- **Google App Passwords Support**: Bypass 2FA securely without exposing primary passwords.
- **Per-User Audit Logs & HTML Reports**: Stores deleted email metadata in JSON files (`deleted_emails/<username>/`) and generates interactive visual HTML dashboards (`inspection_report_<username>.html`).
- **Dry-Run Mode (`--dry-run`)**: Preview recommendations and deletions across all accounts without altering emails.
- **Flexible Target Selection**: Choose Spam (`--targets spam`), Trash (`--targets trash`), Category Labels (`--targets categories`), or all.
- **Zero External Dependencies**: Built using standard Python modules (`imaplib`, `ssl`, `json`, `argparse`, `logging`).
- **Automation Ready**: Easy integration with Windows Task Scheduler or Linux Cron jobs.

---

## Step 1: Generate a Google App Password

To allow the script to access IMAP securely without disabling 2FA or entering your primary Google account password:

Direct URLs:
- 🔑 **Google App Passwords Direct Link**: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
- 🔒 **Google 2-Step Verification Link**: [https://myaccount.google.com/signinoptions/two-step-verification](https://myaccount.google.com/signinoptions/two-step-verification)

### Steps:
1. Ensure **2-Step Verification** is turned ON for your Google Account via the 2-Step Verification link above.
2. Open the **App Passwords** link: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Enter an App Name (e.g., `Gmail Cleaner`) and click **Create**.
4. Copy the generated 16-character password (spaces can be included or omitted).

---

## Step 2: Configure `config.json`

Copy `config.json.example` to `config.json` and add entries for all users:

```json
{
  "accounts": [
    {
      "name": "My Account",
      "email": "myaccount@gmail.com",
      "app_password": "abcd efgh ijkl mnop",
      "enabled": true
    },
    {
      "name": "Family Member",
      "email": "familymember@gmail.com",
      "app_password": "qrst uvwx yzab cdef",
      "enabled": true
    }
  ]
}
```

> ⚠️ **Security Tip**: Never commit `config.json` containing actual App Passwords to public repositories.

---

## Step 3: Usage

### Tiered Deletion & Review Strategy:
- **Promotions & Social**: Automatically purged during cleaning runs.
- **Updates & Primary**: Scanned and rated by deletion confidence score. Candidates are staged and presented in an interactive review menu (`[A]ll`, `[H]igh confidence`, `[S]elect numbers`, `[N]one`) and saved to `review_pending_<username>.json`.

### Clean Single Account (e.g. `addytiwari5@gmail.com`)
```bash
python gmail_cleaner.py --account addytiwari5@gmail.com
```

### Preview Single Account (Dry-Run Mode)
```bash
python gmail_cleaner.py --account addytiwari5@gmail.com --dry-run
```

### Execute Purge for All Accounts
```bash
python gmail_cleaner.py
```

### Clean Only Spam or Trash
```bash
python gmail_cleaner.py --targets spam
python gmail_cleaner.py --targets trash
```

### Inspect Pending Updates & Primary Deletion Candidates
```bash
python list_deleted_titles.py --email addytiwari5@gmail.com --review-pending
```

### Inspect Deleted Email Titles & Location (Interactive Viewer)
```bash
# Interactive selection (holds window open until any key is pressed):
python list_deleted_titles.py

# Direct CLI inspection:
python list_deleted_titles.py --email addytiwari3@gmail.com --date 25_August_2026

# Disable window holding pause (for scripts/automation):
python list_deleted_titles.py --no-pause
```


---

## Audit Log Structure

Deleted emails are automatically cataloged per account into individual subdirectories and date-based JSON files (formatted as `dd_mm_yyyy`) inside the `deleted_emails/` folder:

```
deleted_emails/
├── abc/
│   ├── 23_08_2026_abc.json   # Deleted emails & metadata for abc@gmail.com on 23-Aug-2026
│   └── ...
├── addytiwari3/
│   ├── 23_08_2026_addytiwari3.json
│   └── ...
└── ...
```

Each date-based JSON file (`deleted_emails/<username>/<dd_mm_yyyy>_<username>.json`) stores the history of deleted emails for that specific deletion date with their titles and metadata:
```json
[
  {
    "deleted_at": "2026-08-19T13:22:50.123456",
    "account": "addytiwari3@gmail.com",
    "folder": "[Gmail]/Spam",
    "subject": "Discount Offer on Shoes",
    "from": "promotions@store.com",
    "date": "Wed, 19 Aug 2026 07:15:00 +0000"
  },
  {
    "deleted_at": "2026-08-19T13:25:10.789101",
    "account": "addytiwari3@gmail.com",
    "folder": "[Gmail]/Trash",
    "subject": "Security Alert",
    "from": "no-reply@accounts.google.com",
    "date": "Wed, 19 Aug 2026 08:30:00 +0000"
  }
]
```

---

## Step 4: Automating Execution

### Option A: Windows Task Scheduler
1. Open **Task Scheduler** and click **Create Basic Task**.
2. Name it `Gmail Auto Cleaner` and set Trigger to **Daily** or **Weekly**.
3. Action: **Start a program**.
4. Program/script: `python` (or full path to `python.exe`).
5. Add arguments: `gmail_cleaner.py`
6. Start in: `D:\Antigravity-Projects\utility-projects\gmail_auto_cleaner\`

### Option B: Linux / macOS Cron
Add a daily cron job at 3:00 AM:
```bash
0 3 * * * /usr/bin/python3 /path/to/gmail_auto_cleaner/gmail_cleaner.py >> /path/to/gmail_cleaner.log 2>&1
```
