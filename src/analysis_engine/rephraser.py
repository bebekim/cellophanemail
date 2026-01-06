# ABOUTME: Content rephrasing logic for toxic message transformation
# ABOUTME: Used by Android app to show rephrased versions of toxic messages

from typing import Dict, List, Optional

from .types import AnalysisResult


def build_rephrase_context(analysis: AnalysisResult) -> Dict[str, str]:
    """
    Build context dictionary for rephrasing prompt.

    Args:
        analysis: The analysis result containing toxicity info

    Returns:
        Dict with toxicity_score, detected_patterns, and reasoning
    """
    return {
        "toxicity_score": f"{analysis.toxicity_score:.2f}",
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
    Estimate how difficult the rephrasing will be.

    Used to set expectations and potentially adjust LLM parameters.

    Args:
        analysis: Analysis result with toxicity info

    Returns:
        "easy", "moderate", or "difficult"
    """
    score = analysis.toxicity_score
    num_horsemen = len(analysis.detected_horsemen_names)

    if score < 0.4 and num_horsemen <= 1:
        return "easy"
    elif score < 0.7 and num_horsemen <= 2:
        return "moderate"
    else:
        return "difficult"


def should_attempt_rephrase(analysis: AnalysisResult) -> bool:
    """
    Determine if rephrasing should be attempted.

    Very high toxicity content may be better blocked entirely rather
    than attempting to rephrase.

    Args:
        analysis: Analysis result with toxicity info

    Returns:
        True if rephrasing should be attempted, False if blocking is better
    """
    # Don't attempt to rephrase extremely toxic content
    if analysis.toxicity_score >= 0.90:
        return False

    # Don't attempt if content is safe (no need)
    if analysis.toxicity_score < 0.30:
        return False

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
        "toxicity_score": analysis.toxicity_score,
        "horsemen_detected": analysis.detected_horsemen_names,
        "difficulty": estimate_rephrase_difficulty(analysis),
    }
