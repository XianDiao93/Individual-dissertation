# tests/test_llm_client_helpers.py
import os
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from app.services.llm_client import (
    _normalize_optional_text,
    _resolve_output_language,
    _cleanup_generated_reply,
)

def test_normalize_optional_text():
    assert _normalize_optional_text(None) is None
    assert _normalize_optional_text("   ") is None
    assert _normalize_optional_text("null") is None
    assert _normalize_optional_text(" Alice ") == "Alice"

def test_resolve_output_language_from_country_code():
    facts = {"origin_country_code": "FR"}
    lang = _resolve_output_language("auto", facts, "Hello")
    assert lang == "fr"

def test_resolve_output_language_from_message_heuristic():
    lang = _resolve_output_language("auto", {}, "Bonjour, merci beaucoup")
    assert lang == "fr"

def test_cleanup_generated_reply_removes_headers_and_placeholders():
    raw = """Subject: Test
From: x@example.com

Dear Customer,

Thank you for your message.

Best regards,
[Your Name]
[Your Company Name]
"""
    cleaned = _cleanup_generated_reply(
        raw,
        reply_form="email",
        sender_name="Xian Diao",
        company_name="DIOX Ltd.",
        email=None,
        phone=None,
    )

    assert "Subject:" not in cleaned
    assert "From:" not in cleaned
    assert "[Your Name]" not in cleaned
    assert "[Your Company Name]" not in cleaned
    assert "Xian Diao" in cleaned
    assert "DIOX Ltd." in cleaned