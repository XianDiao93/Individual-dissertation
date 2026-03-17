# backend/app/services/decision_engine.py

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

# 每个 tag 的累计权重
SEVERITY_SCORE = {
    "critical": 10,
    "high": 6,
    "medium": 3,
    "low": 1,
    "unknown": 0,
}


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
        return "unknown"

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
    把累计分数映射为综合等级。
    这些阈值可以后续根据测试数据继续调。
    """
    if total_score <= 0:
        return "unknown"
    if total_score <= 2:
        return "low"
    if total_score <= 7:
        return "medium"
    if total_score <= 14:
        return "high"
    return "critical"


def _final_level_from_severities(severities: List[str]) -> str:
    """
    综合规则：
    1. critical 直接 critical
    2. 用加权总分计算基础等级
    3. 若存在 high，则最终等级至少为 high
    """
    if not severities:
        return "unknown"

    normalized = [_normalize_severity(s) for s in severities]
    highest = _highest_severity(normalized)

    # 硬触发：只要有 critical，直接 critical
    if highest == "critical":
        return "critical"

    total_score = _score_from_severities(normalized)
    level = _level_from_total_score(total_score)

    # 保底规则：只要出现 high，最终等级至少为 high
    if highest == "high" and SEVERITY_PRIORITY[level] < SEVERITY_PRIORITY["high"]:
        return "high"

    return level


def decide_from_tags(tags: List[str], tag_severity_map: Dict[str, str]) -> Dict[str, str | int | List[str]]:
    """
    Decide the final routing action from risk tags.

    Returns:
    {
        "decision": "CLEAR" | "WARN" | "BLOCK",
        "level": "low" | "medium" | "high" | "critical" | "unknown",
        "total_score": int,
        "severities": [...]
    }
    """
    if not tags:
        return {
            "decision": "CLEAR",
            "level": "unknown",
            "total_score": 0,
            "severities": [],
        }

    severities = [
        _normalize_severity(tag_severity_map.get(tag, "unknown"))
        for tag in tags
    ]

    total_score = _score_from_severities(severities)
    level = _final_level_from_severities(severities)
    decision = SEVERITY_TO_DECISION.get(level, "CLEAR")

    return {
        "decision": decision,
        "level": level,
        "total_score": total_score,
        "severities": severities,
    }