"""
Automated Multi-User Gmail Spam, Trash & Category Auto-Cleaner with Smart Retain/Delete Classifier & Audit Logging.
"""

import imaplib
import email
from email.header import decode_header
import json
import os
import sys
import re
import logging
import argparse
import socket
from datetime import datetime
from typing import List, Dict, Any, Tuple

from category_classifier import CategoryClassifier
from report_generator import InspectionReportGenerator

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("GmailCleaner")

# Known folder name variants across different locales / configurations
SPAM_FOLDERS = ["[Gmail]/Spam", "Spam", "[Gmail]/Junk", "Junk"]
TRASH_FOLDERS = ["[Gmail]/Bin", "[Gmail]/Trash", "Trash", "Bin"]

LABEL_QUERIES = {
    "Promotions": ['"\\\\Promotions"', '"Category Promotions"', '"Promotions"'],
    "Social": ['"\\\\Social"', '"Category Social"', '"Social"'],
    "Updates": ['"\\\\Updates"', '"Category Updates"', '"Updates"'],
    "Primary": ['"\\\\Primary"', '"Category Primary"', '"Primary"', 'INBOX'],
    "Forums": ['"\\\\Forums"', '"Category Forums"', '"Forums"']
}

AUTO_DELETE_CATEGORIES = ["Promotions", "Social", "Forums"]
REVIEW_CATEGORIES = ["Updates", "Primary"]



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
    except Exception as e:
        logger.debug(f"Error decoding MIME header '{header_val}': {e}")
        return str(header_val)
    return "".join(decoded_fragments).strip()


def sanitize_filename(name: str, max_len: int = 100) -> str:
    """Sanitize a string to be safe for filenames across Windows, macOS, and Linux."""
    if not name or not name.strip():
        return "No_Subject"
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    sanitized = re.sub(r'[\s_]+', ' ', sanitized).strip()
    sanitized = sanitized.rstrip('. ')
    if not sanitized:
        return "No_Subject"
    return sanitized[:max_len].strip()


def get_account_username(email_address: str) -> str:
    """Extract account username by removing the @domain suffix (e.g. user@gmail.com -> user)."""
    username = email_address.split("@")[0].strip() if "@" in email_address else email_address.strip()
    return sanitize_filename(username, max_len=60)


class GmailCleaner:
    def __init__(self, email_address: str, app_password: str, dry_run: bool = False, log_dir: str = "deleted_emails", timeout: int = 30, interactive: bool = True):
        self.email = email_address
        self.password = app_password
        self.dry_run = dry_run
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993
        self.log_dir = log_dir
        self.timeout = timeout
        self.interactive = interactive
        self.logger = logging.getLogger("GmailCleaner")
        self.classifier = CategoryClassifier()


    def record_deleted_emails(self, records: List[Dict[str, Any]], log_suffix: str = "") -> str:
        """Append metadata of deleted emails into a per-user date-based JSON file in log_dir."""
        if not records:
            return ""

        try:
            username = get_account_username(self.email)
            user_dir = os.path.join(self.log_dir, username)
            os.makedirs(user_dir, exist_ok=True)

            today_str = datetime.now().strftime("%d_%m_%Y")
            suffix_part = f"_{log_suffix}" if log_suffix else ""
            user_log_file = os.path.join(user_dir, f"{today_str}_{username}{suffix_part}.json")

            history = []
            if os.path.exists(user_log_file):
                try:
                    with open(user_log_file, "r", encoding="utf-8") as f:
                        history = json.load(f)
                        if not isinstance(history, list):
                            history = []
                except Exception as e:
                    self.logger.warning(f"[{self.email}] Could not read existing log file '{user_log_file}': {e}. Overwriting.")
                    history = []

            history.extend(records)

            with open(user_log_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)

            return user_log_file
        except Exception as e:
            self.logger.error(f"[{self.email}] Error recording deleted email metadata to log file: {e}")
            return ""

    def get_server_folders(self, mail: imaplib.IMAP4_SSL) -> List[str]:
        """Fetch available folder names directly from Gmail IMAP server."""
        folder_names = []
        try:
            status, data = mail.list()
            if status == "OK" and data:
                for item in data:
                    if isinstance(item, bytes):
                        item_str = item.decode("utf-8", errors="ignore")
                    elif isinstance(item, str):
                        item_str = item
                    else:
                        continue
                    
                    match = re.search(r'\((.*?)\)\s+"([^"]+)"\s+"?([^"]+)"?$', item_str)
                    if match:
                        name = match.group(3).strip('"')
                        folder_names.append(name)
                    else:
                        parts = item_str.rsplit(' "/" ', 1)
                        if len(parts) > 1:
                            folder_names.append(parts[1].strip('" '))
            self.logger.debug(f"[{self.email}] Discovered server folders: {folder_names}")
        except Exception as e:
            self.logger.warning(f"[{self.email}] Could not list IMAP server folders: {e}")
        return folder_names

    def fetch_email_metadata(self, mail: imaplib.IMAP4_SSL, msg_ids: List[bytes], folder_name: str, batch_size: int = 50) -> List[Dict[str, Any]]:
        """Fetch Subject, From, Date headers in batches for high speed and stability."""
        records = []
        purge_timestamp = datetime.now().isoformat()
        total_msgs = len(msg_ids)

        self.logger.info(f"[{self.email}] Fetching metadata for {total_msgs} email(s) in '{folder_name}' (batch size: {batch_size})...")

        for i in range(0, total_msgs, batch_size):
            batch_ids = msg_ids[i:i + batch_size]
            id_sequence = b",".join(batch_ids)

            try:
                self.logger.debug(f"[{self.email}] Fetching batch {(i//batch_size) + 1}/{(total_msgs + batch_size - 1)//batch_size}...")
                status, data = mail.fetch(id_sequence, "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])")
                if status != "OK" or not data:
                    self.logger.warning(f"[{self.email}] IMAP fetch status '{status}' for batch {i+1}-{min(i+batch_size, total_msgs)}")
                    continue

                for item in data:
                    if not isinstance(item, tuple) or len(item) < 2:
                        continue

                    try:
                        raw_email_bytes = item[1]
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
                        self.logger.debug(f"[{self.email}] Error parsing individual message header in batch: {e}")

            except Exception as e:
                self.logger.error(f"[{self.email}] Error fetching metadata batch: {e}")

        return records

    def clean_folder(self, mail: imaplib.IMAP4_SSL, folder_candidates: List[str], folder_label: str = "", server_folders: List[str] = None) -> int:
        target_folder = None
        if server_folders:
            matched = [c for c in folder_candidates if c in server_folders]
            if matched:
                folder_candidates = matched

        self.logger.info(f"[{self.email}] Trying folder candidates for '{folder_label}': {folder_candidates}")

        for candidate in folder_candidates:
            try:
                status, response = mail.select(f'"{candidate}"', readonly=self.dry_run)
                if status == "OK":
                    target_folder = candidate
                    self.logger.info(f"[{self.email}] Successfully selected folder: '{target_folder}'")
                    break
            except Exception as e:
                self.logger.warning(f"[{self.email}] Error selecting candidate folder '{candidate}': {e}")

        if not target_folder:
            self.logger.warning(f"[{self.email}] None of the expected folders found for '{folder_label}': {folder_candidates}")
            return 0

        try:
            status, messages = mail.search(None, "ALL")
            if status != "OK" or not messages or not messages[0]:
                self.logger.info(f"[{self.email}] Folder '{target_folder}' is empty.")
                return 0

            msg_ids = messages[0].split()
            count = len(msg_ids)
            self.logger.info(f"[{self.email}] Found {count} message(s) in '{target_folder}'.")

            metadata_records = self.fetch_email_metadata(mail, msg_ids, target_folder)

            if self.dry_run:
                self.logger.info(f"[{self.email}] [DRY-RUN] Would delete {count} email(s) from '{target_folder}'.")
                return count

            self.logger.info(f"[{self.email}] Flagging {count} email(s) for deletion in '{target_folder}'...")
            status, response = mail.store("1:*", "+FLAGS", "(\\Deleted)")
            if status == "OK":
                expunge_status, expunge_resp = mail.expunge()
                self.logger.info(f"[{self.email}] Successfully purged {count} email(s) from '{target_folder}'.")
                self.record_deleted_emails(metadata_records)
            else:
                count = 0

            try:
                mail.close()
            except Exception:
                pass

            return count

        except Exception as e:
            self.logger.error(f"[{self.email}] Error during cleanup of folder '{target_folder}': {e}")
            return 0

    def prompt_and_execute_review(self, mail: imaplib.IMAP4_SSL, review_candidates: List[Dict[str, Any]], search_folder: str = '"[Gmail]/All Mail"') -> Tuple[int, List[Dict[str, Any]]]:
        """Displays confidence-ranked review table for Updates & Primary emails and executes user-approved deletions."""
        if not review_candidates:
            return 0, []

        def parse_indices(input_str: str) -> set:
            indices = set()
            for part in input_str.split(","):
                part = part.strip()
                if not part:
                    continue
                if "-" in part:
                    sub = part.split("-", 1)
                    if sub[0].isdigit() and sub[1].isdigit():
                        for i in range(int(sub[0]), int(sub[1]) + 1):
                            indices.add(i)
                elif part.isdigit():
                    indices.add(int(part))
            return indices

        print("\n" + "=" * 90)
        print(f" 🔍 PENDING REVIEW: CANDIDATES FOR DELETION (Account: {self.email})")
        print(f"    The following Updates and Primary emails were flagged based on deletion confidence.")
        print(f"    They will NOT be deleted unless explicitly confirmed by you below.")
        print("=" * 90)

        print(f"{'#':<4} | {'Folder':<10} | {'Conf.':<6} | {'Subject':<40} | {'From':<23}")
        print("-" * 90)

        for idx, item in enumerate(review_candidates, 1):
            conf = f"{item.get('confidence', 50)}%"
            folder = item.get("folder", "Unknown")[:10]
            subj = item.get("subject", "(No Subject)")[:38]
            from_addr = item.get("from", "(Unknown)")[:23]
            print(f"{idx:<4} | {folder:<10} | {conf:<6} | {subj:<40} | {from_addr:<23}")

        print("-" * 90)
        print("Review Options:")
        print("  [A] Approve ALL candidates for deletion (Updates & Primary)")
        print("  [H] Approve HIGH confidence candidates only (>= 80% confidence)")
        print("  [U] Approve UPDATES candidates only")
        print("  [P] Approve PRIMARY candidates only")
        print("  [S] Select specific candidate numbers to DELETE (e.g. 1, 3, 5-8)")
        print("  [E] EXCLUDE / KEEP specific candidate numbers (Delete all EXCEPT entered numbers, e.g. 12, 15)")
        print("  [N] Delete NONE (Skip all pending Updates & Primary emails)")
        print("=" * 90)

        approved = []
        try:
            choice = input(f"\nSelect action for {self.email} [A/H/U/P/S/E/N] (default: N): ").strip().upper()
        except (KeyboardInterrupt, EOFError):
            print("\nSkipping review deletion.")
            return 0, []

        if choice == "A":
            approved = review_candidates
        elif choice == "H":
            approved = [item for item in review_candidates if item.get("confidence", 0) >= 80]
        elif choice == "U":
            approved = [item for item in review_candidates if "updates" in item.get("folder", "").lower()]
        elif choice == "P":
            approved = [item for item in review_candidates if "primary" in item.get("folder", "").lower() or "inbox" in item.get("folder", "").lower()]
        elif choice == "E":
            try:
                num_input = input("Enter candidate numbers/ranges to KEEP/RETAIN (e.g. 12, 15 or 5-8): ").strip()
                exclude_indices = parse_indices(num_input)
                approved = [item for idx, item in enumerate(review_candidates, 1) if idx not in exclude_indices]
                print(f"Excluding {len(exclude_indices)} item(s) {sorted(list(exclude_indices))}. Approved {len(approved)} email(s) for deletion.")
            except Exception as e:
                self.logger.warning(f"Error parsing exclusion input: {e}. No items selected.")
                approved = []
        elif choice == "S":
            try:
                num_input = input("Enter candidate numbers/ranges to delete (or type 'EXCEPT 12, 15' / '!12, 15'): ").strip()
                if num_input.upper().startswith("EXCEPT") or num_input.startswith("!") or num_input.startswith("-"):
                    clean_str = re.sub(r'^(EXCEPT|!|-)\s*', '', num_input, flags=re.IGNORECASE)
                    exclude_indices = parse_indices(clean_str)
                    approved = [item for idx, item in enumerate(review_candidates, 1) if idx not in exclude_indices]
                    print(f"Excluding {len(exclude_indices)} item(s) {sorted(list(exclude_indices))}. Approved {len(approved)} email(s) for deletion.")
                else:
                    selected_indices = parse_indices(num_input)
                    approved = [item for idx, item in enumerate(review_candidates, 1) if idx in selected_indices]
            except Exception as e:
                self.logger.warning(f"Error parsing index selection: {e}. No items selected.")
                approved = []

        if not approved:
            self.logger.info(f"[{self.email}] User selected no items for deletion in review step.")
            return 0, []

        self.logger.info(f"[{self.email}] Executing user-approved deletion of {len(approved)} reviewed email(s)...")


        if self.dry_run:
            self.logger.info(f"[{self.email}] [DRY-RUN] Would delete {len(approved)} reviewed email(s).")
            return len(approved), approved

        try:
            select_status, _ = mail.select(search_folder, readonly=False)
            if select_status != "OK":
                mail.select("INBOX", readonly=False)

            uids = [item.get("uid").encode("utf-8") for item in approved if item.get("uid")]
            if uids:
                uid_sequence = b",".join(uids)
                store_status, _ = mail.uid("STORE", uid_sequence, "+FLAGS", "(\\Deleted)")
                if store_status == "OK":
                    mail.expunge()
                    self.logger.info(f"[{self.email}] Successfully expunged {len(approved)} reviewed email(s).")
                    self.record_deleted_emails(approved, log_suffix="reviewed_deletions")
                    for item in approved:
                        item["action"] = "DELETED_POST_REVIEW"
                    return len(approved), approved
        except Exception as e:
            self.logger.error(f"[{self.email}] Error deleting reviewed emails: {e}")

        return 0, []

    def clean_categories(self, mail: imaplib.IMAP4_SSL, max_per_category: int = 100) -> Dict[str, Any]:
        """
        Tiered Category Cleaning:
        1. Auto-purges Promotions & Social mail types.
        2. Scans & rates Updates & Primary emails by confidence score; stages candidates for interactive review.
        """
        self.logger.info(f"[{self.email}] Starting Tiered Category Inspection & Selective Cleanup...")

        search_folder = '"[Gmail]/All Mail"'
        select_status, select_data = mail.select(search_folder, readonly=self.dry_run)
        if select_status != "OK":
            search_folder = "INBOX"
            select_status, select_data = mail.select(search_folder, readonly=self.dry_run)
            if select_status != "OK":
                self.logger.error(f"[{self.email}] Could not select search folder [Gmail]/All Mail or INBOX")
                return {"retained": 0, "deleted": 0, "error": "Search folder unselectable"}

        all_inspected = []
        auto_deleted_records = []
        review_candidates = []
        total_auto_deleted = 0
        total_retained = 0

        for cat_name, label_variants in LABEL_QUERIES.items():
            msg_uids = []
            successful_label = None

            for label_query in label_variants:
                try:
                    status, data = mail.uid("SEARCH", None, "X-GM-LABELS", label_query)
                    if status == "OK" and data and data[0]:
                        found_uids = data[0].split()
                        if found_uids:
                            msg_uids = found_uids
                            successful_label = label_query
                            break
                except Exception as e:
                    self.logger.debug(f"[{self.email}] Label query {label_query} failed: {e}")

            if not msg_uids:
                self.logger.info(f"[{self.email}] Category '{cat_name}': 0 emails found.")
                continue

            target_uids = msg_uids[-max_per_category:]
            uid_sequence = b",".join(target_uids)

            self.logger.info(f"[{self.email}] Fetching headers for {len(target_uids)} email(s) in category '{cat_name}'...")
            fetch_status, headers_data = mail.uid("FETCH", uid_sequence, "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE MESSAGE-ID)])")
            if fetch_status != "OK" or not headers_data:
                continue

            cat_auto_delete_uids = []
            is_auto_delete_tier = cat_name in AUTO_DELETE_CATEGORIES

            for idx_item, item in enumerate(headers_data):
                if not isinstance(item, tuple) or len(item) < 2:
                    continue

                raw_bytes = item[1]
                msg = email.message_from_bytes(raw_bytes)

                header_str = item[0].decode("utf-8", errors="ignore") if isinstance(item[0], bytes) else str(item[0])
                uid_match = imaplib.re.search(r'UID\s+(\d+)', header_str, imaplib.re.IGNORECASE)
                uid_val = uid_match.group(1).encode("utf-8") if uid_match else target_uids[idx_item % len(target_uids)]

                subject = decode_mime_words(msg.get("Subject", "(No Subject)"))
                from_addr = decode_mime_words(msg.get("From", "(Unknown Sender)"))
                date_sent = msg.get("Date", "")
                msg_id = msg.get("Message-ID", "")

                meta = {
                    "account": self.email,
                    "folder": cat_name,
                    "imap_folder": search_folder,
                    "label_used": successful_label,
                    "uid": uid_val.decode("utf-8"),
                    "message_id": msg_id,
                    "subject": subject,
                    "from": from_addr,
                    "date": date_sent
                }

                action, reason, confidence = self.classifier.classify_email(meta)
                meta["action"] = action
                meta["reason"] = reason
                meta["confidence"] = confidence

                all_inspected.append(meta)

                if action == "DELETE":
                    if is_auto_delete_tier:
                        auto_deleted_records.append(meta)
                        cat_auto_delete_uids.append(uid_val)
                        total_auto_deleted += 1
                    else:
                        # Staged for review (Updates & Primary)
                        meta["review_status"] = "PENDING_REVIEW"
                        review_candidates.append(meta)
                else:
                    total_retained += 1

            if is_auto_delete_tier:
                self.logger.info(f"[{self.email}] Auto-Purge Category '{cat_name}': {len(cat_auto_delete_uids)} delete candidate(s) out of {len(target_uids)} parsed.")
                if not self.dry_run and cat_auto_delete_uids:
                    self.logger.info(f"[{self.email}] Executing auto-deletion of {len(cat_auto_delete_uids)} email(s) in category '{cat_name}'...")
                    delete_uid_sequence = b",".join(cat_auto_delete_uids)
                    store_status, store_resp = mail.uid("STORE", delete_uid_sequence, "+FLAGS", "(\\Deleted)")
                    if store_status == "OK":
                        mail.expunge()
                        self.logger.info(f"[{self.email}] Successfully auto-expunged {len(cat_auto_delete_uids)} email(s) from category '{cat_name}'.")
            else:
                review_cnt = len([r for r in review_candidates if r.get("folder") == cat_name])
                self.logger.info(f"[{self.email}] Review Category '{cat_name}': {review_cnt} candidate(s) staged for review out of {len(target_uids)} parsed.")

        # Record auto-deleted records
        if auto_deleted_records and not self.dry_run:
            self.record_deleted_emails(auto_deleted_records, log_suffix="category_autodeletions")

        # Save staged review JSON file
        username = get_account_username(self.email)
        user_dir = os.path.join(self.log_dir, username)
        os.makedirs(user_dir, exist_ok=True)
        
        pending_review_file = os.path.join(user_dir, f"review_pending_{username}.json")
        with open(pending_review_file, "w", encoding="utf-8") as f:
            json.dump(review_candidates, f, indent=2, ensure_ascii=False)

        # Interactive Review Step for Updates & Primary
        total_reviewed_deleted = 0
        if review_candidates and self.interactive:
            total_reviewed_deleted, approved_items = self.prompt_and_execute_review(mail, review_candidates, search_folder=search_folder)

        # Save HTML and Audit JSON
        html_file = os.path.join(user_dir, f"inspection_report_{username}.html")
        InspectionReportGenerator.generate_html_report(self.email, all_inspected, html_file)
        
        json_file = os.path.join(user_dir, f"inspection_data_{username}.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(all_inspected, f, indent=2, ensure_ascii=False)

        return {
            "retained": total_retained,
            "auto_deleted": total_auto_deleted,
            "review_candidates_staged": len(review_candidates),
            "reviewed_deleted": total_reviewed_deleted,
            "total_deleted": total_auto_deleted + total_reviewed_deleted,
            "html_report": html_file,
            "json_data": json_file,
            "pending_review_file": pending_review_file
        }


    def run(self, targets: List[str]) -> Dict[str, Any]:
        results = {}
        self.logger.info(f"[{self.email}] Step 1/3: Connecting to IMAP server ({self.imap_server}:{self.imap_port}) with {self.timeout}s timeout...")

        mail = None
        try:
            socket.setdefaulttimeout(self.timeout)
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, timeout=self.timeout)
            self.logger.info(f"[{self.email}] Step 2/3: Authenticating with App Password...")

            login_status, login_resp = mail.login(self.email, self.password)
            if login_status != "OK":
                raise imaplib.IMAP4.error(f"Login rejected: {login_resp}")

            self.logger.info(f"[{self.email}] Step 3/3: Authentication successful!")
            server_folders = self.get_server_folders(mail)

            if "spam" in targets:
                try:
                    results["spam"] = self.clean_folder(mail, SPAM_FOLDERS, folder_label="Spam", server_folders=server_folders)
                except Exception as e:
                    self.logger.error(f"[{self.email}] Unhandled error cleaning Spam: {e}")
                    results["spam_error"] = str(e)

            if "trash" in targets:
                try:
                    results["trash"] = self.clean_folder(mail, TRASH_FOLDERS, folder_label="Trash/Bin", server_folders=server_folders)
                except Exception as e:
                    self.logger.error(f"[{self.email}] Unhandled error cleaning Trash: {e}")
                    results["trash_error"] = str(e)

            if "categories" in targets or any(t in ["promotions", "updates", "social", "forums"] for t in targets):
                try:
                    results["categories"] = self.clean_categories(mail)
                except Exception as e:
                    self.logger.error(f"[{self.email}] Unhandled error cleaning Categories: {e}")
                    results["categories_error"] = str(e)

            try:
                mail.logout()
            except Exception as e:
                self.logger.debug(f"[{self.email}] Exception during logout: {e}")

        except socket.timeout:
            err_msg = f"Network timeout ({self.timeout}s) connecting to {self.imap_server}:{self.imap_port}."
            self.logger.error(f"[{self.email}] {err_msg}")
            results["error"] = err_msg
        except imaplib.IMAP4.error as e:
            err_msg = f"IMAP Protocol Error / Authentication Failed: {e}"
            self.logger.error(f"[{self.email}] {err_msg}")
            results["error"] = err_msg
        except Exception as e:
            err_msg = f"Unexpected error processing account: {e}"
            self.logger.error(f"[{self.email}] {err_msg}", exc_info=True)
            results["error"] = err_msg

        return results


def load_config(config_path: str) -> List[Dict[str, Any]]:
    logger = logging.getLogger("GmailCleaner")
    logger.info(f"Loading configuration from: '{config_path}'...")
    if not os.path.exists(config_path):
        logger.error(f"Config file not found at path: {config_path}")
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON syntax in config file '{config_path}': {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to read config file '{config_path}': {e}")
        sys.exit(1)

    accounts = data.get("accounts", [])
    if not accounts:
        logger.error(f"No 'accounts' array configured inside '{config_path}'.")
        sys.exit(1)

    return accounts


def main():
    parser = argparse.ArgumentParser(description="Automated Multi-User Gmail Spam, Trash & Category Auto-Cleaner")
    parser.add_argument("--config", default="config.json", help="Path to config JSON file containing credentials.")
    parser.add_argument("--log-dir", default="deleted_emails", help="Directory where per-user deleted email logs will be stored.")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without deleting emails.")
    parser.add_argument("--targets", nargs="+", choices=["spam", "trash", "categories"], default=["spam", "trash", "categories"], help="Folders/categories to clean.")
    parser.add_argument("--account", "--email", "-e", help="Filter execution to a specific target email address (e.g. addytiwari5@gmail.com).")
    parser.add_argument("--no-interactive", action="store_true", help="Disable interactive terminal prompts for Updates/Primary review (stage items to JSON file only).")
    parser.add_argument("--timeout", type=int, default=30, help="IMAP socket timeout in seconds (default: 30s).")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose debug logging.")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = args.config if os.path.isabs(args.config) else os.path.join(script_dir, args.config)
    log_dir = args.log_dir if os.path.isabs(args.log_dir) else os.path.join(script_dir, args.log_dir)

    logger = logging.getLogger("GmailCleaner")
    logger.info("Starting Multi-Account Gmail Auto-Cleaner Process...")
    if args.dry_run:
        logger.info("*** DRY-RUN MODE ENABLED - No emails will be permanently deleted ***")

    accounts = load_config(config_file)

    if args.account:
        filter_str = args.account.strip().lower()
        accounts = [acc for acc in accounts if filter_str in acc.get("email", "").lower()]
        if not accounts:
            logger.error(f"No account matching '{args.account}' found in configuration file '{config_file}'.")
            sys.exit(1)
        logger.info(f"Targeting single account: {accounts[0].get('email')}")

    logger.info(f"Loaded {len(accounts)} account(s) for execution.")

    summary = {}
    for idx, acc in enumerate(accounts, 1):
        email_addr = acc.get("email")
        password = acc.get("app_password")
        enabled = acc.get("enabled", True)

        logger.info(f"--- Processing Account [{idx}/{len(accounts)}]: {email_addr or 'Unknown'} ---")

        if not enabled:
            logger.info(f"Skipping disabled account: {email_addr}")
            summary[email_addr or f"Account_{idx}"] = {"status": "SKIPPED", "reason": "Disabled in config"}
            continue

        if not email_addr or not password:
            logger.warning(f"Skipping account [{idx}]: Missing 'email' or 'app_password' in config")
            summary[email_addr or f"Account_{idx}"] = {"status": "SKIPPED", "reason": "Missing email or app_password"}
            continue

        try:
            cleaner = GmailCleaner(
                email_address=email_addr,
                app_password=password,
                dry_run=args.dry_run,
                log_dir=log_dir,
                timeout=args.timeout,
                interactive=not args.no_interactive
            )
            res = cleaner.run(targets=args.targets)
            summary[email_addr] = res
        except Exception as e:
            logger.error(f"Unhandled crash while processing {email_addr}: {e}", exc_info=True)
            summary[email_addr] = {"error": str(e)}

    logger.info("=" * 70)
    logger.info("GMAIL CLEANUP EXECUTION SUMMARY")
    logger.info("=" * 70)
    for email_addr, stats in summary.items():
        if "error" in stats:
            logger.error(f" ❌ {email_addr}: FAILED - {stats['error']}")
        elif stats.get("status") == "SKIPPED":
            logger.info(f" ⏸️  {email_addr}: SKIPPED ({stats.get('reason')})")
        else:
            spam_cnt = stats.get("spam", 0)
            trash_cnt = stats.get("trash", 0)
            cat_stats = stats.get("categories", {})
            if isinstance(cat_stats, dict):
                cat_auto = cat_stats.get("auto_deleted", 0)
                cat_rev = cat_stats.get("reviewed_deleted", 0)
                cat_staged = cat_stats.get("review_candidates_staged", 0)
                cat_ret = cat_stats.get("retained", 0)
                logger.info(f" ✅ {email_addr}: Cleared {spam_cnt} Spam, {trash_cnt} Trash, Auto-purged {cat_auto} Promos/Social, Reviewed & Deleted {cat_rev}/{cat_staged} Updates/Primary (Retained {cat_ret} Important).")
            else:
                logger.info(f" ✅ {email_addr}: Cleared {spam_cnt} Spam, {trash_cnt} Trash.")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()

