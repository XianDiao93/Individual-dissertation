# backend/app/services/intent_conversation_risk.py

from __future__ import annotations

import re
from typing import Any, Dict, List


# Patterns suggesting weak or unclear purchase intent
LOW_INTENT_PATTERNS = [
    r"\bprice list\b",
    r"\bcatalog\b",
    r"\bbrochure\b",
    r"\bquotation only\b",
    r"\bquote only\b",
    r"\bsend me your price\b",
    r"\bsend your catalog\b",
    r"\bbest price\b",
]

# Patterns suggesting information gathering without clear trade context
INFO_FISHING_PATTERNS = [
    r"\bfull product list\b",
    r"\ball products\b",
    r"\bcomplete specification\b",
    r"\bfull specifications\b",
    r"\btechnical details only\b",
    r"\bcompany profile\b",
    r"\byour customer list\b",
    r"\bshare your supplier details\b",
]

# Patterns suggesting generic bulk-style inquiry
MASS_INQUIRY_PATTERNS = [
    r"\bdear sir/madam\b",
    r"\bto whom it may concern\b",
    r"\bwe are interested in your products\b",
    r"\bplease send your catalog\b",
    r"\bplease share more details\b",
]

# Patterns suggesting concrete purchase-related intent
PURCHASE_SIGNALS = [
    r"\border\b",
    r"\bpurchase\b",
    r"\bbuy\b",
    r"\bneed\b",
    r"\brequire\b",
    r"\bshipment\b",
    r"\bdelivery\b",
    r"\bquantity\b",
    r"\bMOQ\b",
    r"\bpayment terms\b",
]


def _normalize_text(text: str) -> str:
    """
    Normalize input text for pattern matching.
    """
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _has_any_pattern(text: str, patterns: List[str]) -> bool:
    """
    Check whether text matches any regex pattern in the given list.
    """
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False


def analyze(normalized_facts: Dict[str, Any], raw_message: str = "") -> Dict[str, Any]:
    """
    Analyze intent and conversation-level risks from the message and extracted facts.
    """
    text = _normalize_text(raw_message)

    tags: list[str] = []

    missing_fields = normalized_facts.get("missing_fields", [])
    if not isinstance(missing_fields, list):
        missing_fields = []

    product_requested = str(normalized_facts.get("product_requested", "")).strip()
    destination_country_code = str(normalized_facts.get("destination_country_code", "")).strip()
    company_name = str(normalized_facts.get("company_name", "")).strip()
    sender_email = str(normalized_facts.get("sender_email", "")).strip()

    purchase_signal_present = _has_any_pattern(text, PURCHASE_SIGNALS)

    # 1. Low purchase intent:
    # message mainly asks for price/catalog without clear buying context
    if _has_any_pattern(text, LOW_INTENT_PATTERNS) and not purchase_signal_present:
        tags.append("low_purchase_intent")

    # 2. Information fishing:
    # asks for extensive business or technical information with limited transaction context
    if _has_any_pattern(text, INFO_FISHING_PATTERNS):
        tags.append("information_fishing")

    # 3. Incomplete buyer profile:
    # important sender / company context is missing
    incomplete_count = 0
    if not company_name:
        incomplete_count += 1
    if not sender_email:
        incomplete_count += 1
    if not destination_country_code:
        incomplete_count += 1
    if not product_requested:
        incomplete_count += 1

    if incomplete_count >= 2 or len(missing_fields) >= 2:
        tags.append("incomplete_buyer_profile")

    # 4. Mass inquiry:
    # generic short inquiry with little specific detail
    if _has_any_pattern(text, MASS_INQUIRY_PATTERNS):
        if len(text) < 300:
            tags.append("mass_inquiry")

    # Remove duplicate tags
    tags = sorted(set(tags))

    summary = None
    if tags:
        summary = f"Intent/conversation risk tags matched: {', '.join(tags)}."

    return {
        "category": "intent_conversation",
        "tags": tags,
        "summary": summary,
    }