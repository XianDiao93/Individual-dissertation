# tests/test_communication.py
from app.services.communication import generate_reply

def test_generate_reply_passes_arguments(monkeypatch):
    captured = {}

    def fake_generate_business_reply(**kwargs):
        captured.update(kwargs)
        return "mocked reply"

    monkeypatch.setattr(
        "app.services.communication.generate_business_reply",
        fake_generate_business_reply
    )

    result = generate_reply(
        message="Hello",
        language="en",
        region="GB",
        normalized_facts={"origin_country_code": "FR"},
        risk_result={"decision": "WARN"},
    )

    assert result == "mocked reply"
    assert captured["message"] == "Hello"
    assert captured["language"] == "en"
    assert captured["region"] == "GB"
    assert captured["normalized_facts"]["origin_country_code"] == "FR"