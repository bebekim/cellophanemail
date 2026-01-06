# ABOUTME: Portable Four Horseman analysis engine
# ABOUTME: Shared between CellophoneMail web and Android app

from .types import (
    ThreatLevel,
    HorsemanDetection,
    AnalysisResult,
    ProtectionResult,
)
from .scoring import (
    ProtectionAction,
    ProtectionDecision,
    DEFAULT_THRESHOLDS,
    decide_action,
    get_action_description,
)
from .analyzer import IAnalyzer
from .prompts import (
    ANALYSIS_PROMPT,
    REPHRASE_PROMPT,
    format_analysis_prompt,
    format_rephrase_prompt,
)

__all__ = [
    # Types
    "ThreatLevel",
    "HorsemanDetection",
    "AnalysisResult",
    "ProtectionResult",
    # Scoring
    "ProtectionAction",
    "ProtectionDecision",
    "DEFAULT_THRESHOLDS",
    "decide_action",
    "get_action_description",
    # Interface
    "IAnalyzer",
    # Prompts
    "ANALYSIS_PROMPT",
    "REPHRASE_PROMPT",
    "format_analysis_prompt",
    "format_rephrase_prompt",
]
