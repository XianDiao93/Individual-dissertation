# backend/app/services/llm_reply_utils.py
import re
from typing import Optional


def has_flag(flags: list[str], target: str) -> bool:
    """
    Check whether a target flag exists in a flag list.
    """
    return target in flags


def is_empty(value: object) -> bool:
    """
    Return True for None or blank strings.
    """
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def normalize_optional_text(value: Optional[str]) -> Optional[str]:
    """
    Normalize optional text input:
    - strip whitespace
    - convert empty / 'null' to None
    """
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    if value == "" or value.lower() == "null":
        return None
    return value


def join_rules(lines: list[str]) -> str:
    """
    Join a list of rule lines into a bullet-style block.
    """
    clean_lines = [str(line).strip() for line in lines if str(line).strip()]
    if not clean_lines:
        return "- None."
    return "\n".join(f"- {line}" for line in clean_lines)


def build_identity_block(
    *,
    user_name: Optional[str],
    name: Optional[str],
    company_name: Optional[str],
    email: Optional[str],
    phone: Optional[str],
    region: str,
) -> str:
    """
    Build a structured identity block for the communication prompt.
    """
    lines = [
        f"Preferred display name: {name if name else 'NOT PROVIDED'}",
        f"Company name: {company_name if company_name else 'NOT PROVIDED'}",
        f"Account user name: {user_name if user_name else 'NOT PROVIDED'}",
        f"Contact email: {email if email else 'NOT PROVIDED'}",
        f"Contact phone: {phone if phone else 'NOT PROVIDED'}",
        f"Sender region hint: {region if region else 'NOT PROVIDED'}",
    ]
    return "\n".join(lines)


def build_country_guidance(bundle: dict, safe_facts: dict) -> str:
    """
    Build extra country/language guidance for the reply prompt
    based on extracted trade facts.
    """
    country_rules = bundle.get("country_rules", {})

    ambiguity_flags = safe_facts.get("ambiguity_flags", [])
    if not isinstance(ambiguity_flags, list):
        ambiguity_flags = []

    origin_country_name = safe_facts.get("origin_country_name", "")
    origin_country_code = safe_facts.get("origin_country_code", "")
    destination_country_name = safe_facts.get("destination_country_name", "")
    destination_country_code = safe_facts.get("destination_country_code", "")

    lines: list[str] = []

    if has_flag(ambiguity_flags, "origin_country_ambiguous"):
        lines.extend(country_rules.get("origin_ambiguous", []))

    if has_flag(ambiguity_flags, "destination_country_ambiguous"):
        lines.extend(country_rules.get("destination_ambiguous", []))

    if is_empty(origin_country_code):
        lines.extend(country_rules.get("origin_missing", []))
    else:
        lines.append(f"Detected buyer or sender country code: {origin_country_code}.")
        if not is_empty(origin_country_name):
            lines.append(f"Detected buyer or sender country name: {origin_country_name}.")
        lines.extend(country_rules.get("origin_present", []))

    if is_empty(destination_country_code) and is_empty(destination_country_name):
        lines.extend(country_rules.get("destination_missing", []))
    else:
        if not is_empty(destination_country_code):
            lines.append(f"Detected destination country code: {destination_country_code}.")
        if not is_empty(destination_country_name):
            lines.append(f"Detected destination country name: {destination_country_name}.")
        lines.extend(country_rules.get("destination_present", []))

    return join_rules(lines)


def build_reply_rule_block(bundle: dict) -> str:
    """
    Merge reply-related rules from chat_basic.json into one block.
    """
    rule_cfg = bundle.get("reply_rules", {})
    lines: list[str] = []
    lines.extend(rule_cfg.get("normal", []))
    lines.extend(rule_cfg.get("identity", []))
    lines.extend(rule_cfg.get("greeting", []))
    lines.extend(rule_cfg.get("opening", []))
    lines.extend(rule_cfg.get("closing", []))
    return join_rules(lines)


def resolve_output_language(
    requested_language: str,
    normalized_facts: Optional[dict],
    message: str,
) -> str:
    """
    Resolve the output language before calling the LLM.

    Priority:
    1. Explicit language from caller (if not 'auto')
    2. Buyer/sender country from extracted facts
    3. Lightweight language heuristics from the message itself
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


def pick_sender_name(name: Optional[str], user_name: Optional[str]) -> Optional[str]:
    """
    Prefer the real display name first, then fall back to the account user name.
    """
    for candidate in (name, user_name):
        norm = normalize_optional_text(candidate)
        if norm:
            return norm
    return None


def _replace_known_placeholders(
    text: str,
    *,
    sender_name: Optional[str],
    company_name: Optional[str],
    email: Optional[str],
    phone: Optional[str],
) -> str:
    """
    Replace common placeholder markers with real profile values if available.
    If no real value exists, the placeholder will be removed later.
    """
    placeholder_map = {
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
        "[Company Name]": company_name,
        "[Your Company Name]": company_name,
        "[Your Company]": company_name,
        "[Ihr Firmenname]": company_name,
        "[Firmenname]": company_name,
        "[Nom de l'entreprise]": company_name,
        "[Nombre de la empresa]": company_name,
        "[公司名称]": company_name,
        "[会社名]": company_name,
        "[Your Email]": email,
        "[Your Email Address]": email,
        "[Ihre E-Mail]": email,
        "[Ihre E-Mail-Adresse]": email,
        "[Votre e-mail]": email,
        "[Su correo electrónico]": email,
        "[电子邮件]": email,
        "[メールアドレス]": email,
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
    Remove lines that still contain obvious placeholder markers.
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
    Remove junk signature residues after placeholder cleanup.
    """
    lines = text.splitlines()
    cleaned_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            cleaned_lines.append(line)
            continue

        if stripped in {"-", "--", "—", ".", ",", ":", ";"}:
            continue

        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    if not sender_name:
        text = re.sub(r"(?im)^\s*(name|full name|ihr name|nom|nombre|姓名|氏名)\s*$\n?", "", text)

    if not company_name:
        text = re.sub(
            r"(?im)^\s*(company name|firmenname|nom de l'entreprise|nombre de la empresa|公司名称|会社名)\s*$\n?",
            "",
            text,
        )

    if not email:
        text = re.sub(
            r"(?im)^\s*(email|e-mail|email address|e-mail-adresse|correo electrónico|电子邮件|メールアドレス)\s*$\n?",
            "",
            text,
        )

    if not phone:
        text = re.sub(
            r"(?im)^\s*(phone|phone number|telefon|telefonnummer|número de teléfono|电话号码|電話番号)\s*$\n?",
            "",
            text,
        )

    return text


def cleanup_generated_reply(
    text: str,
    reply_form: str = "email",
    sender_name: Optional[str] = None,
    company_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> str:
    """
    Final cleanup pass for generated communication replies.
    """
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
        "[Nom de l'entreprise]",
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