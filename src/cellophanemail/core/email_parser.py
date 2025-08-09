"""Email parser for Gmail forwarded emails."""

import re
import email
from typing import Dict, Optional
from flask import current_app


class EmailParser:
    """Parser for extracting original email data from Gmail forwarded emails."""
    
    def parse_forwarded_email(self, email_content) -> Dict:
        """
        Parse Gmail forwarded email to extract original sender and other metadata.
        
        Args:
            email_content: Raw email content string or envelope object
            
        Returns:
            Dict containing parsed email data
        """
        current_app.logger.info("📋 [EmailParser] Starting parse_forwarded_email")
        
        # Handle envelope object (for Korean tests)
        if hasattr(email_content, 'content'):
            current_app.logger.info(f"📋 [EmailParser] Envelope detected, content length: {len(email_content.content)}")
            content_str = self._decode_content(email_content.content)
            current_app.logger.info(f"📋 [EmailParser] Decoded content (first 200 chars): {content_str[:200]}")
            
            extracted_body = self._extract_body(content_str)
            current_app.logger.info(f"📋 [EmailParser] Extracted body: {extracted_body[:100] if extracted_body else 'NONE'}")
            
            result = {
                'forwarding_user': email_content.mail_from,
                'original_sender': self._extract_header_field(content_str, 'From'),
                'original_subject': self._extract_header_field(content_str, 'Subject'),
                'original_body': extracted_body,
                'original_content': extracted_body
            }
        else:
            # Handle string content (for basic tests)
            current_app.logger.info(f"📋 [EmailParser] String content, length: {len(email_content)}")
            extracted_body = self._extract_body(email_content)
            current_app.logger.info(f"📋 [EmailParser] Extracted body from string: {extracted_body[:100] if extracted_body else 'NONE'}")
            
            result = {
                'original_sender': self._extract_header_field(email_content, 'From'),
                'original_subject': self._extract_header_field(email_content, 'Subject'),
                'original_body': extracted_body
            }
        
        current_app.logger.info(f"📋 [EmailParser] Final result keys: {result.keys()}")
        current_app.logger.info(f"📋 [EmailParser] Body present: {'original_body' in result and result['original_body']}")
        
        return result
    
    def _decode_content(self, content) -> str:
        """Decode email content handling UTF-8 encoding."""
        if isinstance(content, bytes):
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                return content.decode('utf-8', errors='ignore')
        return content
    
    def _extract_header_field(self, email_content: str, field_name: str) -> Optional[str]:
        """Extract a header field value from forwarded email (English + Korean support)."""
        korean_fields = {
            'From': '보낸사람',
            'Subject': '제목', 
            'To': '받는사람'
        }
        
        # If content has Korean forwarded message header, prioritize Korean patterns
        if ('전달된 메시지' in email_content or '원본 메시지' in email_content) and field_name in korean_fields:
            korean_pattern = rf'{korean_fields[field_name]}:\s*([^\n\r]+)'
            match = re.search(korean_pattern, email_content)
            if match:
                return match.group(1).strip()
            
            # Try Outlook Korean patterns (with space)
            outlook_korean_fields = {
                'From': '보낸 사람',
                'Subject': '제목',
                'To': '받는 사람'
            }
            if field_name in outlook_korean_fields:
                outlook_pattern = rf'{outlook_korean_fields[field_name]}:\s*([^\n\r]+)'
                match = re.search(outlook_pattern, email_content)
                if match:
                    return match.group(1).strip()
        
        # Try English patterns
        pattern = rf'{field_name}:\s*([^\n\r]+)'
        match = re.search(pattern, email_content)
        if match:
            return match.group(1).strip()
        
        # Fallback to Korean patterns if English didn't work
        if field_name in korean_fields:
            korean_pattern = rf'{korean_fields[field_name]}:\s*([^\n\r]+)'
            match = re.search(korean_pattern, email_content)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_body(self, email_content: str) -> Optional[str]:
        """
        Extract body content from email (supports multipart MIME and plain text).
        
        Handles both multipart MIME emails (using Python's email module) and 
        traditional forwarded emails (using regex patterns for Korean/English).
        """
        # Try multipart MIME parsing first
        if self._is_multipart_email(email_content):
            body = self._extract_multipart_body(email_content)
            if body:
                return body
        
        # Fall back to regex patterns for traditional forwarded emails
        return self._extract_body_with_regex(email_content)
    
    def _is_multipart_email(self, email_content: str) -> bool:
        """Check if email content is multipart MIME format."""
        return 'Content-Type: multipart' in email_content and 'boundary=' in email_content
    
    def _extract_multipart_body(self, email_content: str) -> Optional[str]:
        """Extract body from multipart MIME email using Python's email module."""
        try:
            msg = email.message_from_string(email_content)
            if msg.is_multipart():
                # Walk through all parts to find text/plain content
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        return self._get_part_payload(part)
            else:
                # Single part message
                return self._get_part_payload(msg)
        except Exception:
            # If multipart parsing fails, fall back to regex
            return None
        return None
    
    def _get_part_payload(self, part) -> Optional[str]:
        """Extract and properly decode payload from an email part."""
        # decode=True automatically handles Base64 and quoted-printable encoding
        body = part.get_payload(decode=True)
        current_app.logger.info(f"📋 [EmailParser] Raw payload type: {type(body)}")
        if isinstance(body, bytes):
            # Decode bytes to string with UTF-8
            decoded = body.decode('utf-8', errors='ignore').strip()
            current_app.logger.info(f"📋 [EmailParser] Decoded from bytes (first 50): {decoded[:50]}")
            return decoded
        elif isinstance(body, str):
            current_app.logger.info(f"📋 [EmailParser] String payload (first 50): {body[:50]}")
            return body.strip()
        return None
    
    def _extract_body_with_regex(self, email_content: str) -> Optional[str]:
        """Extract body using regex patterns for traditional forwarded emails."""
        # Try English "To:" pattern first
        body_match = re.search(r'To:\s*[^\n\r]+\s*\n\s*\n(.*)', email_content, re.DOTALL)
        if body_match:
            return body_match.group(1).strip()
        
        # Try Korean Gmail "받는사람:" pattern
        body_match = re.search(r'받는사람:\s*[^\n\r]+\s*\n\s*\n(.*)', email_content, re.DOTALL)
        if body_match:
            return body_match.group(1).strip()
        
        # Try Korean Outlook "받는 사람:" pattern (with space and subject after)
        body_match = re.search(r'받는 사람:\s*[^\n\r]+\s*\n제목:\s*[^\n\r]+\s*\n\s*\n(.*)', email_content, re.DOTALL)
        if body_match:
            return body_match.group(1).strip()
        
        # Fallback - try after any Korean "To" field
        body_match = re.search(r'받는 사람:\s*[^\n\r]+.*?\n\s*\n(.*)', email_content, re.DOTALL)
        return body_match.group(1).strip() if body_match else None