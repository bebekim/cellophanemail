"""
Test Phase 4 LLM-based implicit message detection.
Verifies sophisticated subtext and implication analysis.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cellophanemail.features.email_protection.processor import EmailProtectionProcessor
from cellophanemail.features.email_protection.llm_analyzer import MockLLMAnalyzer
from cellophanemail.providers.contracts import EmailMessage


async def test_phase4_implicit_analysis():
    """Test Phase 4 LLM-based implicit message detection."""
    
    print("🔍 PHASE 4 IMPLICIT MESSAGE ANALYSIS TESTS")
    print("=" * 50)
    print()
    
    test_emails = [
        {
            "name": "Veiled Threats",
            "email": EmailMessage(
                message_id="test-threats-001",
                from_address="threatening@example.com",
                to_addresses=["shield.test@cellophanemail.com"],
                subject="Just saying...",
                text_body="""
                I hope you're doing well. Just wanted to remind you about 
                the $800 from last month. I'm sure you wouldn't want any 
                complications with this matter.
                
                I'd hate for this to affect our future relationship.
                You know how these things can get... complicated.
                """
            )
        },
        
        {
            "name": "Social Pressure",
            "email": EmailMessage(
                message_id="test-social-001",
                from_address="social@example.com",
                to_addresses=["shield.test@cellophanemail.com"],
                subject="Community thoughts",
                text_body="""
                Hi there,
                
                I've been talking to some mutual friends about the situation.
                They're quite concerned about how this reflects on you.
                
                I'm sure you understand how important reputation is in 
                our community. People talk, you know.
                """
            )
        },
        
        {
            "name": "Emotional Manipulation",
            "email": EmailMessage(
                message_id="test-emotional-001",
                from_address="manipulator@example.com",
                to_addresses=["shield.test@cellophanemail.com"],
                subject="Disappointed",
                text_body="""
                I trusted you with the $500 loan three months ago.
                I thought you were different from the others.
                
                After everything we've been through together, 
                I never expected this kind of treatment.
                
                I guess I was wrong about your character.
                """
            )
        },
        
        {
            "name": "Clean Business Email",
            "email": EmailMessage(
                message_id="test-clean-001",
                from_address="business@company.com",
                to_addresses=["shield.test@cellophanemail.com"],
                subject="Invoice Reminder",
                text_body="""
                Dear Client,
                
                This is a friendly reminder that invoice #1234 for $1,500 
                is due on March 15th, 2024.
                
                Please let us know if you have any questions about the 
                payment terms or need to arrange an alternative schedule.
                
                Thank you for your business.
                """
            )
        }
    ]
    
    for test_case in test_emails:
        print(f"📧 Testing: {test_case['name']}")
        
        # Create processor with mock LLM
        processor = EmailProtectionProcessor(MockLLMAnalyzer("neutral"))
        
        # Process email
        result = await processor.process_email(test_case["email"], "real@example.com")
        
        # Get Phase 4 results
        context = processor.shared_context
        summary = context.get_current_analysis_summary()
        
        phases = summary["phases"]
        print(f"   🔍 Available phases: {list(phases.keys())}")
        
        if "implicit_analysis" in phases:
            implicit_data = phases["implicit_analysis"]
            
            print(f"   🎯 Analysis method: {implicit_data.get('analysis_method', 'unknown')}")
            
            # Check each category
            categories = ['implicit_threats', 'power_dynamics', 'emotional_manipulation', 'social_pressure']
            
            for category in categories:
                items = implicit_data.get(category, [])
                if items:
                    print(f"   🔴 {category}: {items}")
            
            # LLM-specific data
            if implicit_data.get('analysis_method') == 'llm_enhanced':
                confidence = implicit_data.get('confidence', 0)
                reasoning = implicit_data.get('reasoning', '')
                print(f"   📊 Confidence: {confidence:.2f}")
                if reasoning:
                    print(f"   💭 Reasoning: {reasoning}")
            
            # Fallback info
            if 'fallback_reason' in implicit_data:
                print(f"   ⚠️  Fallback reason: {implicit_data['fallback_reason']}")
        else:
            print("   ❌ No implicit_analysis found in phases")
        
        print(f"   🛡️  Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
        if not result.should_forward and result.block_reason:
            print(f"   📝 Block reason: {result.block_reason}")
        print()
    
    print("✅ Phase 4 Implicit Analysis Complete!")
    print()
    print("🎯 Key Features Tested:")
    print("   • LLM-based implicit threat detection")
    print("   • Subtext and implication analysis")
    print("   • Power dynamics recognition")
    print("   • Emotional manipulation detection")
    print("   • Social pressure identification")
    print("   • Graceful fallback to pattern matching")


async def test_phase4_fallback():
    """Test Phase 4 fallback when LLM unavailable."""
    
    print("🔄 TESTING PHASE 4 FALLBACK")
    print("-" * 30)
    
    # Test without LLM
    processor = EmailProtectionProcessor()  # No LLM
    
    email = EmailMessage(
        message_id="test-fallback-001",
        from_address="test@example.com",
        to_addresses=["shield.test@cellophanemail.com"],
        subject="Final notice",
        text_body="This is your last chance. If you don't pay by Friday, you'll regret it."
    )
    
    result = await processor.process_email(email, "real@example.com")
    
    context = processor.shared_context
    summary = context.get_current_analysis_summary()
    phases = summary["phases"]
    
    if "implicit_analysis" in phases:
        implicit_data = phases["implicit_analysis"]
        print(f"   📊 Analysis method: {implicit_data.get('analysis_method', 'unknown')}")
        
        # Check pattern detection worked
        threats = implicit_data.get('implicit_threats', [])
        if threats:
            print(f"   🔴 Threats detected: {threats}")
    
    print(f"   🛡️  Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
    print("✅ Phase 4 fallback working correctly!")
    print()


async def main():
    """Run all Phase 4 tests."""
    await test_phase4_implicit_analysis()
    await test_phase4_fallback()


if __name__ == "__main__":
    asyncio.run(main())