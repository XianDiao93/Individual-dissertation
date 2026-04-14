from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

from app.config import PROJECT_ROOT
from app.services.business_environment import analyze as analyze_business_environment
from app.services.decision_engine import decide_from_tags
from app.services.political_geopolitical import analyze as analyze_political_geopolitical
from app.services.product import analyze as analyze_product
from app.services.intent_conversation import analyze as analyze_intent_conversation
from app.services.transaction_fraud import analyze as analyze_transaction_fraud


RISKS_DIR = (
    PROJECT_ROOT
    / "backend"
    / "app"
    / "database"
    / "risks"
)


def _safe_load_json(path: Path) -> Any:
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_risk_categories() -> List[str]:
    """
    Load risk category names from risk_categories.json if available.
    Fallback to currently implemented categories.
    """
    path = RISKS_DIR / "risk_categories.json"
    data = _safe_load_json(path)

    if isinstance(data, list):
        return [str(item).strip() for item in data if str(item).strip()]

    return [
        "political_geopolitical",
        "business_environment",
        "product",
        "intent_conversation",
        "transaction_fraud",
    ]


@lru_cache(maxsize=1)
def load_tag_metadata_map() -> Dict[str, Dict[str, str]]:
    """
    Load tag metadata from all category tags.json files.

    Expected tag object shape:
    {
      "tag": "dual_use_goods",
      "severity": "medium",
      "description": "..."
    }
    """
    metadata_map: Dict[str, Dict[str, str]] = {}

    for category in load_risk_categories():
        tags_file = RISKS_DIR / category / "tags.json"
        data = _safe_load_json(tags_file)

        if not isinstance(data, list):
            continue

        for item in data:
            if not isinstance(item, dict):
                continue

            tag = str(item.get("tag", "")).strip()
            if not tag:
                continue

            metadata_map[tag] = {
                "severity": str(item.get("severity", "unknown")).strip().lower(),
                "description": str(item.get("description", "")).strip(),
            }

    return metadata_map


@lru_cache(maxsize=1)
def load_tag_severity_map() -> Dict[str, str]:
    metadata_map = load_tag_metadata_map()
    return {
        tag: meta.get("severity", "unknown")
        for tag, meta in metadata_map.items()
    }


def _clean_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _get_ambiguity_flags(normalized_facts: Dict[str, Any]) -> List[str]:
    flags = normalized_facts.get("ambiguity_flags", [])
    if isinstance(flags, list):
        return [str(x).strip() for x in flags if str(x).strip()]
    return []


def _run_modules(normalized_facts: Dict[str, Any], raw_message: str) -> List[Dict[str, Any]]:
    return [
        analyze_political_geopolitical(
            normalized_facts=normalized_facts,
            raw_message=raw_message,
        ),
        analyze_business_environment(
            normalized_facts=normalized_facts,
            raw_message=raw_message,
        ),
        analyze_product(
            normalized_facts=normalized_facts,
            raw_message=raw_message,
        ),
        analyze_intent_conversation(
            normalized_facts=normalized_facts,
            raw_message=raw_message,
        ),
        analyze_transaction_fraud(
            normalized_facts=normalized_facts,
            raw_message=raw_message,
        ),
    ]


def _flatten_unique_tags(module_results: List[Dict[str, Any]]) -> List[str]:
    tags: List[str] = []

    for result in module_results:
        result_tags = result.get("tags", [])
        if isinstance(result_tags, list):
            tags.extend(str(tag).strip() for tag in result_tags if str(tag).strip())

    return sorted(set(tags))


def _build_by_category(module_results: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    by_category: Dict[str, List[str]] = {}

    for result in module_results:
        category = str(result.get("category", "")).strip()
        tags = result.get("tags", [])

        if not category:
            continue

        if isinstance(tags, list):
            by_category[category] = [str(tag) for tag in tags]
        else:
            by_category[category] = []

    return by_category


def _build_summary(
    tags: List[str],
    module_results: List[Dict[str, Any]],
    tag_metadata_map: Dict[str, Dict[str, str]],
    normalized_facts: Dict[str, Any],
) -> str | None:
    """
    Prefer module summaries.
    Only use extraction-quality notes as a lightweight supplement,
    so they do not dominate the communication prompt and over-bias
    the reply toward country/location questions.
    """
    parts: List[str] = []

    for result in module_results:
        summary = result.get("summary")
        if summary:
            summary_text = str(summary).strip()
            if summary_text:
                parts.append(summary_text)

    origin_country_code = _clean_str(normalized_facts.get("origin_country_code"))
    ambiguity_flags = _get_ambiguity_flags(normalized_facts)

    extraction_notes: List[str] = []
    if not origin_country_code:
        extraction_notes.append("Buyer or sender location is not yet confirmed.")
    if "origin_country_ambiguous" in ambiguity_flags:
        extraction_notes.append("Buyer or sender location may need clarification.")

    parts = [p for p in parts if p]

    if parts:
        if extraction_notes:
            parts.extend(extraction_notes)
        return " ".join(parts)

    descriptions = []
    for tag in tags:
        desc = tag_metadata_map.get(tag, {}).get("description", "")
        if desc:
            descriptions.append(desc)

    descriptions = [d for d in descriptions if d]

    if descriptions:
        if extraction_notes:
            descriptions.extend(extraction_notes)
        return " ".join(descriptions)

    if extraction_notes:
        return " ".join(extraction_notes)

    return None


def _build_risk_tag_items(
    tags: List[str],
    tag_severity_map: Dict[str, str],
) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    for tag in tags:
        items.append({
            "tag": tag,
            "severity": tag_severity_map.get(tag, "unknown"),
        })
    return items


def _append_if_available(
    out_tags: List[str],
    candidate_tag: str,
    tag_metadata_map: Dict[str, Dict[str, str]],
) -> None:
    """
    Only append synthetic/helper tags if they already exist in tags.json metadata.
    This avoids returning unknown custom tags that the rest of the system/frontend
    may not understand yet.
    """
    if candidate_tag in tag_metadata_map and candidate_tag not in out_tags:
        out_tags.append(candidate_tag)


def _augment_tags_from_extraction(
    normalized_facts: Dict[str, Any],
    current_tags: List[str],
    tag_metadata_map: Dict[str, Dict[str, str]],
) -> List[str]:
    """
    Add a small number of extraction-driven tags, but only if those tags already
    exist in the configured risk database.

    Current policy:
    - If buyer/sender country is missing -> prefer incomplete_buyer_profile
    - If buyer/sender country is ambiguous -> prefer incomplete_buyer_profile
      and optionally unverified_counterparty
    """
    tags = list(current_tags)

    origin_country_code = _clean_str(normalized_facts.get("origin_country_code"))
    ambiguity_flags = _get_ambiguity_flags(normalized_facts)

    if not origin_country_code:
        _append_if_available(tags, "incomplete_buyer_profile", tag_metadata_map)

    if "origin_country_ambiguous" in ambiguity_flags:
        _append_if_available(tags, "incomplete_buyer_profile", tag_metadata_map)
        _append_if_available(tags, "unverified_counterparty", tag_metadata_map)

    return sorted(set(tags))


def analyze_risks(normalized_facts: Dict[str, Any], raw_message: str = "") -> Dict[str, Any]:
    """
    Central risk controller.

    Returns:
    {
        "decision": "CLEAR" | "WARN" | "BLOCK",
        "risk_tags": [...],
        "risk": {
            "level": "unknown" | "low" | "medium" | "high" | "critical",
            "tags": [...],
            "summary": "..."
        },
        "by_category": {
            "political_geopolitical": [...],
            "business_environment": [...],
            "product": [...],
            "intent_conversation": [...],
            "transaction_fraud": [...]
        }
    }
    """
    module_results = _run_modules(
        normalized_facts=normalized_facts,
        raw_message=raw_message,
    )

    base_risk_tags = _flatten_unique_tags(module_results)
    by_category = _build_by_category(module_results)

    tag_metadata_map = load_tag_metadata_map()
    tag_severity_map = load_tag_severity_map()

    risk_tags = _augment_tags_from_extraction(
        normalized_facts=normalized_facts,
        current_tags=base_risk_tags,
        tag_metadata_map=tag_metadata_map,
    )

    decision_result = decide_from_tags(
        tags=risk_tags,
        tag_severity_map=tag_severity_map,
    )

    risk_tag_items = _build_risk_tag_items(
        tags=risk_tags,
        tag_severity_map=tag_severity_map,
    )

    summary = _build_summary(
        tags=risk_tags,
        module_results=module_results,
        tag_metadata_map=tag_metadata_map,
        normalized_facts=normalized_facts,
    )

    return {
        "decision": decision_result["decision"],
        "risk_tags": risk_tags,
        "risk": {
            "level": decision_result["level"],
            "tags": risk_tag_items,
            "summary": summary,
        },
        "by_category": by_category,
    }