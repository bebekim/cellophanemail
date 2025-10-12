"""
Interface for email toxicity analyzers.
Allows dependency injection and easy testing.
"""

from abc import ABC, abstractmethod
from typing import Protocol
from dataclasses import dataclass
from .models import ThreatLevel, HorsemanDetection


class IEmailAnalyzer(ABC):
    """
    Interface for email toxicity analyzers.
    All analyzers (Anthropic, Llama, Mock) must implement this interface.
    """
    
    @abstractmethod
    def analyze_email_toxicity(self, email_content: str, sender_email: str) -> 'EmailAnalysis':
        """
        Analyze email for toxicity and harmful patterns.
        
        Args:
            email_content: Full email content including subject and body
            sender_email: Email address of sender
            
        Returns:
            EmailAnalysis with toxicity assessment
        """
        pass
    
    @abstractmethod
    def analyze_fact_presentation(self, fact_text: str, full_email_content: str, sender_email: str) -> str:
        """
        Analyze how a fact is presented (positive/neutral/negative).
        
        Args:
            fact_text: The factual statement to analyze
            full_email_content: Complete email for context
            sender_email: Who sent the email
            
        Returns:
            str: "positive", "neutral", or "negative"
        """
        pass


# EmailAnalysis will be imported by implementations