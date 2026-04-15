# backend/app/services/llm_doc_utils.py
import re

from app.models.doc_model import DocumentType


def get_document_purpose(bundle: dict, document_type: DocumentType) -> str:
    """
    Map the document type to a configured purpose string.
    Falls back to a default text if config is missing.
    """
    purposes = bundle.get("doc_purposes", {})
    if not isinstance(purposes, dict):
        purposes = {}

    default_map = {
        DocumentType.sales_contract: (
            "Draft a clear, professional and practical international sales contract "
            "between seller and buyer."
        ),
        DocumentType.quotation: (
            "Draft a clear, professional and concise quotation with pricing and terms."
        ),
        DocumentType.product_manual: (
            "Draft a structured and practical product manual with clear sections."
        ),
    }

    return str(
        purposes.get(document_type.value) or default_map.get(document_type, "")
    ).strip()


def cleanup_generated_document_text(text: str) -> str:
    """
    Final cleanup pass for document generation output.
    Removes obvious placeholders and stray drafting instructions.
    """
    if not text:
        return text

    text = re.sub(
        r"\[(?:[^\[\]\n]{0,80})\]",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"<(?:[^\<\>\n]{0,80})>",
        "",
        text,
        flags=re.IGNORECASE,
    )

    instruction_patterns = [
        r"(?im)^\s*insert .*?$",
        r"(?im)^\s*fill in .*?$",
        r"(?im)^\s*to be completed .*?$",
        r"(?im)^\s*please complete .*?$",
        r"(?im)^\s*placeholder .*?$",
        r"(?im)^\s*draft note:.*?$",
        r"(?im)^\s*note to user:.*?$",
    ]
    for pattern in instruction_patterns:
        text = re.sub(pattern, "", text)

    cleaned_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()

        if not stripped:
            cleaned_lines.append("")
            continue

        if stripped in {"-", "--", "—", ".", ",", ":", ";", "()"}:
            continue

        cleaned_lines.append(line.rstrip())

    text = "\n".join(cleaned_lines)

    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    lines = text.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    return "\n".join(lines).strip()