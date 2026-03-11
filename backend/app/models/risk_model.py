# backend/app/models/risk_model.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RiskRequest(BaseModel):
    message: str
    normalized_facts: Optional[Dict[str, Any]] = None


class RiskDetail(BaseModel):
    level: str = "unknown"
    flags: List[str] = Field(default_factory=list)
    summary: Optional[str] = None


class RiskResult(BaseModel):
    decision: str = "CLEAR"
    risk_tags: List[str] = Field(default_factory=list)
    risk: RiskDetail = Field(default_factory=RiskDetail)
    by_category: Dict[str, List[str]] = Field(default_factory=dict)


class RiskResponse(BaseModel):
    normalized_facts: Dict[str, Any] = Field(default_factory=dict)
    result: RiskResult = Field(default_factory=RiskResult)