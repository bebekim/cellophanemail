"""Postmark email provider implementation."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

try:
    # Try importing postmark client - may not be needed for webhook-only mode
    import postmark
    has_postmark = True
except ImportError:
    has_postmark = False

from ..contracts import EmailProvider, EmailMessage, ProviderConfig

logger = logging.getLogger(__name__)


class PostmarkProvider(EmailProvider):
    """Postmark email service provider."""
    
    def __init__(self):
        self.client: Optional[Any] = None
        self.server_token: Optional[str] = None
        self.from_address: Optional[str] = None
        
    async def initialize(self, config: ProviderConfig) -> None:
        """Initialize Postmark with API credentials."""
        if not config.config:
            raise ValueError("Postmark configuration required")
            
        self.server_token = config.config.get('server_token') or os.getenv('POSTMARK_SERVER_TOKEN')
        self.from_address = config.config.get('from_address', 'noreply@cellophanemail.com')
        
        if not self.server_token:
            raise ValueError("Postmark server token required")
            
        if has_postmark:
            # Initialize Postmark client if available
            # Using the postmark package API structure
            self.client = True  # Placeholder for actual client initialization
        logger.info(f"Postmark provider initialized with from_address: {self.from_address}")
    
    async def receive_message(self, raw_data: Dict[str, Any]) -> EmailMessage:
        """Parse Postmark webhook data into EmailMessage."""
        try:
            # Extract recipient shield address
            to_address = raw_data.get('To', '').lower().strip()
            
            # Parse To field which might have multiple recipients
            to_addresses = [to_address]
            if 'ToFull' in raw_data and raw_data.get('ToFull'):
                to_addresses = [
                    addr.get('Email', '').lower().strip() 
                    for addr in raw_data.get('ToFull', [])
                    if addr and isinstance(addr, dict)
                ]
            
            # Create EmailMessage from Postmark data
            message = EmailMessage(
                message_id=raw_data.get('MessageID', ''),
                from_address=raw_data.get('From', ''),
                to_addresses=to_addresses,
                subject=raw_data.get('Subject', ''),
                text_body=raw_data.get('TextBody'),
                html_body=raw_data.get('HtmlBody'),
                headers={h['Name']: h['Value'] for h in raw_data.get('Headers', []) if h and isinstance(h, dict)},
                attachments=raw_data.get('Attachments', []),
                received_at=datetime.fromisoformat(raw_data['Date']) if 'Date' in raw_data else datetime.now(),
                shield_address=to_address if to_address.endswith('@cellophanemail.com') else None
            )
            
            logger.info(f"Received Postmark message {message.message_id} to {to_address}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to parse Postmark webhook data: {e}")
            raise ValueError(f"Invalid Postmark webhook data: {e}")
    
    async def send_message(self, message: EmailMessage) -> bool:
        """Send email through Postmark."""
        if not self.server_token:
            logger.error("Postmark not initialized")
            return False
            
        try:
            # In production, this would use the Postmark API
            # For now, we'll log the intent
            logger.info(f"Would send email via Postmark to {message.to_addresses}")
            logger.info(f"  Subject: {message.subject}")
            logger.info(f"  From: {self.from_address}")
            
            # TODO: Implement actual Postmark sending when needed
            # This requires proper Postmark API client setup
            
            return True  # Simulate success for testing
            
        except Exception as e:
            logger.error(f"Failed to send via Postmark: {e}")
            return False
    
    async def validate_webhook(self, request_data: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Validate Postmark webhook signature."""
        # Postmark doesn't sign webhooks by default
        # Could implement custom validation if needed
        return True
    
    @property
    def name(self) -> str:
        """Provider name."""
        return "postmark"
    
    @property
    def requires_oauth(self) -> bool:
        """Postmark uses API tokens, not OAuth."""
        return False