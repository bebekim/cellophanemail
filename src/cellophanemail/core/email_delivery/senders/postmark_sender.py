"""Postmark API-based email sender implementation."""

import httpx
from typing import Dict, Any, Optional
from ..base import BaseEmailSender


class PostmarkEmailSender(BaseEmailSender):
    """Postmark API-based email sender using REST API calls."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Postmark sender with configuration."""
        super().__init__(
            service_domain=config['SMTP_DOMAIN'],
            username=config['EMAIL_USERNAME']
        )
        
        # Postmark-specific configuration
        self.api_token = config['POSTMARK_API_TOKEN']
        self.from_email = config.get('POSTMARK_FROM_EMAIL', f'noreply@{self.service_domain}')
        self.api_url = 'https://api.postmarkapp.com/email'
    
    async def send_email(self, to_address: str, subject: str, content: str, headers: Dict[str, str]) -> bool:
        """
        Send email via Postmark API.
        
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
            # Build Postmark API payload
            payload = {
                "From": headers.get('From', self.from_email),
                "To": to_address,
                "Subject": subject,
                "TextBody": content
            }
            
            # Add optional headers if present
            if headers.get('Message-ID'):
                payload['MessageID'] = headers['Message-ID']
            if headers.get('In-Reply-To'):
                payload['InReplyTo'] = headers['In-Reply-To']
            if headers.get('References'):
                payload['References'] = headers['References']
            if headers.get('Reply-To'):
                payload['ReplyTo'] = headers['Reply-To']
            
            # Prepare request headers
            request_headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Postmark-Server-Token': self.api_token
            }
            
            # Send API request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=request_headers
                )
                
                if response.status_code == 200:
                    # Log success (basic logging for now)
                    print(f"✅ Postmark email sent successfully to {to_address}")
                    return True
                else:
                    # Log API error
                    print(f"❌ Postmark API error {response.status_code}: {response.text}")
                    return False
                    
        except Exception as e:
            # Log error but don't crash (matching SMTP error handling)
            print(f"❌ Postmark sending failed: {e}")
            return False