"""Four Horsemen content analysis - self-contained implementation."""

import logging
import time
import hashlib
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from .models import AnalysisResult, HorsemanDetection, ThreatLevel

logger = logging.getLogger(__name__)


class FourHorsemenAnalyzer:
    """
    Enhanced analyzer for the Four Horsemen of relationship destruction.
    Now integrates shared context from all 4 phases for sophisticated detection.
    
    Progressive hierarchy (Gottman's research):
    1. Criticism - Attacks on character (Level 1)
    2. Contempt - Mockery, disgust, superiority (Level 2) 
    3. Defensiveness - Blame deflection, playing victim (Level 3)
    4. Stonewalling - Complete withdrawal (Level 4 - requires longitudinal)
    """
    
    def __init__(self):
        # Simple in-memory cache for demo purposes
        # In production, this would use Redis or similar
        self._cache: Dict[str, AnalysisResult] = {}
        self._cache_ttl = timedelta(minutes=15)
        
        # Progressive Four Horsemen indicators (Level 1-3)
        self.horseman_indicators = {
            "criticism": {  # Level 1 - Character attacks
                "phase_sources": ["fact_manner", "non_factual"],
                "indicators": ["personal_attacks", "character_assassination"],
                "weight": 0.7,
                "level": 1
            },
            "contempt": {  # Level 2 - Mockery, disgust, superiority
                "phase_sources": ["manner_summary", "non_factual"],
                "indicators": ["mockery", "sarcasm", "disgust", "name_calling"],
                "weight": 0.85,
                "level": 2
            },
            "defensiveness": {  # Level 3 - Blame deflection, victim playing
                "phase_sources": ["implicit_analysis", "non_factual"],
                "indicators": ["blame_shifting", "victim_playing", "deflection"],
                "weight": 0.95,
                "level": 3
            },
            # Stonewalling (Level 4) reserved for longitudinal analysis
        }
    
    def _get_cache_key(self, content: str, sender: str) -> str:
        """Generate cache key for content."""
        combined = f"{sender}:{content}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _check_cache(self, cache_key: str) -> Optional[AnalysisResult]:
        """Check if we have a cached analysis."""
        if cache_key in self._cache:
            result = self._cache[cache_key]
            # Check if cache is still valid
            # For simplicity, we're not storing timestamps in this demo
            result.cached = True
            return result
        return None
    
    def analyze(self, content: str, sender: str = "", shared_context: Optional[Any] = None) -> AnalysisResult:
        """
        Analyze email content for harmful patterns.
        
        This is a simplified version for demonstration.
        In production, this would use OpenAI/Anthropic API for sophisticated analysis.
        """
        start_time = time.time()
        
        # Check cache first
        cache_key = self._get_cache_key(content, sender)
        cached_result = self._check_cache(cache_key)
        if cached_result:
            logger.info(f"Using cached analysis for {cache_key[:8]}...")
            return cached_result
        
        # Analyze content
        content_lower = content.lower()
        detected_horsemen: List[HorsemanDetection] = []
        total_score = 0.0
        max_severity = "low"
        
        for horseman, config in self.horseman_indicators.items():
            indicators_found = []
            confidence = 0.0
            
            # Check keywords
            for keyword in config["keywords"]:
                if keyword in content_lower:
                    indicators_found.append(f"Keyword: {keyword}")
                    confidence += 0.3
            
            # Check patterns (simplified - in production would use regex)
            for pattern in config["patterns"]:
                # Simple pattern matching for demo
                pattern_words = pattern.replace(".*", " ").split()
                if all(word in content_lower for word in pattern_words):
                    indicators_found.append(f"Pattern: {pattern}")
                    confidence += 0.5
            
            if indicators_found:
                confidence = min(confidence, 1.0)  # Cap at 1.0
                severity = "high" if confidence > 0.7 else "medium" if confidence > 0.4 else "low"
                
                if severity == "high":
                    max_severity = "high"
                elif severity == "medium" and max_severity != "high":
                    max_severity = "medium"
                
                detected_horsemen.append(HorsemanDetection(
                    horseman=horseman,
                    confidence=confidence,
                    indicators=indicators_found,
                    severity=severity
                ))
                
                total_score += confidence * config["weight"]
        
        # Normalize toxicity score
        toxicity_score = min(total_score / len(self.horseman_indicators), 1.0)
        
        # Determine if safe
        safe = toxicity_score < 0.3 and max_severity != "high"
        
        # Determine threat level
        if toxicity_score > 0.7 or max_severity == "high":
            threat_level = ThreatLevel.HIGH
        elif toxicity_score > 0.5:
            threat_level = ThreatLevel.MEDIUM
        elif toxicity_score > 0.3:
            threat_level = ThreatLevel.LOW
        else:
            threat_level = ThreatLevel.SAFE
        
        # Build reasoning
        if detected_horsemen:
            horsemen_names = [h.horseman for h in detected_horsemen]
            reasoning = f"Detected {', '.join(horsemen_names)} patterns in content"
        else:
            reasoning = "No harmful patterns detected"
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        result = AnalysisResult(
            safe=safe,
            threat_level=threat_level,
            toxicity_score=toxicity_score,
            horsemen_detected=detected_horsemen,
            reasoning=reasoning,
            processing_time_ms=processing_time_ms,
            cached=False
        )
        
        # Cache the result
        self._cache[cache_key] = result
        
        logger.info(f"Analysis complete: safe={safe}, threat_level={threat_level.value}, "
                   f"toxicity={toxicity_score:.2f}, time={processing_time_ms}ms")
        
        return result