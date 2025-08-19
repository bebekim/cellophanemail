"""Gmail webhook handler following the provider/feature architecture."""

import logging
from typing import Dict, Any
from datetime import datetime

from litestar import post, Request, Response
from litestar.controller import Controller
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

from .provider import GmailProvider
from ...features.email_protection import EmailProtectionProcessor
from ...features.shield_addresses import ShieldAddressManager

logger = logging.getLogger(__name__)


class GmailWebhookHandler(Controller):
    """Handle Gmail Pub/Sub push notifications and API webhooks."""
    
    path = "/providers/gmail"
    
    def __init__(self, owner=None):
        super().__init__(owner)
        self.provider = GmailProvider()
        self.protection = EmailProtectionProcessor()
        self.shield_manager = ShieldAddressManager()
    
    @post("/push")
    async def handle_pubsub_push(self, request: Request, data: Dict[str, Any]) -> Response:
        """
        Handle Gmail Pub/Sub push notifications.
        
        Gmail uses Google Cloud Pub/Sub to deliver real-time notifications
        about mailbox changes. This endpoint processes those notifications.
        """
        try:
            logger.info("Received Gmail Pub/Sub push notification")
            
            # Validate the webhook
            is_valid = await self.provider.validate_webhook(data, dict(request.headers))
            if not is_valid:
                logger.warning("Invalid Gmail Pub/Sub webhook")
                return Response(
                    content={"error": "Invalid webhook signature"},
                    status_code=HTTP_401_UNAUTHORIZED
                )
            
            # Parse the Gmail message
            email_message = await self.provider.receive_message(data)
            
            if not email_message.shield_address:
                logger.info(f"Gmail message {email_message.message_id} not for shield address, ignoring")
                return Response(
                    content={"status": "ignored", "reason": "not_shield_address"},
                    status_code=HTTP_200_OK
                )
            
            # Look up user by shield address
            shield_info = await self.shield_manager.lookup_user_by_shield_address(
                email_message.shield_address
            )
            
            if not shield_info:
                logger.warning(f"No user found for shield address: {email_message.shield_address}")
                return Response(
                    content={
                        "status": "rejected",
                        "reason": "shield_address_not_found",
                        "message_id": email_message.message_id
                    },
                    status_code=HTTP_200_OK
                )
            
            # Process through email protection
            protection_result = await self.protection.process_email(
                email_message,
                user_email=shield_info.user_email,
                organization_id=shield_info.organization_id
            )
            
            # Log the outcome
            if protection_result.should_forward:
                logger.info(f"Gmail message {email_message.message_id} forwarded to {shield_info.user_email}")
            else:
                logger.info(f"Gmail message {email_message.message_id} blocked: {protection_result.block_reason}")
            
            # Return processing result
            return Response(
                content={
                    "status": "processed",
                    "message_id": email_message.message_id,
                    "shield_address": email_message.shield_address,
                    "forwarded": protection_result.should_forward,
                    "threat_level": protection_result.analysis.threat_level.value if protection_result.analysis else "unknown",
                    "toxicity_score": protection_result.analysis.toxicity_score if protection_result.analysis else 0.0,
                    "block_reason": protection_result.block_reason,
                    "processing_time_ms": protection_result.analysis.processing_time_ms if protection_result.analysis else 0
                },
                status_code=HTTP_200_OK
            )
            
        except ValueError as e:
            logger.error(f"Gmail webhook data error: {e}")
            return Response(
                content={"error": str(e)},
                status_code=HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Gmail webhook processing error: {e}", exc_info=True)
            return Response(
                content={"error": "Internal processing error"},
                status_code=HTTP_400_BAD_REQUEST
            )
    
    @post("/oauth/callback")
    async def handle_oauth_callback(self, request: Request, data: Dict[str, Any]) -> Response:
        """
        Handle Gmail OAuth2 callback for user authorization.
        
        This endpoint processes the OAuth2 authorization code returned
        by Google after a user grants permission to access their Gmail.
        """
        try:
            auth_code = data.get('code')
            if not auth_code:
                return Response(
                    content={"error": "Authorization code required"},
                    status_code=HTTP_400_BAD_REQUEST
                )
            
            # Exchange the code for credentials
            success = await self.provider.exchange_oauth_code(auth_code)
            
            if success:
                logger.info("Gmail OAuth2 setup completed successfully")
                return Response(
                    content={
                        "status": "success",
                        "message": "Gmail integration configured successfully",
                        "next_steps": [
                            "Configure Gmail filters to forward emails to CellophoneMail",
                            "Test email processing with a test message"
                        ]
                    },
                    status_code=HTTP_200_OK
                )
            else:
                return Response(
                    content={"error": "Failed to configure Gmail integration"},
                    status_code=HTTP_400_BAD_REQUEST
                )
            
        except Exception as e:
            logger.error(f"Gmail OAuth callback error: {e}", exc_info=True)
            return Response(
                content={"error": "OAuth callback processing failed"},
                status_code=HTTP_400_BAD_REQUEST
            )
    
    @post("/test")
    async def test_gmail_integration(self, request: Request, data: Dict[str, Any]) -> Response:
        """
        Test endpoint for Gmail integration development.
        
        This endpoint allows testing the Gmail provider with simulated data
        during development and setup.
        """
        try:
            logger.info("Testing Gmail provider integration")
            
            # Create test email message
            test_message_data = {
                "id": data.get("message_id", "test-gmail-message-123"),
                "from": data.get("from", "test@example.com"),
                "to": data.get("to", "test@cellophanemail.com"),
                "subject": data.get("subject", "Gmail provider test message"),
                "snippet": data.get("content", "This is a test message for Gmail provider integration"),
                "internalDate": str(int(datetime.now().timestamp() * 1000))
            }
            
            # Process through the provider
            email_message = await self.provider.receive_message(test_message_data)
            
            return Response(
                content={
                    "status": "test_success",
                    "provider": "gmail",
                    "message_parsed": {
                        "message_id": email_message.message_id,
                        "from": email_message.from_address,
                        "to": email_message.to_addresses,
                        "subject": email_message.subject,
                        "shield_address": email_message.shield_address,
                        "received_at": email_message.received_at.isoformat() if email_message.received_at else None
                    },
                    "oauth_url": self.provider.get_oauth_url() if self.provider.client_id else None
                },
                status_code=HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Gmail test integration error: {e}", exc_info=True)
            return Response(
                content={"error": f"Test failed: {str(e)}"},
                status_code=HTTP_400_BAD_REQUEST
            )