# backend/app/services/product.py

from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any, Dict

from app.config import PROJECT_ROOT


PRODUCT_KEYWORDS_PATH = (
    PROJECT_ROOT
    / "backend"
    / "app"
    / "database"
    / "risks"
    / "product"
    / "product_keywords.json"
)


@lru_cache(maxsize=1)
def _load_product_keywords() -> Dict[str, list[str]]:
    if not PRODUCT_KEYWORDS_PATH.exists():
        return {}

    with PRODUCT_KEYWORDS_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        return {}

    result: Dict[str, list[str]] = {}
    for tag, keywords in data.items():
        if isinstance(keywords, list):
            result[str(tag)] = [str(keyword).lower().strip() for keyword in keywords if str(keyword).strip()]
    return result


def _normalize_text(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[_/,-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def analyze(normalized_facts: Dict[str, Any], raw_message: str = "") -> Dict[str, Any]:
    product_text = str(normalized_facts.get("product_requested", "")).strip()
    haystack = _normalize_text(f"{product_text} {raw_message}")

    db = _load_product_keywords()
    matched_tags: list[str] = []

    for tag, keywords in db.items():
        for keyword in keywords:
            keyword_norm = _normalize_text(keyword)
            if keyword_norm and keyword_norm in haystack:
                matched_tags.append(tag)
                break

    matched_tags = sorted(set(matched_tags))

    summary = None
    if matched_tags:
        summary = f"Product-related risk tags matched from product description/text: {', '.join(matched_tags)}."

    return {
        "category": "product",
        "tags": matched_tags,
        "summary": summary,
    }