"""Outbound email service for sending processed emails back to users."""

import uuid
from datetime import datetime
from flask import current_app


class OutboundEmailService:
    """Service for sending filtered emails back to users' email providers."""
    
    def __init__(self, app=None):
        """Initialize SMTP service with configuration constants."""
        if app is None:
            app = current_app
        
        # Force reload environment variables at runtime to ensure they're available
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        self.smtp_server = app.config['OUTBOUND_SMTP_HOST']
        self.smtp_port = app.config['OUTBOUND_SMTP_PORT']
        self.use_tls = app.config['OUTBOUND_SMTP_USE_TLS']
        
        # Get credentials directly from environment as fallback
        self.username = app.config.get('EMAIL_USERNAME') or os.environ.get('EMAIL_USERNAME')
        self.password = app.config.get('EMAIL_PASSWORD') or os.environ.get('EMAIL_PASSWORD')
        
        self.service_domain = app.config['SMTP_DOMAIN']
        self.service_constants = app.config['SERVICE_CONSTANTS']
    
    def extract_email_from_shield(self, shield_address):
        """
        Extract user's email address from shield address.
        
        For now, ALL shield addresses map to the configured EMAIL_USERNAME
        since this is a single-user system.
        
        Future: Will use database mapping for multi-user support.
        
        Examples:
        - yh.kim@cellophanemail.com → goldenfermi@gmail.com
        - anything@cellophanemail.com → goldenfermi@gmail.com
        
        Returns None for invalid addresses.
        """
        if not shield_address or '@' not in shield_address:
            return None
            
        # Only process addresses from our service domain
        service_suffix = f'@{self.service_domain}'
        if not shield_address.endswith(service_suffix):
            return None
        
        # For single-user system, always return the configured email
        # This is the email that has the app password configured
        return self.username  # This is EMAIL_USERNAME from .env (goldenfermi@gmail.com)
    
    def extract_gmail_from_shield(self, shield_address):
        """Deprecated: Use extract_email_from_shield() instead."""
        return self.extract_email_from_shield(shield_address)
    
    def build_threading_headers(self, original_email):
        """
        Build email headers to preserve threading in Gmail.
        
        Args:
            original_email: Dict with 'message_id', 'subject', 'from' keys
            
        Returns:
            Dict with threading headers
        """
        headers = {}
        
        # Generate new Message-ID for our response
        unique_id = uuid.uuid4().hex[:12]
        headers['Message-ID'] = f'<{unique_id}@{self.service_domain}>'
        
        # Preserve threading with In-Reply-To and References
        if original_email.get('message_id'):
            headers['In-Reply-To'] = original_email['message_id']
            headers['References'] = original_email['message_id']
        
        return headers
    
    def build_anti_spoofing_headers(self, original_sender, thread_id=None):
        """
        Build headers that comply with anti-spoofing policies.
        
        Args:
            original_sender: The actual sender we're filtering
            thread_id: Optional thread ID for reply routing
            
        Returns:
            Dict with From and Reply-To headers
        """
        headers = {}
        
        # Never spoof the From address - use our service domain
        headers['From'] = f'CellophoneMail Shield <noreply@{self.service_domain}>'
        
        # Set Reply-To for thread management if thread_id provided
        if thread_id:
            headers['Reply-To'] = f'thread-{thread_id}@{self.service_domain}'
        
        return headers
    
    async def send_filtered_email(self, recipient_shield_address, ai_result, original_email_data):
        """
        Send filtered email back to user's real email address.
        
        Args:
            recipient_shield_address: Shield email address (e.g., yh.kim@cellophanemail.com)
            ai_result: Dictionary with AI classification results
            original_email_data: Dictionary with original email data
        """
        import aiosmtplib
        from email.mime.text import MIMEText
        
        # Extract real Gmail address
        real_email = self.extract_email_from_shield(recipient_shield_address)
        
        # Format email based on AI classification
        classification = ai_result.get('ai_classification', 'SAFE')
        original_subject = original_email_data.get('original_subject', 'No Subject')
        original_sender = original_email_data.get('original_sender', 'unknown')
        
        if classification in ['HARMFUL', 'ABUSIVE']:
            # Format filtered email
            subject = f"[Filtered] {original_subject}"
            horsemen = ai_result.get('horsemen_detected', [])
            horsemen_text = ', '.join(horsemen) if horsemen else 'harmful content'
            
            content = f"""⚠️ Email filtered by CellophoneMail
Original sender: {original_sender}
Detected: {horsemen_text}
Classification: {classification}

This message was blocked due to potentially harmful content.
Original will be available after cooling period.

---
CellophoneMail Email Protection Service"""
        else:
            # SAFE email - pass through with footer
            subject = original_subject
            content = f"""{original_email_data.get('original_body', original_email_data.get('content', 'No content'))}

---
Protected by CellophoneMail Email Protection Service"""
        
        # Create email message
        msg = MIMEText(content)
        msg['To'] = real_email
        msg['Subject'] = subject
        
        # Add threading headers to preserve Gmail conversation view
        threading_headers = self.build_threading_headers(original_email_data)
        for header, value in threading_headers.items():
            msg[header] = value
        
        # Add anti-spoofing headers (never spoof the From address)
        thread_id = uuid.uuid4().hex[:8]  # Generate thread ID for this conversation
        anti_spoofing_headers = self.build_anti_spoofing_headers(
            original_sender=original_sender,
            thread_id=thread_id
        )
        for header, value in anti_spoofing_headers.items():
            msg[header] = value
        
        # Send via SMTP using recommended aiosmtplib.send() approach
        try:
            from flask import current_app
            current_app.logger.info(f"📤 Starting SMTP send to {real_email}")
            current_app.logger.info(f"🔗 SMTP Server: {self.smtp_server}:{self.smtp_port}")
            current_app.logger.info(f"👤 Username: {self.username}")
            current_app.logger.info(f"📧 Subject: {subject}")
            
            # Use the recommended aiosmtplib.send() function
            result = await aiosmtplib.send(
                msg,
                hostname=self.smtp_server,
                port=self.smtp_port,
                username=self.username,
                password=self.password
            )
            
            current_app.logger.info(f"✅ Email sent successfully! Result: {result}")
                
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"❌ SMTP sending failed: {e}")
            current_app.logger.error(f"📍 Error type: {type(e).__name__}")
            # Don't re-raise - we want email processing to continue even if sending fails