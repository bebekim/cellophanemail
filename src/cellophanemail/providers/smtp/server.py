"""SMTP server handler for receiving emails directly."""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP as SMTPServer, Envelope, Session

from .provider import SMTPProvider
from ...features.email_protection import EmailProtectionProcessor
from ...features.shield_addresses import ShieldAddressManager

logger = logging.getLogger(__name__)


class SMTPMessageHandler:
    """Handle incoming SMTP messages using the provider/feature architecture."""
    
    def __init__(self):
        self.provider = SMTPProvider()
        self.protection = EmailProtectionProcessor()
        self.shield_manager = ShieldAddressManager()
        logger.info("SMTP message handler initialized")
    
    async def handle_message(self, envelope: Envelope, message_data: bytes) -> str:
        """
        Handle incoming SMTP message.
        
        Args:
            envelope: SMTP envelope containing sender/recipients
            message_data: Raw email message bytes
            
        Returns:
            SMTP response string
        """
        try:
            logger.info(f"Received SMTP message from {envelope.mail_from} to {envelope.rcpt_tos}")
            
            # Parse message using SMTP provider
            email_message = await self.provider.receive_message({
                'envelope': envelope,
                'message_data': message_data
            })
            
            if not email_message.shield_address:
                logger.info(f"SMTP message {email_message.message_id} not for shield address, accepting but not processing")
                return "250 Message accepted"
            
            # Look up user by shield address
            shield_info = await self.shield_manager.lookup_user_by_shield_address(
                email_message.shield_address
            )
            
            if not shield_info:
                logger.warning(f"No user found for shield address: {email_message.shield_address}")
                return "550 Mailbox not found"
            
            # Process through email protection
            protection_result = await self.protection.process_email(
                email_message,
                user_email=shield_info.user_email,
                organization_id=shield_info.organization_id
            )
            
            # Log the outcome
            if protection_result.should_forward:
                logger.info(f"SMTP message {email_message.message_id} forwarded to {shield_info.user_email}")
            else:
                logger.info(f"SMTP message {email_message.message_id} blocked: {protection_result.block_reason}")
            
            return "250 Message accepted"
            
        except Exception as e:
            logger.error(f"SMTP message handling error: {e}", exc_info=True)
            return "451 Temporary failure in processing message"


class SMTPServerHandler:
    """SMTP server controller for CellophoneMail."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 25):
        self.host = host
        self.port = port
        self.controller: Optional[Controller] = None
        self.message_handler = SMTPMessageHandler()
        self.running = False
        
    async def start_server(self) -> None:
        """Start the SMTP server."""
        try:
            # Create SMTP handler
            handler = SMTPHandler(self.message_handler)
            
            # Create controller
            self.controller = Controller(
                handler,
                hostname=self.host,
                port=self.port,
                ready_timeout=30
            )
            
            # Start the controller
            self.controller.start()
            self.running = True
            
            logger.info(f"SMTP server started on {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to start SMTP server: {e}")
            raise
    
    async def stop_server(self) -> None:
        """Stop the SMTP server."""
        if self.controller and self.running:
            try:
                self.controller.stop()
                self.running = False
                logger.info("SMTP server stopped")
            except Exception as e:
                logger.error(f"Error stopping SMTP server: {e}")
    
    def is_running(self) -> bool:
        """Check if SMTP server is running."""
        return self.running
    
    def get_status(self) -> Dict[str, Any]:
        """Get SMTP server status."""
        return {
            "running": self.running,
            "host": self.host,
            "port": self.port,
            "handler": "provider/feature architecture"
        }


class SMTPHandler:
    """aiosmtpd handler that integrates with our message handler."""
    
    def __init__(self, message_handler: SMTPMessageHandler):
        self.message_handler = message_handler
    
    async def handle_RCPT(self, server: SMTPServer, session: Session, envelope: Envelope, address: str, rcpt_options: list) -> str:
        """Handle RCPT TO command - validate recipients."""
        try:
            # Accept all @cellophanemail.com addresses
            if address.lower().endswith('@cellophanemail.com'):
                envelope.rcpt_tos.append(address)
                return '250 OK'
            
            # For other addresses, we could implement additional logic
            # For now, accept all to be permissive
            envelope.rcpt_tos.append(address)
            return '250 OK'
            
        except Exception as e:
            logger.error(f"RCPT TO error for {address}: {e}")
            return '451 Requested action aborted: error in processing'
    
    async def handle_DATA(self, server: SMTPServer, session: Session, envelope: Envelope) -> str:
        """Handle DATA command - process the email message."""
        try:
            # Get the message data
            message_data = envelope.content
            
            # Process through our message handler
            response = await self.message_handler.handle_message(envelope, message_data)
            return response
            
        except Exception as e:
            logger.error(f"DATA handling error: {e}", exc_info=True)
            return '451 Requested action aborted: error in processing'


# Standalone SMTP server for testing
async def run_standalone_smtp_server(host: str = "0.0.0.0", port: int = 25):
    """Run standalone SMTP server for testing."""
    print(f"🚀 Starting standalone SMTP server on {host}:{port}")
    
    server = SMTPServerHandler(host, port)
    
    try:
        await server.start_server()
        print(f"✅ SMTP server running - send test emails to *@cellophanemail.com")
        print("   Press Ctrl+C to stop")
        
        # Keep the server running
        while server.is_running():
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping SMTP server...")
        await server.stop_server()
        print("✅ SMTP server stopped")
    except Exception as e:
        print(f"❌ SMTP server error: {e}")
        await server.stop_server()


if __name__ == "__main__":
    # Run standalone server for testing
    asyncio.run(run_standalone_smtp_server())