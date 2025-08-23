"""
Ad-hoc email test cases runner using streamlined processor architecture.

Uses single-pass LLM analysis (1-2 seconds) instead of legacy 4-phase pipeline (30+ seconds).
Simply add test cases and run with: python test_email_cases.py
"""

import asyncio
import sys
from dataclasses import dataclass
from typing import List, Optional

# Add src to path
sys.path.insert(0, 'src')

from cellophanemail.features.email_protection.streamlined_processor import StreamlinedEmailProtectionProcessor
from cellophanemail.features.email_protection.llm_analyzer import SimpleLLMAnalyzer
from cellophanemail.providers.contracts import EmailMessage
from cellophanemail.features.email_protection.graduated_decision_maker import ProtectionAction


@dataclass
class EmailTestCase:
    """A simple test case for email protection."""
    name: str
    subject: str
    body: str
    expected_action: Optional[ProtectionAction] = None  # None means just observe
    language: str = "en"
    notes: str = ""


# Add your test cases here - just append to this list!
TEST_CASES = [
    EmailTestCase(
        name="Clean professional email",
        subject="Meeting Follow-up", 
        body="Hi Bob, Thank you for the productive meeting yesterday. Please send the timeline by Friday. Best regards, Alice",
        expected_action=ProtectionAction.FORWARD_CLEAN,
        language="en"
    ),
    
    EmailTestCase(
        name="Subtle threat",
        subject="Urgent Request",
        body="You should really consider my offer soon before it's too late.",
        expected_action=ProtectionAction.FORWARD_WITH_CONTEXT,
        language="en"
    ),
    
    EmailTestCase(
        name="Personal attacks",
        subject="Feedback", 
        body="Your work is terrible and you're incompetent. Please send the report by Friday.",
        expected_action=ProtectionAction.REDACT_HARMFUL,
        language="en"
    ),
    
    EmailTestCase(
        name="Extreme toxicity",
        subject="You are pathetic",
        body="You are absolutely worthless and disgusting. I hate dealing with someone as stupid as you.",
        expected_action=ProtectionAction.BLOCK_ENTIRELY,
        language="en"
    ),
    
    EmailTestCase(
        name="Corporate leak threat (Zuckerberg 2010)",
        subject="Please Resign",
        body="This was an act of betrayal. So I'm asking whoever leaked this to resign immediately. If you don't resign, we will almost certainly find out who you are anyway. If you can't handle that, then just leave.",
        notes="Real corporate email with threats and ultimatums",
        language="en"
    ),
    
    EmailTestCase(
        name="Strategic business discussion (Zuckerberg 2022)",
        subject="FB app vision", 
        body="We've spent a lot of time recently on shifting resources from non-Reels/NF FB features to Reels and now to other apps as well. Even though the FB app's engagement is steady in many places, it feels like its cultural relevance is decreasing quickly and I worry that this may be a leading indicator of future health issues.",
        notes="Professional strategic discussion - should be clean",
        language="en"
    ),
    
    # Add more test cases here as needed...
    # Personal/sensitive test cases should be added locally and not committed to git
]


async def run_test_case(processor: StreamlinedEmailProtectionProcessor, test_case: EmailTestCase) -> dict:
    """Run a single test case and return results."""
    
    email = EmailMessage(
        message_id=f"test-{test_case.name.lower().replace(' ', '-')}",
        from_address="test@example.com",
        to_addresses=["user@example.com"],
        subject=test_case.subject,
        text_body=test_case.body,
        html_body=None
    )
    
    result = await processor.process_email(email, "user@example.com")
    
    return {
        'test_case': test_case,
        'result': result,
        'passed': test_case.expected_action is None or result.protection_action == test_case.expected_action
    }


async def main():
    """Run all test cases."""
    
    # Initialize streamlined processor with real LLM (deterministic for consistent testing)
    processor = StreamlinedEmailProtectionProcessor(temperature=0.0)
    
    print("🧪 Running Email Protection Test Cases")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] {test_case.name} ({test_case.language})")
        print("-" * 40)
        
        try:
            test_result = await run_test_case(processor, test_case)
            result = test_result['result']
            
            # Print results
            print(f"📧 Subject: {test_case.subject}")
            print(f"📝 Body: {test_case.body[:100]}{'...' if len(test_case.body) > 100 else ''}")
            print(f"🎯 Action: {result.protection_action}")
            print(f"📊 Toxicity: {result.analysis.toxicity_score:.3f}")
            print(f"🤔 Reasoning: {result.decision_reasoning}")
            
            if test_case.notes:
                print(f"📋 Notes: {test_case.notes}")
            
            # Check expectation
            if test_case.expected_action:
                if test_result['passed']:
                    print(f"✅ PASS - Got expected {test_case.expected_action}")
                    passed += 1
                else:
                    print(f"❌ FAIL - Expected {test_case.expected_action}, got {result.protection_action}")
                    failed += 1
            else:
                print("👀 OBSERVE - No expectation set")
                
        except Exception as e:
            print(f"💥 ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed} passed, {failed} failed, {len(TEST_CASES)} total")
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {failed} tests need attention")


if __name__ == "__main__":
    asyncio.run(main())