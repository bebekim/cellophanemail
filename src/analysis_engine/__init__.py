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
from .rephraser import (
    build_rephrase_context,
    format_rephrased_with_notice,
    get_rephrase_instructions,
    estimate_rephrase_difficulty,
    should_attempt_rephrase,
    create_rephrase_summary,
)
from .mock import (
    MockAnalyzer,
    create_clean_analyzer,
    create_toxic_analyzer,
    create_graduated_analyzer,
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
    # Rephraser
    "build_rephrase_context",
    "format_rephrased_with_notice",
    "get_rephrase_instructions",
    "estimate_rephrase_difficulty",
    "should_attempt_rephrase",
    "create_rephrase_summary",
    # Mock
    "MockAnalyzer",
    "create_clean_analyzer",
    "create_toxic_analyzer",
    "create_graduated_analyzer",
]
