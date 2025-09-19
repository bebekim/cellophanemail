"""Email processing log model for CellophoneMail."""

from piccolo.table import Table
from piccolo.columns import (
    Varchar, Text, Boolean, Timestamp, ForeignKey, UUID, JSON, Decimal
)
from datetime import datetime
import uuid
from enum import Enum
from .organization import Organization
from .user import User


class EmailStatus(Enum):
    PENDING = "pending"
    ANALYZED = "analyzed"
    BLOCKED = "blocked"
    FORWARDED = "forwarded"
    FAILED = "failed"


class DeliveryStatus(Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    REJECTED = "rejected"


class EmailLog(Table, tablename="email_logs"):
    """Log of all processed emails with Four Horsemen analysis."""
    
    # Primary identification
    id = UUID(primary_key=True, default=uuid.uuid4)
    organization = ForeignKey(Organization, null=False, index=True)
    user = ForeignKey(User, null=True, index=True)
    
    # Email metadata (no content stored)
    from_address = Varchar(length=500, null=False)
    to_addresses = JSON(null=False)  # List of recipient emails
    message_id = Varchar(length=500, null=True, index=True)  # External ID only
    
    # Processing results
    status = Varchar(
        length=50,
        default=EmailStatus.PENDING,
        choices=EmailStatus
    )
    
    # Four Horsemen analysis (metadata only, no content)
    toxicity_score = Decimal(digits=(5, 2), null=True)  # 0.00 to 100.00
    horsemen_detected = JSON(default=[])  # List of detected patterns
    blocked = Boolean(default=False)  # Whether email was blocked
    
    # PRIVACY: No email content is ever stored in the database
    # All processing happens in-memory with 5-minute TTL
    
    # Processing metadata
    processing_time_ms = Decimal(digits=(10, 2), null=True)
    ai_model_used = Varchar(length=100, null=True)
    plugin_used = Varchar(length=50, null=True)  # smtp, postmark, gmail_api
    
    # Timestamps
    received_at = Timestamp(null=False, index=True)
    processed_at = Timestamp(null=True)
    created_at = Timestamp(default=datetime.now)
    
    # Delivery tracking
    forwarded_to = JSON(null=True)  # Final delivery addresses
    delivery_status = Varchar(
        length=50,
        default=DeliveryStatus.PENDING,
        choices=DeliveryStatus
    )
    
    def __str__(self):
        return f"EmailLog(from={self.from_address}, status={self.status})"