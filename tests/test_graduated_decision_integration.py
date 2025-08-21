"""
Test integration of GraduatedDecisionMaker into EmailProtectionProcessor.

This test ensures the processor uses the graduated decision maker instead of 
binary forward/block logic, providing more nuanced protection decisions.

TDD Integration Test - This should FAIL until we integrate the GraduatedDecisionMaker.
"""

import pytest
from unittest.mock import Mock, patch
from dataclasses import dataclass

from cellophanemail.features.email_protection.processor import EmailProtectionProcessor
from cellophanemail.features.email_protection.llm_analyzer import SimpleLLMAnalyzer
from cellophanemail.features.email_protection.graduated_decision_maker import (
    GraduatedDecisionMaker, 
    ProtectionAction, 
    ProtectionDecision
)
from cellophanemail.features.email_protection.models import AnalysisResult, ThreatLevel, HorsemanDetection
from cellophanemail.providers.contracts import EmailMessage


@dataclass 
class GraduatedProtectionResult:
    """Enhanced protection result that includes graduated decision."""
    should_forward: bool
    analysis: AnalysisResult
    block_reason: str = None
    forwarded_to: list = None
    logged_at: str = None
    message_id: str = None
    # New graduated decision fields
    protection_action: ProtectionAction = None
    processed_content: str = None
    decision_reasoning: str = None


class TestGraduatedDecisionIntegration:
    """Test processor integration with GraduatedDecisionMaker."""
    
    def setup_method(self):
        """Set up test environment."""
        self.real_llm = SimpleLLMAnalyzer()  # Use real LLM for language-agnostic testing
        self.processor = EmailProtectionProcessor(llm_analyzer=self.real_llm)
        # Configure thresholds for testing with real LLM responses
        # Real LLM responses can vary, so we use broader thresholds
        test_thresholds = {
            'forward_clean': 0.1,        # Below clean content scores
            'forward_context': 0.3,      # For minor toxicity
            'redact_harmful': 0.6,       # For moderate attacks
            'summarize_only': 0.8        # For high toxicity
        }
        self.processor.graduated_decision_maker = GraduatedDecisionMaker(thresholds=test_thresholds)
    
    @pytest.mark.asyncio
    async def test_processor_uses_graduated_decision_maker(self):
        """
        RED PHASE: Test that processor uses GraduatedDecisionMaker.
        
        This test should FAIL because:
        1. Processor doesn't have graduated_decision_maker attribute
        2. Processor result doesn't include graduated decision fields
        3. Binary decision logic is still being used
        """
        # Clean email that should get FORWARD_CLEAN action
        clean_email = EmailMessage(
            message_id="test-clean",
            from_address="sender@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="Project Update",
            text_body="Please review the attached report by Friday. Meeting is at 3pm tomorrow."
        )
        
        # Process the email
        result = await self.processor.process_email(
            email=clean_email,
            user_email="real@example.com"
        )
        
        # VERIFICATION: Processor should have graduated_decision_maker
        assert hasattr(self.processor, 'graduated_decision_maker'), \
            "Processor should have graduated_decision_maker attribute"
        
        assert isinstance(self.processor.graduated_decision_maker, GraduatedDecisionMaker), \
            f"Expected GraduatedDecisionMaker, got {type(self.processor.graduated_decision_maker)}"
        
        # VERIFICATION: Result should include graduated decision fields
        assert hasattr(result, 'protection_action'), \
            "ProtectionResult should include protection_action field"
        
        assert hasattr(result, 'processed_content'), \
            "ProtectionResult should include processed_content field"
        
        assert hasattr(result, 'decision_reasoning'), \
            "ProtectionResult should include decision_reasoning field"
        
        # For clean email, should get FORWARD_CLEAN action
        assert result.protection_action == ProtectionAction.FORWARD_CLEAN, \
            f"Clean email should get FORWARD_CLEAN, got {result.protection_action}"
        
        assert clean_email.text_body in result.processed_content, \
            "Clean email content should be included in processed content"
        
        assert "clean" in result.decision_reasoning.lower(), \
            f"Decision reasoning should mention 'clean', got: {result.decision_reasoning}"
    
    @pytest.mark.asyncio
    async def test_processor_handles_context_addition(self):
        """
        RED PHASE: Test that processor handles FORWARD_WITH_CONTEXT action.
        
        Should add context notes for minor toxicity emails.
        """
        # Email with minor toxicity
        minor_toxic_email = EmailMessage(
            message_id="test-minor-toxic",
            from_address="sender@example.com", 
            to_addresses=["shield.test@cellophanemail.com"],
            subject="Urgent Request",
            text_body="You should really consider my offer soon before it's too late."
        )
        
        result = await self.processor.process_email(
            email=minor_toxic_email,
            user_email="real@example.com"
        )
        
        # Should get FORWARD_WITH_CONTEXT action
        assert result.protection_action == ProtectionAction.FORWARD_WITH_CONTEXT, \
            f"Minor toxic email should get FORWARD_WITH_CONTEXT, got {result.protection_action}"
        
        # Should still forward (for context action)
        assert result.should_forward == True, \
            "FORWARD_WITH_CONTEXT should still forward email"
        
        # Content should include context note
        assert "[CONTEXT:" in result.processed_content, \
            "Processed content should include context note"
        
        assert minor_toxic_email.text_body in result.processed_content, \
            "Original content should be preserved in processed content"
    
    @pytest.mark.asyncio
    async def test_processor_handles_redaction(self):
        """
        RED PHASE: Test that processor handles REDACT_HARMFUL action.
        
        Should redact harmful content while preserving factual information.
        """
        # Email with moderate toxicity that needs redaction
        moderate_toxic_email = EmailMessage(
            message_id="test-redact",
            from_address="sender@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="Feedback",
            text_body="Your work is terrible and you're incompetent. Please send the report by Friday."
        )
        
        result = await self.processor.process_email(
            email=moderate_toxic_email,
            user_email="real@example.com"
        )
        
        # Should get REDACT_HARMFUL action
        assert result.protection_action == ProtectionAction.REDACT_HARMFUL, \
            f"Moderate toxic email should get REDACT_HARMFUL, got {result.protection_action}"
        
        # Should still forward (redacted version)
        assert result.should_forward == True, \
            "REDACT_HARMFUL should still forward email after redaction"
        
        # Harmful content should be redacted
        assert "terrible" not in result.processed_content, \
            "Harmful word 'terrible' should be redacted"
        
        assert "incompetent" not in result.processed_content, \
            "Harmful word 'incompetent' should be redacted"
        
        # Factual content should be preserved
        assert "Friday" in result.processed_content, \
            "Factual information should be preserved"
        
        assert "[REDACTED]" in result.processed_content, \
            "Should indicate that redaction occurred"
    
    @pytest.mark.asyncio
    async def test_processor_handles_summary_only(self):
        """
        RED PHASE: Test that processor handles SUMMARIZE_ONLY action.
        
        Should provide only factual summary for high toxicity.
        """
        # Email with high toxicity requiring summary only
        high_toxic_email = EmailMessage(
            message_id="test-summary",
            from_address="sender@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="Angry Message",
            text_body="You're a worthless piece of garbage and I'll destroy you. Meeting is at 3pm tomorrow."
        )
        
        result = await self.processor.process_email(
            email=high_toxic_email,
            user_email="real@example.com"
        )
        
        # Should get SUMMARIZE_ONLY action
        assert result.protection_action == ProtectionAction.SUMMARIZE_ONLY, \
            f"High toxic email should get SUMMARIZE_ONLY, got {result.protection_action}"
        
        # Should still forward (summary only)
        assert result.should_forward == True, \
            "SUMMARIZE_ONLY should still forward factual summary"
        
        # Should start with summary marker
        assert result.processed_content.startswith("[SUMMARY:"), \
            "Processed content should start with summary marker"
        
        # Harmful content should not be present
        assert "worthless" not in result.processed_content, \
            "Harmful content should not appear in summary"
        
        assert "garbage" not in result.processed_content, \
            "Harmful content should not appear in summary"
        
        # Factual content should be extracted
        assert "3pm" in result.processed_content or "meeting" in result.processed_content.lower(), \
            "Factual information should be extracted in summary"
    
    @pytest.mark.asyncio
    async def test_processor_handles_block_entirely(self):
        """
        RED PHASE: Test that processor handles BLOCK_ENTIRELY action.
        
        Should block emails with extreme toxicity.
        """
        # Email with extreme toxicity requiring complete blocking
        extreme_toxic_email = EmailMessage(
            message_id="test-block",
            from_address="sender@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="Threatening Message",
            text_body="I'm going to hunt you down and make you suffer for everything you've done."
        )
        
        result = await self.processor.process_email(
            email=extreme_toxic_email,
            user_email="real@example.com"
        )
        
        # Should get BLOCK_ENTIRELY action
        assert result.protection_action == ProtectionAction.BLOCK_ENTIRELY, \
            f"Extreme toxic email should get BLOCK_ENTIRELY, got {result.protection_action}"
        
        # Should NOT forward
        assert result.should_forward == False, \
            "BLOCK_ENTIRELY should not forward email"
        
        # Processed content should be empty
        assert result.processed_content == "", \
            "BLOCK_ENTIRELY should result in empty processed content"
        
        # Should have block reason
        assert result.block_reason is not None, \
            "Should provide block reason for blocked email"
        
        assert "extreme" in result.decision_reasoning.lower() or "critical" in result.decision_reasoning.lower(), \
            f"Decision reasoning should indicate severity, got: {result.decision_reasoning}"
    
    @pytest.mark.asyncio
    async def test_processor_backward_compatibility(self):
        """
        Test that existing functionality still works after integration.
        
        Ensures we didn't break the existing API.
        """
        # Test normal processing still returns expected fields
        normal_email = EmailMessage(
            message_id="test-normal",
            from_address="sender@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="Normal Email",
            text_body="This is a normal business email about project status."
        )
        
        result = await self.processor.process_email(
            email=normal_email,
            user_email="real@example.com"
        )
        
        # Original fields should still exist
        assert hasattr(result, 'should_forward'), "Original should_forward field should exist"
        assert hasattr(result, 'analysis'), "Original analysis field should exist"
        assert hasattr(result, 'block_reason'), "Original block_reason field should exist"
        assert hasattr(result, 'forwarded_to'), "Original forwarded_to field should exist"
        assert hasattr(result, 'logged_at'), "Original logged_at field should exist"
        assert hasattr(result, 'message_id'), "Original message_id field should exist"
        
        # Should maintain expected behavior
        assert result.should_forward == True, "Normal email should be forwarded"
        assert result.analysis is not None, "Should include analysis"
        assert result.message_id == normal_email.message_id, "Should preserve message ID"


if __name__ == "__main__":
    # Run this test to see integration failures in RED phase
    print("=== TDD INTEGRATION RED PHASE: Running Failing Tests ===\n")
    
    import asyncio
    
    async def run_integration_red_phase():
        test_instance = TestGraduatedDecisionIntegration()
        test_instance.setup_method()
        
        try:
            await test_instance.test_processor_uses_graduated_decision_maker()
            print("❌ Integration test should have failed! GraduatedDecisionMaker integration shouldn't exist yet.")
        except (AttributeError, AssertionError) as e:
            print(f"✓ EXPECTED FAILURE in integration: {e}")
        
        print("\n=== INTEGRATION RED PHASE COMPLETE ===")
        print("Next step: Integrate GraduatedDecisionMaker into EmailProtectionProcessor!")
    
    asyncio.run(run_integration_red_phase())
