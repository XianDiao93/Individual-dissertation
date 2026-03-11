# backend/app/services/extraction.py

from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any, Dict, Optional

from app.config import PROJECT_ROOT
from app.services.llm_client import client


EXTRACTION_PROMPT_PATH = (
    PROJECT_ROOT / "backend" / "app" / "database" / "system_prompts" / "extraction_basic.json"
)

COUNTRY_CODES_PATH = (
    PROJECT_ROOT / "backend" / "app" / "database" / "regions" / "country_codes.json"
)


@lru_cache(maxsize=1)
def _load_extraction_prompt_bundle() -> Dict[str, Any]:
    if not EXTRACTION_PROMPT_PATH.exists():
        raise FileNotFoundError(f"Extraction prompt file not found: {EXTRACTION_PROMPT_PATH}")

    with EXTRACTION_PROMPT_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("extraction_basic.json must contain a JSON object.")

    required_keys = [
        "system_prompt",
        "user_prompt_template",
        "required_fields",
        "default_values",
    ]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing key '{key}' in extraction_basic.json")

    return data


def _build_prompts(
    message: str,
    user_region: Optional[str] = None,
    preferred_language: Optional[str] = None,
) -> tuple[str, str, Dict[str, Any]]:
    bundle = _load_extraction_prompt_bundle()

    system_prompt = str(bundle["system_prompt"]).strip()
    user_prompt_template = str(bundle["user_prompt_template"])

    user_prompt = user_prompt_template.format(
        message=message,
        user_region=user_region or "N/A",
        preferred_language=preferred_language or "N/A",
    )

    return system_prompt, user_prompt, bundle


@lru_cache(maxsize=1)
def _load_country_codes() -> Dict[str, str]:
    if not COUNTRY_CODES_PATH.exists():
        return {}

    with COUNTRY_CODES_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        return {}

    return {str(code).upper(): str(name) for code, name in data.items()}


def _normalize_country_key(text: str) -> str:
    text = (text or "").strip().lower()
    text = text.replace("&", "and")
    text = re.sub(r"[()_,./\-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


@lru_cache(maxsize=1)
def _build_country_name_lookup() -> Dict[str, str]:
    code_to_name = _load_country_codes()
    lookup: Dict[str, str] = {}

    for code, name in code_to_name.items():
        norm_name = _normalize_country_key(name)
        if norm_name:
            lookup[norm_name] = code

    aliases = {
        "uk": "GB",
        "u.k.": "GB",
        "britain": "GB",
        "great britain": "GB",
        "england": "GB",
        "usa": "US",
        "u.s.": "US",
        "u.s.a.": "US",
        "united states of america": "US",
        "uae": "AE",
        "u.a.e.": "AE",
        "south korea": "KR",
        "north korea": "KP",
        "dr congo": "CD",
        "drc": "CD",
        "democratic republic of the congo": "CD",
        "congo drc": "CD",
        "ivory coast": "CI",
        "czechia": "CZ",
    }

    for alias, code in aliases.items():
        lookup[_normalize_country_key(alias)] = code

    return lookup


def _country_name_to_code(country_name: str) -> str:
    if not country_name:
        return ""

    raw = country_name.strip()
    upper = raw.upper()

    code_to_name = _load_country_codes()
    if upper in code_to_name:
        return upper

    lookup = _build_country_name_lookup()
    norm = _normalize_country_key(raw)

    if norm in lookup:
        return lookup[norm]

    for known_name, code in lookup.items():
        if norm == known_name or norm in known_name or known_name in norm:
            return code

    return ""


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _extract_json_object(text: str) -> str:
    text = _strip_code_fences(text)

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return text


def _safe_json_loads(text: str) -> Dict[str, Any]:
    candidate = _extract_json_object(text)

    try:
        data = json.loads(candidate)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    repaired = candidate.replace("\r\n", "\n").replace("\r", "\n")
    repaired = re.sub(r",\s*}", "}", repaired)
    repaired = re.sub(r",\s*]", "]", repaired)

    try:
        data = json.loads(repaired)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    return {}


def _clean_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        value = value.strip()
        if value.lower() in {"none", "null", "n/a", "unknown", "not provided"}:
            return ""
        return value
    return str(value).strip()


def _guess_message_type(raw_message: str, llm_value: str) -> str:
    val = _clean_str(llm_value).lower()
    if val in {"email", "chat"}:
        return val

    msg = raw_message.lower()
    email_signals = [
        "dear ",
        "best regards",
        "kind regards",
        "sincerely",
        "subject:",
        "from:",
        "to:",
    ]
    if any(signal in msg for signal in email_signals):
        return "email"

    return "chat"


def _detect_missing_fields(data: Dict[str, Any]) -> list[str]:
    important_fields = [
        "product_requested",
        "destination_country_code",
        "recipient_address",
    ]
    return [field for field in important_fields if not _clean_str(data.get(field))]


def _ensure_required_fields(
    llm_data: Dict[str, Any],
    required_fields: list[str],
    default_values: Dict[str, Any],
) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for field in required_fields:
        result[field] = llm_data.get(field, default_values.get(field, ""))
    return result


def _postprocess_extraction(
    raw_message: str,
    llm_data: Dict[str, Any],
    required_fields: list[str],
    default_values: Dict[str, Any],
) -> Dict[str, Any]:
    base = _ensure_required_fields(llm_data, required_fields, default_values)

    origin_country_name = _clean_str(base.get("origin_country_name"))
    destination_country_name = _clean_str(base.get("destination_country_name"))

    result: Dict[str, Any] = {
        "raw_text": raw_message,
        "message_type": _guess_message_type(raw_message, _clean_str(base.get("message_type"))),
        "language": _clean_str(base.get("language")),
        "product_requested": _clean_str(base.get("product_requested")),
        "quantity": _clean_str(base.get("quantity")),
        "origin_country_name": origin_country_name,
        "origin_country_code": _country_name_to_code(origin_country_name),
        "destination_country_name": destination_country_name,
        "destination_country_code": _country_name_to_code(destination_country_name),
        "recipient_address": _clean_str(base.get("recipient_address")),
        "sender_name": _clean_str(base.get("sender_name")),
        "sender_email": _clean_str(base.get("sender_email")),
        "company_name": _clean_str(base.get("company_name")),
        "intent_summary": _clean_str(base.get("intent_summary")),
    }

    result["missing_fields"] = _detect_missing_fields(result)
    return result


def _build_empty_result(
    raw_message: str,
    preferred_language: Optional[str],
    required_fields: list[str],
    default_values: Dict[str, Any],
) -> Dict[str, Any]:
    base = {field: default_values.get(field, "") for field in required_fields}

    result: Dict[str, Any] = {
        "raw_text": raw_message,
        "message_type": "chat",
        "language": preferred_language or _clean_str(base.get("language")),
        "product_requested": _clean_str(base.get("product_requested")),
        "quantity": _clean_str(base.get("quantity")),
        "origin_country_name": _clean_str(base.get("origin_country_name")),
        "origin_country_code": "",
        "destination_country_name": _clean_str(base.get("destination_country_name")),
        "destination_country_code": "",
        "recipient_address": _clean_str(base.get("recipient_address")),
        "sender_name": _clean_str(base.get("sender_name")),
        "sender_email": _clean_str(base.get("sender_email")),
        "company_name": _clean_str(base.get("company_name")),
        "intent_summary": _clean_str(base.get("intent_summary")),
    }

    result["missing_fields"] = _detect_missing_fields(result)
    return result


def extract_trade_facts(
    message: str,
    user_region: Optional[str] = None,
    preferred_language: Optional[str] = None,
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    raw_message = (message or "").strip()

    bundle = _load_extraction_prompt_bundle()
    required_fields = list(bundle.get("required_fields", []))
    default_values = dict(bundle.get("default_values", {}))

    if not raw_message:
        return _build_empty_result(
            raw_message="",
            preferred_language=preferred_language,
            required_fields=required_fields,
            default_values=default_values,
        )

    system_prompt, user_prompt, _ = _build_prompts(
        message=raw_message,
        user_region=user_region,
        preferred_language=preferred_language,
    )

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    output_text = getattr(response, "output_text", None)
    if not output_text:
        output_text = str(response)

    llm_data = _safe_json_loads(output_text)

    return _postprocess_extraction(
        raw_message=raw_message,
        llm_data=llm_data,
        required_fields=required_fields,
        default_values=default_values,
    )