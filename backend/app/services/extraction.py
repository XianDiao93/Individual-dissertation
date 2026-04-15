# backend/app/services/extraction.py

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from typing import Any, Dict, Optional

from app.config import PROJECT_ROOT
from app.services.llm_client import client


# Path to extraction prompt config
EXTRACTION_PROMPT_PATH = (
    PROJECT_ROOT / "backend" / "app" / "database" / "system_prompts" / "extraction_basic.json"
)

# Path to country code / alias mapping
COUNTRY_CODES_PATH = (
    PROJECT_ROOT / "backend" / "app" / "database" / "regions" / "country_codes.json"
)


@lru_cache(maxsize=1)
def _load_extraction_prompt_bundle() -> Dict[str, Any]:
    """
    Load extraction prompt bundle from JSON.
    """
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
    """
    Build system prompt and user prompt for extraction.
    """
    bundle = _load_extraction_prompt_bundle()

    system_prompt = str(bundle["system_prompt"]).strip()
    user_prompt_template = str(bundle["user_prompt_template"])

    user_prompt = user_prompt_template.format(
        message=message,
        user_region=user_region or "N/A",
        preferred_language=preferred_language or "N/A",
    )

    return system_prompt, user_prompt, bundle


def _strip_accents(text: str) -> str:
    """
    Remove accent marks from text for easier normalization.
    """
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(ch)
    )


def _normalize_country_key(text: str) -> str:
    """
    Normalize country name / alias into a comparable lookup key.
    """
    text = (text or "").strip()
    if not text:
        return ""

    text = _strip_accents(text)
    text = text.lower()
    text = text.replace("&", " and ")

    text = re.sub(r"[’'`´]", "", text)
    text = re.sub(r"[()_,./\\\-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


@lru_cache(maxsize=1)
def _load_country_data() -> tuple[Dict[str, str], Dict[str, str]]:
    """
    Load canonical country names and alias lookup table.
    """
    if not COUNTRY_CODES_PATH.exists():
        return {}, {}

    with COUNTRY_CODES_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        return {}, {}

    canonical_names: Dict[str, str] = {}
    alias_lookup: Dict[str, str] = {}

    if "canonical_names" in data or "aliases" in data:
        raw_canonical = data.get("canonical_names", {})
        raw_aliases = data.get("aliases", {})

        if not isinstance(raw_canonical, dict):
            raw_canonical = {}
        if not isinstance(raw_aliases, dict):
            raw_aliases = {}

        for code, name in raw_canonical.items():
            code_str = str(code).strip().upper()
            name_str = str(name).strip()
            if code_str:
                canonical_names[code_str] = name_str

        for alias, code in raw_aliases.items():
            alias_str = str(alias).strip()
            code_str = str(code).strip().upper()
            if not alias_str or not code_str:
                continue
            alias_lookup[_normalize_country_key(alias_str)] = code_str

    else:
        for code, name in data.items():
            code_str = str(code).strip().upper()
            name_str = str(name).strip()
            if code_str:
                canonical_names[code_str] = name_str

    # Add canonical country names and country codes into alias lookup
    for code, name in canonical_names.items():
        norm_name = _normalize_country_key(name)
        if norm_name:
            alias_lookup[norm_name] = code

        alias_lookup[_normalize_country_key(code)] = code

    return canonical_names, alias_lookup


def _clean_str(value: Any) -> str:
    """
    Normalize string-like values and convert null-like values to empty string.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        value = value.strip()
        if value.lower() in {"none", "null", "n/a", "unknown", "not provided"}:
            return ""
        return value
    return str(value).strip()


def _is_ambiguous_country_value(value: Any) -> bool:
    """
    Check whether a country value is explicitly marked as ambiguous.
    """
    return _clean_str(value).lower() == "ambiguous"


def _country_name_to_code(country_name: str) -> str:
    """
    Convert country name or alias into ISO-like country code if possible.
    """
    if not country_name:
        return ""

    raw = country_name.strip()
    if not raw:
        return ""

    if _is_ambiguous_country_value(raw):
        return ""

    canonical_names, alias_lookup = _load_country_data()

    upper = raw.upper()
    if upper in canonical_names:
        return upper

    norm = _normalize_country_key(raw)
    if not norm:
        return ""

    code = alias_lookup.get(norm)
    if code:
        return code

    # Exact alias match fallback
    for known_alias, known_code in alias_lookup.items():
        if norm == known_alias:
            return known_code

    # Loose containment fallback
    for known_alias, known_code in alias_lookup.items():
        if norm in known_alias or known_alias in norm:
            return known_code

    return ""


def _code_to_canonical_country_name(code: str) -> str:
    """
    Convert country code back to canonical country name.
    """
    if not code:
        return ""
    canonical_names, _ = _load_country_data()
    return canonical_names.get(code.strip().upper(), "")


def _strip_code_fences(text: str) -> str:
    """
    Remove Markdown code fences from model output.
    """
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _extract_json_object(text: str) -> str:
    """
    Extract the main JSON object from raw model output.
    """
    text = _strip_code_fences(text)

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start: end + 1]

    return text


def _safe_json_loads(text: str) -> Dict[str, Any]:
    """
    Parse JSON safely, with simple repair for minor formatting issues.
    """
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


def _guess_message_type(raw_message: str, llm_value: str) -> str:
    """
    Infer message type as email or chat.
    """
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
    """
    Detect important fields that are still missing after extraction.
    """
    important_fields = [
        "product_requested",
        "origin_country_code",
        "recipient_address",
    ]
    return [field for field in important_fields if not _clean_str(data.get(field))]


def _detect_ambiguity_flags(data: Dict[str, Any]) -> list[str]:
    """
    Detect ambiguity flags for extracted country fields.
    """
    flags: list[str] = []

    if _is_ambiguous_country_value(data.get("origin_country_name")):
        flags.append("origin_country_ambiguous")

    if _is_ambiguous_country_value(data.get("destination_country_name")):
        flags.append("destination_country_ambiguous")

    return flags


def _ensure_required_fields(
    llm_data: Dict[str, Any],
    required_fields: list[str],
    default_values: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Ensure all required fields exist in extraction output.
    """
    result: Dict[str, Any] = {}
    for field in required_fields:
        result[field] = llm_data.get(field, default_values.get(field, ""))
    return result


def _normalize_country_fields(base: Dict[str, Any]) -> tuple[str, str, str, str]:
    """
    Normalize origin and destination country names and codes.
    """
    raw_origin = _clean_str(base.get("origin_country_name"))
    raw_destination = _clean_str(base.get("destination_country_name"))

    if _is_ambiguous_country_value(raw_origin):
        origin_code = ""
        origin_name = "ambiguous"
    else:
        origin_code = _country_name_to_code(raw_origin)
        origin_name = _code_to_canonical_country_name(origin_code) or raw_origin

    if _is_ambiguous_country_value(raw_destination):
        destination_code = ""
        destination_name = "ambiguous"
    else:
        destination_code = _country_name_to_code(raw_destination)
        destination_name = _code_to_canonical_country_name(destination_code) or raw_destination

    return origin_name, origin_code, destination_name, destination_code


def _postprocess_extraction(
    raw_message: str,
    llm_data: Dict[str, Any],
    required_fields: list[str],
    default_values: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Postprocess raw LLM extraction output into normalized trade facts.
    """
    base = _ensure_required_fields(llm_data, required_fields, default_values)

    (
        origin_country_name,
        origin_country_code,
        destination_country_name,
        destination_country_code,
    ) = _normalize_country_fields(base)

    result: Dict[str, Any] = {
        "raw_text": raw_message,
        "message_type": _guess_message_type(raw_message, _clean_str(base.get("message_type"))),
        "language": _clean_str(base.get("language")),
        "product_requested": _clean_str(base.get("product_requested")),
        "quantity": _clean_str(base.get("quantity")),
        "origin_country_name": origin_country_name,
        "origin_country_code": origin_country_code,
        "destination_country_name": destination_country_name,
        "destination_country_code": destination_country_code,
        "recipient_address": _clean_str(base.get("recipient_address")),
        "sender_name": _clean_str(base.get("sender_name")),
        "sender_email": _clean_str(base.get("sender_email")),
        "company_name": _clean_str(base.get("company_name")),
        "intent_summary": _clean_str(base.get("intent_summary")),
    }

    result["missing_fields"] = _detect_missing_fields(result)
    result["ambiguity_flags"] = _detect_ambiguity_flags(result)
    return result


def _build_empty_result(
    raw_message: str,
    preferred_language: Optional[str],
    required_fields: list[str],
    default_values: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build an empty extraction result for blank input.
    """
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
    result["ambiguity_flags"] = []
    return result


def extract_trade_facts(
    message: str,
    user_region: Optional[str] = None,
    preferred_language: Optional[str] = None,
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """
    Extract structured trade facts from an input message.
    """
    raw_message = (message or "").strip()

    bundle = _load_extraction_prompt_bundle()
    required_fields = list(bundle.get("required_fields", []))
    default_values = dict(bundle.get("default_values", {}))

    # Return empty structured result for blank input
    if not raw_message:
        return _build_empty_result(
            raw_message="",
            preferred_language=preferred_language,
            required_fields=required_fields,
            default_values=default_values,
        )

    # Build prompts for extraction
    system_prompt, user_prompt, _ = _build_prompts(
        message=raw_message,
        user_region=user_region,
        preferred_language=preferred_language,
    )

    # Call LLM for JSON extraction
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

    # Parse and normalize extraction result
    llm_data = _safe_json_loads(output_text)

    return _postprocess_extraction(
        raw_message=raw_message,
        llm_data=llm_data,
        required_fields=required_fields,
        default_values=default_values,
    )