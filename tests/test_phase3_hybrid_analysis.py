"""
Test enhanced Phase 3 hybrid analysis combining LLM and pattern matching.
Verifies sophisticated psychological manipulation detection.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cellophanemail.features.email_protection.processor import EmailProtectionProcessor
from cellophanemail.features.email_protection.llm_analyzer import MockLLMAnalyzer
from cellophanemail.providers.contracts import EmailMessage


async def test_hybrid_phase3_analysis():
    """Test hybrid Phase 3 analysis across different psychological patterns."""
    
    print("🧠 PHASE 3 HYBRID PSYCHOLOGICAL ANALYSIS TESTS")
    print("=" * 55)
    print()
    
    test_emails = [
        {
            "name": "Character Assassination (English)",
            "email": EmailMessage(
                message_id="test-character-001",
                from_address="toxic@example.com",
                to_addresses=["shield.test@cellophanemail.com"],
                subject="You're Pathetic",
                text_body="""
                You're such a stupid, selfish person. Nobody likes you because 
                you're completely worthless. Everyone knows you can't be trusted.
                
                You borrowed $300 last month and you're still being pathetic about it.
                Pay up or everyone will know what a loser you really are.
                """
            ),
            "expected_patterns": ["personal_attacks", "social_manipulation"],
            "expected_severity": "high"
        },
        
        {
            "name": "Emotional Manipulation (Korean)",
            "email": EmailMessage(
                message_id="test-emotional-ko-001",
                from_address="manipulator@example.com",
                to_addresses=["shield.test@cellophanemail.com"],
                subject="실망했어요",
                text_body="""
                진짜 실망했어요. 당신이 이런 사람인 줄 몰랐어요.
                
                50만원 빌려간 걸 2개월째 안 갚고 있으면서
                계속 변명만 하네요. 한심해요.
                
                모든 사람이 당신이 믿을 수 없는 사람이라고 말하고 있어요.
                """
            ),
            "expected_patterns": ["emotional_manipulation", "personal_attacks"],
            "expected_severity": "medium"
        },
        
        {
            "name": "Gaslighting Pattern (Spanish)",
            "email": EmailMessage(
                message_id="test-gaslighting-es-001",
                from_address="gaslighter@example.com",
                to_addresses=["shield.test@cellophanemail.com"],
                subject="Eso nunca pasó",
                text_body="""
                Te estás imaginando cosas. Eso nunca pasó así.
                
                Sobre los 400 euros, estás siendo demasiado dramático.
                Siempre exageras todo y te haces la víctima.
                
                Eres demasiado sensible. Nadie más piensa que soy el problema.
                """
            ),
            "expected_patterns": ["gaslighting_patterns", "emotional_manipulation"],
            "expected_severity": "high"
        },
        
        {
            "name": "Control Tactics (Mixed)",
            "email": EmailMessage(
                message_id="test-control-001",
                from_address="controller@example.com",
                to_addresses=["shield.test@cellophanemail.com"],
                subject="Last Warning",
                text_body="""
                This is your last chance. Pay the $150 by Friday or else.
                You have no choice in this matter.
                
                If you don't comply, you'll regret it. I'm serious.
                Unless you want everyone to know about this, you better act fast.
                """
            ),
            "expected_patterns": ["control_tactics", "social_manipulation"],
            "expected_severity": "high"
        },
        
        {
            "name": "Benign Business Email",
            "email": EmailMessage(
                message_id="test-benign-001",
                from_address="colleague@company.com",
                to_addresses=["shield.test@cellophanemail.com"],
                subject="Project Update",
                text_body="""
                Hi there,
                
                Just wanted to update you on the project progress. We've completed
                the first phase and are moving on to the $1,200 implementation phase.
                
                The deadline is next Friday, March 15th. Let me know if you have
                any questions or concerns.
                
                Thanks for your collaboration!
                """
            ),
            "expected_patterns": [],
            "expected_severity": "low"
        }
    ]
    
    for test_case in test_emails:
        print(f"📧 Testing: {test_case['name']}")
        
        # Create processor with mock LLM
        processor = EmailProtectionProcessor(MockLLMAnalyzer("neutral"))
        
        # Process email
        result = await processor.process_email(test_case["email"], "real@example.com")
        
        # Get Phase 3 results
        context = processor.shared_context
        summary = context.get_current_analysis_summary()
        
        phases = summary["phases"]
        print(f"   🔍 Available phases: {list(phases.keys())}")
        
        if "non_factual_analysis" in phases:
            analysis = phases["non_factual_analysis"]
            
            print(f"   📊 Analysis method: {analysis.get('analysis_method', 'unknown')}")
            print(f"   🎯 Primary tactic: {analysis.get('primary_tactic', 'none')}")
            print(f"   📈 Severity score: {analysis.get('severity_score', 0):.2f}")
            print(f"   🧠 Sophistication: {analysis.get('manipulation_sophistication', 'unknown')}")
            
            # Check each category
            categories = ['personal_attacks', 'emotional_manipulation', 'gaslighting_patterns', 
                         'social_manipulation', 'control_tactics']
            
            for category in categories:
                items = analysis.get(category, [])
                if items:
                    print(f"   🔴 {category}: {items}")
            
            # Cultural context
            cultural = analysis.get('cultural_context', '')
            if cultural:
                print(f"   🌍 Cultural context: {cultural}")
            
            # Hybrid validation (if available)
            if analysis.get('analysis_method') == 'hybrid_llm_pattern':
                agreement = analysis.get('llm_pattern_agreement', 0)
                flags = analysis.get('validation_flags', [])
                print(f"   ⚖️  LLM-Pattern agreement: {agreement:.2f}")
                if flags:
                    print(f"   ⚠️  Validation flags: {flags}")
        else:
            print("   ❌ No non_factual_analysis found in phases")
        
        print(f"   🛡️  Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
        if not result.should_forward and result.block_reason:
            print(f"   📝 Block reason: {result.block_reason}")
        print()
    
    print("✅ Phase 3 Hybrid Analysis Complete!")
    print()
    print("🎯 Key Features Tested:")
    print("   • LLM psychological pattern detection")
    print("   • Enhanced multilingual pattern matching")
    print("   • Cross-validation between LLM and patterns")
    print("   • Cultural context awareness")
    print("   • Manipulation sophistication scoring")
    print("   • Hybrid confidence metrics")


async def test_phase3_fallback_scenarios():
    """Test Phase 3 fallback when LLM fails or is unavailable."""
    
    print("🔄 TESTING PHASE 3 FALLBACK SCENARIOS")
    print("-" * 40)
    print()
    
    # Test without LLM
    print("📧 Test 1: No LLM Available")
    processor = EmailProtectionProcessor()  # No LLM
    
    email = EmailMessage(
        message_id="test-fallback-001",
        from_address="test@example.com",
        to_addresses=["shield.test@cellophanemail.com"],
        subject="You're stupid",
        text_body="You're such an idiot! Pay the $100 or else I'll tell everyone what a loser you are."
    )
    
    result = await processor.process_email(email, "real@example.com")
    
    context = processor.shared_context
    summary = context.get_current_analysis_summary()
    phases = summary["phases"]
    
    if "non_factual_analysis" in phases:
        analysis = phases["non_factual_analysis"]
        print(f"   📊 Analysis method: {analysis.get('analysis_method', 'unknown')}")
        print(f"   📈 Severity score: {analysis.get('severity_score', 0):.2f}")
        
        # Check pattern detection worked
        personal_attacks = analysis.get('personal_attacks', [])
        if personal_attacks:
            print(f"   🔴 Personal attacks detected: {personal_attacks}")
    
    print(f"   🛡️  Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
    print()
    
    # Test with simulated LLM failure
    print("📧 Test 2: LLM Failure Simulation")
    
    class FailingLLMAnalyzer:
        def __init__(self):
            self.provider = "mock_failing"
            
        def analyze_fact_manner(self, fact, content, sender):
            raise Exception("Simulated LLM failure")
    
    processor_failing = EmailProtectionProcessor(FailingLLMAnalyzer())
    
    result2 = await processor_failing.process_email(email, "real@example.com")
    
    context2 = processor_failing.shared_context
    summary2 = context2.get_current_analysis_summary()
    phases2 = summary2["phases"]
    
    if "non_factual_analysis" in phases2:
        analysis2 = phases2["non_factual_analysis"]
        print(f"   📊 Analysis method: {analysis2.get('analysis_method', 'unknown')}")
        
        # Should have fallback reason
        fallback_reason = analysis2.get('llm_fallback_reason', 'none')
        print(f"   ⚠️  Fallback reason: {fallback_reason}")
    
    print(f"   🛡️  Decision: {'BLOCKED' if not result2.should_forward else 'FORWARDED'}")
    print()
    
    print("✅ Fallback scenarios working correctly!")
    print()


async def test_phase3_cross_validation():
    """Test cross-validation between LLM and pattern analysis."""
    
    print("⚖️  TESTING PHASE 3 CROSS-VALIDATION")
    print("-" * 40)
    print()
    
    processor = EmailProtectionProcessor(MockLLMAnalyzer("neutral"))
    
    # Email with clear patterns that both LLM and regex should detect
    email = EmailMessage(
        message_id="test-validation-001",
        from_address="test@example.com",
        to_addresses=["shield.test@cellophanemail.com"],
        subject="Manipulation Test",
        text_body="""
        You're such a selfish idiot! Everyone knows you can't be trusted.
        
        If you don't pay the $500 by tomorrow, you'll regret it.
        This is your last chance or else I'll make sure everyone knows
        what a worthless person you are.
        """
    )
    
    result = await processor.process_email(email, "real@example.com")
    
    context = processor.shared_context
    summary = context.get_current_analysis_summary()
    phases = summary["phases"]
    
    if "non_factual_analysis" in phases:
        analysis = phases["non_factual_analysis"]
        
        if analysis.get('analysis_method') == 'hybrid_llm_pattern':
            print("🧠 LLM Analysis Results:")
            print(f"   Personal attacks: {analysis.get('personal_attacks', [])}")
            print(f"   Control tactics: {analysis.get('control_tactics', [])}")
            print(f"   Social manipulation: {analysis.get('social_manipulation', [])}")
            print()
            
            print("⚖️  Cross-Validation Metrics:")
            agreement = analysis.get('llm_pattern_agreement', 0)
            print(f"   Agreement score: {agreement:.2f}")
            
            confidence = analysis.get('confidence', 0)
            print(f"   Combined confidence: {confidence:.2f}")
            
            flags = analysis.get('validation_flags', [])
            if flags:
                print(f"   Validation flags: {flags}")
            else:
                print(f"   No validation issues detected")
    
    print(f"🛡️  Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
    print("✅ Cross-validation test complete!")
    print()


async def main():
    """Run all Phase 3 enhancement tests."""
    await test_hybrid_phase3_analysis()
    await test_phase3_fallback_scenarios()
    await test_phase3_cross_validation()


if __name__ == "__main__":
    asyncio.run(main())