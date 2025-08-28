"""
TDD RED PHASE: Test for GraduatedDecisionMaker - sophisticated email protection decisions.

This test defines the expected behavior for a graduated decision system that provides
nuanced protection actions beyond simple pass/block decisions.

Expected Actions (Updated 2025-08-27 - Recalibrated thresholds):
- FORWARD_CLEAN: Safe content (toxicity < 0.30)
- FORWARD_WITH_CONTEXT: Add helpful notes (0.30-0.55)  
- REDACT_HARMFUL: Remove toxic parts (0.55-0.70)
- SUMMARIZE_ONLY: Facts only (0.70-0.90)
- BLOCK_ENTIRELY: Too toxic (> 0.90)

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
        RED PHASE: Test that clean emails get FORWARD_CLEAN action.
        
        This test SHOULD FAIL because:
        1. GraduatedDecisionMaker class doesn't exist
        2. ProtectionAction enum doesn't exist
        3. ProtectionDecision dataclass doesn't exist
        """
        # Create clean email analysis (low toxicity)
        clean_analysis = AnalysisResult(
            safe=True,
            threat_level=ThreatLevel.SAFE,
            toxicity_score=0.1,  # Below 0.30 threshold
            horsemen_detected=[],
            reasoning="Clean professional email",
            processing_time_ms=50,
            cached=False
        )
        
        # This should fail because make_decision method doesn't exist
        decision = self.decision_maker.make_decision(clean_analysis, "Thank you for your help with the project.")
        
        # Expected behavior (this assertion will fail in RED phase)
        assert decision.action == ProtectionAction.FORWARD_CLEAN
        assert decision.processed_content == "Thank you for your help with the project."
        assert "clean" in decision.reasoning.lower()
        assert decision.toxicity_score == 0.1
    
    def test_minor_toxicity_forward_with_context_action(self):
        """
        RED PHASE: Test that minor toxicity gets FORWARD_WITH_CONTEXT action.
        
        Toxicity between 0.30-0.55 should add helpful context notes.
        """
        minor_toxic_analysis = AnalysisResult(
            safe=False,
            threat_level=ThreatLevel.LOW,
            toxicity_score=0.40,  # In 0.30-0.55 range
            horsemen_detected=[
                HorsemanDetection(
                    horseman="manipulation",
                    confidence=0.3,
                    indicators=["subtle pressure"],
                    severity="low"
                )
            ],
            reasoning="Minor manipulation detected",
            processing_time_ms=75,
            cached=False
        )
        
        original_content = "You should really consider my offer soon."
        
        decision = self.decision_maker.make_decision(minor_toxic_analysis, original_content)
        
        # Expected behavior
        assert decision.action == ProtectionAction.FORWARD_WITH_CONTEXT
        assert original_content in decision.processed_content
        assert "[CONTEXT:" in decision.processed_content  # Should add context note
        assert "manipulation" in decision.reasoning.lower()
    
    def test_moderate_toxicity_redact_harmful_action(self):
        """
        RED PHASE: Test that moderate toxicity gets REDACT_HARMFUL action.
        
        Toxicity between 0.55-0.70 should redact harmful parts.
        """
        moderate_toxic_analysis = AnalysisResult(
            safe=False,
            threat_level=ThreatLevel.MEDIUM,
            toxicity_score=0.60,  # In 0.55-0.70 range
            horsemen_detected=[
                HorsemanDetection(
                    horseman="harassment",
                    confidence=0.6,
                    indicators=["personal attack", "insulting language"],
                    severity="medium"
                )
            ],
            reasoning="Personal attacks detected",
            processing_time_ms=90,
            cached=False
        )
        
        original_content = "Your work is terrible and you're incompetent. Please send the report by Friday."
        
        decision = self.decision_maker.make_decision(moderate_toxic_analysis, original_content)
        
        # Expected behavior
        assert decision.action == ProtectionAction.REDACT_HARMFUL
        assert "Please send the report by Friday" in decision.processed_content  # Keep factual
        assert "terrible" not in decision.processed_content  # Remove harmful
        assert "incompetent" not in decision.processed_content  # Remove harmful
        assert "[REDACTED]" in decision.processed_content
    
    def test_high_toxicity_summarize_only_action(self):
        """
        RED PHASE: Test that high toxicity gets SUMMARIZE_ONLY action.
        
        Toxicity between 0.70-0.90 should provide only factual summary.
        """
        high_toxic_analysis = AnalysisResult(
            safe=False,
            threat_level=ThreatLevel.HIGH,
            toxicity_score=0.75,  # In 0.70-0.90 range
            horsemen_detected=[
                HorsemanDetection(
                    horseman="harassment",
                    confidence=0.8,
                    indicators=["threats", "hostile language"],
                    severity="high"
                ),
                HorsemanDetection(
                    horseman="manipulation",
                    confidence=0.7,
                    indicators=["coercion", "pressure tactics"],
                    severity="high"
                )
            ],
            reasoning="Multiple threats and manipulation detected",
            processing_time_ms=120,
            cached=False
        )
        
        original_content = "You're a worthless piece of garbage and I'll make you pay. Meeting is at 3pm tomorrow."
        
        decision = self.decision_maker.make_decision(high_toxic_analysis, original_content)
        
        # Expected behavior
        assert decision.action == ProtectionAction.SUMMARIZE_ONLY
        assert "Meeting is at 3pm tomorrow" in decision.processed_content or "3pm" in decision.processed_content
        assert "worthless" not in decision.processed_content
        assert "garbage" not in decision.processed_content
        assert "pay" not in decision.processed_content
        assert decision.processed_content.startswith("[SUMMARY:")
    
    def test_extreme_toxicity_block_entirely_action(self):
        """
        RED PHASE: Test that extreme toxicity gets BLOCK_ENTIRELY action.
        
        Toxicity > 0.90 should block the email entirely.
        """
        extreme_toxic_analysis = AnalysisResult(
            safe=False,
            threat_level=ThreatLevel.CRITICAL,
            toxicity_score=0.95,  # Above 0.90 threshold
            horsemen_detected=[
                HorsemanDetection(
                    horseman="harassment",
                    confidence=0.9,
                    indicators=["explicit threats", "violent language"],
                    severity="high"
                ),
                HorsemanDetection(
                    horseman="deception",
                    confidence=0.8,
                    indicators=["false claims", "manipulation"],
                    severity="high"
                )
            ],
            reasoning="Critical threats and violence detected",
            processing_time_ms=150,
            cached=False
        )
        
        original_content = "I'm going to destroy you and everything you care about. You deserve to suffer."
        
        decision = self.decision_maker.make_decision(extreme_toxic_analysis, original_content)
        
        # Expected behavior
        assert decision.action == ProtectionAction.BLOCK_ENTIRELY
        assert decision.processed_content == ""  # No content forwarded
        assert "critical" in decision.reasoning.lower() or "extreme" in decision.reasoning.lower()
    
    def test_custom_thresholds_configuration(self):
        """
        RED PHASE: Test that decision maker can be configured with custom thresholds.
        
        This tests the configurable nature of the threshold system.
        """
        # Custom thresholds - more lenient
        custom_thresholds = {
            'forward_clean': 0.3,      # Up from 0.2
            'forward_context': 0.5,    # Up from 0.35  
            'redact_harmful': 0.7,     # Up from 0.5
            'summarize_only': 0.85     # Up from 0.7
        }
        
        custom_decision_maker = GraduatedDecisionMaker(thresholds=custom_thresholds)
        
        # Test with toxicity that would normally be FORWARD_WITH_CONTEXT (0.3)
        # but should now be FORWARD_CLEAN with custom thresholds
        analysis = AnalysisResult(
            safe=False,
            threat_level=ThreatLevel.LOW,
            toxicity_score=0.25,  # Between original 0.2 and custom 0.3
            horsemen_detected=[],
            reasoning="Minor toxicity",
            processing_time_ms=50,
            cached=False
        )
        
        decision = custom_decision_maker.make_decision(analysis, "Slightly concerning content")
        
        # With custom thresholds, this should be FORWARD_CLEAN instead of FORWARD_WITH_CONTEXT
        assert decision.action == ProtectionAction.FORWARD_CLEAN
    
    def test_edge_case_exact_threshold_values(self):
        """
        RED PHASE: Test behavior at exact threshold boundaries.
        
        Ensures consistent behavior when toxicity equals threshold values.
        """
        test_cases = [
            (0.20, ProtectionAction.FORWARD_CLEAN),         # Below first threshold
            (0.30, ProtectionAction.FORWARD_WITH_CONTEXT),   # Exactly at threshold
            (0.55, ProtectionAction.REDACT_HARMFUL),        # Exactly at threshold  
            (0.70, ProtectionAction.SUMMARIZE_ONLY),         # Exactly at threshold
            (0.90, ProtectionAction.BLOCK_ENTIRELY),         # Exactly at threshold
        ]
        
        for toxicity_score, expected_action in test_cases:
            analysis = AnalysisResult(
                safe=False,
                threat_level=ThreatLevel.MEDIUM,
                toxicity_score=toxicity_score,
                horsemen_detected=[],
                reasoning=f"Edge case test at {toxicity_score}",
                processing_time_ms=50,
                cached=False
            )
            
            decision = self.decision_maker.make_decision(analysis, "Test content")
            
            assert decision.action == expected_action, \
                f"Toxicity {toxicity_score} should result in {expected_action}, got {decision.action}"


def test_protection_action_enum_exists():
    """
    RED PHASE: Test that ProtectionAction enum has all required values.
    
    This test will fail because the enum doesn't exist yet.
    """
    # This will fail in RED phase
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
    RED PHASE: Test that ProtectionDecision dataclass has correct structure.
    
    This test will fail because the dataclass doesn't exist yet.
    """
    # Test that ProtectionDecision has required fields
    decision = ProtectionDecision(
        action=ProtectionAction.FORWARD_CLEAN,
        processed_content="Test content",
        reasoning="Test reasoning",
        toxicity_score=0.1,
        original_analysis=None
    )
    
    assert hasattr(decision, 'action')
    assert hasattr(decision, 'processed_content')
    assert hasattr(decision, 'reasoning')
    assert hasattr(decision, 'toxicity_score')
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
