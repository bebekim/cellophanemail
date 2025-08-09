"""Content processor for email analysis orchestration."""

from typing import Dict
from flask import current_app
from app.core.content_analyzer import ContentAnalysisService


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
    
    def _generate_filtered_content(self, parsed_email_data: Dict, analysis_result: Dict) -> str:
        """Generate filtered content based on analysis results."""
        # Minimal implementation - just return summary for now
        return f"[SUMMARY] Email from {parsed_email_data.get('original_sender', 'unknown')} - Content filtered for protection"