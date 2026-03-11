# backend/app/services/decision_engine.py

from __future__ import annotations

from typing import Dict, List


SEVERITY_TO_DECISION = {
    "critical": "BLOCK",
    "high": "BLOCK",
    "medium": "WARN",
    "low": "CLEAR",
}


SEVERITY_PRIORITY = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "unknown": 0,
}


def _highest_severity(severities: List[str]) -> str:
    if not severities:
        return "unknown"

    best = "unknown"
    best_score = -1

    for severity in severities:
        sev = (severity or "unknown").lower().strip()
        score = SEVERITY_PRIORITY.get(sev, 0)
        if score > best_score:
            best = sev
            best_score = score

    return best


def decide_from_tags(tags: List[str], tag_severity_map: Dict[str, str]) -> Dict[str, str]:
    """
    Decide the final routing action from risk tags.

    Returns:
    {
        "decision": "CLEAR" | "WARN" | "BLOCK",
        "level": "low" | "medium" | "high" | "critical" | "unknown"
    }
    """
    if not tags:
        return {
            "decision": "CLEAR",
            "level": "unknown",
        }

    severities = [
        tag_severity_map.get(tag, "unknown")
        for tag in tags
    ]

    level = _highest_severity(severities)
    decision = SEVERITY_TO_DECISION.get(level, "CLEAR")

    return {
        "decision": decision,
        "level": level,
    }