# backend/app/models/email_model.py

from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

RiskLevel = Literal["unknown", "low", "medium", "high"]
EmailStatus = Literal["draft", "enriched", "replied"]


class EmailRisk(BaseModel):
    model_config = ConfigDict(extra="ignore")
    level: RiskLevel = "unknown"
    flags: List[str] = Field(default_factory=list)
    summary: Optional[str] = None


class EmailItem(BaseModel):
    """
    Matches your email JSON file schema (em_00001.json)
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(..., pattern=r"^\d{5}$")
    source_region: Optional[str] = None
    language: Optional[str] = None
    subject: Optional[str] = None

    body: str
    reply: Optional[str] = None
    group_id: Optional[str] = None

    from_: Optional[str] = Field(default=None, alias="from")
    status: EmailStatus = "draft"
    risk: EmailRisk = Field(default_factory=EmailRisk)


class EmailSummary(BaseModel):
    """
    Sidebar list summary
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(..., pattern=r"^\d{5}$")
    subject: Optional[str] = None
    from_: Optional[str] = Field(default=None, alias="from")
    status: EmailStatus = "draft"
    group_id: Optional[str] = None
    risk_level: RiskLevel = "unknown"


class EmailListResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ok: bool
    emails: List[EmailSummary] = Field(default_factory=list)
    error: Optional[str] = None


class EmailDetailResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ok: bool
    email: Optional[EmailItem] = None
    error: Optional[str] = None


class EmailUpdateRequest(BaseModel):
    """
    Optional for later writes (archive/reply/enrich).
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    source_region: Optional[str] = None
    language: Optional[str] = None
    subject: Optional[str] = None

    reply: Optional[str] = None
    group_id: Optional[str] = None
    status: Optional[EmailStatus] = None
    risk: Optional[EmailRisk] = None

    from_: Optional[str] = Field(default=None, alias="from")


class EmailUpdateResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ok: bool
    email: Optional[EmailItem] = None
    error: Optional[str] = None

class EmailDeleteResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ok: bool
    error: Optional[str] = None