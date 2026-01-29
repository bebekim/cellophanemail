"""Analysis job model for async batch processing."""

from piccolo.table import Table
from piccolo.columns import (
    Varchar, Integer, Timestamp, ForeignKey, UUID, JSON, Text
)
from datetime import datetime
import uuid
from enum import Enum

from .user import User


class JobStatus(Enum):
    """Job processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisJob(Table, tablename="analysis_jobs"):
    """
    Async job for batch message analysis.

    Used for larger batches (>100 messages) that are processed
    asynchronously by arq workers.
    """

    # Primary identification
    id = UUID(primary_key=True, default=uuid.uuid4)
    user = ForeignKey(User, index=True, null=False)

    # Job status tracking
    status = Varchar(
        length=20,
        default=JobStatus.PENDING,
        choices=JobStatus,
        index=True
    )

    # Message counts
    total_messages = Integer(default=0)
    processed_messages = Integer(default=0)
    failed_messages = Integer(default=0)

    # Message data (stored for async processing)
    # Structure: [{"client_message_id": "...", "content": "...", ...}]
    message_ids = JSON(default=[])  # List of client_message_ids

    # Privacy settings for this job
    # Structure: {"store_body": bool, "body_ttl_hours": int}
    privacy_settings = JSON(default={
        "store_body": False,
        "body_ttl_hours": 24
    })

    # Error tracking
    error_message = Text(null=True)
    failed_message_ids = JSON(default=[])  # client_message_ids that failed

    # arq job reference
    arq_job_id = Varchar(length=100, null=True, index=True)

    # Timestamps
    created_at = Timestamp(default=datetime.now, index=True)
    started_at = Timestamp(null=True)
    completed_at = Timestamp(null=True)
    updated_at = Timestamp(default=datetime.now)

    def __str__(self):
        return f"AnalysisJob(id={self.id}, status={self.status}, {self.processed_messages}/{self.total_messages})"

    @property
    def progress_percent(self) -> float:
        """Calculate job progress percentage."""
        if self.total_messages == 0:
            return 0.0
        return (self.processed_messages / self.total_messages) * 100

    @property
    def is_complete(self) -> bool:
        """Check if job has finished (success or failure)."""
        return self.status in (JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value)
