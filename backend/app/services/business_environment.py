# backend/app/services/business_environment.py

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Dict

from app.config import PROJECT_ROOT


# Path to country-level business environment risk tags database
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
    """
    Load country-level business environment risk tags from JSON.

    Returns:
        Dict[str, list[str]]: Mapping of country_code -> list of risk tags
    """
    if not COUNTRY_TAGS_PATH.exists():
        return {}

    with COUNTRY_TAGS_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        return {}

    # Normalize keys and values
    result: Dict[str, list[str]] = {}
    for code, tags in data.items():
        if isinstance(tags, list):
            result[str(code).upper()] = [str(tag) for tag in tags]
    return result


def analyze(normalized_facts: Dict[str, Any], raw_message: str = "") -> Dict[str, Any]:
    """
    Analyze business environment risks based on destination country.

    Args:
        normalized_facts: Structured trade facts (e.g., country codes)
        raw_message: Original user message (not used here but kept for interface consistency)

    Returns:
        Dict with:
        - category: risk category name
        - tags: list of matched risk tags
        - summary: optional human-readable explanation
    """
    # Extract destination country code
    country_code = str(normalized_facts.get("destination_country_code", "")).upper().strip()

    # Load risk tag database
    db = _load_country_tags()

    # Retrieve tags for the country
    tags = db.get(country_code, [])

    # Build summary if any tags exist
    summary = None
    if tags:
        summary = f"Destination country {country_code} matched business-environment risk tags: {', '.join(tags)}."

    return {
        "category": "business_environment",
        "tags": tags,
        "summary": summary,
    }