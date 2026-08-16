# Multi-User Gmail Spam & Trash Auto-Cleaner

An automated tool to clean the **Spam** and **Trash** (Bin) folders across multiple Gmail accounts securely using standard IMAP SSL protocol and Google App Passwords.

---

## Features

- **Multi-User Support**: Clean multiple family or personal Gmail accounts in a single run.
- **Google App Passwords Support**: Bypass 2FA securely without exposing primary passwords.
- **Dry-Run Mode (`--dry-run`)**: Preview the number of emails that would be purged without actually deleting them.
- **Flexible Target Selection**: Choose to empty only Spam (`--targets spam`), only Trash (`--targets trash`), or both.
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

### Preview Deletions (Dry-Run Mode)
```bash
python gmail_cleaner.py --dry-run
```

### Execute Purge for All Accounts
```bash
python gmail_cleaner.py
```

### Clean Only Spam
```bash
python gmail_cleaner.py --targets spam
```

### Clean Only Trash
```bash
python gmail_cleaner.py --targets trash
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
