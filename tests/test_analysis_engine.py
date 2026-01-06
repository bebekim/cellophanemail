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
    DEFAULT_THRESHOLDS,
    decide_action,
    get_action_description,
    # Prompts
    format_analysis_prompt,
    format_rephrase_prompt,
)


class TestThreatLevel:
    """Tests for ThreatLevel enum and from_score method."""

    def test_threat_level_values(self):
        """Verify all threat level values exist."""
        assert ThreatLevel.SAFE == "safe"
        assert ThreatLevel.LOW == "low"
        assert ThreatLevel.MEDIUM == "medium"
        assert ThreatLevel.HIGH == "high"
        assert ThreatLevel.CRITICAL == "critical"

    def test_from_score_safe(self):
        """Scores below 0.30 should be SAFE."""
        assert ThreatLevel.from_score(0.0) == ThreatLevel.SAFE
        assert ThreatLevel.from_score(0.1) == ThreatLevel.SAFE
        assert ThreatLevel.from_score(0.29) == ThreatLevel.SAFE

    def test_from_score_low(self):
        """Scores 0.30-0.55 should be LOW."""
        assert ThreatLevel.from_score(0.30) == ThreatLevel.LOW
        assert ThreatLevel.from_score(0.40) == ThreatLevel.LOW
        assert ThreatLevel.from_score(0.54) == ThreatLevel.LOW

    def test_from_score_medium(self):
        """Scores 0.55-0.70 should be MEDIUM."""
        assert ThreatLevel.from_score(0.55) == ThreatLevel.MEDIUM
        assert ThreatLevel.from_score(0.60) == ThreatLevel.MEDIUM
        assert ThreatLevel.from_score(0.69) == ThreatLevel.MEDIUM

    def test_from_score_high(self):
        """Scores 0.70-0.90 should be HIGH."""
        assert ThreatLevel.from_score(0.70) == ThreatLevel.HIGH
        assert ThreatLevel.from_score(0.80) == ThreatLevel.HIGH
        assert ThreatLevel.from_score(0.89) == ThreatLevel.HIGH

    def test_from_score_critical(self):
        """Scores 0.90+ should be CRITICAL."""
        assert ThreatLevel.from_score(0.90) == ThreatLevel.CRITICAL
        assert ThreatLevel.from_score(0.95) == ThreatLevel.CRITICAL
        assert ThreatLevel.from_score(1.0) == ThreatLevel.CRITICAL


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
            toxicity_score=0.1,
            horsemen_detected=[],
            reasoning="Clean professional email",
            processing_time_ms=150,
        )
        assert result.safe is True
        assert result.threat_level == ThreatLevel.SAFE
        assert result.toxicity_score == 0.1
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
            toxicity_score=0.75,
            horsemen_detected=horsemen,
            reasoning="Contains contempt and personal attacks",
            processing_time_ms=200,
        )
        assert result.safe is False
        assert result.threat_level == ThreatLevel.HIGH
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
            toxicity_score=0.75,
            horsemen_detected=horsemen,
            reasoning="Test",
            processing_time_ms=100,
        )
        names = result.detected_horsemen_names
        assert names == ["contempt"]
        assert "criticism" not in names

    def test_frozen_model(self):
        """AnalysisResult should be immutable."""
        result = AnalysisResult(
            safe=True,
            threat_level=ThreatLevel.SAFE,
            toxicity_score=0.1,
            horsemen_detected=[],
            reasoning="Test",
            processing_time_ms=100,
        )
        with pytest.raises(Exception):
            result.toxicity_score = 0.9

    def test_toxicity_score_validation(self):
        """Toxicity score must be between 0 and 1."""
        with pytest.raises(ValueError):
            AnalysisResult(
                safe=True,
                threat_level=ThreatLevel.SAFE,
                toxicity_score=1.5,
                horsemen_detected=[],
                reasoning="Test",
                processing_time_ms=100,
            )


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
            toxicity_score=0.95,
            horsemen_detected=[],
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
    """Tests for decide_action function."""

    def test_forward_clean_below_threshold(self):
        """Scores below 0.30 should forward clean."""
        assert decide_action(0.0) == ProtectionAction.FORWARD_CLEAN
        assert decide_action(0.15) == ProtectionAction.FORWARD_CLEAN
        assert decide_action(0.29) == ProtectionAction.FORWARD_CLEAN

    def test_forward_with_context(self):
        """Scores 0.30-0.55 should forward with context."""
        assert decide_action(0.30) == ProtectionAction.FORWARD_WITH_CONTEXT
        assert decide_action(0.40) == ProtectionAction.FORWARD_WITH_CONTEXT
        assert decide_action(0.54) == ProtectionAction.FORWARD_WITH_CONTEXT

    def test_redact_harmful(self):
        """Scores 0.55-0.70 should redact harmful content."""
        assert decide_action(0.55) == ProtectionAction.REDACT_HARMFUL
        assert decide_action(0.60) == ProtectionAction.REDACT_HARMFUL
        assert decide_action(0.69) == ProtectionAction.REDACT_HARMFUL

    def test_summarize_only(self):
        """Scores 0.70-0.90 should summarize only."""
        assert decide_action(0.70) == ProtectionAction.SUMMARIZE_ONLY
        assert decide_action(0.80) == ProtectionAction.SUMMARIZE_ONLY
        assert decide_action(0.89) == ProtectionAction.SUMMARIZE_ONLY

    def test_block_entirely(self):
        """Scores 0.90+ should block entirely."""
        assert decide_action(0.90) == ProtectionAction.BLOCK_ENTIRELY
        assert decide_action(0.95) == ProtectionAction.BLOCK_ENTIRELY
        assert decide_action(1.0) == ProtectionAction.BLOCK_ENTIRELY

    def test_custom_thresholds(self):
        """Can use custom thresholds."""
        custom = {
            "forward_clean": 0.20,
            "forward_context": 0.40,
            "redact_harmful": 0.60,
            "summarize_only": 0.80,
        }
        # Score 0.25 would be FORWARD_CLEAN with defaults, but FORWARD_WITH_CONTEXT with custom
        assert decide_action(0.25, custom) == ProtectionAction.FORWARD_WITH_CONTEXT
        assert decide_action(0.15, custom) == ProtectionAction.FORWARD_CLEAN

    def test_boundary_values(self):
        """Test exact boundary values."""
        # Exactly at threshold should fall into next category
        assert decide_action(0.30) == ProtectionAction.FORWARD_WITH_CONTEXT
        assert decide_action(0.55) == ProtectionAction.REDACT_HARMFUL
        assert decide_action(0.70) == ProtectionAction.SUMMARIZE_ONLY
        assert decide_action(0.90) == ProtectionAction.BLOCK_ENTIRELY


class TestDefaultThresholds:
    """Tests for DEFAULT_THRESHOLDS configuration."""

    def test_thresholds_are_ordered(self):
        """Thresholds should be in ascending order."""
        assert DEFAULT_THRESHOLDS["forward_clean"] < DEFAULT_THRESHOLDS["forward_context"]
        assert DEFAULT_THRESHOLDS["forward_context"] < DEFAULT_THRESHOLDS["redact_harmful"]
        assert DEFAULT_THRESHOLDS["redact_harmful"] < DEFAULT_THRESHOLDS["summarize_only"]

    def test_thresholds_in_valid_range(self):
        """All thresholds should be between 0 and 1."""
        for name, value in DEFAULT_THRESHOLDS.items():
            assert 0.0 <= value <= 1.0, f"Threshold {name} = {value} out of range"

    def test_expected_values(self):
        """Verify expected threshold values (recalibrated 2025-08-23)."""
        assert DEFAULT_THRESHOLDS["forward_clean"] == 0.30
        assert DEFAULT_THRESHOLDS["forward_context"] == 0.55
        assert DEFAULT_THRESHOLDS["redact_harmful"] == 0.70
        assert DEFAULT_THRESHOLDS["summarize_only"] == 0.90


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
        assert "TOXICITY ASSESSMENT" in prompt

    def test_format_analysis_prompt_unknown_sender(self):
        """Analysis prompt handles missing sender."""
        prompt = format_analysis_prompt("Hello world")
        assert "Hello world" in prompt
        assert "unknown" in prompt

    def test_format_rephrase_prompt(self):
        """Rephrase prompt should include all parameters."""
        prompt = format_rephrase_prompt(
            content="You're terrible at this",
            toxicity_score=0.75,
            detected_patterns="contempt, criticism",
            reasoning="Personal attack detected",
        )
        assert "You're terrible at this" in prompt
        assert "0.75" in prompt
        assert "contempt, criticism" in prompt
        assert "Personal attack detected" in prompt
