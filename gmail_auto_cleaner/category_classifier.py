"""
Category Classifier for Gmail Auto Cleaner
Categorizes emails into 'RETAIN' vs 'DELETE' based on header metadata (Subject, Sender, Category/Folder, Date).
"""

import re
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, List

# Keywords indicating important/transactional emails that should be RETAINED
RETAIN_KEYWORDS = [
    r"\binvoice\b", r"\breceipt\b", r"\border\b", r"\bconfirm(?:ation)?\b", r"\bstatement\b",
    r"\btax\b", r"\bbooking\b", r"\bticket\b", r"\baccount\b", r"\bsecurity\b",
    r"\bpasscode\b", r"\botp\b", r"\bpassword\b", r"\bpayment\b", r"\bbill\b",
    r"\btransaction\b", r"\brefund\b", r"\bshipment\b", r"\bshipped\b", r"\btracking\b",
    r"\bpnr\b", r"\bflight\b", r"\btrain\b", r"\bhotel\b", r"\bpolicy\b", r"\bpremium\b",
    r"\bsubscription active\b", r"\bverification\b", r"\bverify\b", r"\bauth\b"
]

# Keywords indicating typical marketing / promotional / digest emails recommended for DELETION
DELETE_KEYWORDS = [
    r"\bunsubscribe\b", r"%\s*off\b", r"\bsale\b", r"\blimited time\b", r"\bnewsletter\b",
    r"\bdigest\b", r"\bdeal\b", r"\bpromo(?:tion)?\b", r"\bdiscount\b", r"\boffer\b",
    r"\bshop now\b", r"\bexplore\b", r"\btrending\b", r"\bweekly recap\b", r"\bdaily digest\b",
    r"\bnew arrivals\b", r"\bwebinar\b", r"\bdon't miss\b", r"\blast chance\b", r"\bexclusive\b"
]

# Known trusted sender domains / keywords to prioritize retaining
RETAIN_SENDER_PATTERNS = [
    r"bank", r"paypal", r"stripe", r"razorpay", r"paytm", r"zerodha", r"groww", r"upstox",
    r"amazon", r"flipkart", r"uber", r"ola", r"swiggy", r"zomato", r"makemytrip", r"goibibo",
    r"irctc", r"indigo", r"airindia", r"vistara", r"redbus", r"apple", r"google", r"microsoft",
    r"github", r"gitlab", r"vercel", r"netlify", r"aws", r"azure"
]


class CategoryClassifier:
    def __init__(self, retain_keywords: List[str] = None, delete_keywords: List[str] = None, sender_whitelist: List[str] = None):
        self.retain_regex = re.compile("|".join(retain_keywords or RETAIN_KEYWORDS), re.IGNORECASE)
        self.delete_regex = re.compile("|".join(delete_keywords or DELETE_KEYWORDS), re.IGNORECASE)
        self.retain_sender_regex = re.compile("|".join(sender_whitelist or RETAIN_SENDER_PATTERNS), re.IGNORECASE)

    def classify_email(self, email_meta: Dict[str, Any]) -> Tuple[str, str, int]:
        """
        Classifies an email metadata dictionary.
        Returns tuple: (Action: 'RETAIN' | 'DELETE', Reason: str, Confidence Score: 0-100)
        """
        subject = email_meta.get("subject", "") or ""
        sender = email_meta.get("from", "") or ""
        folder = email_meta.get("folder", "") or ""

        reasons = []
        retain_score = 0
        delete_score = 0

        # Check Subject for Retain Keywords
        retain_match = self.retain_regex.search(subject)
        if retain_match:
            retain_score += 40
            reasons.append(f"Subject contains retain keyword '{retain_match.group()}'")

        # Check Sender for Retain Patterns
        sender_match = self.retain_sender_regex.search(sender)
        if sender_match:
            retain_score += 35
            reasons.append(f"Sender matches trusted pattern '{sender_match.group()}'")

        # Check Subject for Delete Keywords
        delete_match = self.delete_regex.search(subject)
        if delete_match:
            delete_score += 35
            reasons.append(f"Subject contains promotional keyword '{delete_match.group()}'")

        # Folder heuristics
        folder_lower = folder.lower()
        if "promotions" in folder_lower or "promo" in folder_lower:
            delete_score += 20
        elif "social" in folder_lower:
            delete_score += 25
        elif "updates" in folder_lower:
            # Updates often contain both receipts and notifications
            delete_score += 10

        # Decide Action
        if retain_score > delete_score or retain_score >= 35:
            action = "RETAIN"
            confidence = min(95, 50 + retain_score)
            reason_str = " | ".join(reasons) if reasons else "No clear delete triggers; safety retain"
        elif delete_score > 0:
            action = "DELETE"
            confidence = min(95, 40 + delete_score)
            reason_str = " | ".join(reasons) if reasons else "Promotional / Marketing email pattern"
        else:
            # Default for category emails without specific matches: default candidate for deletion with lower score
            action = "DELETE"
            confidence = 55
            reason_str = f"Default promotional label rule for '{folder}'"

        return action, reason_str, confidence
