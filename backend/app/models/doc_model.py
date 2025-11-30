# backend/app/models/doc_model.py
from enum import Enum
from pydantic import BaseModel
from typing import Optional


class DocumentType(str, Enum):
    sales_contract = "sales_contract"
    quotation = "quotation"
    product_manual = "product_manual"


class BaseDocumentData(BaseModel):
    """
    Core structured data for all trade documents.
    This is independent from HTTP (Form / File) details.
    """
    document_type: DocumentType
    currency: str
    seller_name: str
    buyer_name: str
    product: str
    quantity: int = 0
    unit_price: float = 0.0
    incoterm: Optional[str] = None
    payment_term: Optional[str] = None
    extra_notes: Optional[str] = None


class GeneratedDocument(BaseModel):
    """
    Result of document generation (from the service layer).
    """
    file_path: str        # absolute path on disk
    download_name: str    # suggested filename when downloading
    description: str      # short natural-language description (for UI)
