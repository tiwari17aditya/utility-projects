import imaplib
import email
from email.header import decode_header
import json
import os
import sys
import re
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("GmailCleaner")

# Known folder name variants across different locales / configurations
SPAM_FOLDERS = ["[Gmail]/Spam", "Spam", "[Gmail]/Junk", "Junk"]
TRASH_FOLDERS = ["[Gmail]/Trash", "[Gmail]/Bin", "Trash", "Bin"]

def decode_mime_words(header_val: str) -> str:
    """Safely decode MIME encoded header words (e.g. =?UTF-8?B?...?=)."""
    if not header_val:
        return "(No Subject)"
    decoded_fragments = []
    try:
        for fragment, encoding in decode_header(header_val):
            if isinstance(fragment, bytes):
                try:
                    decoded_fragments.append(fragment.decode(encoding or "utf-8", errors="replace"))
                except Exception:
                    decoded_fragments.append(fragment.decode("latin1", errors="replace"))
            elif isinstance(fragment, str):
                decoded_fragments.append(fragment)
    except Exception:
        return str(header_val)
    return "".join(decoded_fragments).strip()


def sanitize_filename(name: str, max_len: int = 100) -> str:
    """Sanitize a string to be safe for filenames across Windows, macOS, and Linux."""
    if not name or not name.strip():
        return "No_Subject"
    # Replace illegal characters: <>:"/\|?* and control characters with '_'
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    # Collapse multiple spaces / underscores
    sanitized = re.sub(r'[\s_]+', ' ', sanitized).strip()
    # Remove trailing periods and spaces (prohibited on Windows)
    sanitized = sanitized.rstrip('. ')
    if not sanitized:
        return "No_Subject"
    return sanitized[:max_len].strip()


def get_account_username(email_address: str) -> str:
    """Extract account username by removing the @domain suffix (e.g. user@gmail.com -> user)."""
    username = email_address.split("@")[0].strip() if "@" in email_address else email_address.strip()
    return sanitize_filename(username, max_len=60)


class GmailCleaner:
    def __init__(self, email_address: str, app_password: str, dry_run: bool = False, log_dir: str = "deleted_emails"):
        self.email = email_address
        self.password = app_password
        self.dry_run = dry_run
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993
        self.log_dir = log_dir

    def record_deleted_emails(self, records: List[Dict[str, Any]]) -> str:
        """Append metadata of deleted emails into a per-user JSON file in log_dir (e.g. deleted_emails/addytiwari3.json)."""
        if not records:
            return ""

        os.makedirs(self.log_dir, exist_ok=True)
        username = get_account_username(self.email)
        user_log_file = os.path.join(self.log_dir, f"{username}.json")

        history = []
        if os.path.exists(user_log_file):
            try:
                with open(user_log_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    if not isinstance(history, list):
                        history = []
            except Exception:
                history = []

        history.extend(records)

        with open(user_log_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        return user_log_file

    def fetch_email_metadata(self, mail: imaplib.IMAP4_SSL, msg_ids: List[bytes], folder_name: str) -> List[Dict[str, Any]]:
        """Fetch Subject, From, Date headers for each email before deletion."""
        records = []
        purge_timestamp = datetime.now().isoformat()

        logger.info(f"[{self.email}] Fetching titles & metadata for {len(msg_ids)} email(s) in '{folder_name}'...")

        for msg_id in msg_ids:
            try:
                # Fetch header fields without marking message as read
                status, data = mail.fetch(msg_id, "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])")
                if status != "OK" or not data or not data[0]:
                    continue

                raw_email_bytes = data[0][1]
                msg = email.message_from_bytes(raw_email_bytes)

                subject = decode_mime_words(msg.get("Subject", "(No Subject)"))
                from_addr = decode_mime_words(msg.get("From", "(Unknown Sender)"))
                date_sent = msg.get("Date", "")

                records.append({
                    "deleted_at": purge_timestamp,
                    "account": self.email,
                    "folder": folder_name,
                    "subject": subject,
                    "from": from_addr,
                    "date": date_sent
                })
            except Exception as e:
                logger.warning(f"[{self.email}] Failed to fetch metadata for msg ID {msg_id.decode()}: {e}")

        return records

    def clean_folder(self, mail: imaplib.IMAP4_SSL, folder_candidates: List[str]) -> int:
        target_folder = None
        
        for candidate in folder_candidates:
            status, _ = mail.select(f'"{candidate}"', readonly=self.dry_run)
            if status == "OK":
                target_folder = candidate
                break
                
        if not target_folder:
            logger.warning(f"[{self.email}] None of the expected folders found: {folder_candidates}")
            return 0

        status, messages = mail.search(None, "ALL")
        if status != "OK" or not messages[0]:
            logger.info(f"[{self.email}] Folder '{target_folder}' is already empty.")
            return 0

        msg_ids = messages[0].split()
        count = len(msg_ids)

        # Fetch metadata (subject, sender, date) for audit log
        metadata_records = self.fetch_email_metadata(mail, msg_ids, target_folder)

        if self.dry_run:
            logger.info(f"[{self.email}] [DRY-RUN] Would delete {count} email(s) from '{target_folder}'.")
            for rec in metadata_records[:5]:  # Log first 5 subjects preview
                logger.info(f"   ↳ [DRY-RUN Subject]: {rec['subject']} | From: {rec['from']}")
            if len(metadata_records) > 5:
                logger.info(f"   ↳ ... and {len(metadata_records) - 5} more.")
            return count

        logger.info(f"[{self.email}] Deleting {count} email(s) from '{target_folder}'...")

        status, _ = mail.store("1:*", "+FLAGS", "(\\Deleted)")
        if status == "OK":
            mail.expunge()
            logger.info(f"[{self.email}] Successfully purged {count} email(s) from '{target_folder}'.")
            # Save deleted email metadata to per-user file
            user_log_file = self.record_deleted_emails(metadata_records)
            logger.info(f"[{self.email}] Recorded metadata for {len(metadata_records)} deleted email(s) into '{user_log_file}'.")
        else:
            logger.error(f"[{self.email}] Failed to set deleted flag on messages in '{target_folder}'.")
            count = 0

        mail.close()
        return count

    def run(self, targets: List[str]) -> Dict[str, int]:
        results = {}
        logger.info(f"Connecting to Gmail IMAP server for account: {self.email}...")
        
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email, self.password)
            logger.info(f"Authentication successful for {self.email}.")

            if "spam" in targets:
                results["spam"] = self.clean_folder(mail, SPAM_FOLDERS)

            if "trash" in targets:
                results["trash"] = self.clean_folder(mail, TRASH_FOLDERS)

            mail.logout()

        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP Authentication failed for {self.email}: {e}")
            raise
        except Exception as e:
            logger.error(f"An error occurred while processing account {self.email}: {e}")
            raise

        return results


def load_config(config_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(config_path):
        logger.error(f"Config file not found at: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    accounts = data.get("accounts", [])
    if not accounts:
        logger.error("No accounts configured in config file.")
        sys.exit(1)

    return accounts


def main():
    parser = argparse.ArgumentParser(description="Automated Multi-User Gmail Spam & Trash Auto-Cleaner with Audit Logging")
    parser.add_argument("--config", default="config.json", help="Path to config JSON file containing credentials.")
    parser.add_argument("--log-dir", default="deleted_emails", help="Directory where per-user deleted email logs will be stored.")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without deleting emails.")
    parser.add_argument("--targets", nargs="+", choices=["spam", "trash"], default=["spam", "trash"], help="Folders to clean.")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = args.config if os.path.isabs(args.config) else os.path.join(script_dir, args.config)
    log_dir = args.log_dir if os.path.isabs(args.log_dir) else os.path.join(script_dir, args.log_dir)

    logger.info("Starting Gmail Auto-Cleaner Process...")
    if args.dry_run:
        logger.info("*** DRY-RUN MODE ENABLED - No emails will be permanently deleted ***")

    accounts = load_config(config_file)
    logger.info(f"Loaded {len(accounts)} account(s) from configuration.")

    summary = {}
    for acc in accounts:
        email = acc.get("email")
        password = acc.get("app_password")
        enabled = acc.get("enabled", True)

        if not enabled:
            logger.info(f"Skipping disabled account: {email}")
            continue

        if not email or not password:
            logger.warning(f"Invalid account entry missing email or app_password: {acc}")
            continue

        try:
            cleaner = GmailCleaner(email_address=email, app_password=password, dry_run=args.dry_run, log_dir=log_dir)
            res = cleaner.run(targets=args.targets)
            summary[email] = res
        except Exception as e:
            summary[email] = {"error": str(e)}

    logger.info("=" * 60)
    logger.info("GMAIL CLEANUP EXECUTION SUMMARY")
    logger.info("=" * 60)
    for email, stats in summary.items():
        if "error" in stats:
            logger.info(f" - {email}: ERROR ({stats['error']})")
        else:
            spam_cnt = stats.get("spam", 0)
            trash_cnt = stats.get("trash", 0)
            username = get_account_username(email)
            user_log_path = os.path.join(log_dir, f"{username}.json")
            logger.info(f" - {email}: Cleared {spam_cnt} Spam, {trash_cnt} Trash emails. Details saved to '{user_log_path}'.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
