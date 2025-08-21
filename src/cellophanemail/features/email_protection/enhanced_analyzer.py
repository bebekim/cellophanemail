"""
Enhanced Four Horsemen analyzer with configurable weights.
Integrates all 4 phases of shared context for sophisticated detection.
"""

import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

from .models import AnalysisResult, HorsemanDetection, ThreatLevel
from .analysis_config import AnalysisConfig, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class EnhancedFourHorsemenAnalyzer:
    """
    Enhanced analyzer using shared context and configurable weights.
    
    Progressive hierarchy:
    1. Criticism - Character attacks (Level 1)
    2. Contempt - Mockery, superiority (Level 2)
    3. Defensiveness - Blame deflection (Level 3)
    4. Stonewalling - Complete withdrawal (Level 4 - future)
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """Initialize with configuration."""
        self.config = config or DEFAULT_CONFIG
        self.weights = self.config.horseman_weights
        self.phase_weights = self.config.phase_weights
        self.decision_thresholds = self.config.decision_thresholds
    
    def analyze_with_context(self, content: str, sender: str, shared_context: Any) -> AnalysisResult:
        """
        Analyze using shared context from all 4 phases.
        All weights are configurable for optimization.
        """
        start_time = time.time()
        
        # Get phase results
        summary = shared_context.get_current_analysis_summary()
        phases = summary.get("phases", {})
        fact_ratio = summary.get("fact_ratio", 1.0)
        
        # Initialize scores
        detected_horsemen: List[HorsemanDetection] = []
        max_level = 0
        total_toxicity = 0.0
        
        # Level 1: CRITICISM Detection
        criticism_score = self._detect_criticism(phases)
        if criticism_score > self.weights.detection_threshold:
            detected_horsemen.append(HorsemanDetection(
                horseman="criticism",
                confidence=criticism_score,
                indicators=self._get_criticism_indicators(phases),
                severity=self._get_severity(criticism_score)
            ))
            max_level = max(max_level, 1)
            total_toxicity += criticism_score * self.weights.criticism_overall_weight
        
        # Level 2: CONTEMPT Detection
        contempt_score = self._detect_contempt(phases)
        if contempt_score > self.weights.detection_threshold:
            detected_horsemen.append(HorsemanDetection(
                horseman="contempt",
                confidence=contempt_score,
                indicators=self._get_contempt_indicators(phases),
                severity=self._get_severity(contempt_score)
            ))
            max_level = max(max_level, 2)
            total_toxicity += contempt_score * self.weights.contempt_overall_weight
        
        # Level 3: DEFENSIVENESS Detection
        defensiveness_score = self._detect_defensiveness(phases)
        if defensiveness_score > self.weights.detection_threshold:
            detected_horsemen.append(HorsemanDetection(
                horseman="defensiveness",
                confidence=defensiveness_score,
                indicators=self._get_defensiveness_indicators(phases),
                severity=self._get_severity(defensiveness_score)
            ))
            max_level = max(max_level, 3)
            total_toxicity += defensiveness_score * self.weights.defensiveness_overall_weight
        
        # Apply phase-based modifiers
        total_toxicity = self._apply_phase_modifiers(total_toxicity, phases, fact_ratio)
        
        # Normalize toxicity
        if len(detected_horsemen) > 0:
            total_toxicity = total_toxicity / self.weights.toxicity_normalization_factor
        
        # Apply multiple horsemen penalty
        if len(detected_horsemen) > 1:
            total_toxicity += (len(detected_horsemen) - 1) * self.decision_thresholds.multiple_horsemen_penalty
        
        # Cap at 1.0
        total_toxicity = min(total_toxicity, 1.0)
        
        # Determine threat level based on max horseman level
        threat_level = self._get_threat_level(max_level, total_toxicity)
        
        # Determine if safe
        safe = total_toxicity < self.weights.safety_threshold and max_level == 0
        
        # Build reasoning
        reasoning = self._build_reasoning(detected_horsemen, phases, max_level, fact_ratio)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return AnalysisResult(
            safe=safe,
            threat_level=threat_level,
            toxicity_score=total_toxicity,
            horsemen_detected=detected_horsemen,
            reasoning=reasoning,
            processing_time_ms=processing_time_ms,
            cached=False
        )
    
    def _detect_criticism(self, phases: Dict) -> float:
        """Detect Level 1: Criticism using configurable weights."""
        score = 0.0
        
        # Check Phase 3 non-factual analysis
        non_factual = phases.get("non_factual_analysis", {})
        if non_factual.get("personal_attacks"):
            score += self.weights.criticism_personal_attacks
        
        if non_factual.get("primary_tactic") in ["personal_attacks", "character_assassination", "none"]:
            if non_factual.get("primary_tactic") != "none":
                score += self.weights.criticism_primary_tactic
        
        # Check Phase 2 manner
        manner = phases.get("manner_summary", {})
        if str(manner.get("overall_manner", "")).lower() in ["predominantly_negative", "predominantly negative"]:
            score += self.weights.criticism_negative_manner
        
        if manner.get("negative_ratio", 0) > 0.5:
            score += self.weights.criticism_negative_ratio
        
        return min(score, 1.0)
    
    def _detect_contempt(self, phases: Dict) -> float:
        """Detect Level 2: Contempt using configurable weights."""
        score = 0.0
        
        # Check Phase 3 sophistication
        non_factual = phases.get("non_factual_analysis", {})
        if non_factual.get("manipulation_sophistication") == "high":
            score += self.weights.contempt_sophistication
        
        if non_factual.get("emotional_manipulation"):
            score += self.weights.contempt_emotional_manipulation
        
        # Check Phase 2 manipulation
        manner = phases.get("manner_summary", {})
        if manner.get("manipulation_detected"):
            score += self.weights.contempt_manipulation_detected
        
        if manner.get("emotional_loading") == "high":
            score += self.weights.contempt_emotional_loading
        
        return min(score, 1.0)
    
    def _detect_defensiveness(self, phases: Dict) -> float:
        """Detect Level 3: Defensiveness using configurable weights."""
        score = 0.0
        
        # Check Phase 4 implicit analysis
        implicit = phases.get("implicit_analysis", {})
        
        # Power dynamics
        if implicit.get("power_dynamics"):
            score += self.weights.defensiveness_power_dynamics
            
            # Check for specific patterns
            for item in implicit.get("power_dynamics", []):
                item_str = str(item).lower()
                if "authority" in item_str or "experienced" in item_str:
                    score += self.weights.defensiveness_authority_pattern
                    break
        
        # Past reference for blame
        if implicit.get("emotional_manipulation"):
            for item in implicit.get("emotional_manipulation", []):
                item_str = str(item).lower()
                if "past" in item_str or "reference" in item_str or "네 사례" in str(item):
                    score += self.weights.defensiveness_past_reference
                    break
        
        # Gaslighting patterns
        non_factual = phases.get("non_factual_analysis", {})
        if non_factual.get("gaslighting_patterns"):
            score += self.weights.defensiveness_gaslighting
        
        return min(score, 1.0)
    
    def _apply_phase_modifiers(self, base_toxicity: float, phases: Dict, fact_ratio: float) -> float:
        """Apply modifiers based on phase analysis results."""
        modified_toxicity = base_toxicity
        
        # Low fact ratio penalty
        if fact_ratio < self.phase_weights.low_fact_ratio_threshold:
            modified_toxicity += self.phase_weights.low_fact_ratio_penalty
        
        # Manner penalties
        manner = phases.get("manner_summary", {})
        if str(manner.get("overall_manner", "")).lower() in ["predominantly_negative", "predominantly negative"]:
            modified_toxicity += self.phase_weights.negative_manner_penalty
        
        if manner.get("manipulation_detected"):
            modified_toxicity += self.phase_weights.manipulation_detected_penalty
        
        if manner.get("emotional_loading") == "high":
            modified_toxicity += self.phase_weights.high_emotional_loading_penalty
        
        # Personal attack penalties
        non_factual = phases.get("non_factual_analysis", {})
        personal_attacks = len(non_factual.get("personal_attacks", []))
        if personal_attacks > 0:
            attack_penalty = min(
                personal_attacks * self.phase_weights.personal_attack_penalty,
                self.phase_weights.max_personal_attack_penalty
            )
            modified_toxicity += attack_penalty
        
        # Implicit threat penalties
        implicit = phases.get("implicit_analysis", {})
        implicit_threats = len(implicit.get("implicit_threats", []))
        if implicit_threats > 0:
            modified_toxicity += implicit_threats * self.phase_weights.implicit_threat_penalty
        
        if implicit.get("power_dynamics"):
            modified_toxicity += self.phase_weights.power_dynamic_penalty
        
        if implicit.get("emotional_manipulation"):
            modified_toxicity += self.phase_weights.emotional_hook_penalty
        
        return modified_toxicity
    
    def _get_severity(self, score: float) -> str:
        """Determine severity based on configurable thresholds."""
        if score > self.weights.severity_high_threshold:
            return "high"
        elif score > self.weights.severity_medium_threshold:
            return "medium"
        elif score > self.weights.severity_low_threshold:
            return "low"
        else:
            return "low"
    
    def _get_threat_level(self, max_level: int, toxicity: float) -> ThreatLevel:
        """Determine threat level based on horseman level and toxicity."""
        if max_level >= self.weights.threat_level_defensiveness:
            return ThreatLevel.HIGH
        elif max_level >= self.weights.threat_level_contempt:
            return ThreatLevel.MEDIUM
        elif max_level >= self.weights.threat_level_criticism:
            return ThreatLevel.LOW
        elif toxicity > 0.5:
            return ThreatLevel.MEDIUM
        elif toxicity > 0.3:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.SAFE
    
    def _get_criticism_indicators(self, phases: Dict) -> List[str]:
        """Extract criticism indicators."""
        indicators = []
        non_factual = phases.get("non_factual_analysis", {})
        
        if non_factual.get("personal_attacks"):
            attacks = non_factual["personal_attacks"][:3]
            indicators.extend([f"Personal attack: {attack}" for attack in attacks])
        
        manner = phases.get("manner_summary", {})
        if manner.get("negative_ratio", 0) > 0.5:
            indicators.append(f"Negative manner ratio: {manner['negative_ratio']:.1%}")
        
        return indicators
    
    def _get_contempt_indicators(self, phases: Dict) -> List[str]:
        """Extract contempt indicators."""
        indicators = []
        manner = phases.get("manner_summary", {})
        
        if manner.get("manipulation_detected"):
            indicators.append("Manipulation with emotional loading")
        
        non_factual = phases.get("non_factual_analysis", {})
        if non_factual.get("emotional_manipulation"):
            items = non_factual["emotional_manipulation"][:2]
            indicators.extend([f"Emotional: {item}" for item in items])
        
        if non_factual.get("manipulation_sophistication") == "high":
            indicators.append("High sophistication manipulation")
        
        return indicators
    
    def _get_defensiveness_indicators(self, phases: Dict) -> List[str]:
        """Extract defensiveness indicators."""
        indicators = []
        implicit = phases.get("implicit_analysis", {})
        
        if implicit.get("power_dynamics"):
            items = implicit["power_dynamics"][:2]
            indicators.extend([f"Power play: {item}" for item in items])
        
        if implicit.get("emotional_manipulation"):
            for item in implicit["emotional_manipulation"]:
                if "past" in str(item).lower() or "reference" in str(item).lower():
                    indicators.append(f"Using past: {item}")
                    break
        
        return indicators
    
    def _build_reasoning(self, detected_horsemen: List[HorsemanDetection], 
                        phases: Dict, max_level: int, fact_ratio: float) -> str:
        """Build detailed reasoning."""
        if not detected_horsemen:
            return "No harmful patterns detected in context analysis"
        
        level_names = {1: "Criticism", 2: "Contempt", 3: "Defensiveness"}
        horsemen_names = [h.horseman for h in detected_horsemen]
        
        reasoning = f"Level {max_level} ({level_names.get(max_level, 'Unknown')}) detected. "
        reasoning += f"Patterns: {', '.join(horsemen_names)}. "
        
        if fact_ratio < 0.2:
            reasoning += f"Low fact ratio ({fact_ratio:.1%}) indicates manipulation. "
        
        if max_level >= 3:
            reasoning += "Defensive blame patterns with past references detected. "
        elif max_level == 2:
            reasoning += "Contemptuous communication patterns present. "
        elif max_level == 1:
            reasoning += "Critical character attacks identified. "
        
        return reasoning