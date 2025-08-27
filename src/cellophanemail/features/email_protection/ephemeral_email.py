"""EphemeralEmail data class for in-memory email processing."""

import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EphemeralEmail:
    """
    Ephemeral email data class for in-memory processing.
    
    Stores email data temporarily without persistence, with automatic TTL expiration.
    Designed for privacy-focused email processing where content is never persisted.
    
    Attributes:
        message_id: Unique identifier for the email
        from_address: Email sender address
        to_addresses: List of recipient addresses
        subject: Email subject line
        text_body: Plain text content of the email
        user_email: Target user email for delivery
        ttl_seconds: Time-to-live in seconds (default: 300 = 5 minutes)
        html_body: Optional HTML content
    """
    message_id: str
    from_address: str
    to_addresses: List[str]
    subject: str
    text_body: str
    user_email: str
    ttl_seconds: int = 300  # Default 5 minutes
    html_body: Optional[str] = None
    
    # Private field for TTL calculation
    _created_at: float = field(default_factory=time.time, init=False)
    
    @property
    def is_expired(self) -> bool:
        """
        Check if the email has exceeded its TTL.
        
        Returns:
            True if the email has expired, False otherwise
        """
        current_time = time.time()
        return (current_time - self._created_at) > self.ttl_seconds
    
    def get_content_for_analysis(self) -> str:
        """
        Get combined content for LLM analysis.
        
        Combines subject and text body in a format suitable for LLM processing.
        
        Returns:
            Formatted string containing subject and body content
        """
        content_parts = []
        if self.subject:
            content_parts.append(f"Subject: {self.subject}")
        if self.text_body:
            content_parts.append(self.text_body)
        return "\n\n".join(content_parts)