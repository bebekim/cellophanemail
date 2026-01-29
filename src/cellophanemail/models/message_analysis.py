"""Message analysis model for Android client batch processing."""

from piccolo.table import Table
from piccolo.columns import (
    Varchar, Text, Boolean, Timestamp, ForeignKey, UUID, JSON, BigInt
)
from datetime import datetime
import uuid
from enum import Enum

from .user import User


class MessageChannel(Enum):
    """Communication channel types."""
    SMS = "sms"
    EMAIL = "email"
    CHAT = "chat"
    OTHER = "other"


class MessageDirection(Enum):
    """Message direction relative to user."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageAnalysis(Table, tablename="message_analyses"):
    """
    Individual message analysis result with Four Horsemen detection.

    Stores analysis results for batch-processed messages from Android client.
    Privacy-controlled: message body can optionally be stored with TTL for LLM evaluation.
    """

    # Primary identification
    id = UUID(primary_key=True, default=uuid.uuid4)
    user = ForeignKey(User, index=True, null=False)

    # Client-provided identifiers
    client_message_id = Varchar(length=255, index=True, null=False)  # Unique per user
    channel = Varchar(
        length=20,
        default=MessageChannel.SMS,
        choices=MessageChannel,
        index=True
    )
    sender_identifier = Varchar(length=500, index=True, null=False)  # Phone/email/username
    direction = Varchar(
        length=10,
        default=MessageDirection.INBOUND,
        choices=MessageDirection
    )
    message_timestamp = BigInt(null=True)  # Unix epoch ms from client

    # Four Horsemen detection (tags returned to client)
    # Structure: [{"type": "criticism", "confidence": 0.85, "severity": "medium", "indicators": [...]}]
    horsemen_detected = JSON(default=[])
    has_horsemen = Boolean(default=False, index=True)  # Fast filter
    has_criticism = Boolean(default=False, index=True)
    has_contempt = Boolean(default=False, index=True)
    has_defensiveness = Boolean(default=False, index=True)
    has_stonewalling = Boolean(default=False, index=True)

    # Legacy compatibility fields (from existing analyzer)
    toxicity_score = BigInt(null=True)  # Score * 1000 for precision without Decimal
    threat_level = Varchar(length=20, null=True)  # safe, low, medium, high, critical

    # Analysis reasoning
    reasoning = Text(null=True)

    # Privacy-controlled content storage (optional for LLM evaluation)
    message_body = Text(null=True, secret=True)
    body_expires_at = Timestamp(null=True, index=True)

    # Processing metadata
    processing_time_ms = BigInt(null=True)
    model_used = Varchar(length=100, null=True)
    engine_version = Varchar(length=20, default="v1")

    # Timestamps
    analyzed_at = Timestamp(default=datetime.now, index=True)
    created_at = Timestamp(default=datetime.now)

    def __str__(self):
        return f"MessageAnalysis(id={self.client_message_id}, horsemen={self.has_horsemen})"

    @classmethod
    def get_unique_constraint(cls):
        """User + client_message_id should be unique."""
        return ["user", "client_message_id"]
