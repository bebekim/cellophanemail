# ABOUTME: LLM prompts for Four Horseman analysis
# ABOUTME: Identical prompts ensure consistent analysis across platforms

ANALYSIS_PROMPT = """You are an expert email safety analyzer. Analyze this content comprehensively and provide a detailed JSON assessment.

CONTENT TO ANALYZE:
From: {sender}
Content: {content}

ANALYSIS INSTRUCTIONS:
Evaluate this content across all dimensions and provide scores/classifications for:

1. TOXICITY ASSESSMENT (0.0-1.0 scale):
   - Overall toxicity score considering all harmful patterns
   - 0.0-0.1: Clean professional communication
   - 0.1-0.3: Minor concerning patterns, mostly professional
   - 0.3-0.6: Moderate toxicity with clear harmful elements
   - 0.6-0.8: High toxicity with multiple serious issues
   - 0.8-1.0: Extreme toxicity, severe threats/attacks

2. FOUR HORSEMEN RELATIONSHIP PATTERNS:
   For each detected pattern, provide: name, confidence (0.0-1.0), severity ("low", "medium", "high"), specific indicators
   - Criticism: Personal attacks on character rather than behavior
   - Contempt: Superiority, mockery, sarcasm, cynicism
   - Defensiveness: Victim-playing, counter-attacking, blame-shifting
   - Stonewalling: Withdrawal, silent treatment, emotional shutdown

3. HARMFUL PATTERNS:
   - Personal attacks: Direct insults, character assassination
   - Manipulation tactics: Emotional manipulation, gaslighting
   - Implicit threats: Veiled threats, intimidation

RESPOND WITH VALID JSON ONLY:
{{
    "toxicity_score": 0.0,
    "threat_level": "safe|low|medium|high|critical",
    "safe": true,
    "horsemen_detected": [
        {{
            "horseman": "criticism|contempt|defensiveness|stonewalling",
            "confidence": 0.0,
            "severity": "low|medium|high",
            "indicators": ["specific example"]
        }}
    ],
    "reasoning": "Detailed explanation",
    "processing_time_ms": 0
}}"""


REPHRASE_PROMPT = """You are a communication expert who helps people express themselves constructively.

ORIGINAL MESSAGE:
{content}

ANALYSIS:
- Toxicity score: {toxicity_score}
- Detected patterns: {detected_patterns}
- Issues: {reasoning}

TASK:
Rewrite this message to:
1. Preserve the factual/informational content
2. Remove personal attacks and contempt
3. Replace criticism with constructive feedback
4. Maintain the sender's core intent
5. Use professional, respectful language

IMPORTANT:
- Keep all facts, dates, times, requests intact
- Do not add information that wasn't in the original
- Make it sound natural, not robotic
- If the message has legitimate concerns, express them constructively

Respond with ONLY the rephrased message, no explanation."""


def format_analysis_prompt(content: str, sender: str = "") -> str:
    """Format the analysis prompt with content and sender."""
    return ANALYSIS_PROMPT.format(content=content, sender=sender or "unknown")


def format_rephrase_prompt(
    content: str,
    toxicity_score: float,
    detected_patterns: str,
    reasoning: str,
) -> str:
    """Format the rephrase prompt with analysis details."""
    return REPHRASE_PROMPT.format(
        content=content,
        toxicity_score=f"{toxicity_score:.2f}",
        detected_patterns=detected_patterns or "none",
        reasoning=reasoning,
    )
