"""Base email sender class with shared methods."""

from abc import ABC, abstractmethod


class BaseEmailSender(ABC):
    """Abstract base class for email senders with shared functionality."""
    
    def __init__(self, service_domain, username):
        """Initialize with configuration."""
        self.service_domain = service_domain
        self.username = username
    
    def extract_email_from_shield(self, shield_address):
        """
        Extract user's email address from shield address.
        
        For now, ALL shield addresses map to the configured EMAIL_USERNAME
        since this is a single-user system.
        
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
    
    def format_email_content(self, ai_result, original_email_data):
        """
        Format email content based on AI classification results.
        
        Args:
            ai_result: Dictionary with AI classification results
            original_email_data: Dictionary with original email data
            
        Returns:
            Tuple of (subject, content)
        """
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
            original_body = original_email_data.get('original_body', original_email_data.get('content', 'No content'))
            content = f"""{original_body}

---
Protected by CellophoneMail Email Protection Service"""
        
        return subject, content
    
    async def send_filtered_email(self, recipient_shield_address, ai_result, original_email_data):
        """
        Send filtered email back to user's real email address.
        
        Args:
            recipient_shield_address: Shield email address (e.g., yh.kim@cellophanemail.com)
            ai_result: Dictionary with AI classification results
            original_email_data: Dictionary with original email data
        """
        from email.mime.text import MIMEText
        import uuid
        
        # Extract real email address
        real_email = self.extract_email_from_shield(recipient_shield_address)
        if not real_email:
            return  # Invalid shield address
        
        # Format email based on AI classification
        subject, content = self.format_email_content(ai_result, original_email_data)
        
        # Build threading headers to preserve Gmail conversation view
        threading_headers = self.build_threading_headers(original_email_data)
        
        # Build anti-spoofing headers (never spoof the From address)
        thread_id = uuid.uuid4().hex[:8]  # Generate thread ID for this conversation
        original_sender = original_email_data.get('original_sender', 'unknown')
        anti_spoofing_headers = self.build_anti_spoofing_headers(
            original_sender=original_sender,
            thread_id=thread_id
        )
        
        # Combine all headers
        headers = {**threading_headers, **anti_spoofing_headers}
        
        # Send via the concrete implementation's send_email method
        return await self.send_email(real_email, subject, content, headers)
    
    @abstractmethod
    async def send_email(self, to_address, subject, content, headers):
        """Abstract method for sending email - must be implemented by subclasses."""
        pass