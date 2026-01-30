# ABOUTME: LLM prompts for Four Horseman analysis
# ABOUTME: Identical prompts ensure consistent analysis across platforms

ANALYSIS_PROMPT = """Analyze this content for the Four Horsemen of toxic communication.

CONTENT TO ANALYZE:
From: {sender}
Content: {content}

FOUR HORSEMEN DETECTION:
Detect each pattern with confidence (0.0-1.0) and severity (low/medium/high).
CONTEMPT is the MOST DESTRUCTIVE pattern - weight it heavily (Gottman research).

1. CRITICISM: Character attacks on who someone IS rather than specific behavior
   - "you always", "you never", personality attacks, blame for inherent flaws
   - NOT constructive feedback about specific actions

2. CONTEMPT: Superiority, mockery, disgust, sarcasm (MOST DESTRUCTIVE)
   - Eye-rolling language, name-calling, sneering, hostile humor
   - Treating others as inferior or beneath consideration

3. DEFENSIVENESS: Blame-shifting, victim-playing, counter-attacks
   - "It's not my fault", making excuses, deflecting responsibility
   - Reversing blame onto the other person

4. STONEWALLING: Withdrawal, silent treatment, refusing to engage
   - Shutting down, checking out, giving monosyllabic responses
   - Refusing to participate in discussion

RESPOND WITH VALID JSON ONLY:
{{
    "horsemen_detected": [
        {{
            "horseman": "criticism|contempt|defensiveness|stonewalling",
            "confidence": 0.0,
            "severity": "low|medium|high",
            "indicators": ["specific phrase or pattern"]
        }}
    ],
    "safe": true,
    "reasoning": "Detailed explanation of analysis"
}}"""


REPHRASE_PROMPT = """You are a communication expert who helps people express themselves constructively.

ORIGINAL MESSAGE:
{content}

ANALYSIS:
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
    detected_patterns: str,
    reasoning: str,
) -> str:
    """Format the rephrase prompt with analysis details."""
    return REPHRASE_PROMPT.format(
        content=content,
        detected_patterns=detected_patterns or "none",
        reasoning=reasoning,
    )
