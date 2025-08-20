"""
Example usage of the shared context system with different LLM providers.
Shows how to set up and use the enhanced email protection.
"""

import os
import asyncio
from cellophanemail.features.email_protection.processor import EmailProtectionProcessor
from cellophanemail.features.email_protection.llm_analyzer import create_llm_analyzer, MockLLMAnalyzer
from cellophanemail.providers.contracts import EmailMessage


async def demo_with_anthropic():
    """Demo with Anthropic Claude."""
    print("=== Anthropic Claude Demo ===")
    
    # Set up Anthropic LLM analyzer
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set, using mock instead")
        llm_analyzer = MockLLMAnalyzer("negative")
    else:
        llm_analyzer = create_llm_analyzer(
            provider="anthropic",
            api_key=api_key,
            model_name="claude-3-sonnet-20240229"
        )
    
    # Create processor with LLM
    processor = EmailProtectionProcessor(llm_analyzer)
    
    # Test email
    email = EmailMessage(
        message_id="demo-001",
        from_address="toxic@example.com",
        to_addresses=["shield.demo@cellophanemail.com"],
        subject="Payment issue",
        text_content="You're such a loser. You STILL owe me $300 from 6 months ago. Everyone knows you can't be trusted."
    )
    
    # Process email
    result = await processor.process_email(email, "protected@example.com")
    
    # Show results
    context_summary = processor.shared_context.get_current_analysis_summary()
    
    print(f"📧 Email processed (iteration {context_summary['iteration']})")
    print(f"📊 Fact ratio: {context_summary['fact_ratio']:.1%}")
    
    phases = context_summary["phases"]
    print(f"🔍 Phases completed: {', '.join(phases.keys())}")
    
    if "manner_summary" in phases:
        manner = phases["manner_summary"]
        print(f"📈 Overall manner: {manner.get('overall_manner', 'unknown')}")
    
    print(f"🛡️  Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
    if result.block_reason:
        print(f"🚫 Reason: {result.block_reason}")
    
    print()


async def demo_with_openai():
    """Demo with OpenAI GPT."""
    print("=== OpenAI GPT Demo ===")
    
    # Set up OpenAI LLM analyzer
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set, using mock instead")
        llm_analyzer = MockLLMAnalyzer("positive")
    else:
        llm_analyzer = create_llm_analyzer(
            provider="openai",
            api_key=api_key,
            model_name="gpt-4"
        )
    
    # Create processor
    processor = EmailProtectionProcessor(llm_analyzer)
    
    # Test with positive email
    email = EmailMessage(
        message_id="demo-002",
        from_address="friend@example.com",
        to_addresses=["shield.demo@cellophanemail.com"],
        subject="Thanks!",
        text_content="Thank you for the $50 you lent me last month. I'll pay it back this Friday as promised."
    )
    
    result = await processor.process_email(email, "protected@example.com")
    
    # Show results
    context_summary = processor.shared_context.get_current_analysis_summary()
    
    print(f"📧 Positive email processed")
    print(f"📊 Fact ratio: {context_summary['fact_ratio']:.1%}")
    print(f"🛡️  Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
    print()


async def demo_escalation_pattern():
    """Demo escalation detection over multiple emails."""
    print("=== Escalation Pattern Demo ===")
    
    # Use mock analyzer for consistency
    processor = EmailProtectionProcessor(MockLLMAnalyzer("neutral"))
    
    emails = [
        {
            "subject": "Quick question",
            "content": "Hi, when can you return the $100 I lent you last month?"
        },
        {
            "subject": "Follow up",
            "content": "It's been 2 weeks. The $100 is still outstanding. Please let me know when you can pay."
        },
        {
            "subject": "Getting frustrated",
            "content": "You're avoiding me about the $100. This is really unfair and inconsiderate."
        },
        {
            "subject": "Last warning",
            "content": "I'm done with your excuses about the $100. You're selfish and unreliable. Pay up or else."
        }
    ]
    
    for i, email_data in enumerate(emails, 1):
        email = EmailMessage(
            message_id=f"escalation-{i:03d}",
            from_address="escalator@example.com",
            to_addresses=["shield.demo@cellophanemail.com"],
            subject=email_data["subject"],
            text_content=email_data["content"]
        )
        
        result = await processor.process_email(email, "protected@example.com")
        context_summary = processor.shared_context.get_current_analysis_summary()
        
        print(f"📧 Email {i}: {email_data['subject']}")
        print(f"   Fact ratio: {context_summary['fact_ratio']:.1%}")
        print(f"   Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
        
        if "historical_context" in context_summary:
            historical = context_summary["historical_context"]
            if historical.get("escalation_detected"):
                print(f"   🚨 ESCALATION DETECTED over {historical.get('previous_iterations', 0)} emails")
        
        if result.block_reason:
            print(f"   Reason: {result.block_reason[:100]}...")
        print()


async def demo_without_llm():
    """Demo without LLM using fallback analysis."""
    print("=== No LLM (Fallback Mode) Demo ===")
    
    # Create processor without LLM
    processor = EmailProtectionProcessor()  # No LLM analyzer
    
    email = EmailMessage(
        message_id="fallback-001",
        from_address="simple@example.com",
        to_addresses=["shield.demo@cellophanemail.com"],
        subject="Simple test",
        text_content="You still owe me $75. When will you pay it back?"
    )
    
    result = await processor.process_email(email, "protected@example.com")
    context_summary = processor.shared_context.get_current_analysis_summary()
    
    print(f"📧 Email processed without LLM")
    print(f"📊 Fact ratio: {context_summary['fact_ratio']:.1%}")
    print(f"🛡️  Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
    
    # Check what analysis method was used
    phases = context_summary["phases"]
    if "fact_extraction" in phases:
        fact_analyses = phases["fact_extraction"]["fact_analyses"]
        if fact_analyses:
            method = "LLM" if "llm" in str(fact_analyses[0]) else "Fallback"
            print(f"🔧 Analysis method: {method}")
    print()


async def main():
    """Run all demos."""
    print("🚀 CellophoneMail Shared Context System Demo\n")
    
    await demo_with_anthropic()
    await demo_with_openai()
    await demo_escalation_pattern()
    await demo_without_llm()
    
    print("✅ All demos completed!")
    print("\n💡 Key Features Demonstrated:")
    print("   • 4-phase iterative analysis (facts, manner, non-factual, implicit)")
    print("   • LLM-based fact manner classification")
    print("   • Escalation pattern detection")
    print("   • Enhanced blocking reasons")
    print("   • Fallback mode without LLM")


if __name__ == "__main__":
    asyncio.run(main())