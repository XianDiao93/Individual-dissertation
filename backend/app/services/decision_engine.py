from __future__ import annotations

from typing import Dict, List


# Mapping from overall risk level to final decision
SEVERITY_TO_DECISION = {
    "critical": "BLOCK",
    "high": "BLOCK",
    "medium": "WARN",
    "low": "CLEAR",
    "unknown": "CLEAR",
}

# Priority ranking for severity comparison
SEVERITY_PRIORITY = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "unknown": 0,
}

# Numeric score used for aggregated risk calculation
SEVERITY_SCORE = {
    "critical": 10,
    "high": 6,
    "medium": 3,
    "low": 1,
    "unknown": 0,
}

# Default tag used when no risks are detected
NO_RISK_TAG = "no_risk_recognised"


def _normalize_severity(severity: str | None) -> str:
    """
    Normalize severity value and fall back to 'unknown' if invalid.
    """
    sev = (severity or "unknown").lower().strip()
    if sev not in SEVERITY_PRIORITY:
        return "unknown"
    return sev


def _score_from_severities(severities: List[str]) -> int:
    """
    Calculate total numeric risk score from a list of severities.
    """
    total = 0
    for severity in severities:
        sev = _normalize_severity(severity)
        total += SEVERITY_SCORE.get(sev, 0)
    return total


def _highest_severity(severities: List[str]) -> str:
    """
    Return the highest severity from a list.
    """
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
    """
    Convert aggregated numeric score into overall risk level.
    """
    if total_score <= 2:
        return "low"
    if total_score <= 7:
        return "medium"
    if total_score <= 14:
        return "high"
    return "critical"


def _final_level_from_severities(severities: List[str]) -> str:
    """
    Determine final overall risk level from tag severities.

    Rules:
    - No severities -> low
    - Any critical -> critical
    - Otherwise use total score
    - Preserve 'high' if a high-severity tag exists
    """
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
    Decide final risk result from detected tags and tag severity mapping.

    Returns:
    {
        "decision": "CLEAR" | "WARN" | "BLOCK",
        "level": "low" | "medium" | "high" | "critical",
        "total_score": int,
        "severities": [...],
        "effective_tags": [...]
    }
    """
    # Remove empty tag values
    clean_tags = [str(tag).strip() for tag in tags if str(tag).strip()]

    # Return default low-risk result if no tags are present
    if not clean_tags:
        return {
            "decision": "CLEAR",
            "level": "low",
            "total_score": 0,
            "severities": [],
            "effective_tags": [NO_RISK_TAG],
        }

    # Map tags to normalized severities
    severities = [
        _normalize_severity(tag_severity_map.get(tag, "unknown"))
        for tag in clean_tags
    ]

    # Compute total score, final level, and final decision
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