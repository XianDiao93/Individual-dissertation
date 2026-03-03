# backend/app/services/llm_client.py
import json
import os
from pathlib import Path
from typing import Optional
from openai import OpenAI
from functools import lru_cache

from app.models.doc_model import BaseDocumentData, DocumentType
from app.config import CHAT_BASIC_PROMPT_PATH

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY environment variable is not set. "
        "Please set it before starting the backend."
    )

client = OpenAI(api_key=OPENAI_API_KEY)

# load basic promts from database
@lru_cache(maxsize=8)
def _load_chat_prompt_bundle() -> dict:
    path = Path(CHAT_BASIC_PROMPT_PATH)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def generate_business_reply(
    message: str,
    language: str = "auto",
    region: str = "EU",
    tone: str = "formal",
    reply_form: str = "email",
    model: str = "gpt-4o-mini",
) -> str:
    # Normalise tone
    tone_str = tone.lower()
    if tone_str not in {"formal", "neutral", "friendly"}:
        tone_str = "formal"

    # Normalise reply_form
    reply_form_norm = reply_form.lower()
    if reply_form_norm not in {"email", "chat"}:
        reply_form_norm = "email"

    bundle = _load_chat_prompt_bundle()

    modes = bundle.get("modes", {})
    mode_key = "chat" if reply_form_norm == "chat" else "email"
    mode_cfg = modes.get(mode_key) or modes.get("email") or {}

    system_template = bundle.get("system_template", "")

    system_prompt = system_template.format(
        mode_description=mode_cfg.get("mode_description", ""),
        formatting_instructions=mode_cfg.get("formatting_instructions", ""),
        language=language,
        region=region,
        tone_str=tone_str,
    )

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"User message (target region={region}, tone={tone_str}, "
                    f"reply_form={reply_form_norm}, requested_language={language}):\n"
                    f"{message}"
                ),
            },
        ],
    )

    reply_text: Optional[str] = getattr(response, "output_text", None)
    if not reply_text:
        reply_text = str(response)

    return reply_text

def generate_document_text(
    data: BaseDocumentData,
    template_text: Optional[str] = None,
    model: str = "gpt-4o-mini",
) -> str:
    """
    Use the LLM to generate the main body text of a trade document.

    The model receives:
      - document_type (sales_contract / quotation / product_manual)
      - core structured fields (seller, buyer, product, price, terms, etc.)
      - optional template_text as a structural / style reference

    It should output a ready-to-use document body in plain text.
    """

    # High-level instruction depending on document type
    if data.document_type == DocumentType.sales_contract:
        doc_purpose = (
            "Draft a clear and professional international sales contract between seller and buyer. "
            "Use numbered clauses where appropriate."
        )
    elif data.document_type == DocumentType.quotation:
        doc_purpose = (
            "Draft a clear and professional quotation for the buyer, with pricing, terms and validity. "
            "You may use simple headings but keep it concise."
        )
    else:
        # product_manual
        doc_purpose = (
            "Draft a structured product manual / instruction document. "
            "It should have clear sections, such as Overview, Parts and functions, "
            "Usage, Safety instructions and Warranty."
        )

    system_prompt = (
        "You are an AI assistant helping SMEs with international trade documentation.\n\n"
        "Your task is to generate high-quality, professional text for trade documents "
        "(contracts, quotations, product manuals). You must:\n"
        "- Use clear, formal business language.\n"
        "- Organise the content with logical sections and paragraphs.\n"
        "- Do NOT add any placeholder like 'Lorem ipsum'; always use meaningful text.\n\n"
        f"Specific goal for this document:\n{doc_purpose}\n\n"
        "If a reference template is provided, you should:\n"
        "- Follow its overall structure and headings as much as reasonable.\n"
        "- Fill in any placeholders with the given data.\n"
        "- Improve clarity and consistency where needed.\n"
    )

    # Build a compact description of the structured data
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