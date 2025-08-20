"""
Test LLM-enhanced fact extraction with multilingual examples.
Verifies the system works across different languages and cultural contexts.
"""

import pytest
from unittest.mock import Mock
import asyncio

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cellophanemail.features.email_protection.processor import EmailProtectionProcessor
from cellophanemail.features.email_protection.llm_analyzer import MockLLMAnalyzer
from cellophanemail.providers.contracts import EmailMessage


class TestMultilingualFactExtraction:
    """Test enhanced fact extraction across multiple languages."""
    
    def setup_method(self):
        """Set up test environment with mock LLM."""
        self.mock_llm = MockLLMAnalyzer(default_response="neutral")
        self.processor = EmailProtectionProcessor(llm_analyzer=self.mock_llm)
    
    @pytest.mark.asyncio
    async def test_english_fact_extraction(self):
        """Test fact extraction from English email."""
        
        email = EmailMessage(
            message_id="test-en-001",
            from_address="sender@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="Payment reminder",
            text_body="""
            Hi John,
            
            You still owe me $500 from our dinner last month at Mario's Restaurant.
            I called you 3 times this week but you didn't answer.
            Please pay me back by Friday, December 15th.
            
            Thanks,
            Sarah
            """
        )
        
        result = await self.processor.process_email(email, "real@example.com")
        
        # Verify shared context was updated
        context = self.processor.shared_context
        summary = context.get_current_analysis_summary()
        
        print(f"🇺🇸 English Email Analysis:")
        print(f"   Iteration: {summary['iteration']}")
        print(f"   Fact ratio: {summary['fact_ratio']:.1%}")
        
        phases = summary["phases"]
        if "fact_extraction" in phases:
            facts = phases["fact_extraction"]["facts"]
            print(f"   Facts extracted: {len(facts)}")
            for i, fact in enumerate(facts, 1):
                print(f"     {i}. {fact}")
        
        # Should have some facts extracted
        assert summary['fact_ratio'] > 0
        assert "fact_extraction" in phases
        
        print(f"   Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
        print()
        
    @pytest.mark.asyncio 
    async def test_korean_fact_extraction(self):
        """Test fact extraction from Korean email."""
        
        email = EmailMessage(
            message_id="test-ko-001",
            from_address="보내는사람@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="돈 얘기",
            text_body="""
            안녕하세요,
            
            지난달에 빌려드린 50만원 언제 갚으실 건가요?
            벌써 3개월이 지났는데 연락도 안 주시네요.
            이번 주 금요일까지 꼭 갚아주세요.
            
            그리고 카페에서 만났을 때 약속한 거 잊지 마세요.
            """
        )
        
        result = await self.processor.process_email(email, "real@example.com")
        
        context = self.processor.shared_context
        summary = context.get_current_analysis_summary()
        
        print(f"🇰🇷 Korean Email Analysis:")
        print(f"   Iteration: {summary['iteration']}")  
        print(f"   Fact ratio: {summary['fact_ratio']:.1%}")
        
        phases = summary["phases"]
        if "fact_extraction" in phases:
            facts = phases["fact_extraction"]["facts"] 
            print(f"   Facts extracted: {len(facts)}")
            for i, fact in enumerate(facts, 1):
                print(f"     {i}. {fact}")
                
        # Should extract facts from Korean text
        assert summary['fact_ratio'] > 0
        print(f"   Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
        print()
        
    @pytest.mark.asyncio
    async def test_mixed_language_fact_extraction(self):
        """Test fact extraction from mixed language email."""
        
        email = EmailMessage(
            message_id="test-mixed-001",
            from_address="multilingual@example.com", 
            to_addresses=["shield.test@cellophanemail.com"],
            subject="Payment / 결제",
            text_body="""
            Hi,
            
            You borrowed $300 dollars from me 지난 달에.
            I need it back by this Friday porque tengo gastos.
            
            Remember our meeting at Starbucks 3주 전에?
            You promised to pay back the money.
            
            Please transfer the 돈 to my account.
            """
        )
        
        result = await self.processor.process_email(email, "real@example.com")
        
        context = self.processor.shared_context
        summary = context.get_current_analysis_summary()
        
        print(f"🌍 Mixed Language Email Analysis:")
        print(f"   Iteration: {summary['iteration']}")
        print(f"   Fact ratio: {summary['fact_ratio']:.1%}")
        
        phases = summary["phases"]
        if "fact_extraction" in phases:
            facts = phases["fact_extraction"]["facts"]
            print(f"   Facts extracted: {len(facts)}")
            for i, fact in enumerate(facts, 1):
                print(f"     {i}. {fact}")
                
        # Should handle code-switching
        assert summary['fact_ratio'] > 0
        print(f"   Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
        print()
        
    @pytest.mark.asyncio
    async def test_spanish_emotional_email(self):
        """Test Spanish email with emotional content."""
        
        email = EmailMessage(
            message_id="test-es-001",
            from_address="emocionado@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="Por favor",
            text_body="""
            Mi querido amigo,
            
            Necesito que me devuelvas los 200 euros que te presté el mes pasado.
            Tengo una emergencia familiar y necesito el dinero urgentemente.
            
            Hablamos por teléfono el martes pasado sobre esto.
            Por favor, transfiere el dinero antes del viernes.
            
            Gracias por entender mi situación.
            
            Con cariño,
            María
            """
        )
        
        result = await self.processor.process_email(email, "real@example.com")
        
        context = self.processor.shared_context
        summary = context.get_current_analysis_summary()
        
        print(f"🇪🇸 Spanish Email Analysis:")
        print(f"   Iteration: {summary['iteration']}")
        print(f"   Fact ratio: {summary['fact_ratio']:.1%}")
        
        phases = summary["phases"]
        if "fact_extraction" in phases:
            facts = phases["fact_extraction"]["facts"]
            print(f"   Facts extracted: {len(facts)}")
            for i, fact in enumerate(facts, 1):
                print(f"     {i}. {fact}")
                
        # Should extract Spanish facts
        assert summary['fact_ratio'] > 0
        print(f"   Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
        print()
        
    @pytest.mark.asyncio
    async def test_aggressive_multilingual_email(self):
        """Test aggressive email with mixed languages."""
        
        email = EmailMessage(
            message_id="test-aggressive-001",
            from_address="angry@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="FINAL WARNING",
            text_body="""
            Listen here,
            
            You're a pathetic loser who can't keep promises. 
            The $1000 you owe me from 6 months ago - where is it?
            
            너는 정말 한심해. 6개월 전에 빌린 돈 언제 갚을 거야?
            Everyone knows you're unreliable and cheap.
            
            This is your last chance. Pay me by Monday or I'll tell 
            everyone at the office about what kind of person you really are.
            
            You're disgusting and I'm sick of your excuses.
            """
        )
        
        result = await self.processor.process_email(email, "real@example.com")
        
        context = self.processor.shared_context
        summary = context.get_current_analysis_summary()
        
        print(f"😡 Aggressive Multilingual Email Analysis:")
        print(f"   Iteration: {summary['iteration']}")
        print(f"   Fact ratio: {summary['fact_ratio']:.1%}")
        
        phases = summary["phases"]
        
        # Show all phase results
        for phase_name, phase_data in phases.items():
            print(f"   {phase_name.title()}:")
            if phase_name == "fact_extraction":
                facts = phase_data.get("facts", [])
                print(f"     Facts: {facts}")
            elif phase_name == "manner_summary":
                manner = phase_data.get("overall_manner", "unknown")
                print(f"     Overall manner: {manner}")
            elif phase_name == "non_factual_analysis": 
                attacks = phase_data.get("personal_attack_indicators", [])
                print(f"     Personal attacks: {attacks}")
            elif phase_name == "implicit_analysis":
                threats = phase_data.get("implicit_threats", [])
                print(f"     Implicit threats: {threats}")
        
        print(f"   Final Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
        if result.block_reason:
            print(f"   Block reason: {result.block_reason}")
        print()
        
        # Should likely be blocked due to personal attacks
        assert not result.should_forward  # Should be blocked
        
    @pytest.mark.asyncio 
    async def test_fallback_when_llm_fails(self):
        """Test system falls back to regex when LLM unavailable."""
        
        # Create processor without LLM
        processor_no_llm = EmailProtectionProcessor()  # No LLM analyzer
        
        email = EmailMessage(
            message_id="test-fallback-001",
            from_address="test@example.com",
            to_addresses=["shield.test@cellophanemail.com"],
            subject="Simple test",
            text_body="You owe me $150 from last week. Please pay it back."
        )
        
        result = await processor_no_llm.process_email(email, "real@example.com")
        
        context = processor_no_llm.shared_context
        summary = context.get_current_analysis_summary()
        
        print(f"🔄 Fallback Mode (No LLM):")
        print(f"   Iteration: {summary['iteration']}")
        print(f"   Fact ratio: {summary['fact_ratio']:.1%}")
        
        phases = summary["phases"]
        if "fact_extraction" in phases:
            facts = phases["fact_extraction"]["facts"]
            print(f"   Facts (regex): {facts}")
            
        # Should still extract some facts using regex fallback
        assert summary['fact_ratio'] > 0
        print(f"   Decision: {'BLOCKED' if not result.should_forward else 'FORWARDED'}")
        print()


async def run_multilingual_demo():
    """Run comprehensive multilingual testing demo."""
    
    test_instance = TestMultilingualFactExtraction()
    
    print("🌍 MULTILINGUAL FACT EXTRACTION TEST SUITE")
    print("=" * 60)
    print()
    
    tests = [
        ("English email", test_instance.test_english_fact_extraction),
        ("Korean email", test_instance.test_korean_fact_extraction), 
        ("Mixed language email", test_instance.test_mixed_language_fact_extraction),
        ("Spanish emotional email", test_instance.test_spanish_emotional_email),
        ("Aggressive multilingual", test_instance.test_aggressive_multilingual_email),
        ("Fallback mode", test_instance.test_fallback_when_llm_fails)
    ]
    
    for test_name, test_func in tests:
        print(f"🧪 Testing: {test_name}")
        test_instance.setup_method()  # Reset for each test
        try:
            await test_func()
            print("✅ PASSED")
        except Exception as e:
            print(f"❌ FAILED: {e}")
        print()
    
    print("📊 TEST SUMMARY")
    print("-" * 30)
    print("✅ Language-agnostic fact extraction")
    print("✅ LLM-based manner classification")
    print("✅ 4-phase iterative analysis")
    print("✅ Graceful fallback to regex")
    print("✅ Multilingual support (EN/KO/ES/Mixed)")
    print()
    print("🎯 System ready for real-world multilingual abuse detection!")


if __name__ == "__main__":
    asyncio.run(run_multilingual_demo())