"""Unit tests for SMS batch analysis endpoint DTOs."""

import pytest
from pydantic import ValidationError

# Import DTOs for testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cellophanemail.routes.sms import (
    MessageInput,
    BatchAnalyzeRequest,
    PrivacySettings,
    HorsemanDetail,
    MessageAnalysisResponse,
    BatchAnalyzeResponse,
)


class TestMessageInput:
    """Tests for MessageInput DTO validation."""

    def test_valid_message_with_all_fields(self):
        """Valid message with all optional fields."""
        message = MessageInput(
            client_message_id="sms:123456789",
            content="Hello, how are you?",
            sender="+1234567890",
            channel="sms",
            direction="inbound",
            timestamp=1704067200000,
        )
        assert message.client_message_id == "sms:123456789"
        assert message.content == "Hello, how are you?"
        assert message.sender == "+1234567890"
        assert message.channel == "sms"
        assert message.direction == "inbound"
        assert message.timestamp == 1704067200000

    def test_valid_message_minimal(self):
        """Valid message with only required fields."""
        message = MessageInput(
            client_message_id="sms:123",
            content="Test message",
            sender="+1234567890",
        )
        assert message.client_message_id == "sms:123"
        assert message.content == "Test message"
        assert message.channel == "sms"  # Default
        assert message.direction == "inbound"  # Default
        assert message.timestamp is None

    def test_rejects_empty_content(self):
        """Empty content should be rejected."""
        with pytest.raises(ValidationError):
            MessageInput(
                client_message_id="sms:123",
                content="",
                sender="+1234567890",
            )

    def test_rejects_missing_client_message_id(self):
        """Missing client_message_id should be rejected."""
        with pytest.raises(ValidationError):
            MessageInput(
                content="Test message",
                sender="+1234567890",
            )

    def test_rejects_missing_sender(self):
        """Missing sender should be rejected."""
        with pytest.raises(ValidationError):
            MessageInput(
                client_message_id="sms:123",
                content="Test message",
            )

    def test_content_max_length(self):
        """Content text has max length of 50000."""
        # Should work with reasonable length
        MessageInput(
            client_message_id="sms:123",
            content="x" * 1000,
            sender="+1234567890",
        )

        # Should fail with too long content
        with pytest.raises(ValidationError):
            MessageInput(
                client_message_id="sms:123",
                content="x" * 50001,
                sender="+1234567890",
            )


class TestBatchAnalyzeRequest:
    """Tests for BatchAnalyzeRequest validation."""

    def test_valid_batch_single_message(self):
        """Valid batch with single message."""
        request = BatchAnalyzeRequest(
            messages=[
                MessageInput(
                    client_message_id="sms:123",
                    content="Test message",
                    sender="+1234567890",
                )
            ]
        )
        assert len(request.messages) == 1
        assert request.privacy is None

    def test_valid_batch_with_privacy_settings(self):
        """Valid batch with privacy settings."""
        request = BatchAnalyzeRequest(
            messages=[
                MessageInput(
                    client_message_id="sms:123",
                    content="Test message",
                    sender="+1234567890",
                )
            ],
            privacy=PrivacySettings(store_body=True, body_ttl_hours=48),
        )
        assert request.privacy.store_body is True
        assert request.privacy.body_ttl_hours == 48

    def test_rejects_empty_messages(self):
        """Empty messages list should be rejected."""
        with pytest.raises(ValidationError):
            BatchAnalyzeRequest(messages=[])

    def test_max_100_messages(self):
        """Batch is limited to 100 messages."""
        # Should fail with 101 messages
        messages = [
            MessageInput(
                client_message_id=f"sms:{i}",
                content="Test",
                sender="+1234567890",
            )
            for i in range(101)
        ]
        with pytest.raises(ValidationError):
            BatchAnalyzeRequest(messages=messages)


class TestPrivacySettings:
    """Tests for PrivacySettings DTO."""

    def test_default_values(self):
        """Default values are correct."""
        settings = PrivacySettings()
        assert settings.store_body is False
        assert settings.body_ttl_hours == 24

    def test_body_ttl_min_max(self):
        """body_ttl_hours must be between 1 and 168."""
        # Min value
        settings = PrivacySettings(body_ttl_hours=1)
        assert settings.body_ttl_hours == 1

        # Max value
        settings = PrivacySettings(body_ttl_hours=168)
        assert settings.body_ttl_hours == 168

        # Below min
        with pytest.raises(ValidationError):
            PrivacySettings(body_ttl_hours=0)

        # Above max
        with pytest.raises(ValidationError):
            PrivacySettings(body_ttl_hours=169)


class TestHorsemanDetail:
    """Tests for HorsemanDetail DTO."""

    def test_all_horseman_types(self):
        """All four horseman types should be valid."""
        for horseman_type in ["criticism", "contempt", "defensiveness", "stonewalling"]:
            detail = HorsemanDetail(
                type=horseman_type,
                confidence=0.8,
                severity="medium",
                indicators=["example indicator"],
            )
            assert detail.type == horseman_type

    def test_severity_levels(self):
        """All severity levels should be valid."""
        for severity in ["low", "medium", "high"]:
            detail = HorsemanDetail(
                type="criticism",
                confidence=0.5,
                severity=severity,
                indicators=[],
            )
            assert detail.severity == severity


class TestMessageAnalysisResponse:
    """Tests for MessageAnalysisResponse DTO."""

    def test_response_with_horsemen(self):
        """Response with detected horsemen."""
        response = MessageAnalysisResponse(
            client_message_id="sms:123456789",
            horsemen=[
                HorsemanDetail(
                    type="contempt",
                    confidence=0.85,
                    severity="high",
                    indicators=["mocking tone"],
                )
            ],
            horsemen_types=["contempt"],
            has_horsemen=True,
            toxicity_score=0.75,
            threat_level="high",
            reasoning="Contempt detected in message",
            processing_time_ms=1250,
            success=True,
        )

        assert response.client_message_id == "sms:123456789"
        assert response.has_horsemen is True
        assert len(response.horsemen) == 1
        assert response.horsemen[0].type == "contempt"
        assert response.toxicity_score == 0.75
        assert response.threat_level == "high"
        assert response.success is True
        assert response.error is None

    def test_response_safe_message(self):
        """Safe message response format."""
        response = MessageAnalysisResponse(
            client_message_id="sms:123",
            horsemen=[],
            horsemen_types=[],
            has_horsemen=False,
            toxicity_score=0.1,
            threat_level="safe",
            reasoning="No concerning patterns detected",
            processing_time_ms=800,
            success=True,
        )

        assert response.has_horsemen is False
        assert len(response.horsemen) == 0
        assert response.toxicity_score == 0.1
        assert response.threat_level == "safe"

    def test_response_with_error(self):
        """Failed analysis response format."""
        response = MessageAnalysisResponse(
            client_message_id="sms:456",
            horsemen=[],
            horsemen_types=[],
            has_horsemen=False,
            toxicity_score=0.0,
            threat_level="unknown",
            reasoning="",
            processing_time_ms=None,
            success=False,
            error="Analysis service unavailable",
        )

        assert response.success is False
        assert response.error == "Analysis service unavailable"


class TestBatchAnalyzeResponse:
    """Tests for BatchAnalyzeResponse DTO."""

    def test_batch_response_structure(self):
        """Batch response has correct structure."""
        response = BatchAnalyzeResponse(
            results=[
                MessageAnalysisResponse(
                    client_message_id="sms:1",
                    horsemen=[],
                    horsemen_types=[],
                    has_horsemen=False,
                    toxicity_score=0.1,
                    threat_level="safe",
                    reasoning="Clean",
                    processing_time_ms=100,
                    success=True,
                ),
                MessageAnalysisResponse(
                    client_message_id="sms:2",
                    horsemen=[],
                    horsemen_types=[],
                    has_horsemen=False,
                    toxicity_score=0.0,
                    threat_level="unknown",
                    reasoning="",
                    processing_time_ms=None,
                    success=False,
                    error="Failed",
                ),
            ],
            total=2,
            successful=1,
            failed=1,
        )

        assert response.total == 2
        assert response.successful == 1
        assert response.failed == 1
        assert len(response.results) == 2
