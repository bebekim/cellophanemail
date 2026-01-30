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
    threat_level: ThreatLevel
    safe: bool

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
        self.model_name = "claude-sonnet-4-5-20250929"
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
            
            horsemen_names = [h.horseman for h in analysis.horsemen_detected]
            logger.info(f"Email analysis completed in {processing_time}ms, threat_level: {analysis.threat_level.value}, horsemen: {horsemen_names}")
            return analysis
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            # No heuristics fallback - re-raise the error
            raise RuntimeError(f"Email analysis failed, no fallback available: {e}")
    
    def _build_analysis_prompt(self, email_content: str, sender_email: str) -> str:
        """Build comprehensive analysis prompt for LLM."""

        return f"""Analyze this message for the Four Horsemen of toxic communication. Output ONLY valid JSON, no other text.

From: {sender_email}
Content: {email_content}

FOUR HORSEMEN (detect with confidence 0.0-1.0 and severity low/medium/high):
1. CRITICISM: Character attacks ("you always", "you never", personality flaws)
2. CONTEMPT: Superiority, mockery, disgust (MOST DESTRUCTIVE - weight heavily)
3. DEFENSIVENESS: Blame-shifting, victim-playing, counter-attacks
4. STONEWALLING: Withdrawal, silent treatment, refusing to engage

Output this exact JSON structure with your analysis:
{{"safe": true, "horsemen_detected": [{{"horseman": "criticism|contempt|defensiveness|stonewalling", "confidence": 0.0, "severity": "low|medium|high", "indicators": ["specific phrase"]}}], "reasoning": "explanation here", "confidence": 0.9, "language_detected": "en"}}"""

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
    
    def _extract_json(self, response: str) -> str:
        """Extract JSON from LLM response, handling markdown code blocks."""
        import re

        # Try to extract JSON from markdown code blocks
        # Match ```json ... ``` or ``` ... ```
        code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1)

        # Try to find raw JSON object
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json_match.group(0)

        # Return original if no JSON found
        return response

    def _parse_llm_response(self, response: str, original_content: str) -> EmailAnalysis:
        """Parse LLM JSON response into structured analysis."""
        from json_repair import repair_json

        try:
            # Extract JSON from potential markdown wrapping
            json_str = self._extract_json(response)
            # Repair common JSON syntax errors (missing commas, trailing commas, etc.)
            repaired_json = repair_json(json_str)
            data = json.loads(repaired_json)

            # Parse Four Horsemen detections (handle various formats)
            horsemen = []
            horsemen_data = data.get("horsemen_detected", [])
            if isinstance(horsemen_data, list):
                for h in horsemen_data:
                    if isinstance(h, dict):
                        # Full format: {"horseman": "criticism", "confidence": 0.8, ...}
                        horsemen.append(HorsemanDetection(
                            horseman=h.get("horseman", "unknown"),
                            confidence=float(h.get("confidence", 0.5)),
                            indicators=h.get("indicators", []),
                            severity=h.get("severity", "medium")
                        ))
                    elif isinstance(h, str) and h:
                        # Simple format: just the name like "criticism"
                        horsemen.append(HorsemanDetection(
                            horseman=h,
                            confidence=0.7,
                            indicators=[],
                            severity="medium"
                        ))

            # Derive threat level from horsemen (contempt-weighted)
            threat_level = ThreatLevel.from_horsemen(horsemen)

            # Determine safe flag based on threat level
            safe = threat_level == ThreatLevel.SAFE

            return EmailAnalysis(
                threat_level=threat_level,
                safe=safe,
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
            horsemen_detected=analysis.horsemen_detected,
            reasoning=analysis.reasoning,
            processing_time_ms=analysis.processing_time_ms,
            cached=False
        )