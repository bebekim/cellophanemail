"""Email content analysis using AI services."""

import json
from typing import Dict, List, Optional
from flask import current_app
from any_llm import completion
from app.utils.exceptions import AIServiceError


class EmailAnalyzer:
    """AI-powered email content analyzer."""
    
    def __init__(self):
        self.ai_provider = current_app.config['AI_PROVIDER']
        self.ai_model = current_app.config['AI_MODEL']
        self.ai_api_key = current_app.config['AI_API_KEY']
        self.ai_max_tokens = current_app.config['AI_MAX_TOKENS']
        self.ai_temperature = current_app.config['AI_TEMPERATURE']
    
    def analyze_content(self, email_content: str, sender_email: str) -> Dict:
        """
        Analyze email content for potential abuse patterns.
        
        Returns:
            Dict with keys: abuse_score, classification, confidence, patterns, reasoning
        """
        try:
            response = self._call_any_llm_service(email_content, sender_email)
            
            # Parse the JSON response from AI
            ai_result = json.loads(response.choices[0].message.content)
            
            return {
                'abuse_score': ai_result.get('abuse_score', 0.0),
                'classification': ai_result.get('classification', 'SAFE'),
                'confidence': ai_result.get('confidence', 0.0),
                'patterns': ai_result.get('patterns', []),
                'reasoning': ai_result.get('reasoning', '')
            }
            
        except Exception as e:
            current_app.logger.error(f"AI analysis failed: {str(e)}")
            return self._fallback_analysis(email_content)
    
    def extract_features(self, email_content: str) -> Dict:
        """Extract features for ML training."""
        try:
            # For now, use basic feature extraction as this is not the focus of our current TDD cycle
            return self._basic_feature_extraction(email_content)
            
        except Exception as e:
            current_app.logger.error(f"Feature extraction failed: {str(e)}")
            return self._basic_feature_extraction(email_content)
    
    def _call_any_llm_service(self, email_content: str, sender_email: str):
        """Make API call to AI service using any-llm library."""
        model_name = f"{self.ai_provider}/{self.ai_model}"
        
        prompt = f"""Analyze this email content for potential abuse, harassment, or harmful patterns.

Email from: {sender_email}
Content: {email_content}

Provide your analysis as a JSON object with the following structure:
{{
    "classification": "SAFE|WARNING|HARMFUL|ABUSIVE",
    "confidence": 0.0-1.0,
    "abuse_score": 0.0-1.0,
    "reasoning": "explanation of your analysis",
    "patterns": ["list", "of", "detected", "patterns"]
}}

Classification guide:
- SAFE: No concerning content
- WARNING: Mild concerning language or tone
- HARMFUL: Clear aggressive/threatening language
- ABUSIVE: Severe threats, harassment, or abuse"""

        response = completion(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.ai_max_tokens,
            temperature=self.ai_temperature
        )
        
        return response
    
    def _fallback_analysis(self, content: str) -> Dict:
        """Basic keyword-based analysis when AI service fails."""
        abuse_keywords = [
            'threat', 'hurt', 'kill', 'violence', 'stupid', 'worthless',
            'hate', 'destroy', 'revenge', 'punish', 'regret'
        ]
        
        content_lower = content.lower()
        detected_patterns = []
        
        for keyword in abuse_keywords:
            if keyword in content_lower:
                detected_patterns.append(f"keyword:{keyword}")
        
        abuse_score = min(len(detected_patterns) * 0.2, 1.0)
        
        if abuse_score >= 0.7:
            classification = 'ABUSIVE'
        elif abuse_score >= 0.4:
            classification = 'HARMFUL' 
        elif abuse_score >= 0.2:
            classification = 'WARNING'
        else:
            classification = 'SAFE'
        
        return {
            'abuse_score': abuse_score,
            'classification': classification,
            'confidence': 0.6,  # Lower confidence for fallback
            'patterns': detected_patterns,
            'reasoning': 'Fallback keyword analysis'
        }
    
    def _basic_feature_extraction(self, content: str) -> Dict:
        """Basic feature extraction fallback."""
        return {
            'word_count': len(content.split()),
            'character_count': len(content),
            'contains_caps': content.isupper(),
            'exclamation_count': content.count('!'),
            'question_count': content.count('?')
        }