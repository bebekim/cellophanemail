"""SMTP email provider implementation."""

import logging
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime
from email.utils import parsedate_to_datetime
import os

from ..contracts import EmailProvider, EmailMessage, ProviderConfig

logger = logging.getLogger(__name__)


class SMTPProvider(EmailProvider):
    """SMTP provider for sending and receiving emails."""
    
    def __init__(self):
        # SMTP sending configuration
        self.smtp_host: Optional[str] = None
        self.smtp_port: Optional[int] = None
        self.smtp_username: Optional[str] = None
        self.smtp_password: Optional[str] = None
        self.smtp_use_tls: bool = True
        self.from_address: Optional[str] = None
        
        # SMTP server receiving configuration
        self.server_host: str = "0.0.0.0"
        self.server_port: int = 25
        self.server_enabled: bool = False
        
    async def initialize(self, config: ProviderConfig) -> None:
        """Initialize SMTP provider with configuration."""
        if not config.config:
            raise ValueError("SMTP configuration required")
        
        # SMTP sending configuration
        self.smtp_host = config.config.get('smtp_host') or os.getenv('SMTP_HOST')
        self.smtp_port = config.config.get('smtp_port', 587)
        self.smtp_username = config.config.get('smtp_username') or os.getenv('SMTP_USERNAME')
        self.smtp_password = config.config.get('smtp_password') or os.getenv('SMTP_PASSWORD')
        self.smtp_use_tls = config.config.get('smtp_use_tls', True)
        self.from_address = config.config.get('from_address', 'noreply@cellophanemail.com')
        
        # SMTP server configuration
        self.server_host = config.config.get('server_host', '0.0.0.0')
        self.server_port = config.config.get('server_port', 25)
        self.server_enabled = config.config.get('server_enabled', False)
        
        if not self.smtp_host and self.server_enabled:
            logger.warning("SMTP host not configured - sending will not work")
        
        logger.info(f"SMTP provider initialized - sending: {'enabled' if self.smtp_host else 'disabled'}, "
                   f"server: {'enabled' if self.server_enabled else 'disabled'}")
    
    async def receive_message(self, raw_data: Dict[str, Any]) -> EmailMessage:
        """Parse SMTP message data into EmailMessage."""
        try:
            # SMTP raw_data should contain the email envelope and message
            if 'envelope' in raw_data and 'message_data' in raw_data:
                return self._parse_smtp_envelope(raw_data['envelope'], raw_data['message_data'])
            elif 'raw_message' in raw_data:
                # Direct raw email message
                return self._parse_raw_email(raw_data['raw_message'])
            else:
                # Assume raw_data is the message fields
                return self._parse_direct_fields(raw_data)
                
        except Exception as e:
            logger.error(f"Failed to parse SMTP message: {e}")
            raise ValueError(f"Invalid SMTP message data: {e}")
    
    async def send_message(self, message: EmailMessage) -> bool:
        """Send email through SMTP."""
        if not self.smtp_host:
            logger.error("SMTP host not configured")
            return False
        
        try:
            # Create MIME message
            mime_msg = self._create_mime_message(message)
            
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                # Send the message
                server.send_message(mime_msg)
            
            logger.info(f"Sent email via SMTP to {message.to_addresses}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send via SMTP: {e}")
            return False
    
    async def validate_webhook(self, request_data: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """SMTP doesn't use webhooks - always return True for direct connections."""
        # SMTP receives emails directly, not via webhooks
        return True
    
    @property
    def name(self) -> str:
        """Provider name for logging and configuration."""
        return "smtp"
    
    @property
    def requires_oauth(self) -> bool:
        """SMTP uses username/password authentication."""
        return False
    
    def _parse_smtp_envelope(self, envelope: Any, message_data: bytes) -> EmailMessage:
        """Parse SMTP envelope and message data."""
        # Parse the email message
        msg = email.message_from_bytes(message_data)
        
        # Extract recipient from envelope (more reliable than headers)
        to_addresses = getattr(envelope, 'rcpt_tos', [])
        from_address = getattr(envelope, 'mail_from', '') or str(msg.get('From', ''))
        
        # Extract content
        text_body, html_body = self._extract_message_content(msg)
        
        # Extract headers
        headers = {key: value for key, value in msg.items()}
        
        # Parse date
        date_str = msg.get('Date', '')
        received_at = self._parse_email_date(date_str)
        
        # Find shield address
        shield_address = self._find_shield_address(to_addresses)
        
        return EmailMessage(
            message_id=str(msg.get('Message-ID', '')),
            from_address=from_address,
            to_addresses=to_addresses,
            subject=str(msg.get('Subject', '')),
            text_body=text_body,
            html_body=html_body,
            headers=headers,
            attachments=self._extract_attachments(msg),
            received_at=received_at,
            shield_address=shield_address
        )
    
    def _parse_raw_email(self, raw_message: bytes) -> EmailMessage:
        """Parse raw email message bytes."""
        msg = email.message_from_bytes(raw_message)
        
        # Extract addresses from headers
        to_addresses = self._parse_address_header(msg.get('To', ''))
        cc_addresses = self._parse_address_header(msg.get('Cc', ''))
        from_address = str(msg.get('From', ''))
        
        # Extract content
        text_body, html_body = self._extract_message_content(msg)
        
        # Extract headers
        headers = {key: value for key, value in msg.items()}
        
        # Parse date
        date_str = msg.get('Date', '')
        received_at = self._parse_email_date(date_str)
        
        # Find shield address
        all_recipients = to_addresses + cc_addresses
        shield_address = self._find_shield_address(all_recipients)
        
        return EmailMessage(
            message_id=str(msg.get('Message-ID', '')),
            from_address=from_address,
            to_addresses=to_addresses,
            subject=str(msg.get('Subject', '')),
            text_body=text_body,
            html_body=html_body,
            headers=headers,
            attachments=self._extract_attachments(msg),
            received_at=received_at,
            shield_address=shield_address
        )
    
    def _parse_direct_fields(self, raw_data: Dict[str, Any]) -> EmailMessage:
        """Parse message from direct field data."""
        to_addresses = raw_data.get('to_addresses', [])
        if isinstance(to_addresses, str):
            to_addresses = [to_addresses]
        
        shield_address = self._find_shield_address(to_addresses)
        
        # Parse date if provided
        received_at = datetime.now()
        if 'date' in raw_data:
            received_at = self._parse_email_date(raw_data['date'])
        
        return EmailMessage(
            message_id=raw_data.get('message_id', ''),
            from_address=raw_data.get('from_address', ''),
            to_addresses=to_addresses,
            subject=raw_data.get('subject', ''),
            text_body=raw_data.get('text_body'),
            html_body=raw_data.get('html_body'),
            headers=raw_data.get('headers', {}),
            attachments=raw_data.get('attachments', []),
            received_at=received_at,
            shield_address=shield_address
        )
    
    def _extract_message_content(self, msg: email.message.Message) -> tuple[Optional[str], Optional[str]]:
        """Extract text and HTML content from email message."""
        text_body = None
        html_body = None
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain" and not text_body:
                    text_body = part.get_payload(decode=True)
                    if isinstance(text_body, bytes):
                        text_body = text_body.decode('utf-8', errors='ignore')
                elif content_type == "text/html" and not html_body:
                    html_body = part.get_payload(decode=True)
                    if isinstance(html_body, bytes):
                        html_body = html_body.decode('utf-8', errors='ignore')
        else:
            # Non-multipart message
            content_type = msg.get_content_type()
            payload = msg.get_payload(decode=True)
            if isinstance(payload, bytes):
                payload = payload.decode('utf-8', errors='ignore')
            
            if content_type == "text/plain":
                text_body = payload
            elif content_type == "text/html":
                html_body = payload
            else:
                text_body = payload  # Default to text
        
        return text_body, html_body
    
    def _extract_attachments(self, msg: email.message.Message) -> List[Dict[str, Any]]:
        """Extract attachment information from email message."""
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            'name': filename,
                            'content_type': part.get_content_type(),
                            'size': len(part.get_payload(decode=True) or b'')
                        })
        
        return attachments
    
    def _parse_address_header(self, header_value: str) -> List[str]:
        """Parse email address header into list of addresses."""
        if not header_value:
            return []
        
        # Simple parsing - in production, use email.utils.getaddresses
        addresses = []
        for addr in header_value.split(','):
            addr = addr.strip()
            if addr:
                # Extract email from "Name <email@domain.com>" format
                if '<' in addr and '>' in addr:
                    addr = addr[addr.find('<')+1:addr.find('>')]
                addresses.append(addr)
        
        return addresses
    
    def _find_shield_address(self, addresses: List[str]) -> Optional[str]:
        """Find shield address from list of email addresses."""
        for addr in addresses:
            if addr.endswith('@cellophanemail.com'):
                return addr.lower().strip()
        return None
    
    def _parse_email_date(self, date_str: str) -> datetime:
        """Parse email date header."""
        if not date_str:
            return datetime.now()
        
        try:
            return parsedate_to_datetime(date_str)
        except Exception as e:
            logger.warning(f"Failed to parse email date '{date_str}': {e}")
            return datetime.now()
    
    def _create_mime_message(self, message: EmailMessage) -> MIMEMultipart:
        """Create MIME message for sending."""
        # Create multipart message
        mime_msg = MIMEMultipart('alternative')
        
        # Set headers
        mime_msg['From'] = self.from_address or message.from_address
        mime_msg['To'] = ', '.join(message.to_addresses)
        mime_msg['Subject'] = message.subject
        mime_msg['Message-ID'] = message.message_id or email.utils.make_msgid()
        
        # Add additional headers
        if message.headers:
            for key, value in message.headers.items():
                if key.lower() not in ['from', 'to', 'subject', 'message-id']:
                    mime_msg[key] = value
        
        # Add text content
        if message.text_body:
            text_part = MIMEText(message.text_body, 'plain', 'utf-8')
            mime_msg.attach(text_part)
        
        # Add HTML content
        if message.html_body:
            html_part = MIMEText(message.html_body, 'html', 'utf-8')
            mime_msg.attach(html_part)
        
        return mime_msg
    
    # Server configuration helpers
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get SMTP server configuration for running embedded server."""
        return {
            'host': self.server_host,
            'port': self.server_port,
            'enabled': self.server_enabled
        }
    
    def is_server_enabled(self) -> bool:
        """Check if SMTP server should be started."""
        return self.server_enabled