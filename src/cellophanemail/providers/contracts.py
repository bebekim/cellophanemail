"""Contracts that all email providers must implement."""

from typing import Protocol, Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EmailMessage:
    """Common email format used across all providers."""
    message_id: str
    from_address: str
    to_addresses: List[str]
    subject: str
    text_body: Optional[str] = None
    html_body: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    received_at: Optional[datetime] = None
    
    # Internal routing information
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    shield_address: Optional[str] = None


@dataclass
class ProviderConfig:
    """Configuration for a provider."""
    enabled: bool = True
    config: Dict[str, Any] = None


class EmailProvider(Protocol):
    """Contract that all email providers must implement."""
    
    async def initialize(self, config: ProviderConfig) -> None:
        """Initialize the provider with configuration."""
        ...
    
    async def receive_message(self, raw_data: Dict[str, Any]) -> EmailMessage:
        """Parse provider-specific webhook/API data into common format."""
        ...
    
    async def send_message(self, message: EmailMessage) -> bool:
        """Send an email through this provider."""
        ...
    
    async def validate_webhook(self, request_data: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Validate that webhook request is authentic."""
        ...
    
    @property
    def name(self) -> str:
        """Provider name for logging and configuration."""
        ...
    
    @property
    def requires_oauth(self) -> bool:
        """Whether this provider needs OAuth setup."""
        ...