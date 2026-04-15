# tests/test_extraction_helpers.py
from app.services.extraction import (
    _normalize_country_key,
    _safe_json_loads,
    _guess_message_type,
    _postprocess_extraction,
)

def test_normalize_country_key():
    assert _normalize_country_key("Côte d’Ivoire") == "cote divoire"
    assert _normalize_country_key("United-States") == "united states"

def test_safe_json_loads_with_code_fence():
    text = """```json
    {"language": "en", "message_type": "email"}
    ```"""
    data = _safe_json_loads(text)
    assert data["language"] == "en"
    assert data["message_type"] == "email"

def test_guess_message_type_email():
    msg = "Dear Sir,\nThank you.\nBest regards,"
    assert _guess_message_type(msg, "") == "email"

def test_postprocess_extraction_detects_missing_fields():
    llm_data = {
        "message_type": "email",
        "language": "en",
        "product_requested": "",
        "origin_country_name": "",
        "recipient_address": "",
    }
    result = _postprocess_extraction(
        raw_message="Hello",
        llm_data=llm_data,
        required_fields=[
            "message_type",
            "language",
            "product_requested",
            "origin_country_name",
            "destination_country_name",
            "recipient_address",
            "quantity",
            "sender_name",
            "sender_email",
            "company_name",
            "intent_summary",
        ],
        default_values={},
    )
    assert "product_requested" in result["missing_fields"]
    assert "origin_country_code" in result["missing_fields"]
    assert "recipient_address" in result["missing_fields"]