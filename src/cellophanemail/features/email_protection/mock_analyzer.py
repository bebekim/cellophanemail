"""
Mock email analyzer for testing.
Provides deterministic responses without API calls.
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from .analyzer_interface import IEmailAnalyzer
from .models import ThreatLevel, HorsemanDetection

logger = logging.getLogger(__name__)


@dataclass
class EmailAnalysis:
    """Email analysis result - compatible with EmailToxicityAnalyzer."""
    toxicity_score: float
    threat_level: ThreatLevel
    safe: bool
    fact_ratio: float
    communication_manner: str
    personal_attacks: List[str]
    manipulation_tactics: List[str] 
    implicit_threats: List[str]
    horsemen_detected: List[HorsemanDetection]
    reasoning: str
    confidence: float
    processing_time_ms: int
    language_detected: str = "en"


class MockAnalyzer(IEmailAnalyzer):
    """
    Mock email analyzer for testing.
    Returns predefined responses without making API calls.
    """
    
    def __init__(self, default_toxicity: float = 0.05):
        """
        Initialize mock analyzer with default responses.
        
        Args:
            default_toxicity: Default toxicity score for all emails
        """
        self.default_toxicity = default_toxicity
        self.call_count = 0
        self.call_history = []
        self.custom_responses = {}
        self.fact_responses = {}
        
    def set_toxicity_response(self, email_pattern: str, toxicity_score: float, 
                             threat_level: str = "low", safe: bool = True):
        """
        Set custom response for specific email patterns.
        
        Args:
            email_pattern: Pattern to match in email content (simple substring)
            toxicity_score: Toxicity score to return (0.0-1.0)
            threat_level: "safe", "low", "medium", "high", "critical"
            safe: Whether email is considered safe
        """
        threat_map = {
            "safe": ThreatLevel.SAFE,
            "low": ThreatLevel.LOW,
            "medium": ThreatLevel.MEDIUM,
            "high": ThreatLevel.HIGH,
            "critical": ThreatLevel.CRITICAL
        }
        
        self.custom_responses[email_pattern.lower()] = {
            "toxicity_score": toxicity_score,
            "threat_level": threat_map.get(threat_level, ThreatLevel.LOW),
            "safe": safe
        }
        
    def set_fact_response(self, fact_pattern: str, presentation: str):
        """
        Set response for fact presentation analysis.
        
        Args:
            fact_pattern: Pattern to match in fact text
            presentation: "positive", "neutral", or "negative"
        """
        self.fact_responses[fact_pattern.lower()] = presentation
        
    def analyze_email_toxicity(self, email_content: str, sender_email: str) -> EmailAnalysis:
        """
        Mock email toxicity analysis with predictable responses.
        """
        self.call_count += 1
        self.call_history.append({
            "method": "analyze_email_toxicity",
            "content": email_content[:100] + "..." if len(email_content) > 100 else email_content,
            "sender": sender_email
        })
        
        # Check for custom responses based on content patterns
        content_lower = email_content.lower()
        for pattern, response in self.custom_responses.items():
            if pattern in content_lower:
                logger.info(f"MockAnalyzer: Found pattern '{pattern}', returning toxicity {response['toxicity_score']}")
                return EmailAnalysis(
                    toxicity_score=response["toxicity_score"],
                    threat_level=response["threat_level"],
                    safe=response["safe"],
                    fact_ratio=0.5,
                    communication_manner=self._get_manner_from_toxicity(response["toxicity_score"]),
                    personal_attacks=[],
                    manipulation_tactics=[],
                    implicit_threats=[],
                    horsemen_detected=[],
                    reasoning=f"Mock analysis for pattern: {pattern}",
                    confidence=0.9,
                    processing_time_ms=10,  # Very fast mock response
                    language_detected="en"
                )
        
        # Default response
        logger.info(f"MockAnalyzer: No custom pattern found, returning default toxicity {self.default_toxicity}")
        return EmailAnalysis(
            toxicity_score=self.default_toxicity,
            threat_level=ThreatLevel.SAFE if self.default_toxicity < 0.3 else ThreatLevel.LOW,
            safe=self.default_toxicity < 0.3,
            fact_ratio=0.8,
            communication_manner="professional",
            personal_attacks=[],
            manipulation_tactics=[],
            implicit_threats=[],
            horsemen_detected=[],
            reasoning="Mock analysis - default response",
            confidence=0.9,
            processing_time_ms=10,
            language_detected="en"
        )
    
    def analyze_fact_presentation(self, fact_text: str, full_email_content: str, sender_email: str) -> str:
        """
        Mock fact presentation analysis.
        """
        self.call_count += 1
        self.call_history.append({
            "method": "analyze_fact_presentation",
            "fact": fact_text,
            "sender": sender_email
        })
        
        # Check for custom responses
        fact_lower = fact_text.lower()
        for pattern, response in self.fact_responses.items():
            if pattern in fact_lower:
                return response
                
        # Default to neutral
        return "neutral"
    
    def _get_manner_from_toxicity(self, toxicity: float) -> str:
        """Convert toxicity score to communication manner."""
        if toxicity < 0.1:
            return "professional"
        elif toxicity < 0.3:
            return "casual"
        elif toxicity < 0.6:
            return "aggressive"
        elif toxicity < 0.8:
            return "manipulative"
        else:
            return "threatening"
    
    def reset(self):
        """Reset call history and custom responses."""
        self.call_count = 0
        self.call_history.clear()
        self.custom_responses.clear()
        self.fact_responses.clear()


# Predefined mock analyzers for common test scenarios
def create_clean_analyzer() -> MockAnalyzer:
    """Create analyzer that always returns clean/safe results."""
    mock = MockAnalyzer(default_toxicity=0.05)
    return mock


def create_toxic_analyzer() -> MockAnalyzer:
    """Create analyzer that returns high toxicity for typical toxic content."""
    mock = MockAnalyzer(default_toxicity=0.05)
    
    # Set up patterns for toxic content - ordered by severity
    # Critical toxicity (0.95) → BLOCK_ENTIRELY
    mock.set_toxicity_response("hate", 0.95, "critical", False)
    mock.set_toxicity_response("worthless", 0.95, "critical", False)
    mock.set_toxicity_response("hunt you down", 0.95, "critical", False)
    mock.set_toxicity_response("make you pay", 0.95, "critical", False)
    mock.set_toxicity_response("you'll regret", 0.95, "critical", False)
    mock.set_toxicity_response("make you suffer", 0.95, "critical", False)
    mock.set_toxicity_response("threatening message", 0.95, "critical", False)
    mock.set_toxicity_response("you'll regret this", 0.95, "critical", False)  # For test_relative_toxicity_ranking
    
    # High toxicity (0.85) → SUMMARIZE_ONLY  
    mock.set_toxicity_response("stupid idiot", 0.85, "high", False)
    mock.set_toxicity_response("incompetent", 0.85, "high", False)
    mock.set_toxicity_response("sick of dealing", 0.85, "high", False)
    mock.set_toxicity_response("worthless and incompetent", 0.85, "high", False)  # For test_relative_toxicity_ranking
    
    # Medium toxicity (0.65) → REDACT_HARMFUL
    mock.set_toxicity_response("terrible", 0.65, "medium", False)
    mock.set_toxicity_response("disappointing", 0.65, "medium", False)
    mock.set_toxicity_response("really disappointing", 0.65, "medium", False)
    mock.set_toxicity_response("terrible work", 0.65, "medium", False)  # For test_relative_toxicity_ranking
    
    # Minor toxicity (0.35) → FORWARD_WITH_CONTEXT
    mock.set_toxicity_response("too late", 0.35, "low", False)
    mock.set_toxicity_response("time is running out", 0.35, "low", False)
    mock.set_toxicity_response("before it's too late", 0.35, "low", False)
    mock.set_toxicity_response("should really consider", 0.35, "low", False)
    mock.set_toxicity_response("should have done", 0.35, "low", False)
    mock.set_toxicity_response("should have done this earlier", 0.35, "low", False)  # For test_relative_toxicity_ranking
    
    return mock


def create_graduated_analyzer() -> MockAnalyzer:
    """Create analyzer with graduated responses for threshold testing."""
    mock = MockAnalyzer(default_toxicity=0.05)
    
    # Graduated toxicity levels
    mock.set_toxicity_response("minor issue", 0.35, "low", False)      # FORWARD_WITH_CONTEXT
    mock.set_toxicity_response("moderate problem", 0.65, "medium", False)  # REDACT_HARMFUL
    mock.set_toxicity_response("serious issue", 0.85, "high", False)       # SUMMARIZE_ONLY
    mock.set_toxicity_response("extreme threat", 0.95, "critical", False)  # BLOCK_ENTIRELY
    
    return mock