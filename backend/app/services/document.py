# backend/app/services/document.py
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fpdf import FPDF

from app.models.doc_model import BaseDocumentData, DocumentType, GeneratedDocument
from app.services.llm_client import generate_document_text


def _fallback_contract_or_quotation_text(data: BaseDocumentData) -> str:
    """
    Build fallback text for sales contract or quotation when LLM generation fails.
    """
    total = data.quantity * data.unit_price if data.quantity and data.unit_price else 0.0

    if data.document_type == DocumentType.quotation:
        return f"""QUOTATION

To: {data.buyer_name or "The Buyer"}
From: {data.seller_name or "The Seller"}

Product: {data.product}
Quantity: {data.quantity}
Unit price: {data.unit_price:.2f} {data.currency}
Total amount: {total:.2f} {data.currency}

Incoterm: {data.incoterm or "N/A"}
Payment term: {data.payment_term or "N/A"}

Additional notes:
{data.extra_notes or "N/A"}
"""
    return f"""SALES CONTRACT

Seller: {data.seller_name or "The Seller"}
Buyer: {data.buyer_name or "The Buyer"}

Product: {data.product}
Quantity: {data.quantity}
Unit price: {data.unit_price:.2f} {data.currency}
Total amount: {total:.2f} {data.currency}

Incoterm: {data.incoterm or "N/A"}
Payment term: {data.payment_term or "N/A"}

Additional terms:
{data.extra_notes or "N/A"}
"""


def _fallback_manual_text(data: BaseDocumentData) -> str:
    """
    Build fallback text for product manual when LLM generation fails.
    """
    return f"""PRODUCT MANUAL / INSTRUCTION

Product: {data.product}
Supplier: {data.seller_name or "The Supplier"}
Customer: {data.buyer_name or "The Customer"}

Parts and functions:
{data.extra_notes or "N/A"}

Safety and warnings:
- Read this manual carefully before use.
- Follow local regulations and standards.
- Disconnect power before maintenance.
"""


def build_document_text(
    data: BaseDocumentData,
    template_text: Optional[str] = None,
) -> str:
    """
    Generate document text via LLM, with fallback if generation fails.
    """
    try:
        return generate_document_text(data=data, template_text=template_text)
    except Exception:
        if data.document_type in (DocumentType.sales_contract, DocumentType.quotation):
            return _fallback_contract_or_quotation_text(data)
        return _fallback_manual_text(data)


def _render_pdf_with_optional_image(
    text: str,
    image_path: Optional[Path] = None,
) -> bytes:
    """
    Render plain text and optional image into PDF using FPDF.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Insert image if provided
    if image_path and image_path.exists():
        pdf.image(str(image_path), w=120)
        pdf.ln(10)

    # Write text line by line
    for line in text.split("\n"):
        pdf.multi_cell(0, 8, line)

    return pdf.output(dest="S").encode("latin-1")


def generate_document_pdf_bytes(
    data: BaseDocumentData,
    template_text: Optional[str] = None,
    image_path: Optional[Path] = None,
) -> tuple[bytes, str]:
    """
    Generate document text, render PDF bytes, and return a short description.

    Returns:
        tuple[bytes, str]:
            - PDF bytes
            - short description for UI
    """
    text = build_document_text(data, template_text=template_text)

    if data.document_type in (DocumentType.sales_contract, DocumentType.quotation):
        description = (
            f"Generated {data.document_type.value.replace('_', ' ')} PDF "
            f"for buyer '{data.buyer_name}' and product '{data.product}'."
        )
    else:
        description = (
            f"Generated product manual PDF for '{data.product}'. "
            "The file includes the product image (if provided) and instructions."
        )

    pdf_bytes = _render_pdf_with_optional_image(text, image_path=image_path)
    return pdf_bytes, description


def build_generated_document(
    file_path: Path,
    data: BaseDocumentData,
    description: str,
) -> GeneratedDocument:
    """
    Build a GeneratedDocument object from the saved file path.
    """
    return GeneratedDocument(
        file_path=str(file_path),
        download_name=file_path.name,
        description=description,
    )