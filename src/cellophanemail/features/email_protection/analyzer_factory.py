"""
Factory for creating email analyzers based on environment configuration.
Supports Anthropic (production), Llama (privacy), and Mock (testing).
"""

import os
import logging
from typing import Optional
from .analyzer_interface import IEmailAnalyzer

logger = logging.getLogger(__name__)


class AnalyzerFactory:
    """
    Factory for creating appropriate email analyzer based on environment.
    
    Selection logic:
    - TESTING=true → MockAnalyzer (no API calls)
    - PRIVACY_MODE=true → LlamaAnalyzer (local model)  
    - Default → EmailToxicityAnalyzer (Anthropic API)
    """
    
    @staticmethod
    def create_analyzer(temperature: float = 0.0, analyzer_type: Optional[str] = None) -> IEmailAnalyzer:
        """
        Create appropriate analyzer based on environment or explicit type.
        
        Args:
            temperature: LLM temperature for analysis
            analyzer_type: Override environment detection ("mock", "llama", "anthropic")
            
        Returns:
            IEmailAnalyzer implementation
        """
        # Use explicit type if provided
        if analyzer_type:
            return AnalyzerFactory._create_by_type(analyzer_type, temperature)
            
        # Auto-detect based on environment
        if os.getenv("TESTING", "").lower() in ("true", "1", "yes"):
            logger.info("Creating MockAnalyzer for testing environment")
            return AnalyzerFactory._create_mock_analyzer()
            
        if os.getenv("PRIVACY_MODE", "").lower() in ("true", "1", "yes"):
            logger.info("Creating LlamaAnalyzer for privacy mode")
            return AnalyzerFactory._create_llama_analyzer(temperature)
            
        # Default to Anthropic
        logger.info("Creating EmailToxicityAnalyzer for production")
        return AnalyzerFactory._create_anthropic_analyzer(temperature)
    
    @staticmethod
    def _create_by_type(analyzer_type: str, temperature: float) -> IEmailAnalyzer:
        """Create analyzer by explicit type."""
        analyzer_type = analyzer_type.lower()
        
        if analyzer_type == "mock":
            return AnalyzerFactory._create_mock_analyzer()
        elif analyzer_type == "llama":
            return AnalyzerFactory._create_llama_analyzer(temperature)
        elif analyzer_type == "anthropic":
            return AnalyzerFactory._create_anthropic_analyzer(temperature)
        else:
            raise ValueError(f"Unknown analyzer type: {analyzer_type}")
    
    @staticmethod
    def _create_mock_analyzer() -> IEmailAnalyzer:
        """Create mock analyzer for testing."""
        from .mock_analyzer import create_toxic_analyzer
        return create_toxic_analyzer()
    
    @staticmethod 
    def _create_llama_analyzer(temperature: float) -> IEmailAnalyzer:
        """Create Llama analyzer for privacy mode."""
        try:
            from .llama_analyzer import LlamaAnalyzer
            return LlamaAnalyzer(temperature=temperature)
        except ImportError as e:
            logger.error(f"LlamaAnalyzer not available: {e}")
            logger.warning("Falling back to MockAnalyzer")
            return AnalyzerFactory._create_mock_analyzer()
    
    @staticmethod
    def _create_anthropic_analyzer(temperature: float) -> IEmailAnalyzer:
        """Create Anthropic analyzer for production."""
        from .email_toxicity_analyzer import EmailToxicityAnalyzer
        return EmailToxicityAnalyzer(temperature=temperature)
    
    @staticmethod
    def detect_environment() -> str:
        """
        Detect current environment for logging/debugging.
        
        Returns:
            Environment name: "testing", "privacy", or "production"
        """
        if os.getenv("TESTING", "").lower() in ("true", "1", "yes"):
            return "testing"
        elif os.getenv("PRIVACY_MODE", "").lower() in ("true", "1", "yes"):
            return "privacy"
        else:
            return "production"


# Convenience functions for specific scenarios
def create_for_testing() -> IEmailAnalyzer:
    """Create mock analyzer specifically for testing."""
    return AnalyzerFactory.create_analyzer(analyzer_type="mock")


def create_for_production(temperature: float = 0.0) -> IEmailAnalyzer:
    """Create production analyzer (Anthropic).""" 
    return AnalyzerFactory.create_analyzer(temperature, analyzer_type="anthropic")


def create_for_privacy(temperature: float = 0.0) -> IEmailAnalyzer:
    """Create privacy analyzer (Llama local)."""
    return AnalyzerFactory.create_analyzer(temperature, analyzer_type="llama")