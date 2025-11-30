# backend/app/services/document.py
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fpdf import FPDF

from app.models.doc_model import BaseDocumentData, DocumentType, GeneratedDocument
from app.services.llm_client import generate_document_text


def _build_contract_or_quotation_text(
    data: BaseDocumentData,
    template_text: Optional[str] = None,
) -> str:
    """
    Build text for sales_contract or quotation.
    If template_text is provided, do simple placeholder replacement.
    """
    total = data.quantity * data.unit_price if data.quantity and data.unit_price else 0.0

    if data.document_type == DocumentType.quotation:
        title = "QUOTATION"
    else:
        title = "SALES CONTRACT"

    # If user provides a text-like template, we can replace some placeholders
    if template_text:
        text = template_text
        replacements = {
            "{{title}}": title,
            "{{seller}}": data.seller_name,
            "{{buyer}}": data.buyer_name,
            "{{product}}": data.product,
            "{{quantity}}": str(data.quantity),
            "{{unit_price}}": f"{data.unit_price:.2f} {data.currency}",
            "{{total}}": f"{total:.2f} {data.currency}",
            "{{incoterm}}": data.incoterm or "N/A",
            "{{payment_term}}": data.payment_term or "N/A",
            "{{extra_notes}}": data.extra_notes or "N/A",
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text

    # Default simple template
    if data.document_type == DocumentType.quotation:
        body = f"""To: {data.buyer_name}
From: {data.seller_name}

We are pleased to offer the following quotation:

Product: {data.product}
Quantity: {data.quantity}
Unit price: {data.unit_price:.2f} {data.currency}
Total amount: {total:.2f} {data.currency}

Incoterm: {data.incoterm or "N/A"}
Payment term: {data.payment_term or "N/A"}

This quotation is valid for 30 days unless otherwise specified.

Additional notes:
{data.extra_notes or "N/A"}
"""
    else:
        body = f"""This Sales Contract is made between:

Seller: {data.seller_name}
Buyer: {data.buyer_name}

Product: {data.product}
Quantity: {data.quantity}
Unit price: {data.unit_price:.2f} {data.currency}
Total amount: {total:.2f} {data.currency}

Incoterm: {data.incoterm or "N/A"}
Payment term: {data.payment_term or "N/A"}

Additional terms:
{data.extra_notes or "N/A"}

Both parties agree to the above terms.
"""

    return body


def _build_manual_text(data: BaseDocumentData) -> str:
    """
    Build text for product_manual.
    Later you can insert LLM-generated content here (features, usage, safety, FAQ).
    """
    text = f"""PRODUCT MANUAL / INSTRUCTION

Product: {data.product}
Supplier: {data.seller_name}
Customer: {data.buyer_name}

Overview:
This document describes the main parts, functions and safety instructions of the product.

Parts and functions:
{data.extra_notes or "N/A"}

Safety and warnings:
- Read this manual carefully before use.
- Follow local regulations and standards.
- Disconnect power before maintenance.

Warranty:
- Standard warranty terms apply unless otherwise agreed.
"""
    return text


def build_document_text(
    data: BaseDocumentData,
    template_text: Optional[str] = None,
) -> str:
    """
    Public function: choose the right builder by document_type.
    """
    if data.document_type in (DocumentType.sales_contract, DocumentType.quotation):
        body = _build_contract_or_quotation_text(data, template_text)
        return body
    elif data.document_type == DocumentType.product_manual:
        body = _build_manual_text(data)
        return body
    else:
        # Fallback
        return _build_contract_or_quotation_text(data, template_text)


def _render_pdf_with_optional_image(text: str, image_path: Optional[Path] = None) -> bytes:
    """
    Render plain text + optional image into PDF using FPDF.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Insert image if provided
    if image_path and image_path.exists():
        pdf.image(str(image_path), w=120)
        pdf.ln(10)

    for line in text.split("\n"):
        pdf.multi_cell(0, 8, line)

    return pdf.output(dest="S").encode("latin-1")


def generate_document_pdf_bytes(
    data: BaseDocumentData,
    template_text: Optional[str] = None,
    image_path: Optional[Path] = None,
) -> tuple[bytes, str]:
    """
    Build document text + PDF bytes + short description.

    Returns:
        (pdf_bytes, description)
    """
    text = build_document_text(data, template_text=template_text)

    if data.document_type in (DocumentType.sales_contract, DocumentType.quotation):
        desc = (
            f"Generated {data.document_type.value.replace('_', ' ')} PDF "
            f"for buyer '{data.buyer_name}' and product '{data.product}'."
        )
    else:
        desc = (
            f"Generated product manual PDF for '{data.product}'. "
            "The file includes the product image (if provided) and basic instructions."
        )

    pdf_bytes = _render_pdf_with_optional_image(text, image_path=image_path)
    return pdf_bytes, desc


def build_generated_document(
    file_path: Path,
    data: BaseDocumentData,
    description: str,
) -> GeneratedDocument:
    """
    Helper to create a GeneratedDocument object from the saved PDF path.
    """
    download_name = file_path.name
    return GeneratedDocument(
        file_path=str(file_path),
        download_name=download_name,
        description=description,
    )


# -------- LLM-backed text generation with fallback --------

def _fallback_contract_or_quotation_text(
    data: BaseDocumentData,
) -> str:
    """
    Very simple fallback in case LLM fails.
    """
    total = data.quantity * data.unit_price if data.quantity and data.unit_price else 0.0

    if data.document_type == DocumentType.quotation:
        body = f"""QUOTATION

To: {data.buyer_name}
From: {data.seller_name}

Product: {data.product}
Quantity: {data.quantity}
Unit price: {data.unit_price:.2f} {data.currency}
Total amount: {total:.2f} {data.currency}

Incoterm: {data.incoterm or "N/A"}
Payment term: {data.payment_term or "N/A"}

Additional notes:
{data.extra_notes or "N/A"}
"""
    else:
        body = f"""SALES CONTRACT

Seller: {data.seller_name}
Buyer: {data.buyer_name}

Product: {data.product}
Quantity: {data.quantity}
Unit price: {data.unit_price:.2f} {data.currency}
Total amount: {total:.2f} {data.currency}

Incoterm: {data.incoterm or "N/A"}
Payment term: {data.payment_term or "N/A"}

Additional terms:
{data.extra_notes or "N/A"}
"""
    return body


def _fallback_manual_text(data: BaseDocumentData) -> str:
    """
    Very simple fallback manual text.
    """
    return f"""PRODUCT MANUAL / INSTRUCTION

Product: {data.product}
Supplier: {data.seller_name}
Customer: {data.buyer_name}

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
    Public function: use LLM to build document text, with a simple fallback.
    """
    try:
        # Primary path: use LLM
        return generate_document_text(data=data, template_text=template_text)
    except Exception as e:
        # Fallback to deterministic templates if something goes wrong
        # (e.g. API error, network issue)
        # You might want to log this exception in a real system.
        if data.document_type in (DocumentType.sales_contract, DocumentType.quotation):
            return _fallback_contract_or_quotation_text(data)
        else:
            return _fallback_manual_text(data)


# -------- PDF rendering and service-layer result --------

def _render_pdf_with_optional_image(text: str, image_path: Optional[Path] = None) -> bytes:
    """
    Render plain text + optional image into PDF using FPDF.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Insert image if provided
    if image_path and image_path.exists():
        pdf.image(str(image_path), w=120)
        pdf.ln(10)

    for line in text.split("\n"):
        pdf.multi_cell(0, 8, line)

    return pdf.output(dest="S").encode("latin-1")


def generate_document_pdf_bytes(
    data: BaseDocumentData,
    template_text: Optional[str] = None,
    image_path: Optional[Path] = None,
) -> tuple[bytes, str]:
    """
    Build document text via LLM (with fallback) + render PDF bytes + short description.

    Returns:
        (pdf_bytes, description)
    """
    text = build_document_text(data, template_text=template_text)

    if data.document_type in (DocumentType.sales_contract, DocumentType.quotation):
        desc = (
            f"Generated {data.document_type.value.replace('_', ' ')} PDF "
            f"for buyer '{data.buyer_name}' and product '{data.product}'."
        )
    else:
        desc = (
            f"Generated product manual PDF for '{data.product}'. "
            "The file includes the product image (if provided) and instructions."
        )

    pdf_bytes = _render_pdf_with_optional_image(text, image_path=image_path)
    return pdf_bytes, desc


def build_generated_document(
    file_path: Path,
    data: BaseDocumentData,
    description: str,
) -> GeneratedDocument:
    """
    Helper to create a GeneratedDocument object from the saved PDF path.
    """
    download_name = file_path.name
    return GeneratedDocument(
        file_path=str(file_path),
        download_name=download_name,
        description=description,
    )