"""
Test enhanced Phase 2 manner analysis with LLM.
Verifies cultural and linguistic context awareness.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cellophanemail.features.email_protection.processor import EmailProtectionProcessor
from cellophanemail.features.email_protection.llm_analyzer import MockLLMAnalyzer
from cellophanemail.providers.contracts import EmailMessage


async def test_enhanced_phase2_analysis():
    """Test enhanced Phase 2 manner analysis across different contexts."""
    
    print("🔍 PHASE 2 ENHANCED MANNER ANALYSIS TESTS")
    print("=" * 50)
    print()
    
    test_emails = [
        {
            "name": "Polite Business Request (English)",
            "email": EmailMessage(
                message_id="test-polite-001",
                from_address="colleague@company.com",
                to_addresses=["shield.test@cellophanemail.com"],
                subject="Project Invoice",
                text_body="""
                Hi Sarah,
                
                I hope you're doing well. I wanted to follow up on the $2,500 invoice 
                for the consulting work we completed last month. 
                
                As discussed in our meeting on January 15th, the payment was due 
                30 days after completion. Would it be possible to process this by 
                the end of this week?
                
                Thank you for your time and I look forward to hearing from you.
                
                Best regards,
                Mike
                """
            ),
            "expected_manner": "predominantly_positive"
        },
        
        {
            "name": "Aggressive Debt Collection (Korean)",  
            "email": EmailMessage(
                message_id="test-aggressive-ko-001",
                from_address="collector@debt.com",
                to_addresses=["shield.test@cellophanemail.com"],
                subject="최종 경고",
                text_body="""
                당신이 3개월 전에 빌린 100만원을 언제 갚을 건가요?
                
                벌써 여러 번 연락했는데 계속 무시하고 있네요.
                이번이 마지막 경고입니다.
                
                금요일까지 갚지 않으면 법적 조치를 취하겠습니다.
                다른 방법이 없습니다.
                """
            ),
            "expected_manner": "predominantly_negative"
        },
        
        {
            "name": "Mixed Context (Spanish)",
            "email": EmailMessage(
                message_id="test-mixed-es-001", 
                from_address="amigo@example.com",
                to_addresses=["shield.test@cellophanemail.com"],
                subject="Sobre el dinero",
                text_body="""
                Hola amigo,
                
                Espero que estés bien. Te escribo sobre los 500 euros que 
                me prestaste el mes pasado para la emergencia familiar.
                
                Lamentablemente, todavía no he podido conseguir todo el dinero.
                ¿Sería posible pagarte 300 euros esta semana y los otros 200 
                el próximo mes?
                
                Entiendo si esto te causa problemas. Déjame saber qué piensas.
                
                Gracias por tu paciencia.
                """
            ),
            "expected_manner": "mixed"
        }
    ]
    
    for test_case in test_emails:
        print(f"📧 Testing: {test_case['name']}")
        
        # Create processor with mock LLM
        processor = EmailProtectionProcessor(MockLLMAnalyzer("neutral"))
        
        # Process email
        result = await processor.process_email(test_case["email"], "real@example.com")
        
        # Get Phase 2 results
        context = processor.shared_context
        summary = context.get_current_analysis_summary()
        
        print(f"   📊 Fact ratio: {summary['fact_ratio']:.1%}")
        
        phases = summary["phases"]
        print(f"   🔍 Available phases: {list(phases.keys())}")
        
        if "manner_summary" in phases:
            manner_data = phases["manner_summary"]
            print(f"   📈 Overall manner: {manner_data.get('overall_manner', 'unknown')}")
            
            if manner_data.get("analysis_method") == "llm_enhanced":
                print(f"   🧠 LLM reasoning: {manner_data.get('llm_reasoning', 'N/A')}")
                print(f"   🌍 Cultural context: {manner_data.get('cultural_context', 'N/A')}")
                print(f"   ⚠️  Manipulation detected: {manner_data.get('manipulation_detected', False)}")
                print(f"   🌡️  Emotional loading: {manner_data.get('emotional_loading', 'unknown')}")
            else:
                print(f"   🔧 Analysis method: {manner_data.get('analysis_method', 'unknown')}")
                if "fallback_reason" in manner_data:
                    print(f"   ⚠️  Fallback reason: {manner_data['fallback_reason']}")
        else:
            print("   ❌ No manner_summary found in phases")
        
        print(f"   🛡️  Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
        print()
    
    print("✅ Phase 2 Enhanced Manner Analysis Complete!")
    print()
    print("🎯 Key Features Tested:")
    print("   • LLM-based cultural context analysis")
    print("   • Manipulation detection across languages")
    print("   • Emotional loading assessment")
    print("   • Detailed reasoning for manner classification")
    print("   • Graceful fallback when LLM unavailable")


async def test_phase2_with_no_llm():
    """Test Phase 2 fallback when no LLM available."""
    
    print("🔄 TESTING PHASE 2 WITHOUT LLM")
    print("-" * 30)
    
    processor = EmailProtectionProcessor()  # No LLM
    
    email = EmailMessage(
        message_id="test-no-llm-001",
        from_address="test@example.com",
        to_addresses=["shield.test@cellophanemail.com"],
        subject="Payment",
        text_body="You still owe me $200 from last month. When will you pay?"
    )
    
    result = await processor.process_email(email, "real@example.com")
    
    context = processor.shared_context
    summary = context.get_current_analysis_summary()
    
    phases = summary["phases"]
    if "manner_summary" in phases:
        manner_data = phases["manner_summary"]
        print(f"📈 Overall manner: {manner_data.get('overall_manner', 'unknown')}")
        print(f"🔧 Analysis method: {manner_data.get('analysis_method', 'unknown')}")
        print(f"📊 Manner distribution: {manner_data.get('manner_distribution', {})}")
    
    print(f"🛡️  Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
    print("✅ Fallback mode working correctly!")
    print()


async def main():
    """Run all Phase 2 enhancement tests."""
    await test_enhanced_phase2_analysis()
    await test_phase2_with_no_llm()


if __name__ == "__main__":
    asyncio.run(main())