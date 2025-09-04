"""
Email toxicity analyzer that supports multiple LLM providers.
Currently uses Anthropic API, designed to easily switch to Llama later.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

from .models import ThreatLevel, HorsemanDetection, AnalysisResult
from .analyzer_interface import IEmailAnalyzer

logger = logging.getLogger(__name__)

# Load .env from project root, regardless of current working directory  
# Path: /Users/.../cellophanemail/src/cellophanemail/features/email_protection/email_toxicity_analyzer.py
# Go up: email_protection -> features -> cellophanemail -> src -> cellophanemail (project root)
project_root = Path(__file__).parent.parent.parent.parent.parent
env_file = project_root / ".env"
load_dotenv(dotenv_path=env_file)


@dataclass
class EmailAnalysis:
    """Complete email analysis result from LLM."""
    toxicity_score: float  # 0.0-1.0
    threat_level: ThreatLevel
    safe: bool
    
    # Content analysis
    fact_ratio: float
    communication_manner: str
    
    # Harmful patterns
    personal_attacks: List[str]
    manipulation_tactics: List[str] 
    implicit_threats: List[str]
    
    # Four Horsemen detection
    horsemen_detected: List[HorsemanDetection]
    
    # Analysis metadata
    reasoning: str
    confidence: float
    processing_time_ms: int
    language_detected: str = "en"


class EmailToxicityAnalyzer(IEmailAnalyzer):
    """
    Email toxicity analyzer supporting multiple LLM backends.
    
    Currently configured for Anthropic API with easy switching to Llama later.
    No heuristics fallback - uses LLM for all decisions.
    """
    
    def __init__(self, temperature: float = 0.0):
        """
        Initialize email toxicity analyzer.
        
        Args:
            temperature: LLM temperature (0.0 for deterministic results)
        """
        self.temperature = temperature
        self.client = None
        self.model_name = None
        self.provider = None
        
    def _setup_llm_client(self):
        """Setup LLM client - currently Anthropic, easily switchable to Llama."""
        if self.client is not None:
            return  # Already initialized
            
        # Currently using Anthropic API
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
            
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_name = "claude-3-5-sonnet-20241022"
        self.provider = "anthropic"
        
    def analyze_email_toxicity(self, email_content: str, sender_email: str) -> EmailAnalysis:
        """
        Analyze email for toxicity using LLM.
        
        Args:
            email_content: Full email content including subject and body
            sender_email: Email address of sender
            
        Returns:
            EmailAnalysis with comprehensive toxicity assessment
        """
        start_time = datetime.now()
        
        try:
            # Setup LLM client on first use (lazy initialization)
            self._setup_llm_client()
            
            # Build comprehensive analysis prompt
            prompt = self._build_analysis_prompt(email_content, sender_email)
            
            # Call LLM for analysis
            response = self._call_llm(prompt)
            
            # Parse LLM response into structured analysis
            analysis = self._parse_llm_response(response, email_content)
            
            # Set processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            analysis.processing_time_ms = processing_time
            
            logger.info(f"Email analysis completed in {processing_time}ms, toxicity: {analysis.toxicity_score:.3f}")
            return analysis
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            # No heuristics fallback - re-raise the error
            raise RuntimeError(f"Email analysis failed, no fallback available: {e}")
    
    def _build_analysis_prompt(self, email_content: str, sender_email: str) -> str:
        """Build comprehensive analysis prompt for LLM."""
        
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

    def _call_llm(self, prompt: str) -> str:
        """Call LLM API - currently Anthropic, easily switchable."""
        
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=800,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        else:
            # Future: Add Llama support here
            # elif self.provider == "llama":
            #     return self._call_llama(prompt)
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def _parse_llm_response(self, response: str, original_content: str) -> EmailAnalysis:
        """Parse LLM JSON response into structured analysis."""
        
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
            
            return EmailAnalysis(
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
            # No fallback - re-raise the error
            raise RuntimeError(f"LLM response parsing failed: {e}")

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
        prompt = f"""Analyze how this factual statement is presented in the email:

FULL EMAIL: {full_email_content}
FACT: "{fact_text}"
SENDER: {sender_email}

How is this fact presented?
- POSITIVE: Constructive, helpful, supportive
- NEUTRAL: Plain statement without emotion
- NEGATIVE: Destructive, attacking, manipulative

Consider context, tone, and intent.
Respond with one word: POSITIVE, NEUTRAL, or NEGATIVE"""

        try:
            # Setup LLM client on first use (lazy initialization)
            self._setup_llm_client()
            
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=10,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.content[0].text.strip().upper()
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
            
            # Validate and return
            if result in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
                return result.lower()
            else:
                logger.warning(f"Unexpected LLM response: {result}")
                raise RuntimeError(f"Invalid LLM response for fact analysis: {result}")
                
        except Exception as e:
            logger.error(f"Fact presentation analysis failed: {e}")
            # No fallback - re-raise the error
            raise RuntimeError(f"Fact presentation analysis failed: {e}")

    def to_legacy_analysis_result(self, analysis: EmailAnalysis) -> AnalysisResult:
        """Convert EmailAnalysis to legacy AnalysisResult format for compatibility."""
        
        return AnalysisResult(
            safe=analysis.safe,
            threat_level=analysis.threat_level,
            toxicity_score=analysis.toxicity_score,
            horsemen_detected=analysis.horsemen_detected,
            reasoning=analysis.reasoning,
            processing_time_ms=analysis.processing_time_ms,
            cached=False
        )