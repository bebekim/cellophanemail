# ABOUTME: Protection decision logic and toxicity thresholds
# ABOUTME: Identical across all apps (web, Android)

from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel

from .types import AnalysisResult


class ProtectionAction(str, Enum):
    """Available protection actions."""

    FORWARD_CLEAN = "forward_clean"
    FORWARD_WITH_CONTEXT = "forward_with_context"
    REDACT_HARMFUL = "redact_harmful"
    SUMMARIZE_ONLY = "summarize_only"
    BLOCK_ENTIRELY = "block_entirely"


class ProtectionDecision(BaseModel):
    """Decision made by scoring logic."""

    action: ProtectionAction
    processed_content: str
    reasoning: str
    toxicity_score: float
    original_analysis: Optional[AnalysisResult] = None


# Default thresholds - recalibrated 2025-08-23 based on real LLM scoring patterns
DEFAULT_THRESHOLDS: Dict[str, float] = {
    "forward_clean": 0.30,  # Clean emails typically score 0.01-0.20
    "forward_context": 0.55,  # Minor toxicity emails score 0.35-0.50
    "redact_harmful": 0.70,  # Moderate toxicity emails score around 0.65
    "summarize_only": 0.90,  # High toxicity emails score 0.75-0.85
}


def decide_action(
    toxicity_score: float, thresholds: Optional[Dict[str, float]] = None
) -> ProtectionAction:
    """
    Determine protection action based on toxicity score.

    This is the core decision logic shared across all apps.

    Args:
        toxicity_score: Toxicity score from 0.0 to 1.0
        thresholds: Optional custom thresholds (uses DEFAULT_THRESHOLDS if None)

    Returns:
        ProtectionAction indicating how to handle the content
    """
    t = thresholds or DEFAULT_THRESHOLDS

    if toxicity_score < t["forward_clean"]:
        return ProtectionAction.FORWARD_CLEAN
    elif toxicity_score < t["forward_context"]:
        return ProtectionAction.FORWARD_WITH_CONTEXT
    elif toxicity_score < t["redact_harmful"]:
        return ProtectionAction.REDACT_HARMFUL
    elif toxicity_score < t["summarize_only"]:
        return ProtectionAction.SUMMARIZE_ONLY
    else:
        return ProtectionAction.BLOCK_ENTIRELY


def get_action_description(action: ProtectionAction) -> str:
    """Get human-readable description of a protection action."""
    descriptions = {
        ProtectionAction.FORWARD_CLEAN: "Forward as-is (safe content)",
        ProtectionAction.FORWARD_WITH_CONTEXT: "Forward with context notes",
        ProtectionAction.REDACT_HARMFUL: "Redact harmful content",
        ProtectionAction.SUMMARIZE_ONLY: "Provide factual summary only",
        ProtectionAction.BLOCK_ENTIRELY: "Block entirely (too toxic)",
    }
    return descriptions.get(action, "Unknown action")
