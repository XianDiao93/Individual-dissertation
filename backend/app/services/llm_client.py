# backend/app/services/llm_client.py
import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from openai import OpenAI

from app.models.doc_model import BaseDocumentData, DocumentType
from app.config import CHAT_BASIC_PROMPT_PATH, DOC_BASIC_PROMPT_PATH

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY environment variable is not set. "
        "Please set it before starting the backend."
    )

client = OpenAI(api_key=OPENAI_API_KEY)


@lru_cache(maxsize=8)
def _load_chat_prompt_bundle() -> dict:
    path = Path(CHAT_BASIC_PROMPT_PATH)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=8)
def _load_doc_prompt_bundle() -> dict:
    path = Path(DOC_BASIC_PROMPT_PATH)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _has_flag(flags: list[str], target: str) -> bool:
    return target in flags


def _is_empty(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def _normalize_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    if value == "" or value.lower() == "null":
        return None
    return value


def _join_rules(lines: list[str]) -> str:
    clean_lines = [str(line).strip() for line in lines if str(line).strip()]
    if not clean_lines:
        return "- None."
    return "\n".join(f"- {line}" for line in clean_lines)


def _build_identity_block(
    *,
    user_name: Optional[str],
    name: Optional[str],
    company_name: Optional[str],
    email: Optional[str],
    phone: Optional[str],
    region: str,
) -> str:
    lines = [
        f"Preferred display name: {name if name else 'NOT PROVIDED'}",
        f"Company name: {company_name if company_name else 'NOT PROVIDED'}",
        f"Account user name: {user_name if user_name else 'NOT PROVIDED'}",
        f"Contact email: {email if email else 'NOT PROVIDED'}",
        f"Contact phone: {phone if phone else 'NOT PROVIDED'}",
        f"Sender region hint: {region if region else 'NOT PROVIDED'}",
    ]
    return "\n".join(lines)


def _build_country_guidance(bundle: dict, safe_facts: dict) -> str:
    country_rules = bundle.get("country_rules", {})

    ambiguity_flags = safe_facts.get("ambiguity_flags", [])
    if not isinstance(ambiguity_flags, list):
        ambiguity_flags = []

    origin_country_name = safe_facts.get("origin_country_name", "")
    origin_country_code = safe_facts.get("origin_country_code", "")
    destination_country_name = safe_facts.get("destination_country_name", "")
    destination_country_code = safe_facts.get("destination_country_code", "")

    lines: list[str] = []

    if _has_flag(ambiguity_flags, "origin_country_ambiguous"):
        lines.extend(country_rules.get("origin_ambiguous", []))

    if _has_flag(ambiguity_flags, "destination_country_ambiguous"):
        lines.extend(country_rules.get("destination_ambiguous", []))

    if _is_empty(origin_country_code):
        lines.extend(country_rules.get("origin_missing", []))
    else:
        lines.append(f"Detected buyer or sender country code: {origin_country_code}.")
        if not _is_empty(origin_country_name):
            lines.append(f"Detected buyer or sender country name: {origin_country_name}.")
        lines.extend(country_rules.get("origin_present", []))

    if _is_empty(destination_country_code) and _is_empty(destination_country_name):
        lines.extend(country_rules.get("destination_missing", []))
    else:
        if not _is_empty(destination_country_code):
            lines.append(f"Detected destination country code: {destination_country_code}.")
        if not _is_empty(destination_country_name):
            lines.append(f"Detected destination country name: {destination_country_name}.")
        lines.extend(country_rules.get("destination_present", []))

    return _join_rules(lines)


def _build_reply_rule_block(bundle: dict) -> str:
    rule_cfg = bundle.get("reply_rules", {})
    lines: list[str] = []
    lines.extend(rule_cfg.get("normal", []))
    lines.extend(rule_cfg.get("identity", []))
    lines.extend(rule_cfg.get("greeting", []))
    lines.extend(rule_cfg.get("opening", []))
    lines.extend(rule_cfg.get("closing", []))
    return _join_rules(lines)


def _resolve_output_language(
    requested_language: str,
    normalized_facts: Optional[dict],
    message: str,
) -> str:
    """
    Decide the reply language before calling the LLM.

    Priority:
    1. Explicit language from caller (if not 'auto')
    2. Buyer/sender country from extracted facts
    3. Lightweight fallback heuristic from message language
    4. English default
    """
    lang = (requested_language or "auto").strip().lower()
    if lang and lang != "auto":
        return lang

    facts = normalized_facts or {}

    origin_code = str(facts.get("origin_country_code") or "").strip().upper()
    origin_name = str(facts.get("origin_country_name") or "").strip().upper()

    country_to_lang = {
        "FR": "fr",
        "FRANCE": "fr",
        "DE": "de",
        "GERMANY": "de",
        "ES": "es",
        "SPAIN": "es",
        "IT": "it",
        "ITALY": "it",
        "CN": "zh",
        "CHINA": "zh",
        "JP": "ja",
        "JAPAN": "ja",
        "GB": "en",
        "UK": "en",
        "UNITED KINGDOM": "en",
        "US": "en",
        "USA": "en",
        "UNITED STATES": "en",
    }

    if origin_code in country_to_lang:
        return country_to_lang[origin_code]

    if origin_name in country_to_lang:
        return country_to_lang[origin_name]

    text = (message or "").lower()

    # lightweight fallback only when country is unavailable
    if any(token in text for token in ["bonjour", "merci", "cordialement", "bien à vous"]):
        return "fr"
    if any(token in text for token in ["guten tag", "danke", "mit freundlichen grüßen"]):
        return "de"
    if any(token in text for token in ["hola", "gracias", "saludos", "atentamente"]):
        return "es"
    if any(token in text for token in ["ciao", "grazie", "cordiali saluti"]):
        return "it"
    if any(token in text for token in ["你好", "谢谢", "此致", "敬礼"]):
        return "zh"
    if any(token in text for token in ["こんにちは", "ありがとうございます", "よろしくお願いします"]):
        return "ja"

    return "en"


def _pick_sender_name(name: Optional[str], user_name: Optional[str]) -> Optional[str]:
    """
    Prefer the real profile/display name first, then fall back to the account user name.
    """
    for candidate in (name, user_name):
        norm = _normalize_optional_text(candidate)
        if norm:
            return norm
    return None


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

    safe_user_name = _normalize_optional_text(user_name)
    safe_name = _normalize_optional_text(name)
    safe_company_name = _normalize_optional_text(company_name)
    safe_email = _normalize_optional_text(email)
    safe_phone = _normalize_optional_text(phone)
    safe_region = _normalize_optional_text(region) or "GB"

    safe_facts = dict(normalized_facts or {})
    ambiguity_flags = safe_facts.get("ambiguity_flags", [])
    if not isinstance(ambiguity_flags, list):
        safe_facts["ambiguity_flags"] = []

    safe_risk = dict(risk_result or {})

    resolved_language = _resolve_output_language(
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

    identity_block = _build_identity_block(
        user_name=safe_user_name,
        name=safe_name,
        company_name=safe_company_name,
        email=safe_email,
        phone=safe_phone,
        region=safe_region,
    )

    country_guidance_block = _build_country_guidance(bundle, safe_facts)
    reply_rules_block = _build_reply_rule_block(bundle)

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

    sender_name = _pick_sender_name(safe_name, safe_user_name)

    return _cleanup_generated_reply(
        reply_text,
        reply_form=reply_form_norm,
        sender_name=sender_name,
        company_name=safe_company_name,
        email=safe_email,
        phone=safe_phone,
    )


def generate_document_text(
    data: BaseDocumentData,
    template_text: Optional[str] = None,
    model: str = "gpt-4o-mini",
) -> str:
    """
    Use the LLM to generate the main body text of a trade document.
    """
    bundle = _load_doc_prompt_bundle()

    if data.document_type == DocumentType.sales_contract:
        modes = bundle.get("modes", {})
        doc_purpose = modes.get("sales_contract")
    elif data.document_type == DocumentType.quotation:
        modes = bundle.get("modes", {})
        doc_purpose = modes.get("quotation")
    else:
        modes = bundle.get("modes", {})
        doc_purpose = modes.get("product_manual")

    system_template = bundle.get("system_template", "")
    system_prompt = system_template.format(purpose=doc_purpose)

    meta_lines = [
        f"Document type: {data.document_type.value}",
        f"Seller: {data.seller_name}",
        f"Buyer: {data.buyer_name}",
        f"Product: {data.product}",
        f"Quantity: {data.quantity}",
        f"Unit price: {data.unit_price} {data.currency}",
        f"Incoterm: {data.incoterm or 'N/A'}",
        f"Payment term: {data.payment_term or 'N/A'}",
        f"Extra notes: {data.extra_notes or 'N/A'}",
    ]
    meta_str = "\n".join(meta_lines)

    user_content = (
        "Here is the structured data for the document:\n"
        "---------------------------------------------\n"
        f"{meta_str}\n"
        "---------------------------------------------\n\n"
    )

    if template_text:
        user_content += (
            "Here is the optional reference template (you may follow its structure and wording style):\n"
            "---------------------------------------------\n"
            f"{template_text}\n"
            "---------------------------------------------\n\n"
        )

    user_content += (
        "Now generate the full text of the document. "
        "Do not include any explanations about what you are doing; "
        "just output the document content ready to be placed into a PDF."
    )

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

    return doc_text


def _replace_known_placeholders(
    text: str,
    *,
    sender_name: Optional[str],
    company_name: Optional[str],
    email: Optional[str],
    phone: Optional[str],
) -> str:
    """
    Replace common placeholder markers with real profile values when available.
    If no real value exists, the placeholder is left for later line-level cleanup.
    """
    placeholder_map = {
        # name
        "[Your Name]": sender_name,
        "[Your Full Name]": sender_name,
        "[Ihr Name]": sender_name,
        "[Ihr vollständiger Name]": sender_name,
        "[Votre nom]": sender_name,
        "[Nom]": sender_name,
        "[Su nombre]": sender_name,
        "[Nombre]": sender_name,
        "[您的姓名]": sender_name,
        "[会社名担当者名]": sender_name,
        # company
        "[Company Name]": company_name,
        "[Your Company Name]": company_name,
        "[Your Company]": company_name,
        "[Ihr Firmenname]": company_name,
        "[Firmenname]": company_name,
        "[Nom de l’entreprise]": company_name,
        "[Nombre de la empresa]": company_name,
        "[公司名称]": company_name,
        "[会社名]": company_name,
        # email
        "[Your Email]": email,
        "[Your Email Address]": email,
        "[Ihre E-Mail]": email,
        "[Ihre E-Mail-Adresse]": email,
        "[Votre e-mail]": email,
        "[Su correo electrónico]": email,
        "[电子邮件]": email,
        "[メールアドレス]": email,
        # phone
        "[Your Phone]": phone,
        "[Your Phone Number]": phone,
        "[Ihre Telefonnummer]": phone,
        "[Votre numéro de téléphone]": phone,
        "[Su número de teléfono]": phone,
        "[电话号码]": phone,
        "[電話番号]": phone,
    }

    for token, value in placeholder_map.items():
        if value:
            text = text.replace(token, value)

    return text


def _remove_placeholder_lines(text: str) -> str:
    """
    Remove any remaining lines that still contain obvious template placeholders.
    This is intentionally broad, because a visible placeholder is always worse
    than omitting the missing line.
    """
    generic_placeholder_patterns = [
        r"\[[^\]]*(?:your|company|contact|recipient|customer|client|name|email|phone|address|position)[^\]]*\]",
        r"\[[^\]]*(?:ihr|ihre|firmenname|name|e-mail|telefon)[^\]]*\]",
        r"\[[^\]]*(?:nom|entreprise|e-mail|téléphone)[^\]]*\]",
        r"\[[^\]]*(?:nombre|empresa|correo|teléfono)[^\]]*\]",
        r"\[[^\]]*(?:姓名|公司|名称|邮件|电话)[^\]]*\]",
        r"\[[^\]]*(?:会社|氏名|名前|メール|電話)[^\]]*\]",
    ]

    lines = text.splitlines()
    cleaned_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append(line)
            continue

        if any(re.search(pattern, stripped, flags=re.IGNORECASE) for pattern in generic_placeholder_patterns):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def _remove_orphan_signature_lines(
    text: str,
    *,
    sender_name: Optional[str],
    company_name: Optional[str],
    email: Optional[str],
    phone: Optional[str],
) -> str:
    """
    If the model produced a signature block with missing placeholder lines removed,
    keep only real signature content. Also remove orphan punctuation-only lines.
    """
    valid_signature_values = {
        v.strip()
        for v in [sender_name, company_name, email, phone]
        if isinstance(v, str) and v.strip()
    }

    lines = text.splitlines()
    cleaned_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            cleaned_lines.append(line)
            continue

        # Remove lines that became empty-ish after placeholder cleanup.
        if stripped in {"-", "--", "—", ".", ",", ":", ";"}:
            continue

        # Keep all normal content lines. This function mainly prevents obvious junk.
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # If there is no sender name, do not allow generic "Name" style residue lines.
    if not sender_name:
        text = re.sub(r"(?im)^\s*(name|full name|ihr name|nom|nombre|姓名|氏名)\s*$\n?", "", text)

    # If there is no company, remove bare company label residue.
    if not company_name:
        text = re.sub(r"(?im)^\s*(company name|firmenname|nom de l’entreprise|nombre de la empresa|公司名称|会社名)\s*$\n?", "", text)

    # If there is no email, remove bare email label residue.
    if not email:
        text = re.sub(r"(?im)^\s*(email|e-mail|email address|e-mail-adresse|correo electrónico|电子邮件|メールアドレス)\s*$\n?", "", text)

    # If there is no phone, remove bare phone label residue.
    if not phone:
        text = re.sub(r"(?im)^\s*(phone|phone number|telefon|telefonnummer|número de teléfono|电话号码|電話番号)\s*$\n?", "", text)

    return text


def _cleanup_generated_reply(
    text: str,
    reply_form: str = "email",
    sender_name: Optional[str] = None,
    company_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> str:
    if not text:
        return text

    text = _replace_known_placeholders(
        text,
        sender_name=sender_name,
        company_name=company_name,
        email=email,
        phone=phone,
    )

    banned_markers = [
        "[Your Name]",
        "[Your Full Name]",
        "[Your Email]",
        "[Your Email Address]",
        "[Your Phone]",
        "[Your Phone Number]",
        "[Your Address]",
        "[Your Position]",
        "[Company Name]",
        "[Your Company Name]",
        "[Your Contact Information]",
        "[Your Contact Info]",
        "[Your Company]",
        "[Company Address]",
        "[Contact Information]",
        "[Contact Info]",
        "[Recipient]",
        "[Customer Name]",
        "[Client Name]",
        "[Dear recipient]",
        "[Ihr Name]",
        "[Ihr vollständiger Name]",
        "[Ihr Firmenname]",
        "[Ihre E-Mail]",
        "[Ihre E-Mail-Adresse]",
        "[Ihre Telefonnummer]",
        "[Votre nom]",
        "[Nom]",
        "[Nom de l’entreprise]",
        "[Votre e-mail]",
        "[Votre numéro de téléphone]",
        "[Su nombre]",
        "[Nombre]",
        "[Nombre de la empresa]",
        "[Su correo electrónico]",
        "[Su número de teléfono]",
        "[您的姓名]",
        "[公司名称]",
        "[电子邮件]",
        "[电话号码]",
        "[会社名]",
        "[氏名]",
        "[メールアドレス]",
        "[電話番号]",
    ]

    for marker in banned_markers:
        text = text.replace(marker, "")

    text = re.sub(
        r"\[(?:your|company|contact|recipient|customer|client)[^\]]*\]",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = _remove_placeholder_lines(text)

    if reply_form == "email":
        email_header_patterns = [
            r"(?im)^\s*subject\s*:\s*.*(?:\n|$)",
            r"(?im)^\s*re\s*:\s*.*(?:\n|$)",
            r"(?im)^\s*fw\s*:\s*.*(?:\n|$)",
            r"(?im)^\s*fwd\s*:\s*.*(?:\n|$)",
            r"(?im)^\s*to\s*:\s*.*(?:\n|$)",
            r"(?im)^\s*from\s*:\s*.*(?:\n|$)",
            r"(?im)^\s*cc\s*:\s*.*(?:\n|$)",
            r"(?im)^\s*bcc\s*:\s*.*(?:\n|$)",
            r"(?im)^\s*date\s*:\s*.*(?:\n|$)",
        ]
        for pattern in email_header_patterns:
            text = re.sub(pattern, "", text)

    text = _remove_orphan_signature_lines(
        text,
        sender_name=sender_name,
        company_name=company_name,
        email=email,
        phone=phone,
    )

    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    lines = [line.rstrip() for line in text.splitlines()]

    while lines and not lines[0].strip():
        lines.pop(0)

    while lines and not lines[-1].strip():
        lines.pop()

    cleaned = "\n".join(lines).strip()

    cleaned = re.sub(
        r"(?im)(?:\n|^)\s*(best regards|kind regards|regards|sincerely|yours sincerely|yours faithfully|warm regards),\s*$",
        lambda m: ("\n" if "\n" in m.group(0) else "") + f"{m.group(1).title()}.",
        cleaned,
    )

    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned