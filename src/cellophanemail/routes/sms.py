# ABOUTME: SMS analysis API for Android app cloud LLM fallback
# ABOUTME: Leverages existing text-agnostic analysis engine

from typing import List, Optional

from litestar import Controller, post
from litestar.status_codes import HTTP_200_OK
from pydantic import BaseModel, Field

from cellophanemail.middleware.jwt_auth import jwt_auth_required
from cellophanemail.features.email_protection.analyzer_factory import AnalyzerFactory


# Request DTO - matches Android app contract
class SmsAnalyzeRequest(BaseModel):
    """SMS analysis request from Android app."""

    message_text: str = Field(..., min_length=1, max_length=10000)
    sender_phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{7,15}$")
    sender_label: Optional[str] = Field(None, max_length=100)


# Response DTOs - matches Android app contract from docs/API.md
class HorsemanDetected(BaseModel):
    """Single horseman detection in response."""

    type: str  # criticism, contempt, defensiveness, stonewalling
    confidence: float
    severity: str  # low, medium, high
    indicators: List[str]


class SmsAnalyzeResponse(BaseModel):
    """SMS analysis response for Android app."""

    toxicity_score: float
    threat_level: str  # safe, low, medium, high, critical
    is_toxic: bool
    horsemen_detected: List[HorsemanDetected]
    filtered_summary: Optional[str] = None
    processing_time_ms: int
    model_used: str


class SmsController(Controller):
    """SMS analysis endpoints for Android app."""

    path = "/api/v1/sms"
    tags = ["SMS"]
    guards = [jwt_auth_required]

    @post("/analyze", status_code=HTTP_200_OK)
    async def analyze_sms(self, data: SmsAnalyzeRequest) -> SmsAnalyzeResponse:
        """
        Analyze SMS text for Four Horsemen toxicity patterns.

        Used by Android app when local LLM is unavailable.
        """
        # Build sender context string
        sender_context = ""
        if data.sender_label:
            sender_context = data.sender_label
        elif data.sender_phone:
            sender_context = data.sender_phone

        # Create analyzer using factory (respects environment config)
        analyzer = AnalyzerFactory.create_analyzer()

        # Use existing analyzer - works for any text content
        analysis = analyzer.analyze_email_toxicity(
            email_content=data.message_text,
            sender_email=sender_context,
        )

        # Get model name from analyzer
        model_name = getattr(analyzer, "model_name", "anthropic-claude") or "anthropic-claude"

        # Map to Android response format
        return SmsAnalyzeResponse(
            toxicity_score=analysis.toxicity_score,
            threat_level=analysis.threat_level.value,
            is_toxic=not analysis.safe,
            horsemen_detected=[
                HorsemanDetected(
                    type=h.horseman,
                    confidence=h.confidence,
                    severity=h.severity,
                    indicators=h.indicators,
                )
                for h in analysis.horsemen_detected
            ],
            filtered_summary=analysis.reasoning if not analysis.safe else None,
            processing_time_ms=analysis.processing_time_ms,
            model_used=model_name,
        )
