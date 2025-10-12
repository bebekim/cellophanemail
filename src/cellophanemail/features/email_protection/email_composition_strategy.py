"""
Email Composition Strategy for Privacy-Focused Email Protection

Composes emails based on protection actions while preserving original sender
attribution and maintaining transparency about content filtering.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum

from .ephemeral_email import EphemeralEmail
from .in_memory_processor import ProcessingResult, ProtectionAction


@dataclass
class EmailComposition:
    """
    Represents how an email should be composed based on protection action.
    """
    subject: str
    body: str
    headers: Dict[str, str]
    from_address: str
    reply_to: Optional[str] = None


@dataclass 
class DeliveryConfiguration:
    """
    Configuration for email delivery integration.
    """
    sender_type: str = "postmark"  # "postmark" or "smtp"
    config: Dict[str, Any] = field(default_factory=dict)
    service_domain: str = "cellophanemail.com"
    max_retries: int = 3
    add_transparency_headers: bool = True
    preserve_threading: bool = True


class EmailCompositionStrategy:
    """
    Strategy for composing emails based on protection actions.
    
    Transforms ProcessingResult + EphemeralEmail into EmailComposition that
    respects privacy principles while maintaining sender attribution.
    """
    
    def compose_email(self, processing_result: ProcessingResult, original_email: EphemeralEmail, 
                     config: DeliveryConfiguration) -> EmailComposition:
        """
        Compose email for delivery based on protection action.
        
        Args:
            processing_result: Result from email processing containing delivery info
            original_email: Original ephemeral email with metadata
            config: Delivery configuration settings
            
        Returns:
            EmailComposition ready for email sending
        """
        # Route to appropriate composition method by action
        action_handlers = {
            ProtectionAction.FORWARD_CLEAN: self._compose_clean_email,
            ProtectionAction.FORWARD_WITH_CONTEXT: self._compose_context_email,  
            ProtectionAction.REDACT_HARMFUL: self._compose_redacted_email,
            ProtectionAction.SUMMARIZE_ONLY: self._compose_summary_email,
        }
        
        handler = action_handlers.get(processing_result.action)
        if not handler:
            raise ValueError(f"Unknown protection action: {processing_result.action}")
            
        # Call appropriate handler
        composition = handler(processing_result, original_email, config)
        
        # Add common headers
        if config.add_transparency_headers:
            composition.headers = self._add_transparency_headers(
                composition.headers, processing_result, original_email, config
            )
        
        composition.headers = self._add_attribution_headers(
            composition.headers, original_email
        )
        
        if config.preserve_threading:
            composition.headers = self._add_threading_headers(
                composition.headers, original_email
            )
        
        return composition
    
    def _compose_clean_email(self, processing_result: ProcessingResult, original_email: EphemeralEmail, 
                           config: DeliveryConfiguration) -> EmailComposition:
        """Compose clean forwarded email with transparency footer."""
        
        # Use original content with transparency footer
        body = processing_result.processed_content
        footer = self._build_transparency_footer(processing_result.action, processing_result.toxicity_score)
        full_body = f"{body}\n\n{footer}"
        
        return EmailComposition(
            subject=original_email.subject,
            body=full_body,
            headers={},
            from_address=f"noreply@{config.service_domain}",
            reply_to=original_email.from_address
        )
    
    def _compose_redacted_email(self, processing_result: ProcessingResult, original_email: EphemeralEmail,
                              config: DeliveryConfiguration) -> EmailComposition:
        """Compose redacted email with filtering notice."""
        
        # Use processed (redacted) content with filtering notice
        body = processing_result.processed_content
        footer = self._build_transparency_footer(processing_result.action, processing_result.toxicity_score)
        full_body = f"{body}\n\n{footer}"
        
        # Add [Filtered] prefix to subject
        subject = f"[Filtered] {original_email.subject}"
        
        return EmailComposition(
            subject=subject,
            body=full_body,
            headers={},
            from_address=f"protection@{config.service_domain}",
            reply_to=original_email.from_address
        )
    
    def _compose_summary_email(self, processing_result: ProcessingResult, original_email: EphemeralEmail,
                             config: DeliveryConfiguration) -> EmailComposition:
        """Compose summary-only email with original sender info."""
        
        # Use summary content with summarization notice
        body = processing_result.processed_content
        footer = self._build_transparency_footer(processing_result.action, processing_result.toxicity_score)
        full_body = f"{body}\n\n{footer}"
        
        # Add [Summary] prefix to subject
        subject = f"[Summary] {original_email.subject}"
        
        return EmailComposition(
            subject=subject,
            body=full_body,
            headers={},
            from_address=f"summary@{config.service_domain}",
            reply_to=original_email.from_address
        )
    
    def _compose_context_email(self, processing_result: ProcessingResult, original_email: EphemeralEmail,
                             config: DeliveryConfiguration) -> EmailComposition:
        """Compose email with warning context."""
        
        # Use original content with warning header
        warning_header = f"CAUTION: This email may contain suspicious content (toxicity score: {processing_result.toxicity_score:.2f}). Please review carefully before taking any action.\n\n"
        body = warning_header + processing_result.processed_content
        footer = self._build_transparency_footer(processing_result.action, processing_result.toxicity_score)
        full_body = f"{body}\n\n{footer}"
        
        # Add [Caution] prefix to subject
        subject = f"[Caution] {original_email.subject}"
        
        return EmailComposition(
            subject=subject,
            body=full_body,
            headers={},
            from_address=f"caution@{config.service_domain}",
            reply_to=original_email.from_address
        )
    
    def _add_transparency_headers(self, headers: Dict[str, str], processing_result: ProcessingResult, 
                                original_email: EphemeralEmail, config: DeliveryConfiguration) -> Dict[str, str]:
        """Add transparency headers showing protection action taken."""
        
        updated_headers = headers.copy()
        updated_headers["X-Protection-Action"] = processing_result.action.value
        updated_headers["X-Toxicity-Score"] = str(processing_result.toxicity_score)
        
        return updated_headers
    
    def _add_attribution_headers(self, headers: Dict[str, str], original_email: EphemeralEmail) -> Dict[str, str]:
        """Add attribution headers preserving original sender."""
        
        updated_headers = headers.copy()
        updated_headers["X-Original-From"] = original_email.from_address
        
        return updated_headers
    
    def _add_threading_headers(self, headers: Dict[str, str], original_email: EphemeralEmail) -> Dict[str, str]:
        """Add threading headers for conversation continuity."""
        
        updated_headers = headers.copy()
        
        # Preserve threading if original email had these headers
        if hasattr(original_email, 'message_id_header') and original_email.message_id_header:
            updated_headers["Message-ID"] = original_email.message_id_header
            
        if hasattr(original_email, 'in_reply_to') and original_email.in_reply_to:
            updated_headers["In-Reply-To"] = original_email.in_reply_to
            
        if hasattr(original_email, 'references') and original_email.references:
            updated_headers["References"] = original_email.references
        
        return updated_headers
    
    def _build_transparency_footer(self, protection_action: ProtectionAction, toxicity_score: float) -> str:
        """Create appropriate transparency footer based on action taken."""
        
        action_footers = {
            ProtectionAction.FORWARD_CLEAN: "---\nProtected by CellophoneMail",
            ProtectionAction.REDACT_HARMFUL: f"---\nContent filtered by CellophoneMail (toxicity: {toxicity_score:.2f})",
            ProtectionAction.SUMMARIZE_ONLY: "---\nSummarized by CellophoneMail",
            ProtectionAction.FORWARD_WITH_CONTEXT: f"---\nCaution notice added by CellophoneMail (toxicity: {toxicity_score:.2f})"
        }
        
        return action_footers.get(protection_action, "---\nProcessed by CellophoneMail")