"""SMTP server implementation using aiosmtpd."""

import asyncio
import logging
import os
from typing import Optional
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP as SMTPServer, Envelope, Session

from ...core.email_message import EmailMessage
from ...core.email_processor import EmailProcessor

logger = logging.getLogger(__name__)


class SMTPHandler:
    """Handler for SMTP server events."""
    
    def __init__(self, processor: Optional[EmailProcessor] = None):
        """Initialize SMTP handler with email processor."""
        self.processor = processor or EmailProcessor()
        
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
            
            # Process the email through the pipeline
            result = await self.processor.process(email_message)
            
            if result.should_forward:
                logger.info(f"Email {email_message.id} forwarded successfully")
                return '250 Message accepted for delivery'
            else:
                logger.warning(f"Email {email_message.id} blocked: {result.block_reason}")
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
        
        # Create email processor with delivery configuration
        from cellophanemail.config.settings import get_settings
        settings = get_settings()
        email_config = settings.email_delivery_config
        
        processor = EmailProcessor(config=email_config)
        
        # Create handler and controller
        handler = SMTPHandler(processor=processor)
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