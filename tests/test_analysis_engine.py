# ABOUTME: Unit tests for the portable analysis_engine package
# ABOUTME: Tests types.py and scoring.py independently of cellophanemail

import pytest

from analysis_engine import (
    # Types
    ThreatLevel,
    HorsemanDetection,
    AnalysisResult,
    ProtectionResult,
    # Scoring
    ProtectionAction,
    ProtectionDecision,
    decide_action,
    get_action_description,
    # Prompts
    format_analysis_prompt,
    format_rephrase_prompt,
)


class TestThreatLevel:
    """Tests for ThreatLevel enum and from_horsemen method."""

    def test_threat_level_values(self):
        """Verify all threat level values exist."""
        assert ThreatLevel.SAFE == "safe"
        assert ThreatLevel.LOW == "low"
        assert ThreatLevel.MEDIUM == "medium"
        assert ThreatLevel.HIGH == "high"
        assert ThreatLevel.CRITICAL == "critical"

    def test_from_horsemen_safe_no_horsemen(self):
        """No horsemen detected should be SAFE."""
        assert ThreatLevel.from_horsemen([]) == ThreatLevel.SAFE

    def test_from_horsemen_safe_insignificant_horsemen(self):
        """Only insignificant horsemen (confidence <= 0.5) should be SAFE."""
        horsemen = [
            HorsemanDetection(
                horseman="criticism",
                confidence=0.3,  # Below significance threshold
                indicators=["minor complaint"],
                severity="low",
            ),
        ]
        assert ThreatLevel.from_horsemen(horsemen) == ThreatLevel.SAFE

    def test_from_horsemen_low_single_non_contempt(self):
        """Single non-contempt horseman should be LOW."""
        horsemen = [
            HorsemanDetection(
                horseman="criticism",
                confidence=0.6,
                indicators=["character attack"],
                severity="medium",
            ),
        ]
        assert ThreatLevel.from_horsemen(horsemen) == ThreatLevel.LOW

    def test_from_horsemen_medium_two_non_contempt(self):
        """Two non-contempt horsemen should be MEDIUM."""
        horsemen = [
            HorsemanDetection(
                horseman="criticism",
                confidence=0.7,
                indicators=["attack"],
                severity="medium",
            ),
            HorsemanDetection(
                horseman="defensiveness",
                confidence=0.6,
                indicators=["blame-shifting"],
                severity="medium",
            ),
        ]
        assert ThreatLevel.from_horsemen(horsemen) == ThreatLevel.MEDIUM

    def test_from_horsemen_high_contempt_alone(self):
        """Contempt alone should be HIGH."""
        horsemen = [
            HorsemanDetection(
                horseman="contempt",
                confidence=0.8,
                indicators=["mockery", "superiority"],
                severity="high",
            ),
        ]
        assert ThreatLevel.from_horsemen(horsemen) == ThreatLevel.HIGH

    def test_from_horsemen_high_three_non_contempt(self):
        """Three non-contempt horsemen should be HIGH."""
        horsemen = [
            HorsemanDetection(horseman="criticism", confidence=0.7, indicators=["attack"], severity="medium"),
            HorsemanDetection(horseman="defensiveness", confidence=0.6, indicators=["blame"], severity="medium"),
            HorsemanDetection(horseman="stonewalling", confidence=0.6, indicators=["withdrawal"], severity="medium"),
        ]
        assert ThreatLevel.from_horsemen(horsemen) == ThreatLevel.HIGH

    def test_from_horsemen_critical_contempt_plus_other(self):
        """Contempt + any other horseman should be CRITICAL."""
        horsemen = [
            HorsemanDetection(
                horseman="contempt",
                confidence=0.9,
                indicators=["mockery"],
                severity="high",
            ),
            HorsemanDetection(
                horseman="criticism",
                confidence=0.7,
                indicators=["attack"],
                severity="medium",
            ),
        ]
        assert ThreatLevel.from_horsemen(horsemen) == ThreatLevel.CRITICAL

    def test_from_horsemen_critical_all_four(self):
        """All four horsemen should be CRITICAL."""
        horsemen = [
            HorsemanDetection(horseman="criticism", confidence=0.8, indicators=["attack"], severity="high"),
            HorsemanDetection(horseman="contempt", confidence=0.9, indicators=["mockery"], severity="high"),
            HorsemanDetection(horseman="defensiveness", confidence=0.7, indicators=["blame"], severity="medium"),
            HorsemanDetection(horseman="stonewalling", confidence=0.6, indicators=["withdrawal"], severity="medium"),
        ]
        assert ThreatLevel.from_horsemen(horsemen) == ThreatLevel.CRITICAL


class TestHorsemanDetection:
    """Tests for HorsemanDetection value object."""

    def test_create_valid_detection(self):
        """Can create a valid horseman detection."""
        detection = HorsemanDetection(
            horseman="contempt",
            confidence=0.8,
            indicators=["mockery", "eye-rolling language"],
            severity="high",
        )
        assert detection.horseman == "contempt"
        assert detection.confidence == 0.8
        assert len(detection.indicators) == 2
        assert detection.severity == "high"

    def test_is_significant_above_threshold(self):
        """Detection with confidence > 0.5 is significant."""
        detection = HorsemanDetection(
            horseman="criticism",
            confidence=0.6,
            indicators=[],
            severity="medium",
        )
        assert detection.is_significant is True

    def test_is_significant_below_threshold(self):
        """Detection with confidence <= 0.5 is not significant."""
        detection = HorsemanDetection(
            horseman="criticism",
            confidence=0.5,
            indicators=[],
            severity="low",
        )
        assert detection.is_significant is False

    def test_is_significant_at_boundary(self):
        """Detection with confidence exactly 0.5 is not significant."""
        detection = HorsemanDetection(
            horseman="defensiveness",
            confidence=0.5,
            indicators=[],
            severity="low",
        )
        assert detection.is_significant is False

    def test_frozen_model(self):
        """HorsemanDetection should be immutable."""
        detection = HorsemanDetection(
            horseman="stonewalling",
            confidence=0.7,
            indicators=[],
            severity="medium",
        )
        with pytest.raises(Exception):  # Pydantic raises ValidationError
            detection.confidence = 0.9

    def test_confidence_validation_min(self):
        """Confidence must be >= 0.0."""
        with pytest.raises(ValueError):
            HorsemanDetection(
                horseman="criticism",
                confidence=-0.1,
                indicators=[],
                severity="low",
            )

    def test_confidence_validation_max(self):
        """Confidence must be <= 1.0."""
        with pytest.raises(ValueError):
            HorsemanDetection(
                horseman="criticism",
                confidence=1.1,
                indicators=[],
                severity="low",
            )


class TestAnalysisResult:
    """Tests for AnalysisResult entity."""

    def test_create_safe_result(self):
        """Can create a safe analysis result."""
        result = AnalysisResult(
            safe=True,
            threat_level=ThreatLevel.SAFE,
            horsemen_detected=[],
            reasoning="Clean professional email",
            processing_time_ms=150,
        )
        assert result.safe is True
        assert result.threat_level == ThreatLevel.SAFE
        assert result.is_toxic is False
        assert result.cached is False

    def test_create_toxic_result(self):
        """Can create a toxic analysis result with horsemen."""
        horsemen = [
            HorsemanDetection(
                horseman="contempt",
                confidence=0.8,
                indicators=["mockery"],
                severity="high",
            ),
            HorsemanDetection(
                horseman="criticism",
                confidence=0.3,  # Below significance threshold
                indicators=["minor complaint"],
                severity="low",
            ),
        ]
        result = AnalysisResult(
            safe=False,
            threat_level=ThreatLevel.HIGH,
            horsemen_detected=horsemen,
            reasoning="Contains contempt and personal attacks",
            processing_time_ms=200,
        )
        assert result.safe is False
        assert result.threat_level == ThreatLevel.HIGH
        assert result.is_toxic is True
        assert len(result.horsemen_detected) == 2

    def test_detected_horsemen_names_filters_insignificant(self):
        """detected_horsemen_names only returns significant detections."""
        horsemen = [
            HorsemanDetection(
                horseman="contempt",
                confidence=0.8,
                indicators=[],
                severity="high",
            ),
            HorsemanDetection(
                horseman="criticism",
                confidence=0.3,  # Not significant
                indicators=[],
                severity="low",
            ),
        ]
        result = AnalysisResult(
            safe=False,
            threat_level=ThreatLevel.HIGH,
            horsemen_detected=horsemen,
            reasoning="Test",
            processing_time_ms=100,
        )
        names = result.detected_horsemen_names
        assert names == ["contempt"]
        assert "criticism" not in names

    def test_is_toxic_property(self):
        """is_toxic should be True when threat_level is not SAFE."""
        safe_result = AnalysisResult(
            safe=True,
            threat_level=ThreatLevel.SAFE,
            horsemen_detected=[],
            reasoning="Clean",
            processing_time_ms=100,
        )
        assert safe_result.is_toxic is False

        toxic_result = AnalysisResult(
            safe=False,
            threat_level=ThreatLevel.LOW,
            horsemen_detected=[
                HorsemanDetection(horseman="criticism", confidence=0.6, indicators=[], severity="low")
            ],
            reasoning="Minor toxicity",
            processing_time_ms=100,
        )
        assert toxic_result.is_toxic is True


class TestProtectionResult:
    """Tests for ProtectionResult entity."""

    def test_create_forwarded_result(self):
        """Can create a forwarded protection result."""
        result = ProtectionResult(
            should_forward=True,
            message_id="msg-123",
            protection_action="forward_clean",
        )
        assert result.should_forward is True
        assert result.message_id == "msg-123"

    def test_create_blocked_result(self):
        """Can create a blocked protection result."""
        analysis = AnalysisResult(
            safe=False,
            threat_level=ThreatLevel.CRITICAL,
            horsemen_detected=[
                HorsemanDetection(horseman="contempt", confidence=0.9, indicators=["mockery"], severity="high"),
                HorsemanDetection(horseman="criticism", confidence=0.8, indicators=["attack"], severity="high"),
            ],
            reasoning="Extreme toxicity",
            processing_time_ms=100,
        )
        result = ProtectionResult(
            should_forward=False,
            analysis=analysis,
            block_reason="Content too toxic",
            message_id="msg-456",
            protection_action="block_entirely",
        )
        assert result.should_forward is False
        assert result.block_reason == "Content too toxic"
        assert result.analysis is not None


class TestProtectionAction:
    """Tests for ProtectionAction enum."""

    def test_all_actions_exist(self):
        """Verify all protection actions exist."""
        assert ProtectionAction.FORWARD_CLEAN == "forward_clean"
        assert ProtectionAction.FORWARD_WITH_CONTEXT == "forward_with_context"
        assert ProtectionAction.REDACT_HARMFUL == "redact_harmful"
        assert ProtectionAction.SUMMARIZE_ONLY == "summarize_only"
        assert ProtectionAction.BLOCK_ENTIRELY == "block_entirely"


class TestDecideAction:
    """Tests for decide_action function with horsemen-based detection."""

    def test_forward_clean_no_horsemen(self):
        """No horsemen should forward clean."""
        assert decide_action([]) == ProtectionAction.FORWARD_CLEAN

    def test_forward_clean_insignificant_horsemen(self):
        """Only insignificant horsemen should forward clean."""
        horsemen = [
            HorsemanDetection(horseman="criticism", confidence=0.3, indicators=[], severity="low"),
        ]
        assert decide_action(horsemen) == ProtectionAction.FORWARD_CLEAN

    def test_forward_with_context_single_horseman(self):
        """Single non-contempt horseman should forward with context."""
        horsemen = [
            HorsemanDetection(horseman="criticism", confidence=0.6, indicators=["attack"], severity="medium"),
        ]
        assert decide_action(horsemen) == ProtectionAction.FORWARD_WITH_CONTEXT

    def test_redact_harmful_two_horsemen(self):
        """Two non-contempt horsemen should redact harmful content."""
        horsemen = [
            HorsemanDetection(horseman="criticism", confidence=0.7, indicators=["attack"], severity="medium"),
            HorsemanDetection(horseman="defensiveness", confidence=0.6, indicators=["blame"], severity="medium"),
        ]
        assert decide_action(horsemen) == ProtectionAction.REDACT_HARMFUL

    def test_summarize_only_contempt_alone(self):
        """Contempt alone should summarize only."""
        horsemen = [
            HorsemanDetection(horseman="contempt", confidence=0.8, indicators=["mockery"], severity="high"),
        ]
        assert decide_action(horsemen) == ProtectionAction.SUMMARIZE_ONLY

    def test_summarize_only_three_horsemen(self):
        """Three non-contempt horsemen should summarize only."""
        horsemen = [
            HorsemanDetection(horseman="criticism", confidence=0.7, indicators=["attack"], severity="medium"),
            HorsemanDetection(horseman="defensiveness", confidence=0.6, indicators=["blame"], severity="medium"),
            HorsemanDetection(horseman="stonewalling", confidence=0.6, indicators=["withdrawal"], severity="medium"),
        ]
        assert decide_action(horsemen) == ProtectionAction.SUMMARIZE_ONLY

    def test_block_entirely_contempt_plus_other(self):
        """Contempt + any other horseman should block entirely."""
        horsemen = [
            HorsemanDetection(horseman="contempt", confidence=0.9, indicators=["mockery"], severity="high"),
            HorsemanDetection(horseman="criticism", confidence=0.7, indicators=["attack"], severity="medium"),
        ]
        assert decide_action(horsemen) == ProtectionAction.BLOCK_ENTIRELY

    def test_block_entirely_all_four(self):
        """All four horsemen should block entirely."""
        horsemen = [
            HorsemanDetection(horseman="criticism", confidence=0.8, indicators=["attack"], severity="high"),
            HorsemanDetection(horseman="contempt", confidence=0.9, indicators=["mockery"], severity="high"),
            HorsemanDetection(horseman="defensiveness", confidence=0.7, indicators=["blame"], severity="medium"),
            HorsemanDetection(horseman="stonewalling", confidence=0.6, indicators=["withdrawal"], severity="medium"),
        ]
        assert decide_action(horsemen) == ProtectionAction.BLOCK_ENTIRELY


class TestGetActionDescription:
    """Tests for get_action_description helper."""

    def test_all_actions_have_descriptions(self):
        """Every action should have a description."""
        for action in ProtectionAction:
            desc = get_action_description(action)
            assert desc is not None
            assert len(desc) > 0


class TestPromptFormatting:
    """Tests for prompt formatting functions."""

    def test_format_analysis_prompt(self):
        """Analysis prompt should include content and sender."""
        prompt = format_analysis_prompt("Hello world", "test@example.com")
        assert "Hello world" in prompt
        assert "test@example.com" in prompt
        # Should focus on horsemen detection
        assert "horsemen" in prompt.lower() or "contempt" in prompt.lower()

    def test_format_analysis_prompt_unknown_sender(self):
        """Analysis prompt handles missing sender."""
        prompt = format_analysis_prompt("Hello world")
        assert "Hello world" in prompt
        assert "unknown" in prompt

    def test_format_rephrase_prompt(self):
        """Rephrase prompt should include all parameters."""
        prompt = format_rephrase_prompt(
            content="You're terrible at this",
            detected_patterns="contempt, criticism",
            reasoning="Personal attack detected",
        )
        assert "You're terrible at this" in prompt
        assert "contempt, criticism" in prompt
        assert "Personal attack detected" in prompt
