"""
Script to list deleted email titles from 'deleted_emails' log directory.
Features:
- Prompts/accepts email address or username.
- Discovers available log dates and presents a formatted dropdown/selection menu ("date_nameofmonth_year").
- Outputs a formatted, numbered list of deleted email titles along with location (e.g. Bin, Spam, Promotions).
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Base log directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "deleted_emails")


def sanitize_username(email_or_user: str) -> str:
    """Extract and sanitize username from email string."""
    name = email_or_user.split("@")[0].strip() if "@" in email_or_user else email_or_user.strip()
    return re.sub(r'[<>:"/\\|?*\x00-\x1f\s]', '_', name)


def format_folder_location(folder_raw: str) -> str:
    """Convert raw IMAP folder string to clean location name (e.g. Bin, Spam, Promotions)."""
    if not folder_raw:
        return "Unknown"
    
    f_lower = folder_raw.lower()
    if "bin" in f_lower or "trash" in f_lower:
        return "Bin"
    elif "spam" in f_lower or "junk" in f_lower:
        return "Spam"
    elif "promotions" in f_lower or "promo" in f_lower:
        return "Promotions"
    elif "updates" in f_lower:
        return "Updates"
    elif "social" in f_lower:
        return "Social"
    elif "forums" in f_lower:
        return "Forums"
    else:
        # Strip [Gmail]/ prefix if present
        cleaned = re.sub(r'^\[Gmail\]/', '', folder_raw)
        return cleaned.strip()


def get_available_accounts() -> List[str]:
    """Returns list of account usernames present in deleted_emails folder."""
    if not os.path.exists(LOG_DIR):
        return []
    return [d for d in os.listdir(LOG_DIR) if os.path.isdir(os.path.join(LOG_DIR, d))]


def find_date_logs(username: str) -> Dict[str, Tuple[str, List[str]]]:
    """
    Scans user log directory and maps formatted dates ("date_nameofmonth_year", e.g. "25_August_2026")
    to list of corresponding JSON log files.
    """
    user_dir = os.path.join(LOG_DIR, username)
    if not os.path.exists(user_dir):
        return {}

    date_map = {}
    for fname in os.listdir(user_dir):
        if not fname.endswith(".json") or fname.startswith("inspection_data_"):
            continue

        # Match date pattern dd_mm_yyyy at start of file
        match = re.match(r'^(\d{2}_\d{2}_\d{4})', fname)
        if match:
            raw_date_str = match.group(1)
            try:
                dt = datetime.strptime(raw_date_str, "%d_%m_%Y")
                formatted_date = dt.strftime("%d_%B_%Y")  # e.g., 25_August_2026
            except ValueError:
                formatted_date = raw_date_str

            if formatted_date not in date_map:
                date_map[formatted_date] = (raw_date_str, [])
            date_map[formatted_date][1].append(os.path.join(user_dir, fname))

    return date_map


def load_records_for_files(file_paths: List[str]) -> List[Dict[str, Any]]:
    """Loads and deduplicates email records from given JSON files."""
    all_records = []
    seen_ids = set()

    for path in file_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for rec in data:
                        # Deduplicate by subject + from + date if needed
                        sub = rec.get("subject", "")
                        from_addr = rec.get("from", "")
                        d_sent = rec.get("date", "")
                        key = f"{sub}|{from_addr}|{d_sent}"
                        if key not in seen_ids:
                            seen_ids.add(key)
                            all_records.append(rec)
        except Exception as e:
            print(f"Error reading file '{path}': {e}", file=sys.stderr)

    return all_records


def wait_for_keypress(prompt_msg: str = "\nPress any key to close this window..."):
    """
    Holds the terminal window open until a key is pressed.
    Prevents terminal window from closing automatically before reading the output.
    """
    print(prompt_msg, flush=True)
    try:
        if os.name == 'nt':
            try:
                import msvcrt
                # Flush any leftover input buffers
                while msvcrt.kbhit():
                    msvcrt.getch()
                msvcrt.getch()
                return
            except Exception:
                pass
        input()
    except (KeyboardInterrupt, EOFError):
        pass


def select_option_interactive(prompt_msg: str, options: List[str]) -> str:
    """Displays a clean interactive selection menu for terminal users."""
    print(f"\n{prompt_msg}")
    for idx, opt in enumerate(options, 1):
        print(f"  [{idx}] {opt}")
    
    while True:
        try:
            choice = input(f"\nSelect an option (1-{len(options)}): ").strip()
            if choice.isdigit():
                val = int(choice)
                if 1 <= val <= len(options):
                    return options[val - 1]
            print(f"Invalid choice '{choice}'. Please enter a number between 1 and {len(options)}.")
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.")
            sys.exit(0)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="List deleted email titles and location from deleted_emails logs.")
    parser.add_argument("--email", "-e", help="Target email address or username.")
    parser.add_argument("--date", "-d", help="Target date in format 'date_nameofmonth_year' (e.g. 25_August_2026) or 'dd_mm_yyyy'.")
    parser.add_argument("--no-pause", action="store_true", help="Do not wait for keypress before closing window.")
    args = parser.parse_args()

    def finish(code: int = 0):
        if not args.no_pause:
            wait_for_keypress()
        sys.exit(code)

    print("================================================================================")
    print("         GMAIL DELETED EMAILS TITLE & LOCATION VIEWER")
    print("================================================================================")

    # Step 1: Obtain Email / Username
    target_email_input = args.email
    if not target_email_input:
        available_accounts = get_available_accounts()
        if not available_accounts:
            print(f"No deleted email logs found in '{LOG_DIR}'. Run gmail_cleaner.py first.")
            finish(1)

        print("\nAvailable accounts with deletion logs:")
        for idx, acc in enumerate(available_accounts, 1):
            print(f"  [{idx}] {acc}")

        user_input = input("\nEnter email address or select account number: ").strip()
        if user_input.isdigit() and 1 <= int(user_input) <= len(available_accounts):
            target_email_input = available_accounts[int(user_input) - 1]
        else:
            target_email_input = user_input

    username = sanitize_username(target_email_input)
    date_map = find_date_logs(username)

    if not date_map:
        print(f"\n❌ No deletion logs found for account '{target_email_input}' (username dir: '{username}').")
        print(f"Directory checked: {os.path.join(LOG_DIR, username)}")
        finish(1)

    # Step 2 & 3: List Dates & Present Dropdown Selection
    available_dates = list(date_map.keys())
    
    selected_date = args.date
    if selected_date:
        # Match input date with available date formats
        matched_date = None
        for dt_fmt, (dt_raw, files) in date_map.items():
            if selected_date.lower() == dt_fmt.lower() or selected_date.lower() == dt_raw.lower():
                matched_date = dt_fmt
                break
        if not matched_date:
            print(f"❌ Date '{selected_date}' not found in logs for '{username}'.")
            print(f"Available dates: {', '.join(available_dates)}")
            finish(1)
        selected_date = matched_date
    else:
        if len(available_dates) == 1:
            selected_date = available_dates[0]
            print(f"\n📅 Found deletion log date: {selected_date}")
        else:
            selected_date = select_option_interactive(
                prompt_msg=f"📅 Select deletion log date for '{username}':",
                options=available_dates
            )

    # Step 4 & 5: Load & Output Deleted Titles and Location in Numbered Format
    _, file_paths = date_map[selected_date]
    records = load_records_for_files(file_paths)

    if not records:
        print(f"\nNo records found in log files for {selected_date}.")
        finish(0)

    print("\n" + "=" * 80)
    print(f"DELETED EMAIL TITLES REPORT")
    print(f"Account:       {target_email_input}")
    print(f"Date Selected: {selected_date} (date_nameofmonth_year)")
    print(f"Total Emails:  {len(records)}")
    print("=" * 80 + "\n")

    print("Sr No. | Title | Location Deleted |")
    print("-" * 80)

    for idx, r in enumerate(records, 1):
        subject = r.get("subject", "(No Subject)").replace("\r\n", " ").replace("\n", " ").strip()
        folder_raw = r.get("folder", "Unknown")
        location = format_folder_location(folder_raw)

        print(f"{idx} | {subject} | {location}")

    print("-" * 80)
    print(f"Summary: Displayed {len(records)} deleted title(s) for date '{selected_date}'.")

    finish(0)


if __name__ == "__main__":
    main()

