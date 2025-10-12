"""
Consolidated LLM analyzer that performs comprehensive email analysis in a single API call.

Replaces the complex 4-phase pipeline with one optimized prompt that analyzes:
- Factual content vs emotional content ratio
- Communication manner and tone
- Psychological manipulation patterns
- Four Horsemen relationship patterns
- Implicit threats and power dynamics

This reduces 6 API calls to 1, improves performance 5-10x, and provides more consistent results.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from .llm_analyzer import SimpleLLMAnalyzer
from .models import AnalysisResult, ThreatLevel, HorsemanDetection

logger = logging.getLogger(__name__)


@dataclass
class ConsolidatedAnalysis:
    """Complete email analysis result from single LLM call."""
    # Core metrics
    toxicity_score: float  # 0.0-1.0
    threat_level: ThreatLevel
    safe: bool
    
    # Content analysis
    fact_ratio: float  # Percentage of factual vs emotional content
    communication_manner: str  # "professional", "aggressive", "manipulative", etc.
    
    # Psychological patterns
    personal_attacks: List[str]
    manipulation_tactics: List[str] 
    implicit_threats: List[str]
    
    # Four Horsemen detection
    horsemen_detected: List[HorsemanDetection]
    
    # Analysis metadata
    reasoning: str
    confidence: float  # 0.0-1.0
    processing_time_ms: int
    language_detected: str = "en"


class EmailToxicityLLMAnalyzer:
    """
    Single-pass LLM analyzer for comprehensive email protection analysis.
    
    Replaces complex multi-phase pipeline with one optimized prompt that captures
    all necessary information for protection decisions in a single API call.
    """
    
    def __init__(self, llm_analyzer: Optional[SimpleLLMAnalyzer] = None, temperature: float = 0.0):
        """
        Initialize consolidated analyzer.
        
        Args:
            llm_analyzer: Configured LLM client. If None, auto-creates from environment
            temperature: LLM temperature (0.0 for deterministic, higher for creative)
        """
        self.llm_analyzer = llm_analyzer or SimpleLLMAnalyzer()
        self.temperature = temperature  # Use 0.0 for deterministic testing
        
    async def analyze_email(self, email_content: str, sender_email: str) -> ConsolidatedAnalysis:
        """
        Perform comprehensive email analysis in single LLM call.
        
        Args:
            email_content: Full email content including subject and body
            sender_email: Email address of sender
            
        Returns:
            ConsolidatedAnalysis with all necessary data for protection decisions
        """
        start_time = datetime.now()
        
        try:
            # Build comprehensive analysis prompt
            prompt = self._build_comprehensive_prompt(email_content, sender_email)
            
            # Single LLM API call
            response = await self._call_llm(prompt)
            
            # Parse comprehensive response
            analysis = self._parse_llm_response(response, email_content)
            
            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            analysis.processing_time_ms = processing_time
            
            logger.info(f"Consolidated analysis completed in {processing_time}ms, toxicity: {analysis.toxicity_score:.3f}")
            return analysis
            
        except Exception as e:
            logger.error(f"Consolidated LLM analysis failed: {e}")
            # Return minimal safe analysis as fallback
            return self._create_fallback_analysis(email_content, str(e))
    
    def _build_comprehensive_prompt(self, email_content: str, sender_email: str) -> str:
        """Build single comprehensive prompt for all analysis needs."""
        
        return f"""You are an expert email safety analyzer. Analyze this email comprehensively and provide a detailed JSON assessment.

EMAIL TO ANALYZE:
From: {sender_email}
Content: {email_content}

ANALYSIS INSTRUCTIONS:
Evaluate this email across all dimensions and provide scores/classifications for:

1. TOXICITY ASSESSMENT (0.0-1.0 scale):
   - Overall toxicity score considering all harmful patterns
   - 0.0-0.1: Clean professional communication
   - 0.1-0.3: Minor concerning patterns, mostly professional  
   - 0.3-0.6: Moderate toxicity with clear harmful elements
   - 0.6-0.8: High toxicity with multiple serious issues
   - 0.8-1.0: Extreme toxicity, severe threats/attacks

2. CONTENT COMPOSITION:
   - Fact ratio: Percentage of content that is factual vs emotional (0.0-1.0)
   - Communication manner: "professional", "casual", "aggressive", "manipulative", "threatening"

3. HARMFUL PATTERNS (list specific examples found):
   - Personal attacks: Direct insults, character assassination, demeaning language
   - Manipulation tactics: Emotional manipulation, gaslighting, blame-shifting
   - Implicit threats: Veiled threats, intimidation, coercion

4. FOUR HORSEMEN RELATIONSHIP PATTERNS:
   For each detected pattern, provide: name, confidence (0.0-1.0), severity ("low", "medium", "high"), specific indicators
   - Criticism: Personal attacks on character rather than behavior
   - Contempt: Superiority, mockery, sarcasm, cynicism  
   - Defensiveness: Victim-playing, counter-attacking, blame-shifting
   - Stonewalling: Withdrawal, silent treatment, emotional shutdown

5. LANGUAGE AND CULTURAL CONTEXT:
   - Detected language (ISO code)
   - Cultural communication patterns that affect interpretation

RESPOND WITH VALID JSON ONLY:
{{
    "toxicity_score": 0.0,
    "threat_level": "safe|low|medium|high|critical", 
    "safe": true,
    "fact_ratio": 0.0,
    "communication_manner": "professional",
    "personal_attacks": [],
    "manipulation_tactics": [],
    "implicit_threats": [],
    "horsemen_detected": [
        {{
            "horseman": "criticism|contempt|defensiveness|stonewalling",
            "confidence": 0.0,
            "severity": "low|medium|high",
            "indicators": ["specific example from email"]
        }}
    ],
    "reasoning": "Detailed explanation of assessment",
    "confidence": 0.0,
    "language_detected": "en"
}}

Important: Be precise with toxicity scoring. Professional emails should score < 0.1, obvious attacks should score > 0.8. Consider cultural context and language nuances."""

    async def _call_llm(self, prompt: str) -> str:
        """Make single LLM API call with configured temperature."""
        
        if self.llm_analyzer.provider == "anthropic":
            response = self.llm_analyzer.client.messages.create(
                model=self.llm_analyzer.model_name,
                max_tokens=800,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
            
        elif self.llm_analyzer.provider == "openai":
            response = self.llm_analyzer.client.chat.completions.create(
                model=self.llm_analyzer.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=self.temperature
            )
            return response.choices[0].message.content.strip()
            
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_analyzer.provider}")
    
    def _parse_llm_response(self, response: str, original_content: str) -> ConsolidatedAnalysis:
        """Parse comprehensive LLM response into structured analysis."""
        
        try:
            data = json.loads(response)
            
            # Parse Four Horsemen detections
            horsemen = []
            for h in data.get("horsemen_detected", []):
                horsemen.append(HorsemanDetection(
                    horseman=h["horseman"],
                    confidence=float(h["confidence"]),
                    indicators=h.get("indicators", []),
                    severity=h["severity"]
                ))
            
            # Map threat level string to enum
            threat_level_map = {
                "safe": ThreatLevel.SAFE,
                "low": ThreatLevel.LOW, 
                "medium": ThreatLevel.MEDIUM,
                "high": ThreatLevel.HIGH,
                "critical": ThreatLevel.CRITICAL
            }
            
            return ConsolidatedAnalysis(
                toxicity_score=float(data["toxicity_score"]),
                threat_level=threat_level_map.get(data["threat_level"], ThreatLevel.LOW),
                safe=bool(data["safe"]),
                fact_ratio=float(data["fact_ratio"]),
                communication_manner=data["communication_manner"],
                personal_attacks=data.get("personal_attacks", []),
                manipulation_tactics=data.get("manipulation_tactics", []),
                implicit_threats=data.get("implicit_threats", []),
                horsemen_detected=horsemen,
                reasoning=data.get("reasoning", ""),
                confidence=float(data.get("confidence", 0.7)),
                processing_time_ms=0,  # Set by caller
                language_detected=data.get("language_detected", "en")
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}, response: {response[:200]}")
            return self._create_fallback_analysis(original_content, f"Parse error: {e}")
    
    def _create_fallback_analysis(self, email_content: str, error_reason: str) -> ConsolidatedAnalysis:
        """Create minimal safe analysis when LLM fails."""
        
        # Very conservative fallback - assume potentially unsafe
        return ConsolidatedAnalysis(
            toxicity_score=0.5,  # Medium caution
            threat_level=ThreatLevel.MEDIUM,
            safe=False,
            fact_ratio=0.5,
            communication_manner="unknown",
            personal_attacks=[],
            manipulation_tactics=[],
            implicit_threats=[],
            horsemen_detected=[],
            reasoning=f"LLM analysis failed: {error_reason}. Using conservative fallback.",
            confidence=0.3,
            processing_time_ms=0,
            language_detected="unknown"
        )
    
    def to_legacy_analysis_result(self, consolidated: ConsolidatedAnalysis) -> AnalysisResult:
        """Convert consolidated analysis to legacy AnalysisResult format for compatibility."""
        
        return AnalysisResult(
            safe=consolidated.safe,
            threat_level=consolidated.threat_level,
            toxicity_score=consolidated.toxicity_score,
            horsemen_detected=consolidated.horsemen_detected,
            reasoning=consolidated.reasoning,
            processing_time_ms=consolidated.processing_time_ms,
            cached=False
        )