# backend/app/models/email_model.py

from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

# Risk level used for overall email risk
RiskLevel = Literal["unknown", "low", "medium", "high", "critical"]

# Severity used for individual risk tags
RiskSeverity = Literal["unknown", "low", "medium", "high", "critical"]

# Email processing status
EmailStatus = Literal["draft", "enriched", "replied"]


class EmailRiskTag(BaseModel):
    """
    Single risk tag with severity.
    """
    model_config = ConfigDict(extra="ignore")

    tag: str
    severity: RiskSeverity = "unknown"


class EmailRisk(BaseModel):
    """
    Overall risk information for an email.
    """
    model_config = ConfigDict(extra="ignore")

    level: RiskLevel = "unknown"
    tags: List[EmailRiskTag] = Field(default_factory=list)
    summary: Optional[str] = None


class EmailItem(BaseModel):
    """
    Full email detail model.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(..., pattern=r"^\d{5}$")  # 5-digit email ID
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
    Lightweight summary used for sidebar list display.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(..., pattern=r"^\d{5}$")
    subject: Optional[str] = None
    from_: Optional[str] = Field(default=None, alias="from")
    status: EmailStatus = "draft"
    group_id: Optional[str] = None

    risk_level: RiskLevel = "unknown"
    risk_tags: List[EmailRiskTag] = Field(default_factory=list)


class EmailListResponse(BaseModel):
    """
    Response for email list endpoint.
    """
    model_config = ConfigDict(extra="ignore")

    ok: bool
    emails: List[EmailSummary] = Field(default_factory=list)
    error: Optional[str] = None


class EmailDetailResponse(BaseModel):
    """
    Response for single email detail endpoint.
    """
    model_config = ConfigDict(extra="ignore")

    ok: bool
    email: Optional[EmailItem] = None
    error: Optional[str] = None


class EmailUpdateRequest(BaseModel):
    """
    Request model for updating email fields (e.g., reply, status, risk).
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
    """
    Response after updating an email.
    """
    model_config = ConfigDict(extra="ignore")

    ok: bool
    email: Optional[EmailItem] = None
    error: Optional[str] = None


class EmailDeleteResponse(BaseModel):
    """
    Response after deleting an email.
    """
    model_config = ConfigDict(extra="ignore")

    ok: bool
    error: Optional[str] = None