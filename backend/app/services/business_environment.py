# backend/app/services/business_environment.py

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Dict

from app.config import PROJECT_ROOT


COUNTRY_TAGS_PATH = (
    PROJECT_ROOT
    / "backend"
    / "app"
    / "database"
    / "risks"
    / "business_environment"
    / "country_tags.json"
)


@lru_cache(maxsize=1)
def _load_country_tags() -> Dict[str, list[str]]:
    if not COUNTRY_TAGS_PATH.exists():
        return {}

    with COUNTRY_TAGS_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        return {}

    result: Dict[str, list[str]] = {}
    for code, tags in data.items():
        if isinstance(tags, list):
            result[str(code).upper()] = [str(tag) for tag in tags]
    return result


def analyze(normalized_facts: Dict[str, Any], raw_message: str = "") -> Dict[str, Any]:
    country_code = str(normalized_facts.get("destination_country_code", "")).upper().strip()
    db = _load_country_tags()

    tags = db.get(country_code, [])

    summary = None
    if tags:
        summary = f"Destination country {country_code} matched business-environment risk tags: {', '.join(tags)}."

    return {
        "category": "business_environment",
        "tags": tags,
        "summary": summary,
    }