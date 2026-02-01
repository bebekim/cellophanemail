"""Unit tests for batch analyzer service."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock, patch

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestBatchAnalyzerServiceConstants:
    """Tests for BatchAnalyzerService configuration constants."""

    def test_sync_batch_limit(self):
        """Sync batch limit should be 100."""
        from cellophanemail.services.batch_analyzer import BatchAnalyzerService

        assert BatchAnalyzerService.SYNC_BATCH_LIMIT == 100

    def test_async_batch_limit(self):
        """Async batch limit should be 1000."""
        from cellophanemail.services.batch_analyzer import BatchAnalyzerService

        assert BatchAnalyzerService.ASYNC_BATCH_LIMIT == 1000


class TestBatchAnalyzerChannelParsing:
    """Tests for channel parsing logic."""

    def test_parse_valid_channels(self):
        """Valid channels should be parsed correctly."""
        from cellophanemail.services.batch_analyzer import BatchAnalyzerService

        service = BatchAnalyzerService(user_id=uuid4())

        assert service._parse_channel("sms") == "sms"
        assert service._parse_channel("email") == "email"
        assert service._parse_channel("chat") == "chat"
        assert service._parse_channel("other") == "other"

    def test_parse_channels_case_insensitive(self):
        """Channel parsing should be case insensitive."""
        from cellophanemail.services.batch_analyzer import BatchAnalyzerService

        service = BatchAnalyzerService(user_id=uuid4())

        assert service._parse_channel("SMS") == "sms"
        assert service._parse_channel("EMAIL") == "email"
        assert service._parse_channel("Chat") == "chat"

    def test_parse_unknown_channel_defaults_to_other(self):
        """Unknown channels should default to 'other'."""
        from cellophanemail.services.batch_analyzer import BatchAnalyzerService

        service = BatchAnalyzerService(user_id=uuid4())

        assert service._parse_channel("unknown") == "other"
        assert service._parse_channel("whatsapp") == "other"
        assert service._parse_channel("") == "other"


class TestBatchAnalyzerDirectionParsing:
    """Tests for direction parsing logic."""

    def test_parse_valid_directions(self):
        """Valid directions should be parsed correctly."""
        from cellophanemail.services.batch_analyzer import BatchAnalyzerService

        service = BatchAnalyzerService(user_id=uuid4())

        assert service._parse_direction("inbound") == "inbound"
        assert service._parse_direction("outbound") == "outbound"

    def test_parse_directions_case_insensitive(self):
        """Direction parsing should be case insensitive."""
        from cellophanemail.services.batch_analyzer import BatchAnalyzerService

        service = BatchAnalyzerService(user_id=uuid4())

        assert service._parse_direction("INBOUND") == "inbound"
        assert service._parse_direction("OUTBOUND") == "outbound"
        assert service._parse_direction("Inbound") == "inbound"

    def test_parse_unknown_direction_defaults_to_inbound(self):
        """Unknown directions should default to 'inbound'."""
        from cellophanemail.services.batch_analyzer import BatchAnalyzerService

        service = BatchAnalyzerService(user_id=uuid4())

        assert service._parse_direction("unknown") == "inbound"
        assert service._parse_direction("sent") == "inbound"
        assert service._parse_direction("") == "inbound"


class TestBatchAnalyzerResultFormatting:
    """Tests for result formatting logic."""

    def test_format_result_extracts_horsemen_types(self):
        """Format result should correctly extract horsemen types from flags."""
        from cellophanemail.services.batch_analyzer import BatchAnalyzerService
        from cellophanemail.models import MessageAnalysis

        service = BatchAnalyzerService(user_id=uuid4())

        # Create mock analysis with specific horsemen flags
        analysis = MagicMock(spec=MessageAnalysis)
        analysis.client_message_id = "test:123"
        analysis.horsemen_detected = []
        analysis.has_horsemen = True
        analysis.has_criticism = True
        analysis.has_contempt = True
        analysis.has_defensiveness = False
        analysis.has_stonewalling = False
        analysis.threat_level = "high"
        analysis.reasoning = "Test reasoning"
        analysis.processing_time_ms = 500

        result = service._format_result(analysis, {})

        assert result["client_message_id"] == "test:123"
        assert "criticism" in result["horsemen_types"]
        assert "contempt" in result["horsemen_types"]
        assert "defensiveness" not in result["horsemen_types"]
        assert "stonewalling" not in result["horsemen_types"]
        assert result["has_horsemen"] is True
        assert result["threat_level"] == "high"
        assert result["success"] is True

    def test_format_result_handles_no_horsemen(self):
        """Format result should handle messages with no horsemen."""
        from cellophanemail.services.batch_analyzer import BatchAnalyzerService
        from cellophanemail.models import MessageAnalysis

        service = BatchAnalyzerService(user_id=uuid4())

        analysis = MagicMock(spec=MessageAnalysis)
        analysis.client_message_id = "test:456"
        analysis.horsemen_detected = []
        analysis.has_horsemen = False
        analysis.has_criticism = False
        analysis.has_contempt = False
        analysis.has_defensiveness = False
        analysis.has_stonewalling = False
        analysis.threat_level = "safe"
        analysis.reasoning = "Clean message"
        analysis.processing_time_ms = 300

        result = service._format_result(analysis, {})

        assert result["horsemen_types"] == []
        assert result["has_horsemen"] is False
        assert result["threat_level"] == "safe"

    def test_format_result_handles_all_four_horsemen(self):
        """Format result should handle messages with all four horsemen."""
        from cellophanemail.services.batch_analyzer import BatchAnalyzerService
        from cellophanemail.models import MessageAnalysis

        service = BatchAnalyzerService(user_id=uuid4())

        analysis = MagicMock(spec=MessageAnalysis)
        analysis.client_message_id = "test:789"
        analysis.horsemen_detected = []
        analysis.has_horsemen = True
        analysis.has_criticism = True
        analysis.has_contempt = True
        analysis.has_defensiveness = True
        analysis.has_stonewalling = True
        analysis.threat_level = "critical"
        analysis.reasoning = "Highly toxic"
        analysis.processing_time_ms = 800

        result = service._format_result(analysis, {})

        assert len(result["horsemen_types"]) == 4
        assert "criticism" in result["horsemen_types"]
        assert "contempt" in result["horsemen_types"]
        assert "defensiveness" in result["horsemen_types"]
        assert "stonewalling" in result["horsemen_types"]
        assert result["threat_level"] == "critical"


class TestBatchAnalyzerBatchLimits:
    """Tests for batch size limit enforcement."""

    @pytest.mark.asyncio
    async def test_process_batch_rejects_oversized_batch(self):
        """Process batch should reject batches over the sync limit."""
        from cellophanemail.services.batch_analyzer import BatchAnalyzerService

        service = BatchAnalyzerService(user_id=uuid4())

        # Create batch over the limit
        messages = [{"content": f"msg{i}", "client_message_id": f"id:{i}"} for i in range(101)]

        with pytest.raises(ValueError) as exc_info:
            await service.process_batch(messages)

        assert "exceeds sync limit" in str(exc_info.value)
        assert "100" in str(exc_info.value)


class TestPrivacySettings:
    """Tests for privacy settings handling."""

    def test_default_privacy_settings(self):
        """Default privacy settings should not store body."""
        from cellophanemail.routes.sms import PrivacySettings

        settings = PrivacySettings()

        assert settings.store_body is False
        assert settings.body_ttl_hours == 24

    def test_privacy_settings_with_body_storage(self):
        """Privacy settings should support body storage with TTL."""
        from cellophanemail.routes.sms import PrivacySettings

        settings = PrivacySettings(store_body=True, body_ttl_hours=48)

        assert settings.store_body is True
        assert settings.body_ttl_hours == 48

    def test_privacy_settings_ttl_bounds(self):
        """Body TTL should be between 1 and 168 hours (1 week)."""
        from cellophanemail.routes.sms import PrivacySettings
        from pydantic import ValidationError

        # Valid bounds
        PrivacySettings(body_ttl_hours=1)
        PrivacySettings(body_ttl_hours=168)

        # Invalid bounds
        with pytest.raises(ValidationError):
            PrivacySettings(body_ttl_hours=0)

        with pytest.raises(ValidationError):
            PrivacySettings(body_ttl_hours=169)
