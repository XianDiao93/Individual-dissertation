# backend/app/routers/risk_router.py

from __future__ import annotations

from fastapi import APIRouter

from app.models.risk_model import RiskRequest, RiskResponse, RiskResult
from app.services.extraction import extract_trade_facts
from app.services.risk import analyze_risks


router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.post("/analyze", response_model=RiskResponse)
async def analyze_risk_endpoint(req: RiskRequest) -> RiskResponse:
    """
    Analyze risk based on message and optional normalized facts.
    """
    # Use provided normalized facts if available, otherwise extract them
    if req.normalized_facts:
        facts = req.normalized_facts
    else:
        facts = extract_trade_facts(
            message=req.message,
            user_region=None,
            preferred_language=None,
        )

    # Run risk analysis
    result_dict = analyze_risks(
        normalized_facts=facts,
        raw_message=req.message,
    )

    # Convert to response model
    result = RiskResult(**result_dict)

    return RiskResponse(
        normalized_facts=facts,
        result=result,
    )