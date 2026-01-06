# ABOUTME: Integration tests verifying cellophanemail uses analysis_engine correctly
# ABOUTME: Tests Phase 2 - re-exports, type identity, and GraduatedDecisionMaker integration

import pytest

from analysis_engine import (
    ThreatLevel as AE_ThreatLevel,
    HorsemanDetection as AE_HorsemanDetection,
    AnalysisResult as AE_AnalysisResult,
    ProtectionAction as AE_ProtectionAction,
    DEFAULT_THRESHOLDS as AE_DEFAULT_THRESHOLDS,
    decide_action as ae_decide_action,
)

from cellophanemail.features.email_protection.models import (
    ThreatLevel,
    HorsemanDetection,
    AnalysisResult,
    ProtectionResult,
)

from cellophanemail.features.email_protection.graduated_decision_maker import (
    ProtectionAction,
    ProtectionDecision,
    GraduatedDecisionMaker,
)


class TestModelsReExports:
    """Verify models.py correctly re-exports from analysis_engine."""

    def test_threat_level_is_same_object(self):
        """ThreatLevel should be the exact same object from analysis_engine."""
        assert ThreatLevel is AE_ThreatLevel

    def test_horseman_detection_is_same_object(self):
        """HorsemanDetection should be the exact same object from analysis_engine."""
        assert HorsemanDetection is AE_HorsemanDetection

    def test_analysis_result_is_same_object(self):
        """AnalysisResult should be the exact same object from analysis_engine."""
        assert AnalysisResult is AE_AnalysisResult

    def test_protection_result_is_cellophanemail_specific(self):
        """ProtectionResult should be cellophanemail-specific (not from analysis_engine)."""
        # ProtectionResult has extra fields not in analysis_engine
        from datetime import datetime

        result = ProtectionResult(
            should_forward=True,
            analysis=None,
            block_reason=None,
            forwarded_to=["user@example.com"],  # cellophanemail-specific
            logged_at=datetime.now(),  # cellophanemail-specific
            message_id="msg-123",
        )
        assert result.forwarded_to == ["user@example.com"]
        assert result.logged_at is not None

    def test_protection_result_to_dict(self):
        """ProtectionResult.to_dict() should work (cellophanemail-specific method)."""
        from datetime import datetime

        analysis = AnalysisResult(
            safe=True,
            threat_level=ThreatLevel.SAFE,
            toxicity_score=0.1,
            horsemen_detected=[],
            reasoning="Clean",
            processing_time_ms=100,
        )
        result = ProtectionResult(
            should_forward=True,
            analysis=analysis,
            block_reason=None,
            forwarded_to=["user@example.com"],
            logged_at=datetime.now(),
            message_id="msg-123",
            protection_action=ProtectionAction.FORWARD_CLEAN,
        )
        d = result.to_dict()
        assert d["should_forward"] is True
        assert d["threat_level"] == "safe"
        assert d["toxicity_score"] == 0.1
        assert d["protection_action"] == "forward_clean"


class TestGraduatedDecisionMakerReExports:
    """Verify graduated_decision_maker.py correctly uses analysis_engine."""

    def test_protection_action_is_same_object(self):
        """ProtectionAction should be the exact same object from analysis_engine."""
        assert ProtectionAction is AE_ProtectionAction

    def test_default_thresholds_match(self):
        """GraduatedDecisionMaker should use analysis_engine DEFAULT_THRESHOLDS."""
        gdm = GraduatedDecisionMaker()
        assert gdm.thresholds == AE_DEFAULT_THRESHOLDS

    def test_custom_thresholds_override(self):
        """Custom thresholds should override analysis_engine defaults."""
        custom = {"forward_clean": 0.20}
        gdm = GraduatedDecisionMaker(thresholds=custom)
        assert gdm.thresholds["forward_clean"] == 0.20
        # Other thresholds should remain from analysis_engine
        assert gdm.thresholds["forward_context"] == AE_DEFAULT_THRESHOLDS["forward_context"]


class TestGraduatedDecisionMakerUsesAnalysisEngine:
    """Verify GraduatedDecisionMaker.make_decision uses analysis_engine.decide_action."""

    def _create_analysis(self, toxicity: float) -> AnalysisResult:
        """Helper to create an AnalysisResult with given toxicity."""
        return AnalysisResult(
            safe=toxicity < 0.3,
            threat_level=ThreatLevel.from_score(toxicity),
            toxicity_score=toxicity,
            horsemen_detected=[],
            reasoning="Test",
            processing_time_ms=100,
        )

    def test_decision_matches_analysis_engine_forward_clean(self):
        """GraduatedDecisionMaker should return same action as analysis_engine.decide_action."""
        gdm = GraduatedDecisionMaker()
        analysis = self._create_analysis(0.1)

        decision = gdm.make_decision(analysis, "Test content")
        expected_action = ae_decide_action(0.1)

        assert decision.action == expected_action
        assert decision.action == ProtectionAction.FORWARD_CLEAN

    def test_decision_matches_analysis_engine_forward_context(self):
        """Score 0.4 should result in FORWARD_WITH_CONTEXT."""
        gdm = GraduatedDecisionMaker()
        analysis = self._create_analysis(0.4)

        decision = gdm.make_decision(analysis, "Test content")
        expected_action = ae_decide_action(0.4)

        assert decision.action == expected_action
        assert decision.action == ProtectionAction.FORWARD_WITH_CONTEXT

    def test_decision_matches_analysis_engine_redact(self):
        """Score 0.6 should result in REDACT_HARMFUL."""
        gdm = GraduatedDecisionMaker()
        analysis = self._create_analysis(0.6)

        decision = gdm.make_decision(analysis, "Test content")
        expected_action = ae_decide_action(0.6)

        assert decision.action == expected_action
        assert decision.action == ProtectionAction.REDACT_HARMFUL

    def test_decision_matches_analysis_engine_summarize(self):
        """Score 0.8 should result in SUMMARIZE_ONLY."""
        gdm = GraduatedDecisionMaker()
        analysis = self._create_analysis(0.8)

        decision = gdm.make_decision(analysis, "Test content")
        expected_action = ae_decide_action(0.8)

        assert decision.action == expected_action
        assert decision.action == ProtectionAction.SUMMARIZE_ONLY

    def test_decision_matches_analysis_engine_block(self):
        """Score 0.95 should result in BLOCK_ENTIRELY."""
        gdm = GraduatedDecisionMaker()
        analysis = self._create_analysis(0.95)

        decision = gdm.make_decision(analysis, "Test content")
        expected_action = ae_decide_action(0.95)

        assert decision.action == expected_action
        assert decision.action == ProtectionAction.BLOCK_ENTIRELY

    def test_custom_thresholds_affect_decision(self):
        """Custom thresholds should change decision boundaries."""
        # With default thresholds, 0.25 -> FORWARD_CLEAN
        gdm_default = GraduatedDecisionMaker()
        analysis = self._create_analysis(0.25)
        decision_default = gdm_default.make_decision(analysis, "Test")
        assert decision_default.action == ProtectionAction.FORWARD_CLEAN

        # With custom threshold, 0.25 -> FORWARD_WITH_CONTEXT
        gdm_custom = GraduatedDecisionMaker(thresholds={"forward_clean": 0.20})
        decision_custom = gdm_custom.make_decision(analysis, "Test")
        assert decision_custom.action == ProtectionAction.FORWARD_WITH_CONTEXT


class TestCellophaneMailSpecificProcessing:
    """Verify cellophanemail-specific content processing still works."""

    def _create_analysis(self, toxicity: float, horsemen: list = None) -> AnalysisResult:
        """Helper to create an AnalysisResult."""
        return AnalysisResult(
            safe=toxicity < 0.3,
            threat_level=ThreatLevel.from_score(toxicity),
            toxicity_score=toxicity,
            horsemen_detected=horsemen or [],
            reasoning="Test",
            processing_time_ms=100,
        )

    def test_forward_with_context_adds_notes(self):
        """FORWARD_WITH_CONTEXT should add context notes (cellophanemail-specific)."""
        gdm = GraduatedDecisionMaker()
        horsemen = [
            HorsemanDetection(
                horseman="manipulation",
                confidence=0.7,
                indicators=["guilt-tripping"],
                severity="medium",
            )
        ]
        analysis = self._create_analysis(0.4, horsemen)

        decision = gdm.make_decision(analysis, "Original content")

        assert "[CONTEXT:" in decision.processed_content
        assert "manipulation" in decision.processed_content.lower()

    def test_redact_harmful_redacts_words(self):
        """REDACT_HARMFUL should redact harmful words (cellophanemail-specific)."""
        gdm = GraduatedDecisionMaker()
        analysis = self._create_analysis(0.6)

        decision = gdm.make_decision(analysis, "You are terrible and stupid")

        assert "[REDACTED]" in decision.processed_content

    def test_summarize_only_creates_summary(self):
        """SUMMARIZE_ONLY should create factual summary (cellophanemail-specific)."""
        gdm = GraduatedDecisionMaker()
        analysis = self._create_analysis(0.8)

        decision = gdm.make_decision(analysis, "Meeting is at 3pm tomorrow. You're awful.")

        assert "[SUMMARY:" in decision.processed_content

    def test_block_entirely_returns_empty(self):
        """BLOCK_ENTIRELY should return empty content."""
        gdm = GraduatedDecisionMaker()
        analysis = self._create_analysis(0.95)

        decision = gdm.make_decision(analysis, "Extremely toxic content")

        assert decision.processed_content == ""
