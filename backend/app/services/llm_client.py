# backend/app/services/llm_client.py
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from openai import OpenAI

from app.config import CHAT_BASIC_PROMPT_PATH, DOC_BASIC_PROMPT_PATH
from app.models.doc_model import BaseDocumentData
from app.utils.llm_doc_utils import (
    cleanup_generated_document_text,
    get_document_purpose,
)
from app.utils.llm_reply_utils import (
    build_country_guidance,
    build_identity_block,
    build_reply_rule_block,
    cleanup_generated_reply,
    normalize_optional_text,
    pick_sender_name,
    resolve_output_language,
)


# =========================================================
# OpenAI client setup
# =========================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY environment variable is not set. "
        "Please set it before starting the backend."
    )

client = OpenAI(api_key=OPENAI_API_KEY)


# =========================================================
# Prompt bundle loaders
# =========================================================

@lru_cache(maxsize=8)
def _load_chat_prompt_bundle() -> dict:
    """
    Load and cache the chat prompt bundle from JSON.
    """
    path = Path(CHAT_BASIC_PROMPT_PATH)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=8)
def _load_doc_prompt_bundle() -> dict:
    """
    Load and cache the document prompt bundle from JSON.
    """
    path = Path(DOC_BASIC_PROMPT_PATH)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# =========================================================
# Public API: communication generation
# =========================================================

def generate_business_reply(
    message: str,
    language: str = "auto",
    region: str = "GB",
    tone: str = "formal",
    reply_form: str = "email",
    user_name: Optional[str] = None,
    name: Optional[str] = None,
    company_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    normalized_facts: Optional[dict] = None,
    risk_result: Optional[dict] = None,
    model: str = "gpt-4o-mini",
) -> str:
    """
    Generate a business reply for an incoming trade message.
    """
    tone_str = (tone or "formal").lower()
    if tone_str not in {"formal", "neutral", "friendly"}:
        tone_str = "formal"

    reply_form_norm = (reply_form or "email").lower()
    if reply_form_norm not in {"email", "chat"}:
        reply_form_norm = "email"

    bundle = _load_chat_prompt_bundle()

    modes = bundle.get("modes", {})
    mode_key = "chat" if reply_form_norm == "chat" else "email"
    mode_cfg = modes.get(mode_key) or modes.get("email") or {}

    system_template = bundle.get("system_template", "")
    section_cfg = bundle.get("user_sections", {})

    safe_user_name = normalize_optional_text(user_name)
    safe_name = normalize_optional_text(name)
    safe_company_name = normalize_optional_text(company_name)
    safe_email = normalize_optional_text(email)
    safe_phone = normalize_optional_text(phone)
    safe_region = normalize_optional_text(region) or "GB"

    safe_facts = dict(normalized_facts or {})
    ambiguity_flags = safe_facts.get("ambiguity_flags", [])
    if not isinstance(ambiguity_flags, list):
        safe_facts["ambiguity_flags"] = []

    safe_risk = dict(risk_result or {})

    resolved_language = resolve_output_language(
        requested_language=language,
        normalized_facts=safe_facts,
        message=message,
    )

    facts_block = json.dumps(safe_facts, indent=2, ensure_ascii=False)
    risk_block = json.dumps(safe_risk, indent=2, ensure_ascii=False)

    system_prompt = system_template.format(
        mode_description=mode_cfg.get("mode_description", ""),
        formatting_instructions=mode_cfg.get("formatting_instructions", ""),
        language=resolved_language,
        region=safe_region,
        tone_str=tone_str,
    )

    identity_block = build_identity_block(
        user_name=safe_user_name,
        name=safe_name,
        company_name=safe_company_name,
        email=safe_email,
        phone=safe_phone,
        region=safe_region,
    )

    country_guidance_block = build_country_guidance(bundle, safe_facts)
    reply_rules_block = build_reply_rule_block(bundle)

    message_header = section_cfg.get(
        "message_header",
        "User message (target region={region}, tone={tone}, reply_form={reply_form}, requested_language={language}):",
    ).format(
        region=safe_region,
        tone=tone_str,
        reply_form=reply_form_norm,
        language=resolved_language,
    )

    facts_header = section_cfg.get("facts_header", "Extracted trade facts:")
    risk_header = section_cfg.get("risk_header", "Risk assessment:")
    country_header = section_cfg.get("country_header", "Country handling guidance:")
    identity_header = section_cfg.get("identity_header", "Available sender information:")
    task_header = section_cfg.get("task_header", "Task-specific reply instructions:")

    user_content = (
        f"{message_header}\n"
        "---------------------------------\n"
        f"{message}\n"
        "---------------------------------\n\n"
        f"{facts_header}\n"
        "---------------------------------\n"
        f"{facts_block}\n"
        "---------------------------------\n\n"
        f"{risk_header}\n"
        "---------------------------------\n"
        f"{risk_block}\n"
        "---------------------------------\n\n"
        f"{country_header}\n"
        "---------------------------------\n"
        f"{country_guidance_block}\n"
        "---------------------------------\n\n"
        f"{identity_header}\n"
        "---------------------------------\n"
        f"{identity_block}\n"
        "---------------------------------\n\n"
        f"{task_header}\n"
        "---------------------------------\n"
        f"{reply_rules_block}\n"
        "---------------------------------\n"
    )

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )

    reply_text: Optional[str] = getattr(response, "output_text", None)
    if not reply_text:
        reply_text = str(response)

    sender_name = pick_sender_name(safe_name, safe_user_name)

    return cleanup_generated_reply(
        reply_text,
        reply_form=reply_form_norm,
        sender_name=sender_name,
        company_name=safe_company_name,
        email=safe_email,
        phone=safe_phone,
    )


# =========================================================
# Public API: document generation
# =========================================================

def generate_document_text(
    data: BaseDocumentData,
    template_text: Optional[str] = None,
    model: str = "gpt-4o-mini",
) -> str:
    """
    Generate the main text body of a trade document.
    Includes prompt-level anti-placeholder rules and a final cleanup pass.
    """
    bundle = _load_doc_prompt_bundle()

    doc_purpose = get_document_purpose(bundle, data.document_type)

    system_template = str(bundle.get("system_template", "")).strip()
    system_prompt = system_template.format(purpose=doc_purpose)

    meta_lines = [
        f"Document type: {data.document_type.value}",
        f"Seller name: {data.seller_name or ''}",
        f"Buyer name: {data.buyer_name or ''}",
        f"Product: {data.product or ''}",
        f"Quantity: {data.quantity}",
        f"Unit price: {data.unit_price} {data.currency}",
        f"Currency: {data.currency}",
        f"Incoterm: {data.incoterm or ''}",
        f"Payment term: {data.payment_term or ''}",
        f"Extra notes: {data.extra_notes or ''}",
    ]
    meta_str = "\n".join(meta_lines)

    user_parts: list[str] = [
        "Here is the structured data for the document:",
        "---------------------------------------------",
        meta_str,
        "---------------------------------------------",
        "",
    ]

    if template_text:
        user_parts.extend([
            "Here is the optional reference template.",
            "Use it only as a structural or stylistic reference.",
            "Do not copy any placeholder text, blank fields, bracketed text, drafting notes or template markers into the final output.",
            "---------------------------------------------",
            template_text,
            "---------------------------------------------",
            "",
        ])

    user_parts.extend([
        "Now generate the full text of the document.",
        "",
        "Critical output rules:",
        "- Output only the final document text.",
        "- Do not include explanations, notes or commentary.",
        "- Do not use placeholders such as [Your Name], [Company Name], [Address], [Email], [Phone], [Date], [Signature], <...> or similar.",
        "- If some information is missing, omit it naturally or use neutral wording such as 'the Seller', 'the Buyer', 'the Supplier' or 'the Company' where appropriate.",
        "- The result must read like a complete real business document ready to be placed into a PDF.",
    ])

    user_content = "\n".join(user_parts)

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )

    doc_text: Optional[str] = getattr(response, "output_text", None)
    if not doc_text:
        doc_text = str(response)

    return cleanup_generated_document_text(doc_text)