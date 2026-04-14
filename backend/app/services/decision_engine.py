from __future__ import annotations

from typing import Dict, List


SEVERITY_TO_DECISION = {
    "critical": "BLOCK",
    "high": "BLOCK",
    "medium": "WARN",
    "low": "CLEAR",
    "unknown": "CLEAR",
}

SEVERITY_PRIORITY = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "unknown": 0,
}

SEVERITY_SCORE = {
    "critical": 10,
    "high": 6,
    "medium": 3,
    "low": 1,
    "unknown": 0,
}

NO_RISK_TAG = "no_risk_recognised"


def _normalize_severity(severity: str | None) -> str:
    sev = (severity or "unknown").lower().strip()
    if sev not in SEVERITY_PRIORITY:
        return "unknown"
    return sev


def _score_from_severities(severities: List[str]) -> int:
    total = 0
    for severity in severities:
        sev = _normalize_severity(severity)
        total += SEVERITY_SCORE.get(sev, 0)
    return total


def _highest_severity(severities: List[str]) -> str:
    if not severities:
        return "low"

    best = "unknown"
    best_score = -1

    for severity in severities:
        sev = _normalize_severity(severity)
        score = SEVERITY_PRIORITY.get(sev, 0)
        if score > best_score:
            best = sev
            best_score = score

    return best


def _level_from_total_score(total_score: int) -> str:

    if total_score <= 2:
        return "low"
    if total_score <= 7:
        return "medium"
    if total_score <= 14:
        return "high"
    return "critical"


def _final_level_from_severities(severities: List[str]) -> str:

    if not severities:
        return "low"

    normalized = [_normalize_severity(s) for s in severities]
    highest = _highest_severity(normalized)

    if highest == "critical":
        return "critical"

    total_score = _score_from_severities(normalized)
    level = _level_from_total_score(total_score)

    if highest == "high" and SEVERITY_PRIORITY[level] < SEVERITY_PRIORITY["high"]:
        return "high"

    return level


def decide_from_tags(tags: List[str], tag_severity_map: Dict[str, str]) -> Dict[str, str | int | List[str]]:
    """
    Returns:
    {
        "decision": "CLEAR" | "WARN" | "BLOCK",
        "level": "low" | "medium" | "high" | "critical",
        "total_score": int,
        "severities": [...],
        "effective_tags": [...]
    }
    """
    clean_tags = [str(tag).strip() for tag in tags if str(tag).strip()]

    if not clean_tags:
        return {
            "decision": "CLEAR",
            "level": "low",
            "total_score": 0,
            "severities": [],
            "effective_tags": [NO_RISK_TAG],
        }

    severities = [
        _normalize_severity(tag_severity_map.get(tag, "unknown"))
        for tag in clean_tags
    ]

    total_score = _score_from_severities(severities)
    level = _final_level_from_severities(severities)
    decision = SEVERITY_TO_DECISION.get(level, "CLEAR")

    return {
        "decision": decision,
        "level": level,
        "total_score": total_score,
        "severities": severities,
        "effective_tags": clean_tags,
    }