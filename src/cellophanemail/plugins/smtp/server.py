"""SMTP server implementation using aiosmtpd."""

import asyncio
import logging
import os
from typing import Optional
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP as SMTPServer, Envelope, Session

from ...core.email_message import EmailMessage
from ...features.email_protection import EmailProtectionProcessor
from ...features.shield_addresses import ShieldAddressManager

logger = logging.getLogger(__name__)


class SMTPHandler:
    """Handler for SMTP server events."""
    
    def __init__(self):
        """Initialize SMTP handler with new architecture components."""
        self.protection = EmailProtectionProcessor()
        self.shield_manager = ShieldAddressManager()
        
    async def handle_RCPT(self, server: SMTPServer, session: Session, envelope: Envelope, address: str, rcpt_options: list):
        """Handle RCPT TO command."""
        envelope.rcpt_tos.append(address)
        return '250 OK'
    
    async def handle_DATA(self, server: SMTPServer, session: Session, envelope: Envelope):
        """Handle email data reception."""
        try:
            # Log receipt
            logger.info(f"Received email from {envelope.mail_from} to {envelope.rcpt_tos}")
            
            # Convert to standardized format
            email_message = EmailMessage.from_smtp_envelope(
                envelope=envelope,
                message_data=envelope.content,
                source="smtp"
            )
            
            # Look up user by shield address 
            shield_info = await self.shield_manager.lookup_user_by_shield_address(
                email_message.to_addresses[0] if email_message.to_addresses else ""
            )
            
            if not shield_info:
                logger.warning(f"Shield address not found: {email_message.to_addresses}")
                return '550 Recipient not found'
            
            # Process through email protection
            result = await self.protection.process_email(
                email_message,
                user_email=shield_info.user_email,
                organization_id=shield_info.organization_id
            )
            
            if result.should_forward:
                logger.info(f"Email {email_message.message_id} forwarded successfully")
                return '250 Message accepted for delivery'
            else:
                logger.warning(f"Email {email_message.message_id} blocked: {result.block_reason}")
                # Still return 250 to avoid bounces
                return '250 Message accepted but filtered'
                
        except Exception as e:
            logger.error(f"Error processing email: {e}", exc_info=True)
            return '451 Temporary failure, please try again later'


class SMTPServerRunner:
    """Manages the SMTP server lifecycle."""
    
    def __init__(self, host: str = None, port: int = None):
        """Initialize SMTP server configuration."""
        self.host = host or os.getenv("SMTP_HOST", "localhost")
        self.port = int(port or os.getenv("SMTP_PORT", 2525))
        self.controller = None
        
    async def start(self):
        """Start the SMTP server."""
        logger.info(f"Starting SMTP server on {self.host}:{self.port}")
        
        # Create handler with new architecture
        handler = SMTPHandler()
        self.controller = Controller(
            handler,
            hostname=self.host,
            port=self.port
        )
        
        # Start the server
        self.controller.start()
        logger.info(f"SMTP server started successfully on {self.host}:{self.port}")
        
    async def stop(self):
        """Stop the SMTP server."""
        if self.controller:
            logger.info("Stopping SMTP server...")
            self.controller.stop()
            logger.info("SMTP server stopped")
            
    async def run_forever(self):
        """Run the SMTP server until interrupted."""
        await self.start()
        try:
            # Keep the server running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await self.stop()


async def main():
    """Main entry point for running SMTP server standalone."""
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if os.getenv("DEBUG") else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run server
    server = SMTPServerRunner()
    await server.run_forever()


if __name__ == "__main__":
    # Run the SMTP server
    asyncio.run(main())