# backend/app/models/risk_model.py

from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field, ConfigDict


# Overall risk level
RiskLevel = Literal["unknown", "low", "medium", "high", "critical"]

# Severity for individual risk tags
RiskSeverity = Literal["unknown", "low", "medium", "high", "critical"]


class RiskRequest(BaseModel):
    """
    Request model for risk analysis.
    """
    message: str
    normalized_facts: Optional[Dict[str, Any]] = None


class RiskTagItem(BaseModel):
    """
    Individual risk tag with severity.
    """
    model_config = ConfigDict(extra="ignore")

    tag: str
    severity: RiskSeverity = "unknown"


class RiskDetail(BaseModel):
    """
    Detailed risk information including level and tags.
    """
    model_config = ConfigDict(extra="ignore")

    level: RiskLevel = "unknown"
    tags: List[RiskTagItem] = Field(default_factory=list)
    summary: Optional[str] = None


class RiskResult(BaseModel):
    """
    Full risk analysis result.
    """
    model_config = ConfigDict(extra="ignore")

    decision: str = "CLEAR"
    risk_tags: List[str] = Field(default_factory=list)
    risk: RiskDetail = Field(default_factory=RiskDetail)
    by_category: Dict[str, List[str]] = Field(default_factory=dict)


class RiskResponse(BaseModel):
    """
    Response model for risk analysis endpoint.
    """
    model_config = ConfigDict(extra="ignore")

    normalized_facts: Dict[str, Any] = Field(default_factory=dict)
    result: RiskResult = Field(default_factory=RiskResult)