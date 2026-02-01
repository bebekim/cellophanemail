"""
TDD RED PHASE: Test for GraduatedDecisionMaker - sophisticated email protection decisions.

This test defines the expected behavior for a graduated decision system that provides
nuanced protection actions beyond simple pass/block decisions.

Expected Actions (Updated - Horsemen-based detection):
- FORWARD_CLEAN: No significant horsemen detected (SAFE)
- FORWARD_WITH_CONTEXT: Single non-contempt horseman (LOW)
- REDACT_HARMFUL: 2 non-contempt horsemen (MEDIUM)
- SUMMARIZE_ONLY: Contempt detected, OR 3+ non-contempt horsemen (HIGH)
- BLOCK_ENTIRELY: Contempt + any other horseman, OR all 4 horsemen (CRITICAL)

This test SHOULD FAIL because GraduatedDecisionMaker doesn't exist yet.
"""

import pytest
from typing import List
from dataclasses import dataclass

# This import will fail because we haven't created the module yet
try:
    from cellophanemail.features.email_protection.graduated_decision_maker import (
        GraduatedDecisionMaker,
        ProtectionAction,
        ProtectionDecision
    )
except ImportError:
    # Expected failure in RED phase
    pass

from cellophanemail.features.email_protection.models import AnalysisResult, ThreatLevel, HorsemanDetection


class TestGraduatedDecisionMaker:
    """Test the graduated decision maker for nuanced email protection."""

    def setup_method(self):
        """Set up test environment."""
        # This will fail in RED phase because GraduatedDecisionMaker doesn't exist
        try:
            self.decision_maker = GraduatedDecisionMaker()
        except NameError:
            # Expected in RED phase
            self.decision_maker = None

    def test_clean_email_forward_clean_action(self):
        """
        Test that clean emails (no horsemen) get FORWARD_CLEAN action.
        """
        # Create clean email analysis (no horsemen)
        clean_analysis = AnalysisResult(
            safe=True,
            threat_level=ThreatLevel.SAFE,
            horsemen_detected=[],
            reasoning="Clean professional email",
            processing_time_ms=50,
            cached=False
        )

        decision = self.decision_maker.make_decision(clean_analysis, "Thank you for your help with the project.")

        assert decision.action == ProtectionAction.FORWARD_CLEAN
        assert decision.processed_content == "Thank you for your help with the project."
        assert "clean" in decision.reasoning.lower()
        assert decision.threat_level == ThreatLevel.SAFE

    def test_minor_toxicity_forward_with_context_action(self):
        """
        Test that single non-contempt horseman gets FORWARD_WITH_CONTEXT action.
        """
        minor_toxic_analysis = AnalysisResult(
            safe=False,
            threat_level=ThreatLevel.LOW,
            horsemen_detected=[
                HorsemanDetection(
                    horseman="criticism",
                    confidence=0.6,
                    indicators=["subtle pressure"],
                    severity="low"
                )
            ],
            reasoning="Minor criticism detected",
            processing_time_ms=75,
            cached=False
        )

        original_content = "You should really consider my offer soon."

        decision = self.decision_maker.make_decision(minor_toxic_analysis, original_content)

        assert decision.action == ProtectionAction.FORWARD_WITH_CONTEXT
        assert original_content in decision.processed_content
        assert "[CONTEXT:" in decision.processed_content  # Should add context note
        assert "criticism" in decision.reasoning.lower()

    def test_moderate_toxicity_redact_harmful_action(self):
        """
        Test that two non-contempt horsemen get REDACT_HARMFUL action.
        """
        moderate_toxic_analysis = AnalysisResult(
            safe=False,
            threat_level=ThreatLevel.MEDIUM,
            horsemen_detected=[
                HorsemanDetection(
                    horseman="criticism",
                    confidence=0.7,
                    indicators=["personal attack"],
                    severity="medium"
                ),
                HorsemanDetection(
                    horseman="defensiveness",
                    confidence=0.6,
                    indicators=["blame-shifting"],
                    severity="medium"
                )
            ],
            reasoning="Criticism and defensiveness detected",
            processing_time_ms=90,
            cached=False
        )

        original_content = "Your work is terrible and you're incompetent. Please send the report by Friday."

        decision = self.decision_maker.make_decision(moderate_toxic_analysis, original_content)

        assert decision.action == ProtectionAction.REDACT_HARMFUL
        assert "Please send the report by Friday" in decision.processed_content  # Keep factual
        assert "[REDACTED]" in decision.processed_content

    def test_high_toxicity_summarize_only_action(self):
        """
        Test that contempt alone gets SUMMARIZE_ONLY action.
        """
        high_toxic_analysis = AnalysisResult(
            safe=False,
            threat_level=ThreatLevel.HIGH,
            horsemen_detected=[
                HorsemanDetection(
                    horseman="contempt",
                    confidence=0.8,
                    indicators=["mockery", "superiority"],
                    severity="high"
                )
            ],
            reasoning="Contempt detected - most destructive pattern",
            processing_time_ms=120,
            cached=False
        )

        original_content = "You're a worthless piece of garbage. Meeting is at 3pm tomorrow."

        decision = self.decision_maker.make_decision(high_toxic_analysis, original_content)

        assert decision.action == ProtectionAction.SUMMARIZE_ONLY
        assert "worthless" not in decision.processed_content
        assert "garbage" not in decision.processed_content
        assert "[SUMMARY:" in decision.processed_content

    def test_extreme_toxicity_block_entirely_action(self):
        """
        Test that contempt + other horseman gets BLOCK_ENTIRELY action.
        """
        extreme_toxic_analysis = AnalysisResult(
            safe=False,
            threat_level=ThreatLevel.CRITICAL,
            horsemen_detected=[
                HorsemanDetection(
                    horseman="contempt",
                    confidence=0.95,
                    indicators=["hatred", "superiority"],
                    severity="high"
                ),
                HorsemanDetection(
                    horseman="criticism",
                    confidence=0.9,
                    indicators=["character attack"],
                    severity="high"
                )
            ],
            reasoning="Critical: contempt with criticism",
            processing_time_ms=150,
            cached=False
        )

        original_content = "I'm going to destroy you and everything you care about. You deserve to suffer."

        decision = self.decision_maker.make_decision(extreme_toxic_analysis, original_content)

        assert decision.action == ProtectionAction.BLOCK_ENTIRELY
        assert decision.processed_content == ""  # No content forwarded
        assert "critical" in decision.reasoning.lower() or "extreme" in decision.reasoning.lower()

    def test_three_non_contempt_horsemen_is_high(self):
        """
        Test that 3 non-contempt horsemen result in HIGH threat level and SUMMARIZE_ONLY.
        """
        analysis = AnalysisResult(
            safe=False,
            threat_level=ThreatLevel.HIGH,
            horsemen_detected=[
                HorsemanDetection(horseman="criticism", confidence=0.7, indicators=["attack"], severity="medium"),
                HorsemanDetection(horseman="defensiveness", confidence=0.6, indicators=["blame"], severity="medium"),
                HorsemanDetection(horseman="stonewalling", confidence=0.6, indicators=["withdrawal"], severity="medium"),
            ],
            reasoning="Three non-contempt horsemen detected",
            processing_time_ms=100,
            cached=False
        )

        decision = self.decision_maker.make_decision(analysis, "Test content")

        assert decision.action == ProtectionAction.SUMMARIZE_ONLY

    def test_all_four_horsemen_is_critical(self):
        """
        Test that all 4 horsemen result in CRITICAL threat level and BLOCK_ENTIRELY.
        """
        analysis = AnalysisResult(
            safe=False,
            threat_level=ThreatLevel.CRITICAL,
            horsemen_detected=[
                HorsemanDetection(horseman="criticism", confidence=0.8, indicators=["attack"], severity="high"),
                HorsemanDetection(horseman="contempt", confidence=0.9, indicators=["mockery"], severity="high"),
                HorsemanDetection(horseman="defensiveness", confidence=0.7, indicators=["blame"], severity="medium"),
                HorsemanDetection(horseman="stonewalling", confidence=0.6, indicators=["withdrawal"], severity="medium"),
            ],
            reasoning="All four horsemen detected",
            processing_time_ms=150,
            cached=False
        )

        decision = self.decision_maker.make_decision(analysis, "Test content")

        assert decision.action == ProtectionAction.BLOCK_ENTIRELY


def test_protection_action_enum_exists():
    """
    Test that ProtectionAction enum has all required values.
    """
    actions = list(ProtectionAction)
    expected_actions = [
        ProtectionAction.FORWARD_CLEAN,
        ProtectionAction.FORWARD_WITH_CONTEXT,
        ProtectionAction.REDACT_HARMFUL,
        ProtectionAction.SUMMARIZE_ONLY,
        ProtectionAction.BLOCK_ENTIRELY
    ]

    for action in expected_actions:
        assert action in actions


def test_protection_decision_dataclass_structure():
    """
    Test that ProtectionDecision dataclass has correct structure.
    """
    decision = ProtectionDecision(
        action=ProtectionAction.FORWARD_CLEAN,
        processed_content="Test content",
        reasoning="Test reasoning",
        threat_level=ThreatLevel.SAFE,
        original_analysis=None
    )

    assert hasattr(decision, 'action')
    assert hasattr(decision, 'processed_content')
    assert hasattr(decision, 'reasoning')
    assert hasattr(decision, 'threat_level')
    assert hasattr(decision, 'original_analysis')


if __name__ == "__main__":
    # Run this test to see it fail in RED phase
    print("=== TDD RED PHASE: Running Failing Tests ===\n")

    test_instance = TestGraduatedDecisionMaker()
    print("1. Setting up test...")

    try:
        test_instance.setup_method()
        print("❌ Setup should have failed! GraduatedDecisionMaker shouldn't exist yet.")
    except (NameError, ImportError) as e:
        print(f"✓ EXPECTED FAILURE in setup: {e}")

    print("\n2. Testing imports...")
    try:
        test_protection_action_enum_exists()
        print("❌ Enum test should have failed!")
    except (NameError, ImportError) as e:
        print(f"✓ EXPECTED FAILURE with enum: {e}")

    print("\n=== RED PHASE COMPLETE ===")
    print("Next step: Implement GraduatedDecisionMaker to make these tests pass!")
