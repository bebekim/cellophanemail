"""
Test integration of streamlined processor with graduated decision making.

Tests that the streamlined architecture correctly implements graduated protection
decisions using empirically calibrated thresholds.
"""

import pytest

from cellophanemail.features.email_protection.processor import EmailProtectionProcessor
from cellophanemail.features.email_protection.graduated_decision_maker import ProtectionAction
from cellophanemail.providers.contracts import EmailMessage


class TestGraduatedDecisionIntegration:
    """Test streamlined processor with graduated decision making."""
    
    def setup_method(self):
        """Set up test environment."""
        # Use streamlined processor with deterministic temperature
        self.processor = EmailProtectionProcessor(temperature=0.0)
    
    @pytest.mark.asyncio
    async def test_processor_uses_graduated_decision_maker(self):
        """
        Test that streamlined processor provides graduated decisions.
        """
        # Clean email that should get FORWARD_CLEAN or FORWARD_WITH_CONTEXT
        clean_email = EmailMessage(
            message_id="test-clean",
            from_address="sender@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="Project Update",
            text_body="Please review the attached report by Friday. Meeting is at 3pm tomorrow."
        )
        
        result = await self.processor.process_email(
            email=clean_email,
            user_email="real@example.com"
        )
        
        # Verify graduated decision fields exist
        assert hasattr(result, 'protection_action'), "Should include protection_action field"
        assert hasattr(result, 'processed_content'), "Should include processed_content field"
        assert hasattr(result, 'decision_reasoning'), "Should include decision_reasoning field"
        
        # Clean email should get light protection
        assert result.protection_action in [
            ProtectionAction.FORWARD_CLEAN, 
            ProtectionAction.FORWARD_WITH_CONTEXT
        ], f"Clean email should get light protection, got {result.protection_action}"
        
        assert result.should_forward is True, "Clean email should be forwarded"
        
        print(f"Clean email: action={result.protection_action}, toxicity={result.analysis.toxicity_score:.3f}")
    
    @pytest.mark.asyncio
    async def test_processor_handles_context_addition(self):
        """
        Test that processor handles minor toxicity with context addition.
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
        
        # Should get some form of protection but still forward
        assert result.should_forward is True, "Minor toxic email should still be forwarded"
        assert result.protection_action in [
            ProtectionAction.FORWARD_WITH_CONTEXT,
            ProtectionAction.REDACT_HARMFUL,
            ProtectionAction.SUMMARIZE_ONLY
        ], f"Minor toxic email should get protection, got {result.protection_action}"
        
        print(f"Minor toxic: action={result.protection_action}, toxicity={result.analysis.toxicity_score:.3f}")
    
    @pytest.mark.asyncio
    async def test_processor_handles_redaction(self):
        """
        Test that processor handles moderate toxicity appropriately.
        """
        # Email with moderate toxicity that may need redaction
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
        
        # Should get significant protection
        assert result.protection_action in [
            ProtectionAction.REDACT_HARMFUL,
            ProtectionAction.SUMMARIZE_ONLY,
            ProtectionAction.BLOCK_ENTIRELY
        ], f"Moderate toxic email should get significant protection, got {result.protection_action}"
        
        print(f"Moderate toxic: action={result.protection_action}, toxicity={result.analysis.toxicity_score:.3f}")
    
    @pytest.mark.asyncio
    async def test_processor_handles_summary_only(self):
        """
        Test that processor handles high toxicity with summary or blocking.
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
        
        # Should get strong protection
        assert result.protection_action in [
            ProtectionAction.SUMMARIZE_ONLY,
            ProtectionAction.BLOCK_ENTIRELY
        ], f"High toxic email should get strong protection, got {result.protection_action}"
        
        print(f"High toxic: action={result.protection_action}, toxicity={result.analysis.toxicity_score:.3f}")
    
    @pytest.mark.asyncio
    async def test_processor_handles_block_entirely(self):
        """
        Test that processor handles extreme toxicity appropriately.
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
            extreme_toxic_email,
            user_email="real@example.com"
        )
        
        # Extreme toxicity should get maximum protection
        assert result.protection_action in [
            ProtectionAction.SUMMARIZE_ONLY,
            ProtectionAction.BLOCK_ENTIRELY
        ], f"Extreme toxic email should get maximum protection, got {result.protection_action}"
        
        # Verify proper reasoning
        assert result.decision_reasoning is not None, "Should provide decision reasoning"
        
        print(f"Extreme toxic: action={result.protection_action}, toxicity={result.analysis.toxicity_score:.3f}")
    
    @pytest.mark.asyncio
    async def test_processor_backward_compatibility(self):
        """
        Test that existing functionality still works after streamlining.
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
        assert result.should_forward is True, "Normal email should be forwarded"
        assert result.analysis is not None, "Should include analysis"
        assert result.message_id == normal_email.message_id, "Should preserve message ID"
        
        print(f"Normal email: action={result.protection_action}, toxicity={result.analysis.toxicity_score:.3f}")


if __name__ == "__main__":
    # Run integration tests
    import asyncio
    
    async def run_integration_tests():
        test_instance = TestGraduatedDecisionIntegration()
        test_instance.setup_method()
        
        print("=== Streamlined Processor Integration Tests ===\n")
        
        await test_instance.test_processor_uses_graduated_decision_maker()
        await test_instance.test_processor_handles_context_addition()
        await test_instance.test_processor_handles_redaction()
        await test_instance.test_processor_handles_summary_only()
        await test_instance.test_processor_handles_block_entirely()
        await test_instance.test_processor_backward_compatibility()
        
        print("\n=== All integration tests completed ===")
    
    asyncio.run(run_integration_tests())