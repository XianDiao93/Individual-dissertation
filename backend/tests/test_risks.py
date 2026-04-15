# tests/test_risk.py
from app.services.risk import analyze_risks

def test_analyze_risks_builds_expected_structure(monkeypatch):
    monkeypatch.setattr(
        "app.services.risk._run_modules",
        lambda normalized_facts, raw_message: [
            {"category": "product", "tags": ["dual_use_goods"], "summary": "Potentially sensitive goods."},
            {"category": "transaction_fraud", "tags": ["unverified_counterparty"], "summary": ""},
        ],
    )
    monkeypatch.setattr(
        "app.services.risk.load_tag_metadata_map",
        lambda: {
            "dual_use_goods": {"severity": "medium", "description": "Sensitive product."},
            "unverified_counterparty": {"severity": "medium", "description": "Counterparty not verified."},
        },
    )
    monkeypatch.setattr(
        "app.services.risk.load_tag_severity_map",
        lambda: {
            "dual_use_goods": "medium",
            "unverified_counterparty": "medium",
        },
    )

    result = analyze_risks({"origin_country_code": "FR"}, raw_message="hello")

    assert "decision" in result
    assert "risk_tags" in result
    assert "risk" in result
    assert "by_category" in result
    assert result["risk"]["tags"][0]["tag"] in {"dual_use_goods", "unverified_counterparty"}