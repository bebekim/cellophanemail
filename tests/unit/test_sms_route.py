"""Unit tests for SMS analysis endpoint."""

import pytest
from unittest.mock import MagicMock, patch
from pydantic import ValidationError

# Import DTOs for testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cellophanemail.routes.sms import (
    SmsAnalyzeRequest,
    SmsAnalyzeResponse,
    HorsemanDetected,
)


class TestSmsAnalyzeRequest:
    """Tests for SMS analysis request validation."""

    def test_valid_request_with_all_fields(self):
        """Valid request with all optional fields."""
        request = SmsAnalyzeRequest(
            message_text="Hello, how are you?",
            sender_phone="+1234567890",
            sender_label="Client - John D.",
        )
        assert request.message_text == "Hello, how are you?"
        assert request.sender_phone == "+1234567890"
        assert request.sender_label == "Client - John D."

    def test_valid_request_minimal(self):
        """Valid request with only required field."""
        request = SmsAnalyzeRequest(message_text="Test message")
        assert request.message_text == "Test message"
        assert request.sender_phone is None
        assert request.sender_label is None

    def test_rejects_empty_message(self):
        """Empty message should be rejected."""
        with pytest.raises(ValidationError):
            SmsAnalyzeRequest(message_text="")

    def test_rejects_missing_message(self):
        """Missing message_text should be rejected."""
        with pytest.raises(ValidationError):
            SmsAnalyzeRequest()

    def test_validates_phone_format(self):
        """Phone number must match pattern."""
        # Valid formats
        SmsAnalyzeRequest(message_text="test", sender_phone="+1234567890")
        SmsAnalyzeRequest(message_text="test", sender_phone="1234567890123")

        # Invalid format
        with pytest.raises(ValidationError):
            SmsAnalyzeRequest(message_text="test", sender_phone="invalid")

    def test_message_max_length(self):
        """Message text has max length."""
        # Should work with reasonable length
        SmsAnalyzeRequest(message_text="x" * 1000)

        # Should fail with too long message
        with pytest.raises(ValidationError):
            SmsAnalyzeRequest(message_text="x" * 10001)


class TestSmsAnalyzeResponse:
    """Tests for SMS analysis response format."""

    def test_response_matches_android_contract(self):
        """Response should have all fields expected by Android app."""
        response = SmsAnalyzeResponse(
            toxicity_score=0.75,
            threat_level="high",
            is_toxic=True,
            horsemen_detected=[
                HorsemanDetected(
                    type="contempt",
                    confidence=0.85,
                    severity="high",
                    indicators=["mocking tone"],
                )
            ],
            filtered_summary="Client expressing frustration",
            processing_time_ms=1250,
            model_used="claude-3-5-sonnet-20241022",
        )

        # Verify all expected fields
        assert response.toxicity_score == 0.75
        assert response.threat_level == "high"
        assert response.is_toxic is True
        assert len(response.horsemen_detected) == 1
        assert response.horsemen_detected[0].type == "contempt"
        assert response.filtered_summary == "Client expressing frustration"
        assert response.processing_time_ms == 1250
        assert response.model_used == "claude-3-5-sonnet-20241022"

    def test_response_safe_message(self):
        """Safe message response format."""
        response = SmsAnalyzeResponse(
            toxicity_score=0.1,
            threat_level="safe",
            is_toxic=False,
            horsemen_detected=[],
            filtered_summary=None,
            processing_time_ms=800,
            model_used="claude-3-5-sonnet-20241022",
        )

        assert response.is_toxic is False
        assert response.filtered_summary is None
        assert len(response.horsemen_detected) == 0


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


class TestSenderContextLogic:
    """Tests for sender context building logic."""

    def test_label_takes_priority_over_phone(self):
        """Sender label should take priority over phone number."""
        # Mimics the logic in analyze_sms endpoint
        sender_label = "Client - John D."
        sender_phone = "+1234567890"

        sender_context = ""
        if sender_label:
            sender_context = sender_label
        elif sender_phone:
            sender_context = sender_phone

        assert sender_context == "Client - John D."

    def test_phone_used_when_no_label(self):
        """Phone should be used when no label provided."""
        sender_label = None
        sender_phone = "+1234567890"

        sender_context = ""
        if sender_label:
            sender_context = sender_label
        elif sender_phone:
            sender_context = sender_phone

        assert sender_context == "+1234567890"

    def test_empty_context_when_neither_provided(self):
        """Empty string when neither label nor phone provided."""
        sender_label = None
        sender_phone = None

        sender_context = ""
        if sender_label:
            sender_context = sender_label
        elif sender_phone:
            sender_context = sender_phone

        assert sender_context == ""

    def test_empty_label_falls_back_to_phone(self):
        """Empty string label should fall back to phone."""
        sender_label = ""
        sender_phone = "+1234567890"

        sender_context = ""
        if sender_label:
            sender_context = sender_label
        elif sender_phone:
            sender_context = sender_phone

        assert sender_context == "+1234567890"
