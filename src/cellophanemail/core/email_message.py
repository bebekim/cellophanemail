"""Standardized email message format for pipeline processing."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4


@dataclass
class EmailMessage:
    """Standardized email message format used throughout the pipeline."""
    
    # Unique identifier
    id: UUID = field(default_factory=uuid4)
    
    # Email metadata
    from_address: str = ""
    to_addresses: List[str] = field(default_factory=list)
    cc_addresses: List[str] = field(default_factory=list)
    bcc_addresses: List[str] = field(default_factory=list)
    subject: str = ""
    message_id: str = ""
    
    # Content
    text_content: str = ""
    html_content: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    
    # Processing metadata
    received_at: datetime = field(default_factory=datetime.now)
    source_plugin: str = ""  # Which plugin received this (smtp, postmark, gmail)
    raw_message: Optional[bytes] = None  # Original raw message if available
    
    # Organization context (for multi-tenant processing)
    organization_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "from_address": self.from_address,
            "to_addresses": self.to_addresses,
            "cc_addresses": self.cc_addresses,
            "bcc_addresses": self.bcc_addresses,
            "subject": self.subject,
            "message_id": self.message_id,
            "text_content": self.text_content,
            "html_content": self.html_content,
            "headers": self.headers,
            "attachments": self.attachments,
            "received_at": self.received_at.isoformat(),
            "source_plugin": self.source_plugin,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
        }
    
    @classmethod
    def from_postmark_webhook(cls, webhook_data: Dict[str, Any]) -> "EmailMessage":
        """Create EmailMessage from Postmark webhook payload."""
        # Process Headers from Postmark format (robust against malformed data)
        headers = {}
        if "Headers" in webhook_data and webhook_data["Headers"]:
            for header in webhook_data["Headers"]:
                # Skip None, non-dict, or malformed headers
                if header and isinstance(header, dict) and "Name" in header and "Value" in header:
                    headers[header["Name"]] = header["Value"]
        
        # Process Attachments from Postmark format
        attachments = []
        if "Attachments" in webhook_data and webhook_data["Attachments"]:
            for attachment in webhook_data["Attachments"]:
                attachments.append({
                    "name": attachment.get("Name", ""),
                    "content_type": attachment.get("ContentType", ""),
                    "content_length": attachment.get("ContentLength", 0),
                    "content": attachment.get("Content", "")  # Base64 encoded
                })
        
        # Parse To field to get all recipients (handle comma-separated)
        to_field = webhook_data.get("To", "")
        to_addresses = [addr.strip() for addr in to_field.split(",") if addr.strip()] if to_field else []
        
        return cls(
            from_address=webhook_data.get("From", ""),
            to_addresses=to_addresses,
            subject=webhook_data.get("Subject", ""),
            message_id=webhook_data.get("MessageID", ""),
            text_content=webhook_data.get("TextBody") or "",  # Handle None by converting to empty string
            html_content=webhook_data.get("HtmlBody") or "",  # Handle None by converting to empty string
            headers=headers,
            attachments=attachments,
            source_plugin="postmark"
        )
    
    @classmethod
    def from_smtp_envelope(cls, envelope, message_data: bytes, source: str = "smtp") -> "EmailMessage":
        """Create EmailMessage from SMTP envelope and data."""
        import email
        from email import policy
        
        # Parse the email message
        msg = email.message_from_bytes(message_data, policy=policy.default)
        
        # Extract basic fields
        from_addr = envelope.mail_from if hasattr(envelope, 'mail_from') else str(msg.get("From", ""))
        to_addrs = envelope.rcpt_tos if hasattr(envelope, 'rcpt_tos') else []
        
        # Extract text and HTML content
        text_content = ""
        html_content = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    text_content = part.get_content()
                elif content_type == "text/html":
                    html_content = part.get_content()
        else:
            content_type = msg.get_content_type()
            if content_type == "text/plain":
                text_content = msg.get_content()
            elif content_type == "text/html":
                html_content = msg.get_content()
        
        # Extract headers
        headers = {key: value for key, value in msg.items()}
        
        return cls(
            from_address=from_addr,
            to_addresses=to_addrs,
            subject=str(msg.get("Subject", "")),
            message_id=str(msg.get("Message-ID", "")),
            text_content=text_content,
            html_content=html_content,
            headers=headers,
            source_plugin=source,
            raw_message=message_data,
        )