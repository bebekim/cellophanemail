"""Postmark email provider implementation."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from email.utils import parsedate_to_datetime
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
        self.dry_run: bool = False  # Enable to prevent actual API calls
        self.sent_count: int = 0  # Track sends in dry-run mode
        
    async def initialize(self, config: ProviderConfig) -> None:
        """Initialize Postmark with API credentials."""
        if not config.config:
            raise ValueError("Postmark configuration required")
            
        self.server_token = config.config.get('server_token') or os.getenv('POSTMARK_SERVER_TOKEN')
        self.from_address = config.config.get('from_address', 'noreply@cellophanemail.com')
        
        # Check for dry-run mode from config or environment
        self.dry_run = (
            config.config.get('dry_run', False) or 
            os.getenv('POSTMARK_DRY_RUN', '').lower() in ['true', '1', 'yes'] or
            os.getenv('CELLOPHANEMAIL_TEST_MODE', '').lower() in ['true', '1', 'yes']
        )
        
        if self.dry_run:
            logger.warning("🚫 Postmark running in DRY-RUN mode - no emails will be sent!")
            logger.info("Set POSTMARK_DRY_RUN=false to send real emails")
        elif not self.server_token:
            logger.warning("No Postmark server token - enabling dry-run mode automatically")
            self.dry_run = True
            
        if has_postmark and not self.dry_run:
            # Initialize Postmark client if available and not in dry-run
            # Using the postmark package API structure
            self.client = True  # Placeholder for actual client initialization
            
        mode = "DRY-RUN" if self.dry_run else "LIVE"
        logger.info(f"Postmark provider initialized [{mode}] with from_address: {self.from_address}")
    
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
            
            # Parse date - Postmark uses RFC 2822 format
            received_at = datetime.now()
            if 'Date' in raw_data and raw_data['Date']:
                try:
                    received_at = parsedate_to_datetime(raw_data['Date'])
                except Exception as e:
                    logger.warning(f"Failed to parse date '{raw_data['Date']}': {e}, using current time")
            
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
                received_at=received_at,
                shield_address=to_address if to_address.endswith('@cellophanemail.com') else None
            )
            
            logger.info(f"Received Postmark message {message.message_id} to {to_address}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to parse Postmark webhook data: {e}")
            raise ValueError(f"Invalid Postmark webhook data: {e}")
    
    async def send_message(self, message: EmailMessage) -> bool:
        """Send email through Postmark."""
        if self.dry_run:
            # Dry-run mode - just log what would be sent
            self.sent_count += 1
            logger.info(f"🔵 [DRY-RUN] Postmark send #{self.sent_count}")
            logger.info(f"  To: {message.to_addresses}")
            logger.info(f"  Subject: {message.subject}")
            logger.info(f"  From: {self.from_address or message.from_address}")
            logger.info(f"  Size: {len(message.text_body or '')} chars (text), {len(message.html_body or '')} chars (html)")
            
            # Store in a file for debugging if needed
            if os.getenv('POSTMARK_LOG_DRY_RUN'):
                import json
                log_file = f"postmark_dry_run_{datetime.now().strftime('%Y%m%d')}.jsonl"
                with open(log_file, 'a') as f:
                    f.write(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'to': message.to_addresses,
                        'subject': message.subject,
                        'from': self.from_address,
                        'message_id': message.message_id,
                        'dry_run': True
                    }) + '\n')
            
            return True  # Always succeed in dry-run
            
        if not self.server_token:
            logger.error("Postmark not initialized and not in dry-run mode")
            return False
            
        try:
            # TODO: Implement actual Postmark API call here
            # For now, still mocked but shows it would make real call
            logger.warning("⚠️ Postmark real sending not yet implemented - simulating success")
            logger.info(f"Would send REAL email via Postmark to {message.to_addresses}")
            logger.info(f"  Subject: {message.subject}")
            logger.info(f"  From: {self.from_address}")
            
            return True  # Simulate success for now
            
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