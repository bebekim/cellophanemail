"""Email delivery service using Postmark API."""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

import httpx
from ..core.email_message import EmailMessage
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class DeliveryResult:
    """Result of email delivery attempt."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    delivery_time_ms: Optional[float] = None


class PostmarkDeliveryService:
    """Email delivery service using Postmark API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://api.postmarkapp.com"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": self.settings.postmark_api_token
        }
    
    async def send_email(self, email_message: EmailMessage) -> DeliveryResult:
        """Send email via Postmark API."""
        try:
            if not self.settings.postmark_api_token:
                logger.error("Postmark API token not configured")
                return DeliveryResult(
                    success=False,
                    error="Postmark API token not configured"
                )
            
            # Prepare Postmark payload
            payload = self._prepare_postmark_payload(email_message)
            
            logger.info(f"Sending email {email_message.id} via Postmark to {email_message.to_addresses}")
            logger.debug(f"Postmark payload: From={payload.get('From')}, To={payload.get('To')}, Subject={payload.get('Subject')}")
            
            # Send via Postmark API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/email",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Email {email_message.id} sent successfully via Postmark: {result.get('MessageID')}")
                    return DeliveryResult(
                        success=True,
                        message_id=result.get("MessageID"),
                        delivery_time_ms=result.get("SubmittedAt")
                    )
                else:
                    error_msg = f"Postmark API error: {response.status_code} - {response.text}"
                    logger.error(f"Failed to send email {email_message.id}: {error_msg}")
                    return DeliveryResult(
                        success=False,
                        error=error_msg
                    )
                    
        except Exception as e:
            logger.error(f"Exception sending email {email_message.id} via Postmark: {e}", exc_info=True)
            return DeliveryResult(
                success=False,
                error=str(e)
            )
    
    def _prepare_postmark_payload(self, email_message: EmailMessage) -> Dict[str, Any]:
        """Prepare Postmark API payload from EmailMessage."""
        
        # Use configured from address or fallback to domain
        from_address = self.settings.postmark_from_email
        if not from_address:
            # If no from address configured, use noreply@cellophanemail.com
            from_address = "noreply@cellophanemail.com"
        
        # Prepare basic payload
        payload = {
            "From": from_address,
            "To": ", ".join(email_message.to_addresses),  # Postmark expects comma-separated string
            "Subject": email_message.subject,
            "MessageID": email_message.message_id
        }
        
        # Add text content if available
        if email_message.text_content:
            payload["TextBody"] = email_message.text_content
        
        # Add HTML content if available
        if email_message.html_content:
            payload["HtmlBody"] = email_message.html_content
        
        # Add reply-to if needed (use original sender)
        if email_message.from_address:
            payload["ReplyTo"] = email_message.from_address
            
        # Add headers to preserve original context
        payload["Headers"] = [
            {"Name": "X-CellophoneMail-Original-From", "Value": email_message.from_address},
            {"Name": "X-CellophoneMail-Forwarded", "Value": "true"},
            {"Name": "X-CellophoneMail-Message-ID", "Value": str(email_message.id)}
        ]
        
        # Add custom tag for tracking
        payload["Tag"] = "cellophanemail-forwarded"
        
        return payload


class EmailDeliveryService:
    """Main email delivery service that routes to appropriate provider."""
    
    def __init__(self):
        self.settings = get_settings()
        self.postmark = PostmarkDeliveryService()
    
    async def send_email(self, email_message: EmailMessage) -> DeliveryResult:
        """Send email using configured delivery method."""
        
        delivery_method = self.settings.email_delivery_method.lower()
        
        if delivery_method == "postmark":
            return await self.postmark.send_email(email_message)
        elif delivery_method == "smtp":
            # TODO: Implement SMTP delivery for local testing
            logger.warning("SMTP delivery not yet implemented, using Postmark")
            return await self.postmark.send_email(email_message)
        else:
            logger.error(f"Unknown email delivery method: {delivery_method}")
            return DeliveryResult(
                success=False,
                error=f"Unknown delivery method: {delivery_method}"
            )
    
    async def send_multiple_emails(self, email_messages: List[EmailMessage]) -> List[DeliveryResult]:
        """Send multiple emails concurrently."""
        import asyncio
        
        # Send all emails concurrently
        tasks = [self.send_email(msg) for msg in email_messages]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to DeliveryResult
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(DeliveryResult(
                    success=False,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results