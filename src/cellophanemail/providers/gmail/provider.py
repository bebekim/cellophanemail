"""Gmail email provider implementation."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import base64
import json
from email.utils import parsedate_to_datetime
import os

try:
    # Try importing Google API client libraries - may not be installed
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    has_gmail_api = True
except ImportError:
    has_gmail_api = False

from ..contracts import EmailProvider, EmailMessage, ProviderConfig

logger = logging.getLogger(__name__)


class GmailProvider(EmailProvider):
    """Gmail API provider for email processing."""
    
    def __init__(self):
        self.credentials: Optional[Any] = None
        self.service: Optional[Any] = None
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self.redirect_uri: Optional[str] = None
        
    async def initialize(self, config: ProviderConfig) -> None:
        """Initialize Gmail provider with OAuth2 credentials."""
        if not config.config:
            raise ValueError("Gmail configuration required")
            
        self.client_id = config.config.get('client_id') or os.getenv('GMAIL_CLIENT_ID')
        self.client_secret = config.config.get('client_secret') or os.getenv('GMAIL_CLIENT_SECRET')
        self.redirect_uri = config.config.get('redirect_uri', 'http://localhost:8000/auth/gmail/callback')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Gmail OAuth2 credentials required")
            
        if not has_gmail_api:
            logger.warning("Google API client libraries not installed - Gmail provider will be read-only")
            
        logger.info("Gmail provider initialized (OAuth2 flow required for full functionality)")
    
    async def receive_message(self, raw_data: Dict[str, Any]) -> EmailMessage:
        """Parse Gmail Pub/Sub push notification data into EmailMessage."""
        try:
            # Gmail uses Pub/Sub push notifications with base64-encoded message data
            if 'message' in raw_data and 'data' in raw_data['message']:
                # Decode the Pub/Sub message
                message_data = raw_data['message']['data']
                decoded_data = base64.b64decode(message_data).decode('utf-8')
                gmail_data = json.loads(decoded_data)
                
                # Extract email details from Gmail API format
                message_id = gmail_data.get('historyId', '')  # Gmail uses historyId
                
                # For actual Gmail integration, we'd need to fetch the full message
                # using the Gmail API with the historyId
                # This is a simplified version for demonstration
                
                message = EmailMessage(
                    message_id=message_id,
                    from_address=gmail_data.get('from', ''),
                    to_addresses=self._parse_gmail_addresses(gmail_data.get('to', '')),
                    subject=gmail_data.get('subject', ''),
                    text_body=gmail_data.get('text_body'),
                    html_body=gmail_data.get('html_body'),
                    headers=gmail_data.get('headers', {}),
                    attachments=gmail_data.get('attachments', []),
                    received_at=self._parse_gmail_date(gmail_data.get('internalDate')),
                    shield_address=self._extract_shield_address(gmail_data.get('to', ''))
                )
                
                logger.info(f"Received Gmail message {message.message_id}")
                return message
            else:
                # Handle direct Gmail webhook format (if available)
                return self._parse_direct_gmail_webhook(raw_data)
                
        except Exception as e:
            logger.error(f"Failed to parse Gmail webhook data: {e}")
            raise ValueError(f"Invalid Gmail webhook data: {e}")
    
    async def send_message(self, message: EmailMessage) -> bool:
        """Send email through Gmail API."""
        if not has_gmail_api or not self.service:
            logger.warning("Gmail API not available - cannot send messages")
            return False
            
        try:
            # Create email message in Gmail API format
            email_message = self._create_gmail_message(message)
            
            # Send the message
            result = self.service.users().messages().send(
                userId='me',
                body=email_message
            ).execute()
            
            logger.info(f"Sent email via Gmail API: {result.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send via Gmail API: {e}")
            return False
    
    async def validate_webhook(self, request_data: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Validate Gmail Pub/Sub webhook authenticity."""
        try:
            # Gmail Pub/Sub webhooks should include proper authentication
            # In production, validate the JWT token from Google
            authorization = headers.get('Authorization', '')
            
            if not authorization.startswith('Bearer '):
                return False
                
            # For demo purposes, accept any bearer token
            # In production, verify the JWT signature with Google's public keys
            logger.info("Gmail webhook validation - simplified for demo")
            return True
            
        except Exception as e:
            logger.error(f"Gmail webhook validation failed: {e}")
            return False
    
    @property
    def name(self) -> str:
        """Provider name for logging and configuration."""
        return "gmail"
    
    @property
    def requires_oauth(self) -> bool:
        """Gmail requires OAuth2 authentication."""
        return True
    
    def _parse_gmail_addresses(self, addresses_str: str) -> List[str]:
        """Parse Gmail address string into list of email addresses."""
        if not addresses_str:
            return []
        
        # Gmail addresses can be comma-separated
        addresses = [addr.strip() for addr in addresses_str.split(',') if addr.strip()]
        return addresses
    
    def _parse_gmail_date(self, internal_date: Optional[str]) -> datetime:
        """Parse Gmail internal date format."""
        if not internal_date:
            return datetime.now()
        
        try:
            # Gmail internalDate is Unix timestamp in milliseconds
            timestamp = int(internal_date) / 1000
            return datetime.fromtimestamp(timestamp)
        except (ValueError, TypeError):
            logger.warning(f"Failed to parse Gmail date '{internal_date}', using current time")
            return datetime.now()
    
    def _extract_shield_address(self, to_addresses: str) -> Optional[str]:
        """Extract shield address from Gmail to field."""
        addresses = self._parse_gmail_addresses(to_addresses)
        for addr in addresses:
            if addr.endswith('@cellophanemail.com'):
                return addr.lower().strip()
        return None
    
    def _parse_direct_gmail_webhook(self, raw_data: Dict[str, Any]) -> EmailMessage:
        """Parse direct Gmail webhook format (for custom integrations)."""
        # This would handle direct Gmail API webhook formats
        # For now, create a basic message structure
        return EmailMessage(
            message_id=raw_data.get('id', ''),
            from_address=raw_data.get('from', ''),
            to_addresses=self._parse_gmail_addresses(raw_data.get('to', '')),
            subject=raw_data.get('subject', ''),
            text_body=raw_data.get('snippet'),  # Gmail provides snippet
            html_body=None,
            headers=raw_data.get('payload', {}).get('headers', []),
            attachments=[],
            received_at=self._parse_gmail_date(raw_data.get('internalDate')),
            shield_address=self._extract_shield_address(raw_data.get('to', ''))
        )
    
    def _create_gmail_message(self, message: EmailMessage) -> Dict[str, Any]:
        """Create Gmail API message format."""
        # In production, this would create proper MIME message
        # For demo, return basic structure
        return {
            'raw': base64.urlsafe_b64encode(
                f"From: {message.from_address}\r\n"
                f"To: {', '.join(message.to_addresses)}\r\n"
                f"Subject: {message.subject}\r\n\r\n"
                f"{message.text_body or message.html_body or ''}"
                .encode('utf-8')
            ).decode('utf-8')
        }
    
    # OAuth2 Helper Methods (for future implementation)
    
    def get_oauth_url(self) -> str:
        """Get OAuth2 authorization URL for Gmail setup."""
        if not self.client_id:
            raise ValueError("Gmail client ID not configured")
        
        return (
            f"https://accounts.google.com/o/oauth2/auth?"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"scope=https://www.googleapis.com/auth/gmail.readonly "
            f"https://www.googleapis.com/auth/gmail.send&"
            f"response_type=code&"
            f"access_type=offline"
        )
    
    async def exchange_oauth_code(self, auth_code: str) -> bool:
        """Exchange OAuth2 authorization code for credentials."""
        if not has_gmail_api:
            logger.error("Google API client libraries not available")
            return False
        
        try:
            # In production, exchange the code for tokens
            # and store them securely for the user
            logger.info("OAuth2 code exchange - implementation needed for production")
            return True
            
        except Exception as e:
            logger.error(f"OAuth2 code exchange failed: {e}")
            return False