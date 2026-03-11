# backend/app/services/transaction_fraud_risk.py

from __future__ import annotations

import re
from typing import Any, Dict, List


SUSPICIOUS_URGENCY_PATTERNS = [
    r"\burgent\b",
    r"\basap\b",
    r"\bimmediately\b",
    r"\bright now\b",
    r"\bwithout delay\b",
    r"\bwithin 24 hours\b",
    r"\btoday only\b",
]

SCAM_LANGUAGE_PATTERNS = [
    r"\bkindly\b",
    r"\btrusted partner\b",
    r"\bgood day\b",
    r"\bdear friend\b",
    r"\bwaiting for your urgent reply\b",
    r"\bhope to hear from you soonest\b",
]

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

LOW_DETAIL_PATTERNS = [
    r"\bsend price\b",
    r"\bsend quotation\b",
    r"\bbest price\b",
    r"\bsend details\b",
    r"\bneed products\b",
]

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
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _has_any_pattern(text: str, patterns: List[str]) -> bool:
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False


def _email_domain(email: str) -> str:
    email = (email or "").strip().lower()
    if "@" not in email:
        return ""
    return email.split("@", 1)[1]


def analyze(normalized_facts: Dict[str, Any], raw_message: str = "") -> Dict[str, Any]:
    text = _normalize_text(raw_message)

    tags: list[str] = []

    sender_email = str(normalized_facts.get("sender_email", "")).strip()
    company_name = str(normalized_facts.get("company_name", "")).strip()
    product_requested = str(normalized_facts.get("product_requested", "")).strip()

    # 1. suspicious urgency
    if _has_any_pattern(text, SUSPICIOUS_URGENCY_PATTERNS):
        tags.append("suspicious_urgency")

    # 2. possible scam pattern
    scam_signal_count = 0
    if _has_any_pattern(text, SCAM_LANGUAGE_PATTERNS):
        scam_signal_count += 1
    if _has_any_pattern(text, PAYMENT_RISK_PATTERNS):
        scam_signal_count += 1
    if _has_any_pattern(text, LOW_DETAIL_PATTERNS) and len(text) < 250:
        scam_signal_count += 1

    if scam_signal_count >= 2:
        tags.append("possible_scam_pattern")

    # 3. unverified counterparty
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

    tags = sorted(set(tags))

    summary = None
    if tags:
        summary = f"Transaction/fraud risk tags matched: {', '.join(tags)}."

    return {
        "category": "transaction_fraud",
        "tags": tags,
        "summary": summary,
    }