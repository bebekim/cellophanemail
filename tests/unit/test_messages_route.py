"""Unit tests for platform-agnostic message analysis endpoint."""

import pytest
from pydantic import ValidationError

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cellophanemail.routes.messages import (
    MessageAnalyzeRequest,
    MessageAnalyzeResponse,
    HorsemanDetected,
    MessageChannel,
    Classification,
)


class TestMessageChannel:
    """Tests for MessageChannel enum."""

    def test_all_channels_defined(self):
        """All expected channels should be defined."""
        assert MessageChannel.SMS.value == "sms"
        assert MessageChannel.EMAIL.value == "email"
        assert MessageChannel.CHAT.value == "chat"
        assert MessageChannel.OTHER.value == "other"

    def test_channel_count(self):
        """Should have exactly 4 channel types."""
        assert len(MessageChannel) == 4


class TestClassification:
    """Tests for 4-tier Classification enum."""

    def test_all_classifications_defined(self):
        """All classification levels should be defined."""
        assert Classification.SAFE.value == "SAFE"
        assert Classification.WARNING.value == "WARNING"
        assert Classification.HARMFUL.value == "HARMFUL"
        assert Classification.ABUSIVE.value == "ABUSIVE"

    def test_classification_from_threat_level(self):
        """Mapping from 5-tier to 4-tier should be correct."""
        # SAFE -> SAFE
        assert Classification.from_threat_level("safe") == Classification.SAFE
        # LOW, MEDIUM -> WARNING
        assert Classification.from_threat_level("low") == Classification.WARNING
        assert Classification.from_threat_level("medium") == Classification.WARNING
        # HIGH -> HARMFUL
        assert Classification.from_threat_level("high") == Classification.HARMFUL
        # CRITICAL -> ABUSIVE
        assert Classification.from_threat_level("critical") == Classification.ABUSIVE

    def test_classification_case_insensitive(self):
        """Threat level mapping should be case insensitive."""
        assert Classification.from_threat_level("SAFE") == Classification.SAFE
        assert Classification.from_threat_level("Safe") == Classification.SAFE
        assert Classification.from_threat_level("HIGH") == Classification.HARMFUL

    def test_unknown_threat_level_defaults_to_safe(self):
        """Unknown threat levels should default to SAFE."""
        assert Classification.from_threat_level("unknown") == Classification.SAFE
        assert Classification.from_threat_level("") == Classification.SAFE


class TestMessageAnalyzeRequest:
    """Tests for platform-agnostic request validation."""

    def test_valid_request_minimal(self):
        """Valid request with only required field."""
        request = MessageAnalyzeRequest(content="Hello world")
        assert request.content == "Hello world"
        assert request.channel == MessageChannel.OTHER  # default
        assert request.sender is None
        assert request.sender_label is None
        assert request.timestamp is None
        assert request.device_id is None

    def test_valid_request_sms(self):
        """Valid SMS request with all fields."""
        request = MessageAnalyzeRequest(
            content="Test message",
            channel=MessageChannel.SMS,
            sender="+1234567890",
            sender_label="Client - John D.",
            timestamp=1704067200000,
            device_id="device123",
            thread_id="thread456",
        )
        assert request.channel == MessageChannel.SMS
        assert request.sender == "+1234567890"
        assert request.sender_label == "Client - John D."
        assert request.timestamp == 1704067200000

    def test_valid_request_email(self):
        """Valid email request with metadata."""
        request = MessageAnalyzeRequest(
            content="Email body content",
            channel=MessageChannel.EMAIL,
            sender="john@example.com",
            metadata={"subject": "Important meeting"},
        )
        assert request.channel == MessageChannel.EMAIL
        assert request.sender == "john@example.com"
        assert request.metadata == {"subject": "Important meeting"}

    def test_rejects_empty_content(self):
        """Empty content should be rejected."""
        with pytest.raises(ValidationError):
            MessageAnalyzeRequest(content="")

    def test_rejects_missing_content(self):
        """Missing content should be rejected."""
        with pytest.raises(ValidationError):
            MessageAnalyzeRequest()

    def test_content_max_length(self):
        """Content has max length of 50000."""
        # Should work with long content
        MessageAnalyzeRequest(content="x" * 50000)

        # Should fail with too long content
        with pytest.raises(ValidationError):
            MessageAnalyzeRequest(content="x" * 50001)

    def test_channel_validation(self):
        """Channel must be valid enum value."""
        # Valid channels
        for channel in MessageChannel:
            MessageAnalyzeRequest(content="test", channel=channel)

        # Invalid channel (string not matching enum)
        with pytest.raises(ValidationError):
            MessageAnalyzeRequest(content="test", channel="invalid")


class TestMessageAnalyzeResponse:
    """Tests for platform-agnostic response format."""

    def test_response_with_all_fields(self):
        """Response should have all expected fields."""
        response = MessageAnalyzeResponse(
            is_toxic=True,
            threat_level="high",
            classification="HARMFUL",
            horsemen_detected=[
                HorsemanDetected(
                    type="contempt",
                    confidence=0.85,
                    severity="high",
                    indicators=["mocking tone"],
                )
            ],
            horsemen=["contempt"],
            filtered_summary="Facts extracted from message",
            reasoning="Contains contempt patterns",
            specific_examples=["example phrase"],
            processing_time_ms=1250,
            model_used="claude-3-5-sonnet-20241022",
            channel="sms",
        )

        assert response.is_toxic is True
        assert response.threat_level == "high"
        assert response.classification == "HARMFUL"
        assert len(response.horsemen_detected) == 1
        assert response.horsemen == ["contempt"]
        assert response.filtered_summary == "Facts extracted from message"
        assert response.processing_time_ms == 1250
        assert response.channel == "sms"

    def test_response_safe_message(self):
        """Safe message response format."""
        response = MessageAnalyzeResponse(
            is_toxic=False,
            threat_level="safe",
            classification="SAFE",
            horsemen_detected=[],
            horsemen=[],
            filtered_summary=None,
            reasoning="No toxic patterns detected",
            specific_examples=[],
            processing_time_ms=500,
            model_used="claude-3-5-sonnet-20241022",
            channel="email",
        )

        assert response.is_toxic is False
        assert response.classification == "SAFE"
        assert response.filtered_summary is None
        assert len(response.horsemen_detected) == 0
        assert response.channel == "email"


class TestHorsemanDetected:
    """Tests for horseman detection DTO."""

    def test_all_horseman_types(self):
        """All four horseman types should be valid."""
        for horseman_type in ["criticism", "contempt", "defensiveness", "stonewalling"]:
            detection = HorsemanDetected(
                type=horseman_type,
                confidence=0.8,
                severity="medium",
                indicators=["example"],
            )
            assert detection.type == horseman_type

    def test_severity_levels(self):
        """All severity levels should be valid."""
        for severity in ["low", "medium", "high"]:
            detection = HorsemanDetected(
                type="criticism",
                confidence=0.5,
                severity=severity,
                indicators=[],
            )
            assert detection.severity == severity

    def test_confidence_bounds(self):
        """Confidence should be between 0 and 1."""
        # Valid bounds
        HorsemanDetected(
            type="criticism", confidence=0.0, severity="low", indicators=[]
        )
        HorsemanDetected(
            type="criticism", confidence=1.0, severity="high", indicators=[]
        )

        # Invalid bounds
        with pytest.raises(ValidationError):
            HorsemanDetected(
                type="criticism", confidence=-0.1, severity="low", indicators=[]
            )
        with pytest.raises(ValidationError):
            HorsemanDetected(
                type="criticism", confidence=1.1, severity="low", indicators=[]
            )


class TestSenderContextLogic:
    """Tests for sender context priority logic."""

    def test_label_takes_priority_over_sender(self):
        """Sender label should take priority over sender."""
        request = MessageAnalyzeRequest(
            content="test",
            sender="+1234567890",
            sender_label="Client - John D.",
        )

        # Mimics the logic in analyze_message endpoint
        sender_context = ""
        if request.sender_label:
            sender_context = request.sender_label
        elif request.sender:
            sender_context = request.sender

        assert sender_context == "Client - John D."

    def test_sender_used_when_no_label(self):
        """Sender should be used when no label provided."""
        request = MessageAnalyzeRequest(
            content="test",
            sender="john@example.com",
        )

        sender_context = ""
        if request.sender_label:
            sender_context = request.sender_label
        elif request.sender:
            sender_context = request.sender

        assert sender_context == "john@example.com"

    def test_empty_context_when_neither_provided(self):
        """Empty string when neither label nor sender provided."""
        request = MessageAnalyzeRequest(content="test")

        sender_context = ""
        if request.sender_label:
            sender_context = request.sender_label
        elif request.sender:
            sender_context = request.sender

        assert sender_context == ""


class TestCrossChannelCompatibility:
    """Tests for cross-channel API compatibility."""

    def test_sms_request_format(self):
        """SMS format should work with platform-agnostic API."""
        request = MessageAnalyzeRequest(
            content="Urgent: call me back",
            channel=MessageChannel.SMS,
            sender="+1234567890",
            timestamp=1704067200000,
            device_id="android123",
        )
        assert request.channel == MessageChannel.SMS

    def test_email_request_format(self):
        """Email format should work with platform-agnostic API."""
        request = MessageAnalyzeRequest(
            content="Subject: Meeting\n\nPlease see attached.",
            channel=MessageChannel.EMAIL,
            sender="boss@company.com",
            metadata={"subject": "Meeting", "has_attachments": True},
        )
        assert request.channel == MessageChannel.EMAIL
        assert request.metadata["subject"] == "Meeting"

    def test_chat_request_format(self):
        """Chat format should work with platform-agnostic API."""
        request = MessageAnalyzeRequest(
            content="Hey, are you there?",
            channel=MessageChannel.CHAT,
            sender="user123",
            thread_id="room_general",
            metadata={"platform": "slack"},
        )
        assert request.channel == MessageChannel.CHAT
        assert request.thread_id == "room_general"
