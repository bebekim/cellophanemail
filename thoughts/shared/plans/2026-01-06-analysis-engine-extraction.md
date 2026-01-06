# Analysis Engine Extraction Implementation Plan

## Overview

Extract the Four Horseman analysis engine from cellophanemail into a standalone, portable package that can be shared between:
1. **CellophoneMail Web** - Current SaaS email protection
2. **Android App** - SMS/email reading with toxicity analysis and rephrasing

This is a **minimal extraction**, not a full DDD restructuring. The goal is portability of the analysis logic only.

## Current State Analysis

### Files to Extract
Located in `src/cellophanemail/features/email_protection/`:

| File | Purpose | Portable? |
|------|---------|-----------|
| `models.py` | `ThreatLevel`, `HorsemanDetection`, `AnalysisResult`, `ProtectionResult` | Yes - pure dataclasses |
| `graduated_decision_maker.py` | `ProtectionAction`, `ProtectionDecision`, `GraduatedDecisionMaker` | Yes - pure Python |
| `analyzer_interface.py` | `IEmailAnalyzer` ABC | Yes - abstract interface |
| `consolidated_analyzer.py` | `ConsolidatedAnalysis`, `EmailToxicityLLMAnalyzer` | Partially - has LLM client deps |
| `llm_analyzer.py` | `SimpleLLMAnalyzer`, `MockLLMAnalyzer` | No - provider-specific |
| `ephemeral_email.py` | `EphemeralEmail` dataclass | Yes - pure dataclass |

### Key Discoveries

1. **Thresholds are configurable** (`graduated_decision_maker.py:46-59`):
   ```python
   self.thresholds = {
       'forward_clean': 0.30,
       'forward_context': 0.55,
       'redact_harmful': 0.70,
       'summarize_only': 0.90
   }
   ```

2. **Analyzer interface exists** (`analyzer_interface.py:12-30`):
   ```python
   class IEmailAnalyzer(ABC):
       @abstractmethod
       def analyze_email_toxicity(self, email_content: str, sender_email: str) -> 'EmailAnalysis'
   ```

3. **LLM prompt is embedded** in `consolidated_analyzer.py:107-170` - needs extraction

4. **No rephrasing logic exists yet** - must be added for Android app

## Desired End State

```
cellophanemail/
├── src/
│   ├── cellophanemail/           # Web app (unchanged structure)
│   │   └── features/email_protection/
│   │       └── ... (imports from analysis_engine)
│   │
│   └── analysis_engine/          # NEW: Portable package
│       ├── __init__.py
│       ├── types.py              # ThreatLevel, HorsemanDetection, AnalysisResult
│       ├── scoring.py            # ProtectionAction, thresholds, decide_action()
│       ├── prompts.py            # LLM prompts for analysis and rephrasing
│       ├── rephraser.py          # NEW: Rephrasing logic
│       └── analyzer.py           # IAnalyzer ABC (async interface)
```

### Verification
- [ ] `from analysis_engine import AnalysisResult, decide_action` works
- [ ] cellophanemail still functions with imports from analysis_engine
- [ ] analysis_engine has zero dependencies on cellophanemail
- [ ] analysis_engine has zero framework dependencies (no Litestar, Piccolo)
- [ ] All existing tests pass

## What We're NOT Doing

- Full DDD restructuring of cellophanemail
- Repository ports/adapters pattern
- Moving user/auth/billing code
- Changing the database layer
- Creating a separate Git repository (yet)

## Implementation Approach

Extract analysis logic into `src/analysis_engine/` as a sibling package to `src/cellophanemail/`. Both packages share the same `src/` directory, so imports work naturally. Later, `analysis_engine` can be extracted to its own repo if needed.

---

## Phase 1: Create analysis_engine Package Structure

### Overview
Create the new package with core types, moving and refactoring existing code.

### Changes Required:

#### 1. Create Package Structure
**File**: `src/analysis_engine/__init__.py`
```python
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
)
from .analyzer import IAnalyzer
from .prompts import ANALYSIS_PROMPT, REPHRASE_PROMPT

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
    # Interface
    "IAnalyzer",
    # Prompts
    "ANALYSIS_PROMPT",
    "REPHRASE_PROMPT",
]
```

#### 2. Extract Types
**File**: `src/analysis_engine/types.py`

Move and convert from `features/email_protection/models.py`:
- `ThreatLevel` enum
- `HorsemanDetection` dataclass (convert to Pydantic with `frozen=True`)
- `AnalysisResult` dataclass (convert to Pydantic with `frozen=True`)
- `ProtectionResult` dataclass

```python
# ABOUTME: Core types for Four Horseman analysis
# ABOUTME: Pure Pydantic models - no framework dependencies

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ThreatLevel(str, Enum):
    """Email threat level classification."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_score(cls, score: float) -> "ThreatLevel":
        """Derive threat level from toxicity score."""
        if score < 0.30:
            return cls.SAFE
        elif score < 0.55:
            return cls.LOW
        elif score < 0.70:
            return cls.MEDIUM
        elif score < 0.90:
            return cls.HIGH
        else:
            return cls.CRITICAL


class HorsemanDetection(BaseModel):
    """Detection of a specific horseman pattern."""
    horseman: str  # harassment, deception, exploitation, manipulation
    confidence: float = Field(..., ge=0.0, le=1.0)
    indicators: List[str] = Field(default_factory=list)
    severity: str  # low, medium, high

    model_config = {"frozen": True}

    @property
    def is_significant(self) -> bool:
        return self.confidence > 0.5


class AnalysisResult(BaseModel):
    """Result of Four Horseman analysis."""
    safe: bool
    threat_level: ThreatLevel
    toxicity_score: float = Field(..., ge=0.0, le=1.0)
    horsemen_detected: List[HorsemanDetection] = Field(default_factory=list)
    reasoning: str
    processing_time_ms: int
    cached: bool = False

    model_config = {"frozen": True}

    @property
    def detected_horsemen_names(self) -> List[str]:
        return [h.horseman for h in self.horsemen_detected if h.is_significant]


class ProtectionResult(BaseModel):
    """Final result of protection processing."""
    should_forward: bool
    analysis: Optional[AnalysisResult] = None
    block_reason: Optional[str] = None
    message_id: str
    protection_action: Optional[str] = None
    processed_content: Optional[str] = None
    decision_reasoning: Optional[str] = None
```

#### 3. Extract Scoring Logic
**File**: `src/analysis_engine/scoring.py`

Move from `graduated_decision_maker.py`:

```python
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


# Default thresholds - recalibrated 2025-08-23
DEFAULT_THRESHOLDS: Dict[str, float] = {
    'forward_clean': 0.30,
    'forward_context': 0.55,
    'redact_harmful': 0.70,
    'summarize_only': 0.90,
}


def decide_action(
    toxicity_score: float,
    thresholds: Optional[Dict[str, float]] = None
) -> ProtectionAction:
    """
    Determine protection action based on toxicity score.

    This is the core decision logic shared across all apps.
    """
    t = thresholds or DEFAULT_THRESHOLDS

    if toxicity_score < t['forward_clean']:
        return ProtectionAction.FORWARD_CLEAN
    elif toxicity_score < t['forward_context']:
        return ProtectionAction.FORWARD_WITH_CONTEXT
    elif toxicity_score < t['redact_harmful']:
        return ProtectionAction.REDACT_HARMFUL
    elif toxicity_score < t['summarize_only']:
        return ProtectionAction.SUMMARIZE_ONLY
    else:
        return ProtectionAction.BLOCK_ENTIRELY
```

#### 4. Extract Analyzer Interface
**File**: `src/analysis_engine/analyzer.py`

```python
# ABOUTME: Abstract analyzer interface for LLM backends
# ABOUTME: Implemented by Anthropic (cloud) and Llama (on-device)

from abc import ABC, abstractmethod
from .types import AnalysisResult


class IAnalyzer(ABC):
    """
    Abstract interface for content analysis.

    Implementations:
    - AnthropicAnalyzer (cloud API)
    - LlamaAnalyzer (on-device, Android)
    - MockAnalyzer (testing)
    """

    @abstractmethod
    async def analyze(self, content: str, sender: str = "") -> AnalysisResult:
        """
        Analyze content for Four Horseman patterns.

        Args:
            content: Text content to analyze (email body, SMS, etc.)
            sender: Optional sender identifier for context

        Returns:
            AnalysisResult with toxicity assessment
        """
        pass

    @abstractmethod
    async def rephrase(self, content: str, analysis: AnalysisResult) -> str:
        """
        Rephrase toxic content to be less harmful.

        Args:
            content: Original toxic content
            analysis: Analysis result with detected patterns

        Returns:
            Rephrased content with toxicity removed
        """
        pass
```

#### 5. Extract LLM Prompts
**File**: `src/analysis_engine/prompts.py`

```python
# ABOUTME: LLM prompts for Four Horseman analysis
# ABOUTME: Identical prompts ensure consistent analysis across platforms

ANALYSIS_PROMPT = '''You are an expert email safety analyzer. Analyze this content comprehensively and provide a detailed JSON assessment.

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
}}'''


REPHRASE_PROMPT = '''You are a communication expert who helps people express themselves constructively.

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

Respond with ONLY the rephrased message, no explanation.'''
```

### Success Criteria:

#### Automated Verification:
- [ ] Package imports work: `python -c "from analysis_engine import AnalysisResult, decide_action"`
- [ ] Type checking passes: `mypy src/analysis_engine/`
- [ ] No cellophanemail imports in analysis_engine: `grep -r "cellophanemail" src/analysis_engine/`

#### Manual Verification:
- [ ] Package structure matches plan
- [ ] All types have ABOUTME comments

---

## Phase 2: Update cellophanemail to Use analysis_engine

### Overview
Refactor cellophanemail's email_protection feature to import from analysis_engine instead of local definitions.

### Changes Required:

#### 1. Update models.py
**File**: `src/cellophanemail/features/email_protection/models.py`

Replace local definitions with imports:

```python
"""Models for email protection feature - re-exports from analysis_engine."""

# Re-export from portable analysis_engine
from analysis_engine import (
    ThreatLevel,
    HorsemanDetection,
    AnalysisResult,
    ProtectionResult,
)

# Keep any cellophanemail-specific extensions here if needed

__all__ = [
    "ThreatLevel",
    "HorsemanDetection",
    "AnalysisResult",
    "ProtectionResult",
]
```

#### 2. Update graduated_decision_maker.py
**File**: `src/cellophanemail/features/email_protection/graduated_decision_maker.py`

```python
"""Graduated Decision Maker - uses analysis_engine scoring."""

from analysis_engine import (
    ProtectionAction,
    ProtectionDecision,
    DEFAULT_THRESHOLDS,
    decide_action,
)
from analysis_engine.types import AnalysisResult

# Re-export for backwards compatibility
__all__ = [
    "ProtectionAction",
    "ProtectionDecision",
    "GraduatedDecisionMaker",
]


class GraduatedDecisionMaker:
    """
    Makes graduated protection decisions based on toxicity levels.
    Wraps analysis_engine scoring logic with content processing.
    """

    def __init__(self, thresholds=None):
        self.thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}

    def make_decision(self, analysis: AnalysisResult, original_content: str) -> ProtectionDecision:
        action = decide_action(analysis.toxicity_score, self.thresholds)

        # Content processing stays here (cellophanemail-specific)
        if action == ProtectionAction.FORWARD_CLEAN:
            processed_content = original_content
            reasoning = f"Clean content (toxicity: {analysis.toxicity_score:.3f})"
        elif action == ProtectionAction.FORWARD_WITH_CONTEXT:
            processed_content = self._add_context_notes(original_content, analysis)
            reasoning = f"Minor toxicity (toxicity: {analysis.toxicity_score:.3f})"
        # ... rest of processing logic

        return ProtectionDecision(
            action=action,
            processed_content=processed_content,
            reasoning=reasoning,
            toxicity_score=analysis.toxicity_score,
            original_analysis=analysis,
        )

    # Keep content processing methods (_add_context_notes, _redact_harmful_content, etc.)
```

#### 3. Update consolidated_analyzer.py
**File**: `src/cellophanemail/features/email_protection/consolidated_analyzer.py`

```python
"""Consolidated LLM analyzer - Anthropic implementation of IAnalyzer."""

from analysis_engine import IAnalyzer, AnalysisResult, HorsemanDetection, ThreatLevel
from analysis_engine.prompts import ANALYSIS_PROMPT, REPHRASE_PROMPT

# ... rest stays similar but uses imported prompts and types
```

### Success Criteria:

#### Automated Verification:
- [ ] All existing tests pass: `pytest tests/`
- [ ] Import check: `python -c "from cellophanemail.features.email_protection.models import AnalysisResult"`
- [ ] Type checking: `mypy src/cellophanemail/`

#### Manual Verification:
- [ ] cellophanemail web app starts without errors
- [ ] Email analysis still works end-to-end

---

## Phase 3: Add Rephrasing Logic

### Overview
Add rephrasing capability to analysis_engine for Android app use case.

### Changes Required:

#### 1. Create Rephraser Module
**File**: `src/analysis_engine/rephraser.py`

```python
# ABOUTME: Content rephrasing logic for toxic message transformation
# ABOUTME: Used by Android app to show rephrased versions of toxic messages

from typing import List
from .types import AnalysisResult, HorsemanDetection


def build_rephrase_context(analysis: AnalysisResult) -> dict:
    """Build context for rephrasing prompt."""
    return {
        "toxicity_score": f"{analysis.toxicity_score:.2f}",
        "detected_patterns": ", ".join(analysis.detected_horsemen_names) or "none",
        "reasoning": analysis.reasoning,
    }


def format_rephrased_with_notice(
    original: str,
    rephrased: str,
    analysis: AnalysisResult
) -> str:
    """
    Format rephrased content with notice for user.

    Returns message with clear indication it was rephrased.
    """
    patterns = analysis.detected_horsemen_names
    pattern_text = f" ({', '.join(patterns)})" if patterns else ""

    return f"""[This message was rephrased for your wellbeing{pattern_text}]

{rephrased}

---
Original message archived."""
```

#### 2. Update __init__.py exports
**File**: `src/analysis_engine/__init__.py`

Add:
```python
from .rephraser import build_rephrase_context, format_rephrased_with_notice
```

### Success Criteria:

#### Automated Verification:
- [ ] Import works: `python -c "from analysis_engine import build_rephrase_context"`
- [ ] Unit tests pass for rephraser

#### Manual Verification:
- [ ] Rephrased output includes notice
- [ ] Original meaning preserved in rephrasing

---

## Phase 4: Create Mock Analyzer for Testing

### Overview
Create MockAnalyzer implementing IAnalyzer for testing without LLM calls.

### Changes Required:

#### 1. Create Mock Implementation
**File**: `src/analysis_engine/mock.py`

```python
# ABOUTME: Mock analyzer for testing without LLM API calls
# ABOUTME: Configurable responses for different test scenarios

from typing import Optional, List
from .analyzer import IAnalyzer
from .types import AnalysisResult, ThreatLevel, HorsemanDetection


class MockAnalyzer(IAnalyzer):
    """Mock analyzer for testing."""

    def __init__(
        self,
        default_toxicity: float = 0.1,
        default_safe: bool = True,
        rephrase_prefix: str = "[Rephrased] ",
    ):
        self.default_toxicity = default_toxicity
        self.default_safe = default_safe
        self.rephrase_prefix = rephrase_prefix
        self.call_history: List[dict] = []

    async def analyze(self, content: str, sender: str = "") -> AnalysisResult:
        self.call_history.append({"method": "analyze", "content": content[:50]})

        return AnalysisResult(
            safe=self.default_safe,
            threat_level=ThreatLevel.SAFE if self.default_safe else ThreatLevel.MEDIUM,
            toxicity_score=self.default_toxicity,
            horsemen_detected=[],
            reasoning="Mock analysis",
            processing_time_ms=1,
        )

    async def rephrase(self, content: str, analysis: AnalysisResult) -> str:
        self.call_history.append({"method": "rephrase", "content": content[:50]})
        return f"{self.rephrase_prefix}{content}"
```

### Success Criteria:

#### Automated Verification:
- [ ] MockAnalyzer passes interface contract tests
- [ ] Can be used in cellophanemail tests

---

## Testing Strategy

### Unit Tests
- Test types validation (ThreatLevel.from_score, HorsemanDetection.is_significant)
- Test scoring logic (decide_action with various scores)
- Test prompt formatting

### Integration Tests
- Test cellophanemail still works with analysis_engine imports
- Test full analysis flow with MockAnalyzer

### Manual Testing Steps
1. Start cellophanemail web app
2. Send test email through webhook
3. Verify analysis and protection decision works
4. Check logs for any import errors

## Migration Notes

- No database changes required
- No API changes - this is internal refactoring
- Backwards compatibility maintained via re-exports
- Android app can import analysis_engine directly once extracted to separate repo

## References

- Research: `thoughts/shared/research/2026-01-06-ddd-multi-app-architecture-restructuring.md` (if created)
- Current code: `src/cellophanemail/features/email_protection/`
- Reference repos: `~/repositories/sumvibe`, `~/repositories/paymentreminder`
