# ABOUTME: Content rephrasing logic for toxic message transformation
# ABOUTME: Used by Android app to show rephrased versions of toxic messages

from typing import Dict, List, Optional

from .types import AnalysisResult, ThreatLevel


def build_rephrase_context(analysis: AnalysisResult) -> Dict[str, str]:
    """
    Build context dictionary for rephrasing prompt.

    Args:
        analysis: The analysis result containing toxicity info

    Returns:
        Dict with threat_level, detected_patterns, and reasoning
    """
    return {
        "threat_level": analysis.threat_level.value,
        "detected_patterns": ", ".join(analysis.detected_horsemen_names) or "none",
        "reasoning": analysis.reasoning,
    }


def format_rephrased_with_notice(
    original: str,
    rephrased: str,
    analysis: AnalysisResult,
    include_archive_note: bool = True,
) -> str:
    """
    Format rephrased content with notice for user.

    Adds a clear header indicating the message was rephrased for wellbeing,
    includes detected patterns if any, and optionally notes that the
    original is archived.

    Args:
        original: The original toxic content (not included in output)
        rephrased: The rephrased, less toxic version
        analysis: Analysis result with detected patterns
        include_archive_note: Whether to add "Original archived" note

    Returns:
        Formatted message with rephrasing notice
    """
    patterns = analysis.detected_horsemen_names
    pattern_text = f" ({', '.join(patterns)})" if patterns else ""

    parts = [
        f"[This message was rephrased for your wellbeing{pattern_text}]",
        "",
        rephrased,
    ]

    if include_archive_note:
        parts.extend(["", "---", "Original message archived."])

    return "\n".join(parts)


def get_rephrase_instructions(analysis: AnalysisResult) -> List[str]:
    """
    Get specific rephrasing instructions based on detected horsemen.

    Returns tailored instructions for the LLM based on what patterns
    were detected in the original content.

    Args:
        analysis: Analysis result with detected patterns

    Returns:
        List of specific instructions for rephrasing
    """
    instructions = []

    horsemen_map = {
        "criticism": "Replace personal attacks with specific, constructive feedback about behavior",
        "contempt": "Remove mockery, sarcasm, and superiority; use respectful language",
        "defensiveness": "Remove blame-shifting and victim-playing; focus on facts",
        "stonewalling": "Add engagement and acknowledgment; remove dismissive language",
        "manipulation": "Remove guilt-tripping and emotional manipulation tactics",
        "harassment": "Remove hostile language and personal attacks",
        "deception": "Clarify misleading statements; present information honestly",
        "exploitation": "Remove exploitative tactics; present requests fairly",
    }

    for horseman in analysis.detected_horsemen_names:
        horseman_lower = horseman.lower()
        if horseman_lower in horsemen_map:
            instructions.append(horsemen_map[horseman_lower])

    # Add general instructions if no specific patterns detected
    if not instructions:
        instructions = [
            "Remove hostile or aggressive language",
            "Maintain factual content while improving tone",
            "Use respectful, professional language",
        ]

    return instructions


def estimate_rephrase_difficulty(analysis: AnalysisResult) -> str:
    """
    Estimate how difficult the rephrasing will be based on horsemen detected.

    Used to set expectations and potentially adjust LLM parameters.

    Args:
        analysis: Analysis result with horsemen info

    Returns:
        "easy", "moderate", or "difficult"
    """
    horsemen = analysis.detected_horsemen_names
    num_horsemen = len(horsemen)
    has_contempt = "contempt" in [h.lower() for h in horsemen]

    # Contempt is the hardest to rephrase (Gottman research)
    if has_contempt or num_horsemen >= 3:
        return "difficult"
    elif num_horsemen == 2:
        return "moderate"
    else:
        return "easy"


def should_attempt_rephrase(analysis: AnalysisResult) -> bool:
    """
    Determine if rephrasing should be attempted based on threat level.

    Very high toxicity content (CRITICAL) may be better blocked entirely.
    Safe content doesn't need rephrasing.

    Args:
        analysis: Analysis result with threat level info

    Returns:
        True if rephrasing should be attempted, False if blocking is better
    """
    # Don't attempt to rephrase CRITICAL content - should be blocked
    if analysis.threat_level == ThreatLevel.CRITICAL:
        return False

    # Don't attempt if content is SAFE (no need)
    if analysis.threat_level == ThreatLevel.SAFE:
        return False

    # Attempt rephrase for LOW, MEDIUM, and HIGH threat levels
    return True


def create_rephrase_summary(
    original_length: int,
    rephrased_length: int,
    analysis: AnalysisResult,
) -> Dict[str, any]:
    """
    Create a summary of the rephrasing operation.

    Useful for logging, analytics, and user feedback.

    Args:
        original_length: Character count of original content
        rephrased_length: Character count of rephrased content
        analysis: Analysis result

    Returns:
        Dict with summary statistics
    """
    return {
        "original_length": original_length,
        "rephrased_length": rephrased_length,
        "length_change_percent": round(
            ((rephrased_length - original_length) / original_length) * 100, 1
        )
        if original_length > 0
        else 0,
        "is_toxic": analysis.is_toxic,
        "threat_level": analysis.threat_level.value,
        "horsemen_detected": analysis.detected_horsemen_names,
        "difficulty": estimate_rephrase_difficulty(analysis),
    }
