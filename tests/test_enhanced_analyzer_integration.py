"""
Test integration of EnhancedFourHorsemenAnalyzer into EmailProtectionProcessor.
This test verifies the processor uses the enhanced analyzer with shared context.
"""

import pytest
from unittest.mock import Mock, patch

from cellophanemail.features.email_protection.processor import EmailProtectionProcessor
from cellophanemail.features.email_protection.llm_analyzer import SimpleLLMAnalyzer
from cellophanemail.features.email_protection.enhanced_analyzer import EnhancedFourHorsemenAnalyzer
from cellophanemail.providers.contracts import EmailMessage


class TestEnhancedAnalyzerIntegration:
    """Test processor integration with EnhancedFourHorsemenAnalyzer."""
    
    def setup_method(self):
        """Set up test environment."""
        self.real_llm = SimpleLLMAnalyzer(default_response="neutral")
        self.processor = EmailProtectionProcessor(llm_analyzer=self.real_llm)
    
    @pytest.mark.asyncio
    async def test_processor_uses_enhanced_analyzer_with_shared_context(self):
        """
        RED PHASE: This test SHOULD FAIL because processor still uses old analyzer.
        
        Test that the processor uses EnhancedFourHorsemenAnalyzer instead of 
        the old FourHorsemenAnalyzer and passes shared_context to it.
        """
        # Create test email with defensiveness pattern
        email = EmailMessage(
            message_id="test-001",
            from_address="defensive@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="It's not my fault",
            text_body="It's not my fault, you made me do this. I suffered enough from your previous mistakes."
        )
        
        # Mock the analyzer instance to verify it gets called with shared context
        from cellophanemail.features.email_protection.models import AnalysisResult, ThreatLevel
        mock_analysis_result = AnalysisResult(
            safe=False,
            threat_level=ThreatLevel.HIGH,
            toxicity_score=0.8,
            horsemen_detected=[],
            reasoning="Test defensiveness detected",
            processing_time_ms=100,
            cached=False
        )
        
        # VERIFICATION: Processor should be using EnhancedFourHorsemenAnalyzer
        from cellophanemail.features.email_protection.enhanced_analyzer import EnhancedFourHorsemenAnalyzer
        assert isinstance(self.processor.analyzer, EnhancedFourHorsemenAnalyzer), \
            f"Expected EnhancedFourHorsemenAnalyzer, got {type(self.processor.analyzer)}"
        
        # Mock the analyzer's analyze_with_context method
        with patch.object(self.processor.analyzer, 'analyze_with_context', return_value=mock_analysis_result) as mock_analyze:
            # Process the email
            result = await self.processor.process_email(
                email=email,
                user_email="real@example.com"
            )
            
            # VERIFICATION: analyze_with_context should be called with shared context
            mock_analyze.assert_called_once()
            call_args = mock_analyze.call_args
            
            # Check that the method was called with correct parameters
            assert len(call_args[0]) == 3  # content, sender, shared_context
            content, sender, shared_context = call_args[0]
            
            assert "It's not my fault" in content
            assert sender == "defensive@example.com"
            assert shared_context is self.processor.shared_context
            
            # Verify the result uses the enhanced analysis
            assert result.analysis == mock_analysis_result
            assert not result.should_forward  # Should be blocked due to high toxicity
    
    @pytest.mark.asyncio 
    async def test_enhanced_analyzer_detects_defensiveness_patterns(self):
        """
        Test that the enhanced analyzer can detect defensiveness patterns
        that the old analyzer might miss.
        """
        # Test various defensiveness patterns
        test_cases = [
            {
                "content": "It's not my fault, you made me do this",
                "pattern": "blame_shifting"
            },
            {
                "content": "I suffered enough from your previous mistakes", 
                "pattern": "victim_playing"
            },
            {
                "content": "You're pathetic and worthless",
                "pattern": "contempt"
            }
        ]
        
        for test_case in test_cases:
            email = EmailMessage(
                message_id=f"test-{test_case['pattern']}",
                from_address="sender@example.com",
                to_addresses=["shield.test@cellophanemail.com"],
                subject="Test",
                text_body=test_case["content"]
            )
            
            # Use fresh processor for each test to avoid context contamination
            fresh_processor = EmailProtectionProcessor(llm_analyzer=self.real_llm)
            
            result = await fresh_processor.process_email(
                email=email,
                user_email="real@example.com"
            )
            
            # Enhanced analyzer should detect these patterns and block
            assert not result.should_forward, f"Should block {test_case['pattern']}: {test_case['content']}"
            # Note: SimpleLLMAnalyzer affects scoring, so we check that it's not safe rather than specific toxicity
            assert not result.analysis.safe, f"Should detect harmful pattern for {test_case['pattern']}"
            print(f"✓ Detected {test_case['pattern']}: toxicity={result.analysis.toxicity_score:.3f}, " +
                  f"horsemen={[h.horseman for h in result.analysis.horsemen_detected]}")
    
    @pytest.mark.asyncio
    async def test_clean_email_vs_aggressive_email_comparison(self):
        """
        Test that the enhanced analyzer differentiates between clean and aggressive emails.
        Since SimpleLLMAnalyzer affects absolute scores, we test relative behavior.
        """
        # Clean email
        clean_email = EmailMessage(
            message_id="test-clean",
            from_address="sender@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="Invoice Request",
            text_body="Please send the invoice by Friday. Thank you."
        )
        
        # Aggressive email
        aggressive_email = EmailMessage(
            message_id="test-aggressive",
            from_address="sender@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="You're an idiot",
            text_body="You're a complete idiot and worthless person. I hate you."
        )
        
        clean_result = await self.processor.process_email(
            clean_email, "real@example.com"
        )
        
        # Use fresh processor for second email to avoid context contamination
        fresh_processor = EmailProtectionProcessor(llm_analyzer=self.real_llm)
        
        aggressive_result = await fresh_processor.process_email(
            aggressive_email, "real@example.com"
        )
        
        # The aggressive email should have higher toxicity than clean
        assert aggressive_result.analysis.toxicity_score > clean_result.analysis.toxicity_score, \
            f"Aggressive email toxicity ({aggressive_result.analysis.toxicity_score:.3f}) should be higher than clean ({clean_result.analysis.toxicity_score:.3f})"
        
        print(f"✓ Clean email toxicity: {clean_result.analysis.toxicity_score:.3f}")
        print(f"✓ Aggressive email toxicity: {aggressive_result.analysis.toxicity_score:.3f}")
        print(f"✓ Enhanced analyzer properly differentiates email types")


if __name__ == "__main__":
    # Run the failing test to demonstrate RED phase
    import asyncio
    
    async def run_red_phase_demo():
        print("=== TDD RED PHASE: Running Failing Test ===\n")
        
        test_instance = TestEnhancedAnalyzerIntegration()
        test_instance.setup_method()
        
        try:
            await test_instance.test_processor_uses_enhanced_analyzer_with_shared_context()
            print("❌ TEST SHOULD HAVE FAILED! This indicates the integration is already working.")
        except Exception as e:
            print(f"✓ EXPECTED FAILURE: {e}")
            print("This confirms we need to implement the integration.")
        
        print("\n=== RED PHASE COMPLETE ===")
    
    asyncio.run(run_red_phase_demo())
