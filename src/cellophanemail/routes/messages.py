# ABOUTME: Platform-agnostic message analysis API
# ABOUTME: Supports SMS, email, chat and future channels

from enum import Enum
from typing import List, Optional

from litestar import Controller, post
from litestar.status_codes import HTTP_200_OK
from pydantic import BaseModel, Field

from cellophanemail.middleware.jwt_auth import jwt_auth_required
from cellophanemail.features.email_protection.analyzer_factory import AnalyzerFactory


class MessageChannel(str, Enum):
    """Communication channel types."""

    SMS = "sms"
    EMAIL = "email"
    CHAT = "chat"
    OTHER = "other"


class Classification(str, Enum):
    """4-tier classification for Android compatibility.

    Maps from internal 5-tier ThreatLevel:
    - SAFE -> SAFE
    - LOW -> WARNING
    - MEDIUM -> WARNING
    - HIGH -> HARMFUL
    - CRITICAL -> ABUSIVE
    """

    SAFE = "SAFE"
    WARNING = "WARNING"
    HARMFUL = "HARMFUL"
    ABUSIVE = "ABUSIVE"

    @classmethod
    def from_threat_level(cls, threat_level: str) -> "Classification":
        """Convert 5-tier threat level to 4-tier classification."""
        mapping = {
            "safe": cls.SAFE,
            "low": cls.WARNING,
            "medium": cls.WARNING,
            "high": cls.HARMFUL,
            "critical": cls.ABUSIVE,
        }
        return mapping.get(threat_level.lower(), cls.SAFE)


# ============================================================================
# Request DTOs
# ============================================================================


class MessageAnalyzeRequest(BaseModel):
    """Platform-agnostic message analysis request.

    Works for SMS, email, chat, and future channels.
    """

    # Required fields
    content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Message content to analyze",
    )

    # Channel identification
    channel: MessageChannel = Field(
        default=MessageChannel.OTHER,
        description="Communication channel (sms, email, chat, other)",
    )

    # Sender context (flexible for different channels)
    sender: Optional[str] = Field(
        None,
        max_length=500,
        description="Sender identifier (phone, email, username, etc.)",
    )
    sender_label: Optional[str] = Field(
        None,
        max_length=100,
        description="Human-readable sender label (e.g., 'Client - John D.')",
    )

    # Optional metadata
    timestamp: Optional[int] = Field(
        None,
        description="Message timestamp in milliseconds (Unix epoch)",
    )
    device_id: Optional[str] = Field(
        None,
        max_length=100,
        description="Client device identifier for rate limiting/analytics",
    )
    thread_id: Optional[str] = Field(
        None,
        max_length=100,
        description="Conversation thread identifier",
    )

    # Channel-specific metadata (extensible)
    metadata: Optional[dict] = Field(
        None,
        description="Channel-specific metadata (e.g., email subject, chat room)",
    )


# ============================================================================
# Response DTOs
# ============================================================================


class HorsemanDetected(BaseModel):
    """Single horseman pattern detection."""

    type: str = Field(
        ...,
        description="Horseman type: criticism, contempt, defensiveness, stonewalling",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Detection confidence (0-1)",
    )
    severity: str = Field(
        ...,
        description="Severity level: low, medium, high",
    )
    indicators: List[str] = Field(
        default_factory=list,
        description="Specific phrases/patterns that triggered detection",
    )


class MessageAnalyzeResponse(BaseModel):
    """Platform-agnostic message analysis response.

    Includes both 5-tier threat_level (internal) and 4-tier classification
    (Android compatibility).
    """

    # Core analysis results
    is_toxic: bool = Field(
        ...,
        description="Quick boolean: is message considered toxic? (threat_level != SAFE)",
    )

    # Classification systems
    threat_level: str = Field(
        ...,
        description="5-tier: safe, low, medium, high, critical",
    )
    classification: str = Field(
        ...,
        description="4-tier Android format: SAFE, WARNING, HARMFUL, ABUSIVE",
    )

    # Four Horsemen detection
    horsemen_detected: List[HorsemanDetected] = Field(
        default_factory=list,
        description="List of detected Four Horsemen patterns",
    )
    horsemen: List[str] = Field(
        default_factory=list,
        description="Simple list of horsemen types (for Android)",
    )

    # Content processing
    filtered_summary: Optional[str] = Field(
        None,
        description="Fact-only summary for toxic messages",
    )
    reasoning: str = Field(
        ...,
        description="Explanation of the analysis",
    )
    specific_examples: List[str] = Field(
        default_factory=list,
        description="Specific toxic phrases found",
    )

    # Metadata
    processing_time_ms: int = Field(
        ...,
        description="Analysis processing time in milliseconds",
    )
    model_used: str = Field(
        ...,
        description="AI model that performed analysis",
    )
    channel: str = Field(
        ...,
        description="Channel that was analyzed",
    )


# ============================================================================
# Controller
# ============================================================================


class MessagesController(Controller):
    """Platform-agnostic message analysis endpoints."""

    path = "/api/v1/messages"
    tags = ["Messages"]
    guards = [jwt_auth_required]

    @post("/analyze", status_code=HTTP_200_OK)
    async def analyze_message(
        self, data: MessageAnalyzeRequest
    ) -> MessageAnalyzeResponse:
        """
        Analyze message content for Four Horsemen toxicity patterns.

        Platform-agnostic endpoint supporting SMS, email, chat, and other channels.
        Used by mobile apps when local LLM is unavailable.
        """
        # Build sender context string (label takes priority)
        sender_context = ""
        if data.sender_label:
            sender_context = data.sender_label
        elif data.sender:
            sender_context = data.sender

        # Create analyzer using factory (respects environment config)
        analyzer = AnalyzerFactory.create_analyzer()

        # Use existing analyzer - text-agnostic by design
        analysis = analyzer.analyze_email_toxicity(
            email_content=data.content,
            sender_email=sender_context,
        )

        # Get model name from analyzer
        model_name = (
            getattr(analyzer, "model_name", "anthropic-claude") or "anthropic-claude"
        )

        # Map threat level to 4-tier classification
        classification = Classification.from_threat_level(analysis.threat_level.value)

        # Extract specific examples from horsemen indicators
        specific_examples = []
        for h in analysis.horsemen_detected:
            specific_examples.extend(h.indicators[:2])  # Max 2 per horseman

        # Build response with both classification systems
        return MessageAnalyzeResponse(
            # Core results
            is_toxic=not analysis.safe,
            # Both classification systems
            threat_level=analysis.threat_level.value,
            classification=classification.value,
            # Horsemen - both formats
            horsemen_detected=[
                HorsemanDetected(
                    type=h.horseman,
                    confidence=h.confidence,
                    severity=h.severity,
                    indicators=h.indicators,
                )
                for h in analysis.horsemen_detected
            ],
            horsemen=[h.horseman for h in analysis.horsemen_detected],
            # Content
            filtered_summary=analysis.reasoning if not analysis.safe else None,
            reasoning=analysis.reasoning,
            specific_examples=specific_examples[:6],  # Max 6 examples
            # Metadata
            processing_time_ms=analysis.processing_time_ms,
            model_used=model_name,
            channel=data.channel.value,
        )
