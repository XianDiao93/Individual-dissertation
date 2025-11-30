# backend/app/services/llm_client.py
import os
from typing import Optional

from openai import OpenAI
from app.models.doc_model import BaseDocumentData, DocumentType

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

***REMOVED***
    raise RuntimeError(
        "OPENAI_API_KEY environment variable is not set. "
        "Please set it before starting the backend."
    )

client = OpenAI(api_key=OPENAI_API_KEY)


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

    if reply_form_norm == "chat":
        mode_description = (
            "You are chatting with the user in a business context. "
            "Provide a short, direct conversational reply, as in a live chat or "
            "instant messaging tool. You may skip formal email headers and "
            "sign-offs (no need for 'Dear ...' and 'Best regards')."
        )
        formatting_instructions = (
            "- Keep the reply short (1–3 short paragraphs or a few sentences).\n"
            "- You can use 'Hi' or no greeting at all if it feels natural.\n"
            "- Do NOT include signatures or long closings."
        )
    else:
        mode_description = (
            "You are composing a full business email reply for the user. "
            "Include an appropriate greeting and closing, and use a clear email structure."
        )
        formatting_instructions = (
            "- Include a greeting (e.g. 'Dear ...').\n"
            "- Use one or more paragraphs to answer the inquiry clearly.\n"
            "- Finish with a polite closing (e.g. 'Best regards, ...')."
        )

    system_prompt = (
        "You are an AI assistant helping SMEs with international trade communication.\n\n"
        f"{mode_description}\n\n"
        "LANGUAGE HANDLING:\n"
        "1. First, detect the language of the user's message.\n"
        f"2. The requested output language is: '{language}'.\n"
        "- If the requested language is 'auto', always reply in the detected input language.\n"
        "- If the requested language is a specific language (e.g. 'en', 'zh') and it matches\n"
        "  the detected language, reply in that language.\n"
        "- If the requested language conflicts with the detected language, prioritise the\n"
        "  detected input language and reply in that detected language.\n\n"
        "REGION & TONE:\n"
        f"- Target region: {region}. Adapt the style, politeness and phrasing to typical\n"
        "  business communication practices in this region (e.g. EU/US/ME/ASIA).\n"
        f"- Tone: {tone_str}. Make the reply consistent with this tone.\n\n"
        "FORMATTING:\n"
        f"{formatting_instructions}\n"
        "- Do NOT explain what you are doing; just output the final text."
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