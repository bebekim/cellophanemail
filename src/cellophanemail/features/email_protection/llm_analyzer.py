"""
LLM analyzer for fact manner analysis.
Simple function-based approach with provider and model as parameters.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def analyze_fact_manner_with_llm(
    fact_text: str, 
    full_email_content: str, 
    sender_email: str,
    llm_provider: str,
    llm_client,
    model_name: str
) -> str:
    """
    Analyze how a fact is presented using any LLM provider.
    
    Args:
        fact_text: The factual statement to analyze
        full_email_content: Complete email for context
        sender_email: Who sent the email
        llm_provider: "anthropic", "openai", etc.
        llm_client: Configured client for the provider
        model_name: Model to use (e.g., "claude-3-sonnet-20240229", "gpt-4")
        
    Returns:
        str: "positive", "neutral", or "negative"
    """
    
    prompt = f"""
    Analyze how this factual statement is presented in the email:
    
    FULL EMAIL: {full_email_content}
    FACT: "{fact_text}"
    SENDER: {sender_email}
    
    How is this fact presented?
    - POSITIVE: Constructive, helpful, supportive
    - NEUTRAL: Plain statement without emotion
    - NEGATIVE: Destructive, attacking, manipulative
    
    Consider context, tone, and intent.
    Respond with one word: POSITIVE, NEUTRAL, or NEGATIVE
    """
    
    try:
        if llm_provider == "anthropic":
            response = llm_client.messages.create(
                model=model_name,
                max_tokens=10,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.content[0].text.strip().upper()
            
        elif llm_provider == "openai":
            response = llm_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            result = response.choices[0].message.content.strip().upper()
            
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")
            
        # Validate and return
        if result in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
            return result.lower()
        else:
            logger.warning(f"Unexpected response: {result}")
            return "neutral"
            
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        raise


class SimpleLLMAnalyzer:
    """Simple wrapper for LLM analysis with configurable provider and model."""
    
    def __init__(self, provider: str, client, model_name: str):
        """
        Initialize LLM analyzer.
        
        Args:
            provider: LLM provider name ("anthropic", "openai")
            client: Configured client for the provider
            model_name: Specific model to use
        """
        self.provider = provider
        self.client = client
        self.model_name = model_name
        
    def analyze_fact_manner(self, fact_text: str, full_email_content: str, sender_email: str) -> str:
        """Analyze fact presentation manner using configured LLM."""
        return analyze_fact_manner_with_llm(
            fact_text, 
            full_email_content, 
            sender_email,
            self.provider,
            self.client,
            self.model_name
        )


# Factory function for easy setup
def create_llm_analyzer(provider: str, api_key: str, model_name: str) -> Optional[SimpleLLMAnalyzer]:
    """
    Factory function to create LLM analyzers.
    
    Args:
        provider: "anthropic" or "openai"
        api_key: API key for the provider
        model_name: Specific model to use
        
    Returns:
        Configured LLM analyzer or None if setup fails
    """
    try:
        if provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            return SimpleLLMAnalyzer(provider, client, model_name)
        
        elif provider == "openai":
            import openai
            client = openai.OpenAI(api_key=api_key)
            return SimpleLLMAnalyzer(provider, client, model_name)
        
        else:
            logger.error(f"Unknown LLM provider: {provider}")
            return None
            
    except ImportError as e:
        logger.error(f"Required package not installed: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to create LLM analyzer: {e}")
        return None


class MockLLMAnalyzer:
    """Mock LLM analyzer for testing."""
    
    def __init__(self, default_response="neutral"):
        self.default_response = default_response
        self.call_count = 0
        self.call_history = []
        
    def analyze_fact_manner(self, fact_text: str, full_email_content: str, sender_email: str) -> str:
        """Mock analysis for testing."""
        self.call_count += 1
        self.call_history.append({
            "fact": fact_text,
            "content": full_email_content[:50] + "..." if len(full_email_content) > 50 else full_email_content,
            "sender": sender_email
        })
        
        # Simple mock logic
        if "stupid" in full_email_content.lower() or "$" in fact_text:
            return "negative"
        elif "thank" in full_email_content.lower():
            return "positive"
        else:
            return self.default_response