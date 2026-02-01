"""Unit tests for Android client backend API models."""

import pytest
from datetime import datetime
from uuid import uuid4

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cellophanemail.models.message_analysis import (
    MessageAnalysis,
    MessageChannel,
    MessageDirection,
)
from cellophanemail.models.sender_summary import SenderSummary
from cellophanemail.models.analysis_job import AnalysisJob, JobStatus


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


class TestMessageDirection:
    """Tests for MessageDirection enum."""

    def test_all_directions_defined(self):
        """All expected directions should be defined."""
        assert MessageDirection.INBOUND.value == "inbound"
        assert MessageDirection.OUTBOUND.value == "outbound"

    def test_direction_count(self):
        """Should have exactly 2 direction types."""
        assert len(MessageDirection) == 2


class TestJobStatus:
    """Tests for JobStatus enum."""

    def test_all_statuses_defined(self):
        """All expected job statuses should be defined."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"

    def test_status_count(self):
        """Should have exactly 5 status types."""
        assert len(JobStatus) == 5


class TestMessageAnalysisModel:
    """Tests for MessageAnalysis model structure."""

    def test_table_name(self):
        """Table should have correct name."""
        assert MessageAnalysis._meta.tablename == "message_analyses"

    def test_required_columns_exist(self):
        """All required columns should exist."""
        columns = {col._meta.name for col in MessageAnalysis._meta.columns}

        required = {
            "id",
            "user",
            "client_message_id",
            "channel",
            "sender_identifier",
            "direction",
            "message_timestamp",
            "horsemen_detected",
            "has_horsemen",
            "has_criticism",
            "has_contempt",
            "has_defensiveness",
            "has_stonewalling",
            "toxicity_score",
            "threat_level",
            "reasoning",
            "message_body",
            "body_expires_at",
            "processing_time_ms",
            "model_used",
            "engine_version",
            "analyzed_at",
            "created_at",
        }

        assert required.issubset(columns)

    def test_horsemen_boolean_flags(self):
        """All four horsemen should have boolean flag columns."""
        columns = {col._meta.name for col in MessageAnalysis._meta.columns}

        horsemen_flags = {
            "has_horsemen",
            "has_criticism",
            "has_contempt",
            "has_defensiveness",
            "has_stonewalling",
        }

        assert horsemen_flags.issubset(columns)


class TestSenderSummaryModel:
    """Tests for SenderSummary model structure."""

    def test_table_name(self):
        """Table should have correct name."""
        assert SenderSummary._meta.tablename == "sender_summaries"

    def test_required_columns_exist(self):
        """All required columns should exist."""
        columns = {col._meta.name for col in SenderSummary._meta.columns}

        required = {
            "id",
            "user",
            "sender_identifier",
            "channel",
            "total_messages",
            "messages_with_horsemen",
            "clean_messages",
            "criticism_count",
            "contempt_count",
            "defensiveness_count",
            "stonewalling_count",
            "horsemen_counts",
            "first_message_at",
            "last_message_at",
            "last_horseman_at",
            "created_at",
            "updated_at",
        }

        assert required.issubset(columns)

    def test_horsemen_count_columns(self):
        """All four horsemen should have count columns."""
        columns = {col._meta.name for col in SenderSummary._meta.columns}

        horsemen_counts = {
            "criticism_count",
            "contempt_count",
            "defensiveness_count",
            "stonewalling_count",
        }

        assert horsemen_counts.issubset(columns)


class TestAnalysisJobModel:
    """Tests for AnalysisJob model structure."""

    def test_table_name(self):
        """Table should have correct name."""
        assert AnalysisJob._meta.tablename == "analysis_jobs"

    def test_required_columns_exist(self):
        """All required columns should exist."""
        columns = {col._meta.name for col in AnalysisJob._meta.columns}

        required = {
            "id",
            "user",
            "status",
            "total_messages",
            "processed_messages",
            "failed_messages",
            "message_ids",
            "privacy_settings",
            "error_message",
            "failed_message_ids",
            "arq_job_id",
            "created_at",
            "started_at",
            "completed_at",
            "updated_at",
        }

        assert required.issubset(columns)


class TestFourHorsemenTypes:
    """Tests for Four Horsemen consistency across models."""

    FOUR_HORSEMEN = ["criticism", "contempt", "defensiveness", "stonewalling"]

    def test_message_analysis_has_all_horsemen_flags(self):
        """MessageAnalysis should have flag for each horseman."""
        columns = {col._meta.name for col in MessageAnalysis._meta.columns}

        for horseman in self.FOUR_HORSEMEN:
            flag_name = f"has_{horseman}"
            assert flag_name in columns, f"Missing flag: {flag_name}"

    def test_sender_summary_has_all_horsemen_counts(self):
        """SenderSummary should have count for each horseman."""
        columns = {col._meta.name for col in SenderSummary._meta.columns}

        for horseman in self.FOUR_HORSEMEN:
            count_name = f"{horseman}_count"
            assert count_name in columns, f"Missing count: {count_name}"
