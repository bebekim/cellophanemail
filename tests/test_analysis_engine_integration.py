# ABOUTME: Integration tests verifying cellophanemail uses analysis_engine correctly
# ABOUTME: Tests Phase 2 - re-exports, type identity, and GraduatedDecisionMaker integration

import pytest

from analysis_engine import (
    ThreatLevel as AE_ThreatLevel,
    HorsemanDetection as AE_HorsemanDetection,
    AnalysisResult as AE_AnalysisResult,
    ProtectionAction as AE_ProtectionAction,
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
        assert d["is_toxic"] is False
        assert d["protection_action"] == "forward_clean"


class TestGraduatedDecisionMakerReExports:
    """Verify graduated_decision_maker.py correctly uses analysis_engine."""

    def test_protection_action_is_same_object(self):
        """ProtectionAction should be the exact same object from analysis_engine."""
        assert ProtectionAction is AE_ProtectionAction

    def test_graduated_decision_maker_creates_without_thresholds(self):
        """GraduatedDecisionMaker should not require thresholds (uses horsemen-based detection)."""
        gdm = GraduatedDecisionMaker()
        assert gdm is not None


class TestGraduatedDecisionMakerUsesAnalysisEngine:
    """Verify GraduatedDecisionMaker.make_decision uses analysis_engine.decide_action."""

    def _create_analysis(self, horsemen: list = None) -> AnalysisResult:
        """Helper to create an AnalysisResult with given horsemen."""
        horsemen = horsemen or []
        threat_level = ThreatLevel.from_horsemen(horsemen)
        return AnalysisResult(
            safe=threat_level == ThreatLevel.SAFE,
            threat_level=threat_level,
            horsemen_detected=horsemen,
            reasoning="Test",
            processing_time_ms=100,
        )

    def test_decision_matches_analysis_engine_forward_clean(self):
        """GraduatedDecisionMaker should return same action as analysis_engine.decide_action."""
        gdm = GraduatedDecisionMaker()
        horsemen = []  # No horsemen = SAFE = FORWARD_CLEAN
        analysis = self._create_analysis(horsemen)

        decision = gdm.make_decision(analysis, "Test content")
        expected_action = ae_decide_action(horsemen)

        assert decision.action == expected_action
        assert decision.action == ProtectionAction.FORWARD_CLEAN

    def test_decision_matches_analysis_engine_forward_context(self):
        """Single non-contempt horseman should result in FORWARD_WITH_CONTEXT."""
        gdm = GraduatedDecisionMaker()
        horsemen = [
            HorsemanDetection(horseman="criticism", confidence=0.6, indicators=["attack"], severity="medium")
        ]
        analysis = self._create_analysis(horsemen)

        decision = gdm.make_decision(analysis, "Test content")
        expected_action = ae_decide_action(horsemen)

        assert decision.action == expected_action
        assert decision.action == ProtectionAction.FORWARD_WITH_CONTEXT

    def test_decision_matches_analysis_engine_redact(self):
        """Two non-contempt horsemen should result in REDACT_HARMFUL."""
        gdm = GraduatedDecisionMaker()
        horsemen = [
            HorsemanDetection(horseman="criticism", confidence=0.7, indicators=["attack"], severity="medium"),
            HorsemanDetection(horseman="defensiveness", confidence=0.6, indicators=["blame"], severity="medium"),
        ]
        analysis = self._create_analysis(horsemen)

        decision = gdm.make_decision(analysis, "Test content")
        expected_action = ae_decide_action(horsemen)

        assert decision.action == expected_action
        assert decision.action == ProtectionAction.REDACT_HARMFUL

    def test_decision_matches_analysis_engine_summarize(self):
        """Contempt alone should result in SUMMARIZE_ONLY."""
        gdm = GraduatedDecisionMaker()
        horsemen = [
            HorsemanDetection(horseman="contempt", confidence=0.8, indicators=["mockery"], severity="high"),
        ]
        analysis = self._create_analysis(horsemen)

        decision = gdm.make_decision(analysis, "Test content")
        expected_action = ae_decide_action(horsemen)

        assert decision.action == expected_action
        assert decision.action == ProtectionAction.SUMMARIZE_ONLY

    def test_decision_matches_analysis_engine_block(self):
        """Contempt + another horseman should result in BLOCK_ENTIRELY."""
        gdm = GraduatedDecisionMaker()
        horsemen = [
            HorsemanDetection(horseman="contempt", confidence=0.9, indicators=["mockery"], severity="high"),
            HorsemanDetection(horseman="criticism", confidence=0.7, indicators=["attack"], severity="medium"),
        ]
        analysis = self._create_analysis(horsemen)

        decision = gdm.make_decision(analysis, "Test content")
        expected_action = ae_decide_action(horsemen)

        assert decision.action == expected_action
        assert decision.action == ProtectionAction.BLOCK_ENTIRELY


class TestCellophaneMailSpecificProcessing:
    """Verify cellophanemail-specific content processing still works."""

    def _create_analysis(self, horsemen: list = None) -> AnalysisResult:
        """Helper to create an AnalysisResult."""
        horsemen = horsemen or []
        threat_level = ThreatLevel.from_horsemen(horsemen)
        return AnalysisResult(
            safe=threat_level == ThreatLevel.SAFE,
            threat_level=threat_level,
            horsemen_detected=horsemen,
            reasoning="Test",
            processing_time_ms=100,
        )

    def test_forward_with_context_adds_notes(self):
        """FORWARD_WITH_CONTEXT should add context notes (cellophanemail-specific)."""
        gdm = GraduatedDecisionMaker()
        horsemen = [
            HorsemanDetection(
                horseman="criticism",
                confidence=0.6,
                indicators=["character attack"],
                severity="medium",
            )
        ]
        analysis = self._create_analysis(horsemen)

        decision = gdm.make_decision(analysis, "Original content")

        assert "[CONTEXT:" in decision.processed_content
        assert "criticism" in decision.processed_content.lower()

    def test_redact_harmful_redacts_words(self):
        """REDACT_HARMFUL should redact harmful words (cellophanemail-specific)."""
        gdm = GraduatedDecisionMaker()
        horsemen = [
            HorsemanDetection(horseman="criticism", confidence=0.7, indicators=["attack"], severity="medium"),
            HorsemanDetection(horseman="defensiveness", confidence=0.6, indicators=["blame"], severity="medium"),
        ]
        analysis = self._create_analysis(horsemen)

        decision = gdm.make_decision(analysis, "You are terrible and stupid")

        assert "[REDACTED]" in decision.processed_content

    def test_summarize_only_creates_summary(self):
        """SUMMARIZE_ONLY should create factual summary (cellophanemail-specific)."""
        gdm = GraduatedDecisionMaker()
        horsemen = [
            HorsemanDetection(horseman="contempt", confidence=0.8, indicators=["mockery"], severity="high"),
        ]
        analysis = self._create_analysis(horsemen)

        decision = gdm.make_decision(analysis, "Meeting is at 3pm tomorrow. You're awful.")

        assert "[SUMMARY:" in decision.processed_content

    def test_block_entirely_returns_empty(self):
        """BLOCK_ENTIRELY should return empty content."""
        gdm = GraduatedDecisionMaker()
        horsemen = [
            HorsemanDetection(horseman="contempt", confidence=0.9, indicators=["mockery"], severity="high"),
            HorsemanDetection(horseman="criticism", confidence=0.8, indicators=["attack"], severity="high"),
        ]
        analysis = self._create_analysis(horsemen)

        decision = gdm.make_decision(analysis, "Extremely toxic content")

        assert decision.processed_content == ""
