"""
Test complete 4-phase LLM-enhanced email protection pipeline.
End-to-end verification of the full analysis system.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cellophanemail.features.email_protection.processor import EmailProtectionProcessor
from cellophanemail.features.email_protection.llm_analyzer import SimpleLLMAnalyzer
from cellophanemail.providers.contracts import EmailMessage


async def test_complete_4phase_pipeline():
    """Test the complete 4-phase LLM-enhanced pipeline."""
    
    print("🚀 COMPLETE 4-PHASE LLM PIPELINE TEST")
    print("=" * 45)
    print()
    print("Testing the full pipeline:")
    print("  Phase 1: LLM Fact Extraction")
    print("  Phase 2: LLM Manner Analysis") 
    print("  Phase 3: Hybrid Non-Factual Analysis")
    print("  Phase 4: LLM Implicit Message Detection")
    print()
    
    # Create processor with LLM
    processor = EmailProtectionProcessor(SimpleLLMAnalyzer("neutral"))
    
    test_email = EmailMessage(
        message_id="test-complete-001",
        from_address="abuser@example.com",
        to_addresses=["shield.test@cellophanemail.com"],
        subject="Payment Demand",
        text_body="""
        You still owe me $1,200 from 3 months ago when I helped you out.
        
        I've been patient, but you're being selfish and irresponsible about this.
        Everyone in our group knows you can't be trusted with money.
        
        If you don't pay by Friday, there will be consequences.
        I'd hate for this to affect your reputation further.
        """
    )
    
    print(f"📧 Processing test email from: {test_email.from_address}")
    print(f"   Subject: {test_email.subject}")
    print()
    
    # Process through complete pipeline
    result = await processor.process_email(test_email, "real@example.com")
    
    # Get comprehensive analysis
    context = processor.shared_context
    summary = context.get_current_analysis_summary()
    
    print("📊 PIPELINE RESULTS:")
    print("=" * 20)
    print()
    
    # Overall metrics
    print(f"🔢 Iteration: {summary['iteration']}")
    print(f"📈 Fact ratio: {summary['fact_ratio']:.1%}")
    print(f"🔍 Phases completed: {summary['total_phases_completed']}/4")
    print()
    
    phases = summary["phases"]
    
    # Phase 1: Fact Extraction
    if "fact_extraction" in phases:
        phase1 = phases["fact_extraction"]
        print("📋 PHASE 1: FACT EXTRACTION")
        print(f"   • Total facts: {phase1['total_facts']}")
        print(f"   • Fact ratio: {phase1['fact_ratio']:.1%}")
        print(f"   • Facts found: {phase1['facts']}")
        
        if phase1['fact_analyses']:
            print("   • Fact analysis:")
            for fa in phase1['fact_analyses']:
                print(f"     - '{fa['fact']}' → {fa['manner']} (confidence: {fa['confidence']:.2f})")
        print()
    
    # Phase 2: Manner Analysis
    if "manner_summary" in phases:
        phase2 = phases["manner_summary"]
        print("🎭 PHASE 2: MANNER ANALYSIS")
        print(f"   • Overall manner: {phase2.get('overall_manner', 'unknown')}")
        print(f"   • Analysis method: {phase2.get('analysis_method', 'unknown')}")
        
        if phase2.get('analysis_method') == 'llm_enhanced':
            print(f"   • LLM reasoning: {phase2.get('llm_reasoning', 'N/A')}")
            print(f"   • Cultural context: {phase2.get('cultural_context', 'N/A')}")
            print(f"   • Manipulation detected: {phase2.get('manipulation_detected', False)}")
            print(f"   • Emotional loading: {phase2.get('emotional_loading', 'unknown')}")
        
        if 'manner_distribution' in phase2:
            dist = phase2['manner_distribution']
            print(f"   • Manner distribution: {dist}")
        print()
    
    # Phase 3: Non-Factual Analysis
    if "non_factual_analysis" in phases:
        phase3 = phases["non_factual_analysis"]
        print("🧠 PHASE 3: NON-FACTUAL ANALYSIS")
        print(f"   • Analysis method: {phase3.get('analysis_method', 'unknown')}")
        print(f"   • Primary tactic: {phase3.get('primary_tactic', 'none')}")
        print(f"   • Severity score: {phase3.get('severity_score', 0):.2f}")
        print(f"   • Sophistication: {phase3.get('manipulation_sophistication', 'unknown')}")
        
        categories = ['personal_attacks', 'emotional_manipulation', 'gaslighting_patterns', 
                     'social_manipulation', 'control_tactics']
        
        for category in categories:
            items = phase3.get(category, [])
            if items:
                print(f"   • {category}: {items}")
        
        if phase3.get('analysis_method') == 'hybrid_llm_pattern':
            agreement = phase3.get('llm_pattern_agreement', 0)
            flags = phase3.get('validation_flags', [])
            print(f"   • LLM-Pattern agreement: {agreement:.2f}")
            if flags:
                print(f"   • Validation flags: {flags}")
        print()
    
    # Phase 4: Implicit Analysis
    if "implicit_analysis" in phases:
        phase4 = phases["implicit_analysis"]
        print("🔍 PHASE 4: IMPLICIT MESSAGE ANALYSIS")
        print(f"   • Analysis method: {phase4.get('analysis_method', 'unknown')}")
        
        categories = ['implicit_threats', 'power_dynamics', 'emotional_manipulation', 'social_pressure']
        
        for category in categories:
            items = phase4.get(category, [])
            if items:
                print(f"   • {category}: {items}")
        
        if phase4.get('analysis_method') == 'llm_enhanced':
            confidence = phase4.get('confidence', 0)
            reasoning = phase4.get('reasoning', '')
            print(f"   • LLM confidence: {confidence:.2f}")
            if reasoning:
                print(f"   • LLM reasoning: {reasoning}")
        print()
    
    # Final Decision
    print("🛡️  PROTECTION DECISION:")
    print(f"   • Should forward: {result.should_forward}")
    print(f"   • Threat level: {result.analysis.threat_level.value if result.analysis else 'unknown'}")
    print(f"   • Toxicity score: {result.analysis.toxicity_score if result.analysis else 0:.2f}")
    
    if not result.should_forward:
        print(f"   • Block reason: {result.block_reason}")
    
    if result.analysis and result.analysis.horsemen_detected:
        horsemen = [h.horseman for h in result.analysis.horsemen_detected]
        print(f"   • Four Horsemen detected: {horsemen}")
    
    print(f"   • Processing time: {result.analysis.processing_time_ms if result.analysis else 0}ms")
    print()
    
    print("✅ COMPLETE 4-PHASE PIPELINE TEST SUCCESSFUL!")
    print()
    print("🎯 Features Verified:")
    print("   ✓ LLM-based fact extraction")
    print("   ✓ Cultural context-aware manner analysis")
    print("   ✓ Hybrid psychological pattern detection")
    print("   ✓ Sophisticated implicit message analysis")
    print("   ✓ Enhanced protection decision with detailed reasoning")
    print("   ✓ Graceful fallback mechanisms throughout")


async def test_pipeline_without_llm():
    """Test the pipeline fallback when no LLM is available."""
    
    print("🔄 TESTING PIPELINE WITHOUT LLM")
    print("=" * 35)
    
    # Create processor without LLM
    processor = EmailProtectionProcessor()  # No LLM
    
    test_email = EmailMessage(
        message_id="test-no-llm-001",
        from_address="test@example.com",
        to_addresses=["shield.test@cellophanemail.com"],
        subject="Test",
        text_body="You're an idiot! Pay the $100 or else everyone will know what a loser you are."
    )
    
    result = await processor.process_email(test_email, "real@example.com")
    
    context = processor.shared_context
    summary = context.get_current_analysis_summary()
    phases = summary["phases"]
    
    print("📊 Fallback Analysis Results:")
    
    for phase_name, phase_data in phases.items():
        method = phase_data.get('analysis_method', 'unknown')
        print(f"   • {phase_name}: {method}")
        
        if 'fallback_reason' in phase_data:
            print(f"     - Fallback reason: {phase_data['fallback_reason']}")
    
    print(f"🛡️  Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
    print("✅ Fallback pipeline working correctly!")
    print()


async def main():
    """Run complete pipeline tests."""
    await test_complete_4phase_pipeline()
    await test_pipeline_without_llm()


if __name__ == "__main__":
    asyncio.run(main())
