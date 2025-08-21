"""
Configuration for Four Horsemen analysis weights and thresholds.
All parameters are tunable for optimization.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class HorsemanWeights:
    """Configurable weights for each horseman detection."""
    
    # Level 1: Criticism weights
    criticism_personal_attacks: float = 0.4
    criticism_primary_tactic: float = 0.3
    criticism_negative_manner: float = 0.2
    criticism_negative_ratio: float = 0.1
    criticism_overall_weight: float = 0.7
    
    # Level 2: Contempt weights
    contempt_sophistication: float = 0.3
    contempt_emotional_manipulation: float = 0.2
    contempt_manipulation_detected: float = 0.3
    contempt_emotional_loading: float = 0.2
    contempt_overall_weight: float = 0.85
    
    # Level 3: Defensiveness weights
    defensiveness_power_dynamics: float = 0.3
    defensiveness_authority_pattern: float = 0.2
    defensiveness_past_reference: float = 0.3
    defensiveness_gaslighting: float = 0.2
    defensiveness_overall_weight: float = 0.95
    
    # Detection thresholds
    detection_threshold: float = 0.3  # Minimum score to detect horseman
    severity_low_threshold: float = 0.4
    severity_medium_threshold: float = 0.5
    severity_high_threshold: float = 0.7
    
    # Toxicity calculation
    toxicity_normalization_factor: float = 3.0  # Divide by number of horsemen
    safety_threshold: float = 0.3  # Below this is considered safe
    
    # Threat level thresholds based on max level
    threat_level_criticism: int = 1  # Level 1 → LOW threat
    threat_level_contempt: int = 2   # Level 2 → MEDIUM threat
    threat_level_defensiveness: int = 3  # Level 3 → HIGH threat


@dataclass
class PhaseWeights:
    """Weights for how much each phase contributes to analysis."""
    
    # Phase contribution weights
    phase1_fact_ratio_weight: float = 0.15
    phase2_manner_weight: float = 0.25
    phase3_psychological_weight: float = 0.35
    phase4_implicit_weight: float = 0.25
    
    # Fact ratio impact
    low_fact_ratio_threshold: float = 0.2  # Below this indicates manipulation
    low_fact_ratio_penalty: float = 0.15   # Toxicity boost for low facts
    
    # Manner impact
    negative_manner_penalty: float = 0.1
    manipulation_detected_penalty: float = 0.2
    high_emotional_loading_penalty: float = 0.15
    
    # Non-factual content impact
    personal_attack_penalty: float = 0.05  # Per attack
    max_personal_attack_penalty: float = 0.3  # Cap total penalty
    
    # Implicit message impact
    implicit_threat_penalty: float = 0.1   # Per threat
    power_dynamic_penalty: float = 0.08
    emotional_hook_penalty: float = 0.06


@dataclass
class DecisionThresholds:
    """Thresholds for graduated decision system."""
    
    # Decision boundaries (toxicity scores)
    forward_clean_max: float = 0.2
    forward_with_context_max: float = 0.35
    redact_harmful_max: float = 0.5
    summarize_only_max: float = 0.7
    # Above 0.7 → BLOCK_ENTIRELY
    
    # Level-based decision modifiers
    criticism_decision_boost: float = 0.0   # No change for Level 1
    contempt_decision_boost: float = 0.15   # Push toward stricter action
    defensiveness_decision_boost: float = 0.3  # Strong push to block/summarize
    
    # Special case thresholds
    high_manipulation_threshold: float = 0.6  # Force at least REDACT
    multiple_horsemen_penalty: float = 0.1    # Per additional horseman


@dataclass
class AnalysisConfig:
    """Complete configuration for email protection analysis."""
    
    horseman_weights: HorsemanWeights
    phase_weights: PhaseWeights
    decision_thresholds: DecisionThresholds
    
    # Feature flags
    use_llm_analysis: bool = True
    use_pattern_fallback: bool = True
    enable_cross_validation: bool = True
    enable_cultural_context: bool = True
    
    # Performance tuning
    cache_ttl_minutes: int = 15
    max_content_length: int = 50000
    
    @classmethod
    def default(cls) -> "AnalysisConfig":
        """Create default configuration."""
        return cls(
            horseman_weights=HorsemanWeights(),
            phase_weights=PhaseWeights(),
            decision_thresholds=DecisionThresholds()
        )
    
    @classmethod
    def strict(cls) -> "AnalysisConfig":
        """Create strict configuration (more protective)."""
        config = cls.default()
        # Lower all thresholds for more aggressive protection
        config.horseman_weights.detection_threshold = 0.2
        config.horseman_weights.safety_threshold = 0.2
        config.decision_thresholds.forward_clean_max = 0.1
        config.decision_thresholds.forward_with_context_max = 0.25
        return config
    
    @classmethod
    def lenient(cls) -> "AnalysisConfig":
        """Create lenient configuration (less protective)."""
        config = cls.default()
        # Raise thresholds for less aggressive protection
        config.horseman_weights.detection_threshold = 0.4
        config.horseman_weights.safety_threshold = 0.4
        config.decision_thresholds.forward_clean_max = 0.3
        config.decision_thresholds.forward_with_context_max = 0.45
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization/optimization."""
        return {
            "horseman_weights": {
                k: v for k, v in self.horseman_weights.__dict__.items()
            },
            "phase_weights": {
                k: v for k, v in self.phase_weights.__dict__.items()
            },
            "decision_thresholds": {
                k: v for k, v in self.decision_thresholds.__dict__.items()
            },
            "use_llm_analysis": self.use_llm_analysis,
            "use_pattern_fallback": self.use_pattern_fallback,
            "enable_cross_validation": self.enable_cross_validation,
            "enable_cultural_context": self.enable_cultural_context,
            "cache_ttl_minutes": self.cache_ttl_minutes,
            "max_content_length": self.max_content_length
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisConfig":
        """Create from dictionary (for loading optimized configs)."""
        return cls(
            horseman_weights=HorsemanWeights(**data.get("horseman_weights", {})),
            phase_weights=PhaseWeights(**data.get("phase_weights", {})),
            decision_thresholds=DecisionThresholds(**data.get("decision_thresholds", {})),
            use_llm_analysis=data.get("use_llm_analysis", True),
            use_pattern_fallback=data.get("use_pattern_fallback", True),
            enable_cross_validation=data.get("enable_cross_validation", True),
            enable_cultural_context=data.get("enable_cultural_context", True),
            cache_ttl_minutes=data.get("cache_ttl_minutes", 15),
            max_content_length=data.get("max_content_length", 50000)
        )


# Default configurations for different use cases
DEFAULT_CONFIG = AnalysisConfig.default()
STRICT_CONFIG = AnalysisConfig.strict()
LENIENT_CONFIG = AnalysisConfig.lenient()