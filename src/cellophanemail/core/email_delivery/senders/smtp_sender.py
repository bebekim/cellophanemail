"""SMTP-based email sender implementation."""

import aiosmtplib
from email.mime.text import MIMEText
from typing import Dict, Any
from ..base import BaseEmailSender


class SMTPEmailSender(BaseEmailSender):
    """SMTP-based email sender (refactored from OutboundEmailService)."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize SMTP sender with configuration."""
        super().__init__(
            service_domain=config['SMTP_DOMAIN'],
            username=config['EMAIL_USERNAME']
        )
        
        # SMTP-specific configuration
        self.smtp_server = config['OUTBOUND_SMTP_HOST']
        self.smtp_port = config['OUTBOUND_SMTP_PORT']
        self.use_tls = config['OUTBOUND_SMTP_USE_TLS']
        self.password = config.get('EMAIL_PASSWORD')
    
    async def send_email(self, to_address: str, subject: str, content: str, headers: Dict[str, str]) -> bool:
        """
        Send email via SMTP.
        
        This is the only unique implementation - all other email logic is shared in BaseEmailSender.
        
        Args:
            to_address: Recipient email address
            subject: Email subject
            content: Email body content
            headers: Dict of email headers to include
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create email message
            msg = MIMEText(content)
            msg['To'] = to_address
            msg['Subject'] = subject
            
            # Add all headers
            for header_name, header_value in headers.items():
                msg[header_name] = header_value
            
            # Send via SMTP using aiosmtplib (your original working code)
            result = await aiosmtplib.send(
                msg,
                hostname=self.smtp_server,
                port=self.smtp_port,
                username=self.username,
                password=self.password
            )
            
            # Log success (basic logging for now)
            print(f"✅ SMTP email sent successfully to {to_address}")
            return True
            
        except Exception as e:
            # Log error but don't crash (matching your original error handling)
            print(f"❌ SMTP sending failed: {e}")
            return False