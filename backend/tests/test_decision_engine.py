# tests/test_decision_engine.py
from app.services.decision_engine import decide_from_tags, NO_RISK_TAG

def test_no_tags_returns_low_and_no_risk_tag():
    result = decide_from_tags([], {})
    assert result["decision"] == "CLEAR"
    assert result["level"] == "low"
    assert result["total_score"] == 0
    assert result["effective_tags"] == [NO_RISK_TAG]

def test_single_low_tag_stays_low():
    result = decide_from_tags(["tag_a"], {"tag_a": "low"})
    assert result["level"] == "low"
    assert result["decision"] == "CLEAR"

def test_many_low_tags_upgrade_to_medium():
    result = decide_from_tags(
        ["a", "b", "c", "d", "e"],
        {"a": "low", "b": "low", "c": "low", "d": "low", "e": "low"}
    )
    assert result["level"] == "medium"
    assert result["decision"] == "WARN"

def test_high_tag_forces_high():
    result = decide_from_tags(["tag_a"], {"tag_a": "high"})
    assert result["level"] == "high"
    assert result["decision"] == "BLOCK"

def test_critical_tag_forces_critical():
    result = decide_from_tags(["tag_a"], {"tag_a": "critical"})
    assert result["level"] == "critical"
    assert result["decision"] == "BLOCK"