"""Postmark-based email sender that replaces SMTP with Postmark API."""

from flask import current_app


class PostmarkEmailSender:
    """Email sender service using Postmark API instead of SMTP."""
    
    def __init__(self, app=None):
        """Initialize Postmark service with configuration."""
        if app is None:
            app = current_app
        
        self.api_token = app.config['POSTMARK_API_TOKEN']
        self.service_domain = app.config['SMTP_DOMAIN']
        self.username = app.config['EMAIL_USERNAME']
        self.service_constants = app.config['SERVICE_CONSTANTS']
    
    def extract_email_from_shield(self, shield_address):
        """
        Extract user's email address from shield address.
        
        For now, ALL shield addresses map to the configured EMAIL_USERNAME
        since this is a single-user system.
        
        Returns None for invalid addresses.
        """
        if not shield_address or '@' not in shield_address:
            return None
            
        # Only process addresses from our service domain
        service_suffix = f'@{self.service_domain}'
        if not shield_address.endswith(service_suffix):
            return None
        
        # For single-user system, always return the configured email
        return self.username
    
    def build_threading_headers(self, original_email):
        """
        Build email headers to preserve threading in Gmail.
        
        Args:
            original_email: Dict with 'message_id', 'subject', 'from' keys
            
        Returns:
            Dict with threading headers
        """
        import uuid
        
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
        Send filtered email back to user's real email address using Postmark API.
        
        Args:
            recipient_shield_address: Shield email address (e.g., yh.kim@cellophanemail.com)
            ai_result: Dictionary with AI classification results
            original_email_data: Dictionary with original email data
        """
        import uuid
        from postmark import SendingAPIApi, Configuration, ApiClient
        from postmark.models import SendEmailRequest
        
        # Extract real email address
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
        
        # Build headers
        threading_headers = self.build_threading_headers(original_email_data)
        thread_id = uuid.uuid4().hex[:8]
        anti_spoofing_headers = self.build_anti_spoofing_headers(
            original_sender=original_sender,
            thread_id=thread_id
        )
        
        # Create Postmark configuration and API client
        configuration = Configuration()
        configuration.api_key['X-Postmark-Server-Token'] = self.api_token
        api_client = ApiClient(configuration)
        sending_api = SendingAPIApi(api_client)
        
        # Create email request
        email_request = SendEmailRequest(
            _from=anti_spoofing_headers['From'],
            to=real_email,
            subject=subject,
            text_body=content
        )
        
        # Add custom headers
        headers = []
        for header_name, header_value in {**threading_headers, **anti_spoofing_headers}.items():
            if header_name not in ['From']:  # Don't duplicate From header
                headers.append({'Name': header_name, 'Value': header_value})
        
        if headers:
            email_request.headers = headers
        
        try:
            # Get logger - try current_app first, fallback to print for testing
            try:
                from flask import current_app
                logger = current_app.logger
            except (ImportError, RuntimeError):
                # Fallback for testing - no flask context
                import logging
                logger = logging.getLogger(__name__)
            
            logger.info(f"📤 Starting Postmark send to {real_email}")
            logger.info(f"📧 Subject: {subject}")
            
            # Send via Postmark API
            result = sending_api.send_email(send_email_request=email_request)
            
            logger.info(f"✅ Email sent successfully! Message ID: {result.message_id}")
                
        except Exception as e:
            # Get logger for error handling too
            try:
                from flask import current_app
                logger = current_app.logger
            except (ImportError, RuntimeError):
                import logging
                logger = logging.getLogger(__name__)
                
            logger.error(f"❌ Postmark sending failed: {e}")
            logger.error(f"📍 Error type: {type(e).__name__}")
            # Don't re-raise - we want email processing to continue even if sending fails