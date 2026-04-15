# backend/app/routers/doc_router.py
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional
from io import BytesIO
from pathlib import Path

from app.models.doc_model import BaseDocumentData, DocumentType
from app.services.document import (
    generate_document_pdf_bytes,
    build_generated_document,
)
from app.utils.file_utils import save_bytes_to_output, save_upload_to_output

router = APIRouter()


async def _read_template_text(template_file: Optional[UploadFile]) -> str:
    """
    Read uploaded template file as text (best effort decoding).
    """
    if not template_file:
        return ""
    try:
        raw = await template_file.read()
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("latin-1", errors="ignore")
    finally:
        await template_file.close()


@router.post("/document/pdf")
async def generate_document_pdf(
    # Form fields (common)
    document_type: str = Form(...),
    currency: str = Form(...),
    seller_name: str = Form(...),
    buyer_name: str = Form(...),
    product: str = Form(...),
    quantity: int = Form(0),
    unit_price: float = Form(0.0),
    incoterm: str = Form(""),
    payment_term: str = Form(""),
    extra_notes: str = Form(""),

    # Optional files
    template_file: UploadFile | None = File(None),
    product_image: UploadFile | None = File(None),
):
    """
    Generate a PDF document.

    - Uses optional template for contracts/quotations
    - Uses optional image for product manuals
    - Saves generated PDF to output directory
    """
    # Convert document_type to enum (fallback to sales_contract if invalid)
    try:
        doc_type_enum = DocumentType(document_type)
    except ValueError:
        doc_type_enum = DocumentType.sales_contract

    # Build structured document data
    data = BaseDocumentData(
        document_type=doc_type_enum,
        currency=currency,
        seller_name=seller_name,
        buyer_name=buyer_name,
        product=product,
        quantity=quantity,
        unit_price=unit_price,
        incoterm=incoterm or None,
        payment_term=payment_term or None,
        extra_notes=extra_notes or None,
    )

    # Read template text if provided (for contract/quotation)
    template_text = ""
    if doc_type_enum in (DocumentType.sales_contract, DocumentType.quotation) and template_file:
        template_text = await _read_template_text(template_file)

    # Handle product image (for manuals)
    image_path: Optional[Path] = None
    if doc_type_enum == DocumentType.product_manual and product_image:
        image_path = save_upload_to_output(product_image, prefix="manual_image")

        # Write uploaded image bytes to file
        img_bytes = await product_image.read()
        image_path.write_bytes(img_bytes)

    # Generate PDF content and description
    pdf_bytes, description = generate_document_pdf_bytes(
        data=data,
        template_text=template_text or None,
        image_path=image_path,
    )

    # Save PDF to output directory
    pdf_path = save_bytes_to_output(pdf_bytes, prefix=data.document_type.value, suffix=".pdf")
    generated = build_generated_document(pdf_path, data, description)

    # Return PDF as downloadable response
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{generated.download_name}"',
            "X-Doc-Description": generated.description,
        },
    )