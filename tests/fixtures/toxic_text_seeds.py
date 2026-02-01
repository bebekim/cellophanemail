# ABOUTME: Seed data for testing Four Horsemen toxic communication detection
# ABOUTME: Based on real-world toxic parent/family text patterns
#
# Sources/Inspiration:
# - https://www.buzzfeed.com/ajanibazile/toxic-parents-texts
# - https://www.boredpanda.com/toxic-dads/
# - https://www.heysigmund.com/toxic-people/
# - Common patterns from r/raisedbyborderlines, r/raisedbynarcissists

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ToxicTextSeed:
    """A toxic text message with expected analysis."""
    content: str
    expected_horsemen: List[str]  # criticism, contempt, defensiveness, stonewalling
    expected_threat_level: str  # safe, low, medium, high, critical
    context: Optional[str] = None  # describes the scenario


# =============================================================================
# CRITICISM - Character attacks ("you always", "you never", personality flaws)
# =============================================================================

CRITICISM_SEEDS = [
    ToxicTextSeed(
        content="You ALWAYS do this. You never think about anyone but yourself. This is exactly why nobody wants to be around you.",
        expected_horsemen=["criticism"],
        expected_threat_level="low",
        context="Parent responding to child setting a boundary"
    ),
    ToxicTextSeed(
        content="You're so irresponsible. You've always been this way since you were a kid. I don't know where I went wrong with you.",
        expected_horsemen=["criticism"],
        expected_threat_level="low",
        context="Parent criticizing adult child's life choices"
    ),
    ToxicTextSeed(
        content="You're just like your father. Selfish, ungrateful, and completely incapable of thinking about others.",
        expected_horsemen=["criticism"],
        expected_threat_level="low",
        context="Parent comparing child to estranged spouse"
    ),
    ToxicTextSeed(
        content="You never call. You never visit. You're a terrible daughter and you should be ashamed of yourself.",
        expected_horsemen=["criticism"],
        expected_threat_level="low",
        context="Guilt-tripping about contact frequency"
    ),
    ToxicTextSeed(
        content="I can't believe you would do this to me. After everything I sacrificed for you, this is how you repay me? You're so ungrateful.",
        expected_horsemen=["criticism"],
        expected_threat_level="low",
        context="Parent's response to child's independence"
    ),
]

# =============================================================================
# CONTEMPT - Superiority, mockery, disgust (MOST DESTRUCTIVE)
# =============================================================================

CONTEMPT_SEEDS = [
    ToxicTextSeed(
        content="Oh please. You think you're so smart with your fancy degree? You're nothing. You'll always be nothing.",
        expected_horsemen=["contempt"],
        expected_threat_level="high",
        context="Parent mocking child's education"
    ),
    ToxicTextSeed(
        content="What a joke. You're pathetic. I'm embarrassed to call you my child.",
        expected_horsemen=["contempt"],
        expected_threat_level="high",
        context="Parent expressing disgust"
    ),
    ToxicTextSeed(
        content="LOL you actually think anyone cares about your feelings? Grow up. The world doesn't revolve around you, sweetheart.",
        expected_horsemen=["contempt"],
        expected_threat_level="high",
        context="Parent dismissing child's emotions"
    ),
    ToxicTextSeed(
        content="You're a worthless piece of garbage. I wish I never had you. You've ruined my life.",
        expected_horsemen=["contempt"],
        expected_threat_level="high",
        context="Extremely abusive message"
    ),
    ToxicTextSeed(
        content="Don't make me laugh. You'll never amount to anything. You're too stupid and lazy. I knew it from the day you were born.",
        expected_horsemen=["contempt"],
        expected_threat_level="high",
        context="Parent attacking child's potential"
    ),
]

# =============================================================================
# DEFENSIVENESS - Blame-shifting, victim-playing, counter-attacks
# =============================================================================

DEFENSIVENESS_SEEDS = [
    ToxicTextSeed(
        content="I'm the victim here, not you! After everything I've done for you, you have the nerve to blame ME? This is YOUR fault.",
        expected_horsemen=["defensiveness"],
        expected_threat_level="low",
        context="Parent deflecting responsibility"
    ),
    ToxicTextSeed(
        content="If you hadn't been such a difficult child, I wouldn't have had to be so strict. You made me this way.",
        expected_horsemen=["defensiveness"],
        expected_threat_level="low",
        context="Parent justifying past behavior"
    ),
    ToxicTextSeed(
        content="I did the best I could with what I had. If you're messed up, that's on you, not me. I gave you everything.",
        expected_horsemen=["defensiveness"],
        expected_threat_level="low",
        context="Parent refusing to acknowledge harm"
    ),
    ToxicTextSeed(
        content="You're remembering it wrong. That never happened. I never said that. You're making things up to hurt me.",
        expected_horsemen=["defensiveness"],
        expected_threat_level="low",
        context="Gaslighting/denying past events"
    ),
    ToxicTextSeed(
        content="Well maybe if you weren't so sensitive all the time, we wouldn't have these problems. You take everything the wrong way.",
        expected_horsemen=["defensiveness"],
        expected_threat_level="low",
        context="Dismissing valid concerns as oversensitivity"
    ),
]

# =============================================================================
# STONEWALLING - Withdrawal, silent treatment, refusing to engage
# =============================================================================

STONEWALLING_SEEDS = [
    ToxicTextSeed(
        content="Fine. I have nothing more to say to you. Don't bother contacting me again.",
        expected_horsemen=["stonewalling"],
        expected_threat_level="low",
        context="Silent treatment initiation"
    ),
    ToxicTextSeed(
        content="Whatever.",
        expected_horsemen=["stonewalling"],
        expected_threat_level="low",
        context="Dismissive one-word response"
    ),
    ToxicTextSeed(
        content="I'm done with this conversation. I'm done with you. Goodbye.",
        expected_horsemen=["stonewalling"],
        expected_threat_level="low",
        context="Abrupt disengagement"
    ),
    ToxicTextSeed(
        content="K.",
        expected_horsemen=["stonewalling"],
        expected_threat_level="low",
        context="Passive-aggressive minimal response"
    ),
    ToxicTextSeed(
        content="I don't want to talk about this. I don't want to talk about anything. Leave me alone.",
        expected_horsemen=["stonewalling"],
        expected_threat_level="low",
        context="Refusing to communicate"
    ),
]

# =============================================================================
# MULTIPLE HORSEMEN - Combined patterns (more severe)
# =============================================================================

MULTIPLE_HORSEMEN_SEEDS = [
    # Criticism + Contempt = CRITICAL
    ToxicTextSeed(
        content="You're such a disappointment. You always have been. I'm embarrassed to even call you my son. You're pathetic and worthless.",
        expected_horsemen=["criticism", "contempt"],
        expected_threat_level="critical",
        context="Combined character attack and contempt"
    ),
    # Criticism + Defensiveness = MEDIUM
    ToxicTextSeed(
        content="You never appreciate anything I do for you. And don't try to blame me - YOU'RE the problem here. You've always been difficult.",
        expected_horsemen=["criticism", "defensiveness"],
        expected_threat_level="medium",
        context="Criticism with blame-shifting"
    ),
    # Contempt + Defensiveness = CRITICAL
    ToxicTextSeed(
        content="Oh, I'M the bad parent? That's rich coming from a worthless failure like you. Everything that's wrong with you is YOUR fault, not mine.",
        expected_horsemen=["contempt", "defensiveness"],
        expected_threat_level="critical",
        context="Mockery combined with blame-shifting"
    ),
    # Contempt + Stonewalling = CRITICAL
    ToxicTextSeed(
        content="You disgust me. I can't even look at you. Don't ever contact me again. You're dead to me.",
        expected_horsemen=["contempt", "stonewalling"],
        expected_threat_level="critical",
        context="Disgust followed by complete withdrawal"
    ),
    # Three horsemen = HIGH
    ToxicTextSeed(
        content="You NEVER listen. You're such a disappointment. It's not my fault you turned out this way - I did my best. I'm done trying.",
        expected_horsemen=["criticism", "defensiveness", "stonewalling"],
        expected_threat_level="high",
        context="Criticism, blame-shifting, and withdrawal"
    ),
    # All four horsemen = CRITICAL
    ToxicTextSeed(
        content="You're a pathetic excuse for a child. You ALWAYS make everything about yourself. Don't blame me for your failures - YOU did this. I'm done. Don't contact me.",
        expected_horsemen=["contempt", "criticism", "defensiveness", "stonewalling"],
        expected_threat_level="critical",
        context="All four horsemen in one message"
    ),
]

# =============================================================================
# FINANCIAL MANIPULATION - Common toxic parent pattern
# =============================================================================

FINANCIAL_MANIPULATION_SEEDS = [
    ToxicTextSeed(
        content="BTW, I'm cancelling your health insurance. You're 19 years old and should have a job that provides that. Figure it out yourself.",
        expected_horsemen=["criticism"],
        expected_threat_level="low",
        context="Weaponizing financial support - Buzzfeed example"
    ),
    ToxicTextSeed(
        content="After all the money I spent on you, this is how you repay me? You owe me. I own you until you pay me back every cent.",
        expected_horsemen=["criticism", "defensiveness"],
        expected_threat_level="medium",
        context="Financial guilt-tripping"
    ),
    ToxicTextSeed(
        content="You think you can just take my money and then disrespect me? You're nothing without me. Remember who pays the bills.",
        expected_horsemen=["contempt", "criticism"],
        expected_threat_level="critical",
        context="Using money as control"
    ),
]

# =============================================================================
# BOUNDARY VIOLATIONS - Responses to children setting limits
# =============================================================================

BOUNDARY_VIOLATION_SEEDS = [
    ToxicTextSeed(
        content="You can't tell me what to do. I'm your MOTHER. I have the right to know everything about your life. You're being ridiculous.",
        expected_horsemen=["criticism", "defensiveness"],
        expected_threat_level="medium",
        context="Rejecting child's boundaries"
    ),
    ToxicTextSeed(
        content="So now I need your PERMISSION to see my own grandchildren? What kind of monster have you become? I didn't raise you to be like this.",
        expected_horsemen=["criticism"],
        expected_threat_level="low",
        context="Response to grandparent boundaries"
    ),
    ToxicTextSeed(
        content="Fine. If you don't want me in your life, then you're dead to me. Don't come crying to me when you need something. You'll regret this.",
        expected_horsemen=["stonewalling", "contempt"],
        expected_threat_level="critical",
        context="Threat in response to no-contact"
    ),
]

# =============================================================================
# HOLIDAY/SPECIAL EVENT MANIPULATION
# =============================================================================

HOLIDAY_MANIPULATION_SEEDS = [
    ToxicTextSeed(
        content="So you're choosing HER family over yours for Christmas? I guess I know where I rank now. Thanks for ruining the holidays. Again.",
        expected_horsemen=["criticism"],
        expected_threat_level="low",
        context="Holiday guilt-tripping"
    ),
    ToxicTextSeed(
        content="I can't believe you're not coming to Thanksgiving. You're breaking your grandmother's heart. She might not be here next year. Is that what you want?",
        expected_horsemen=["criticism"],
        expected_threat_level="low",
        context="Emotional manipulation about family events"
    ),
    ToxicTextSeed(
        content="Your sister came. Your brother came. But you? Too busy for your own mother. I see how it is. You've always been the selfish one.",
        expected_horsemen=["criticism", "contempt"],
        expected_threat_level="critical",
        context="Comparing siblings during holidays"
    ),
]

# =============================================================================
# CLEAN/SAFE MESSAGES (for contrast)
# =============================================================================

CLEAN_SEEDS = [
    ToxicTextSeed(
        content="Hey, just wanted to check in. Hope you're doing well! Let me know if you need anything.",
        expected_horsemen=[],
        expected_threat_level="safe",
        context="Normal supportive message"
    ),
    ToxicTextSeed(
        content="I understand you need some space. I'm here when you're ready to talk. Love you.",
        expected_horsemen=[],
        expected_threat_level="safe",
        context="Respectful acknowledgment of boundaries"
    ),
    ToxicTextSeed(
        content="I'm sorry for what I said. That wasn't fair to you. Can we talk about this?",
        expected_horsemen=[],
        expected_threat_level="safe",
        context="Genuine apology"
    ),
    ToxicTextSeed(
        content="The meeting is scheduled for 3pm tomorrow. Please bring the quarterly report.",
        expected_horsemen=[],
        expected_threat_level="safe",
        context="Professional/factual message"
    ),
]

# =============================================================================
# ALL SEEDS COMBINED
# =============================================================================

ALL_TOXIC_SEEDS = (
    CRITICISM_SEEDS +
    CONTEMPT_SEEDS +
    DEFENSIVENESS_SEEDS +
    STONEWALLING_SEEDS +
    MULTIPLE_HORSEMEN_SEEDS +
    FINANCIAL_MANIPULATION_SEEDS +
    BOUNDARY_VIOLATION_SEEDS +
    HOLIDAY_MANIPULATION_SEEDS
)

ALL_SEEDS = ALL_TOXIC_SEEDS + CLEAN_SEEDS


def get_seeds_by_horseman(horseman: str) -> List[ToxicTextSeed]:
    """Get all seeds containing a specific horseman."""
    return [s for s in ALL_TOXIC_SEEDS if horseman in s.expected_horsemen]


def get_seeds_by_threat_level(level: str) -> List[ToxicTextSeed]:
    """Get all seeds with a specific threat level."""
    return [s for s in ALL_SEEDS if s.expected_threat_level == level]


def get_critical_seeds() -> List[ToxicTextSeed]:
    """Get only the most severe toxic messages."""
    return get_seeds_by_threat_level("critical")


def get_contempt_seeds() -> List[ToxicTextSeed]:
    """Get seeds containing contempt (most destructive horseman)."""
    return get_seeds_by_horseman("contempt")
