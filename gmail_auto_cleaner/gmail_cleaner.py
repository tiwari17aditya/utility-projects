import imaplib
import json
import os
import sys
import logging
import argparse
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

class GmailCleaner:
    def __init__(self, email_address: str, app_password: str, dry_run: bool = False):
        self.email = email_address
        self.password = app_password
        self.dry_run = dry_run
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993

    def clean_folder(self, mail: imaplib.IMAP4_SSL, folder_candidates: List[str]) -> int:
        target_folder = None
        
        # Discover existing folder name
        for candidate in folder_candidates:
            status, _ = mail.select(f'"{candidate}"', readonly=self.dry_run)
            if status == "OK":
                target_folder = candidate
                break
                
        if not target_folder:
            logger.warning(f"[{self.email}] None of the expected folders found: {folder_candidates}")
            return 0

        # Search for all message sequence IDs in folder
        status, messages = mail.search(None, "ALL")
        if status != "OK" or not messages[0]:
            logger.info(f"[{self.email}] Folder '{target_folder}' is already empty.")
            return 0

        msg_ids = messages[0].split()
        count = len(msg_ids)

        if self.dry_run:
            logger.info(f"[{self.email}] [DRY-RUN] Would delete {count} email(s) from '{target_folder}'.")
            return count

        logger.info(f"[{self.email}] Deleting {count} email(s) from '{target_folder}'...")

        # Mark all items deleted and expunge
        status, _ = mail.store("1:*", "+FLAGS", "(\\Deleted)")
        if status == "OK":
            mail.expunge()
            logger.info(f"[{self.email}] Successfully purged {count} email(s) from '{target_folder}'.")
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
    parser = argparse.ArgumentParser(description="Automated Multi-User Gmail Spam & Trash Auto-Cleaner")
    parser.add_argument("--config", default="config.json", help="Path to config JSON file containing credentials.")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without deleting emails.")
    parser.add_argument("--targets", nargs="+", choices=["spam", "trash"], default=["spam", "trash"], help="Folders to clean.")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = args.config if os.path.isabs(args.config) else os.path.join(script_dir, args.config)

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
            cleaner = GmailCleaner(email_address=email, app_password=password, dry_run=args.dry_run)
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
            logger.info(f" - {email}: Cleared {spam_cnt} Spam, {trash_cnt} Trash emails.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
