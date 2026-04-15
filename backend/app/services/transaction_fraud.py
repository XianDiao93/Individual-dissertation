# backend/app/services/transaction_fraud_risk.py

from __future__ import annotations

import re
from typing import Any, Dict, List


# Patterns indicating suspicious urgency in communication
SUSPICIOUS_URGENCY_PATTERNS = [
    r"\burgent\b",
    r"\basap\b",
    r"\bimmediately\b",
    r"\bright now\b",
    r"\bwithout delay\b",
    r"\bwithin 24 hours\b",
    r"\btoday only\b",
]

# Language patterns commonly found in scam-like messages
SCAM_LANGUAGE_PATTERNS = [
    r"\bkindly\b",
    r"\btrusted partner\b",
    r"\bgood day\b",
    r"\bdear friend\b",
    r"\bwaiting for your urgent reply\b",
    r"\bhope to hear from you soonest\b",
]

# Risky or non-standard payment method indicators
PAYMENT_RISK_PATTERNS = [
    r"\bwestern union\b",
    r"\bmoneygram\b",
    r"\bcrypto\b",
    r"\bbitcoin\b",
    r"\busdt\b",
    r"\badvance payment only\b",
    r"\bpersonal account\b",
    r"\bprivate account\b",
]

# Low-information request patterns (often seen in scam or low-quality inquiries)
LOW_DETAIL_PATTERNS = [
    r"\bsend price\b",
    r"\bsend quotation\b",
    r"\bbest price\b",
    r"\bsend details\b",
    r"\bneed products\b",
]

# Common free email providers (lower trust than corporate domains)
FREE_EMAIL_DOMAINS = [
    "gmail.com",
    "outlook.com",
    "hotmail.com",
    "yahoo.com",
    "qq.com",
    "163.com",
    "126.com",
    "icloud.com",
]


def _normalize_text(text: str) -> str:
    """
    Normalize text for pattern matching.
    """
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _has_any_pattern(text: str, patterns: List[str]) -> bool:
    """
    Check whether any regex pattern matches the text.
    """
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False


def _email_domain(email: str) -> str:
    """
    Extract domain from email address.
    """
    email = (email or "").strip().lower()
    if "@" not in email:
        return ""
    return email.split("@", 1)[1]


def analyze(normalized_facts: Dict[str, Any], raw_message: str = "") -> Dict[str, Any]:
    """
    Detect transaction and fraud-related risks from message content and sender profile.
    """
    text = _normalize_text(raw_message)

    tags: list[str] = []

    sender_email = str(normalized_facts.get("sender_email", "")).strip()
    company_name = str(normalized_facts.get("company_name", "")).strip()
    product_requested = str(normalized_facts.get("product_requested", "")).strip()

    # 1. Suspicious urgency signals
    if _has_any_pattern(text, SUSPICIOUS_URGENCY_PATTERNS):
        tags.append("suspicious_urgency")

    # 2. Possible scam pattern (combined signals)
    scam_signal_count = 0
    if _has_any_pattern(text, SCAM_LANGUAGE_PATTERNS):
        scam_signal_count += 1
    if _has_any_pattern(text, PAYMENT_RISK_PATTERNS):
        scam_signal_count += 1
    if _has_any_pattern(text, LOW_DETAIL_PATTERNS) and len(text) < 250:
        scam_signal_count += 1

    if scam_signal_count >= 2:
        tags.append("possible_scam_pattern")

    # 3. Unverified counterparty detection
    domain = _email_domain(sender_email)
    unverified_score = 0

    if not company_name:
        unverified_score += 1
    if not sender_email:
        unverified_score += 1
    elif domain in FREE_EMAIL_DOMAINS:
        unverified_score += 1

    if not product_requested:
        unverified_score += 1

    if unverified_score >= 2:
        tags.append("unverified_counterparty")

    # Remove duplicates
    tags = sorted(set(tags))

    summary = None
    if tags:
        summary = f"Transaction/fraud risk tags matched: {', '.join(tags)}."

    return {
        "category": "transaction_fraud",
        "tags": tags,
        "summary": summary,
    }