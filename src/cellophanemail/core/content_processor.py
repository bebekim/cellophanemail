"""Content processor for email analysis orchestration."""

from typing import Dict, Optional, List
from dataclasses import dataclass
from uuid import UUID
from .content_analyzer import ContentAnalysisService
from .email_message import EmailMessage


@dataclass
class AnalysisResult:
    """Structured result from content analysis."""
    classification: str  # SAFE, WARNING, HARMFUL, ABUSIVE
    horsemen_detected: List[str]
    reasoning: str
    specific_examples: List[str]
    confidence_score: float = 1.0


@dataclass
class ProcessingContext:
    """Context information for email processing."""
    organization_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    source_plugin: str = "unknown"
    processing_rules: Dict[str, any] = None
    
    def __post_init__(self):
        if self.processing_rules is None:
            self.processing_rules = {}


@dataclass
class EmailProcessingResult:
    """Complete result of email content processing."""
    should_forward: bool
    analysis: AnalysisResult
    filtered_content: Optional[str] = None
    block_reason: Optional[str] = None
    toxicity_score: float = 0.0


class ContentProcessor:
    """Orchestrates email content analysis workflow with Four Horsemen detection."""
    
    def __init__(self):
        """Initialize ContentProcessor with proper Four Horsemen analyzer."""
        # Use the ContentAnalysisService with Four Horsemen framework
        self.analyzer = ContentAnalysisService()
    
    def process_email(self, user_id: int, parsed_email_data: Dict, raw_email_content: str) -> Dict:
        """
        Process email through analysis workflow.
        
        Args:
            user_id: ID of the user receiving the email
            parsed_email_data: Parsed email data from EmailParser
            raw_email_content: Raw email content for storage
            
        Returns:
            Dict containing analysis results and filtered content
        """
        # Use Four Horsemen ContentAnalysisService
        analysis_result = self._analyze_content(parsed_email_data)
        
        # Generate filtered content based on analysis
        filtered_content = self._generate_filtered_content(parsed_email_data, analysis_result)
        
        return {
            'ai_classification': analysis_result['classification'],
            'filtered_content': filtered_content,
            'horsemen_detected': analysis_result.get('horsemen_detected', []),
            'reasoning': analysis_result.get('reasoning', ''),
            'specific_examples': analysis_result.get('specific_examples', [])
        }
    
    def _analyze_content(self, parsed_email_data: Dict) -> Dict:
        """Analyze using Four Horsemen ContentAnalysisService."""
        email_content = parsed_email_data.get('original_body', '')
        sender_email = parsed_email_data.get('original_sender', '')
        
        current_app.logger.info(f"🔍 [ContentProcessor] Analyzing content")
        current_app.logger.info(f"🔍 [ContentProcessor] Email content length: {len(email_content)}")
        current_app.logger.info(f"🔍 [ContentProcessor] Email content (first 100): {email_content[:100] if email_content else 'EMPTY'}")
        current_app.logger.info(f"🔍 [ContentProcessor] Sender: {sender_email}")
        
        return self.analyzer.analyze_content(email_content, sender_email)
    
    # Legacy method for backwards compatibility
    def process_email(self, user_id: int, parsed_email_data: Dict, raw_email_content: str) -> Dict:
        """Legacy method - converts old interface to new one."""
        # Convert old format to new EmailMessage (simplified)
        from uuid import uuid4
        
        email = EmailMessage(
            id=uuid4(),
            from_address=parsed_email_data.get('original_sender', ''),
            to_addresses=[parsed_email_data.get('recipient', '')],
            subject=parsed_email_data.get('subject', ''),
            text_content=parsed_email_data.get('original_body', ''),
            html_content=None,
            message_id=parsed_email_data.get('message_id', ''),
            received_at=None
        )
        
        context = ProcessingContext(user_id=UUID(int=user_id) if user_id else None)
        result = self.process_email_content(email, context)
        
        # Convert back to old format
        return {
            'ai_classification': result.analysis.classification,
            'filtered_content': result.filtered_content,
            'horsemen_detected': result.analysis.horsemen_detected,
            'reasoning': result.analysis.reasoning,
            'specific_examples': result.analysis.specific_examples
        }