"""Sender summary model for aggregated Four Horsemen statistics."""

from piccolo.table import Table
from piccolo.columns import (
    Varchar, Integer, Timestamp, ForeignKey, UUID, JSON
)
from datetime import datetime
import uuid

from .user import User
from .message_analysis import MessageChannel


class SenderSummary(Table, tablename="sender_summaries"):
    """
    Pre-computed aggregates for sender-level Four Horsemen statistics.

    Incrementally updated when new messages are analyzed.
    Enables fast sender-level queries without scanning all messages.
    """

    # Primary identification
    id = UUID(primary_key=True, default=uuid.uuid4)
    user = ForeignKey(User, index=True, null=False)
    sender_identifier = Varchar(length=500, index=True, null=False)
    channel = Varchar(
        length=20,
        default=MessageChannel.SMS,
        choices=MessageChannel
    )

    # Message counts
    total_messages = Integer(default=0)
    messages_with_horsemen = Integer(default=0)
    clean_messages = Integer(default=0)  # No horsemen detected

    # Four Horsemen frequency (primary metrics)
    criticism_count = Integer(default=0)
    contempt_count = Integer(default=0)
    defensiveness_count = Integer(default=0)
    stonewalling_count = Integer(default=0)

    # For client convenience - denormalized counts
    horsemen_counts = JSON(default={
        "criticism": 0,
        "contempt": 0,
        "defensiveness": 0,
        "stonewalling": 0
    })

    # Sender metadata (optional - can be set by client)
    sender_label = Varchar(length=255, null=True)  # Human-readable name

    # Timestamps
    first_message_at = Timestamp(null=True)
    last_message_at = Timestamp(null=True)
    last_horseman_at = Timestamp(null=True)  # When horsemen last detected
    created_at = Timestamp(default=datetime.now)
    updated_at = Timestamp(default=datetime.now)

    def __str__(self):
        return f"SenderSummary(sender={self.sender_identifier}, total={self.total_messages})"

    @classmethod
    def get_unique_constraint(cls):
        """User + sender_identifier + channel should be unique."""
        return ["user", "sender_identifier", "channel"]
