"""
Test the shared context system integration.
Demonstrates the iterative analysis through 4 phases.
"""

import pytest
from unittest.mock import Mock

from cellophanemail.features.email_protection.processor import EmailProtectionProcessor
from cellophanemail.features.email_protection.llm_analyzer import SimpleLLMAnalyzer
from cellophanemail.providers.contracts import EmailMessage


class TestSharedContextIntegration:
    """Test enhanced email protection with shared context."""
    
    def setup_method(self):
        """Set up test environment."""
        # Use mock LLM analyzer for testing
        self.real_llm = SimpleLLMAnalyzer(default_response="neutral")
        self.processor = EmailProtectionProcessor(llm_analyzer=self.real_llm)
    
    @pytest.mark.asyncio
    async def test_basic_shared_context_flow(self):
        """Test the 4-phase shared context analysis."""
        
        # Create test email with facts and attacks
        email = EmailMessage(
            message_id="test-001",
            from_address="abuser@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="About the money",
            text_body="You STILL owe me $500 from last year. You're so selfish and cheap."
        )
        
        # Process through enhanced pipeline
        result = await self.processor.process_email(
            email=email,
            user_email="real@example.com"
        )
        
        # Verify LLM was called
        assert self.real_llm.call_count > 0
        assert len(self.real_llm.call_history) > 0
        
        # Verify shared context was updated
        context = self.processor.shared_context
        assert context.iteration == 1
        assert len(context.fact_ratios) == 1
        assert len(context.fact_analyses) > 0
        
        # Check that facts were extracted
        summary = context.get_current_analysis_summary()
        assert summary["iteration"] == 1
        assert summary["fact_ratio"] > 0  # Should find "$500" and "last year"
        
        # Check phases were completed
        phases = summary["phases"]
        assert "fact_extraction" in phases
        assert "manner_summary" in phases
        assert "non_factual_analysis" in phases
        assert "implicit_analysis" in phases
        
        print(f"✓ Test completed - Context Summary:")
        print(f"  Iteration: {summary['iteration']}")
        print(f"  Fact Ratio: {summary['fact_ratio']:.2%}")
        print(f"  Phases: {list(phases.keys())}")
        
    @pytest.mark.asyncio
    async def test_escalation_detection_over_iterations(self):
        """Test that shared context detects escalation over multiple emails."""
        
        # First email - moderate
        email1 = EmailMessage(
            message_id="test-001",
            from_address="sender@example.com", 
            to_addresses=["shield.test@cellophanemail.com"],
            subject="Reminder",
            text_body="Hi, just a reminder about the $100 payment due next week."
        )
        
        await self.processor.process_email(email1, "real@example.com")
        
        # Second email - more aggressive
        email2 = EmailMessage(
            message_id="test-002",
            from_address="sender@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="Payment overdue",
            text_body="You're late with the $100. This is unacceptable."
        )
        
        await self.processor.process_email(email2, "real@example.com")
        
        # Third email - hostile
        email3 = EmailMessage(
            message_id="test-003",
            from_address="sender@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="Final warning",
            text_body="I'm sick of your excuses. Pay the $100 NOW or face consequences."
        )
        
        result = await self.processor.process_email(email3, "real@example.com")
        
        # Check escalation detection
        context = self.processor.shared_context
        summary = context.get_current_analysis_summary()
        
        assert context.iteration == 3
        assert "historical_context" in summary
        
        # Print results
        print(f"✓ Escalation test completed:")
        print(f"  Total iterations: {context.iteration}")
        print(f"  Historical context: {summary.get('historical_context', {})}")
        print(f"  Final decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
        print(f"  Block reason: {result.block_reason}")
        
    @pytest.mark.asyncio
    async def test_fact_manner_analysis(self):
        """Test fact manner classification with mock LLM."""
        
        # Configure mock to return "negative" for this test
        self.real_llm.default_response = "negative"
        
        email = EmailMessage(
            message_id="test-manner",
            from_address="aggressor@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="Money issue",
            text_body="You STILL haven't paid the $200 like you promised 3 months ago!"
        )
        
        result = await self.processor.process_email(email, "real@example.com")
        
        # Check shared context analysis
        context = self.processor.shared_context
        summary = context.get_current_analysis_summary()
        phases = summary["phases"]
        
        # Should have extracted facts
        fact_data = phases["fact_extraction"]
        assert fact_data["total_facts"] > 0
        # Check for money amount in the fact analyses (flexible format)
        fact_texts = [str(fa) for fa in fact_data["fact_analyses"]]
        assert any("200" in text or "$" in text for text in fact_texts), f"Expected money facts in: {fact_texts}"
        
        # Should have analyzed manner
        manner_data = phases.get("manner_summary", {})
        if manner_data:
            print(f"✓ Manner analysis:")
            print(f"  Overall manner: {manner_data.get('overall_manner')}")
            print(f"  Distribution: {manner_data.get('manner_distribution')}")
        
        # Should have found non-factual content
        non_factual_data = phases["non_factual_analysis"]
        print(f"✓ Non-factual analysis:")
        print(f"  Personal attacks: {non_factual_data.get('personal_attack_indicators', [])}")
        print(f"  Manipulation patterns: {non_factual_data.get('manipulation_indicators', [])}")
        
        print(f"✓ Final result: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")

if __name__ == "__main__":
    # Run tests manually for demonstration
    import asyncio
    
    async def demo():
        test_instance = TestSharedContextIntegration()
        test_instance.setup_method()
        
        print("=== Shared Context Integration Demo ===\n")
        
        print("1. Testing basic 4-phase analysis...")
        await test_instance.test_basic_shared_context_flow()
        print()
        
        print("2. Testing escalation detection over iterations...")
        test_instance.setup_method()  # Reset context
        await test_instance.test_escalation_detection_over_iterations()
        print()
        
        print("3. Testing fact manner analysis...")
        test_instance.setup_method()  # Reset context
        await test_instance.test_fact_manner_analysis()
        print()
        
        print("=== Demo Complete ===")
    
    # Run demo
    asyncio.run(demo())
