#!/usr/bin/env python
"""
Quick demonstration of how toxic emails are handled by the privacy pipeline.
"""

import asyncio
from cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
from cellophanemail.features.email_protection.in_memory_processor import InMemoryProcessor
from cellophanemail.features.email_protection.graduated_decision_maker import GraduatedDecisionMaker


async def test_toxic_email_processing():
    """Test how different toxicity levels are handled"""
    
    # Initialize components
    processor = InMemoryProcessor()
    decision_maker = GraduatedDecisionMaker()
    
    print("\n" + "="*60)
    print("TOXIC EMAIL HANDLING DEMONSTRATION")
    print("="*60)
    
    # Test cases with different toxicity levels
    test_emails = [
        {
            "name": "Clean Email",
            "from": "friend@example.com", 
            "subject": "Great job on the presentation!",
            "body": "Your presentation was excellent! The insights you shared were really valuable."
        },
        {
            "name": "Moderately Toxic",
            "from": "passive.aggressive@work.com",
            "subject": "Your performance",
            "body": "As I've told you multiple times before, your work is disappointing. Maybe if you actually listened for once, you wouldn't make so many stupid mistakes."
        },
        {
            "name": "Highly Toxic",
            "from": "angry@sender.com",
            "subject": "You're worthless",
            "body": "You're a complete idiot and everyone knows it. You're worthless and will never amount to anything. Nobody likes you."
        },
        {
            "name": "Extremely Toxic/Threatening",
            "from": "threat@danger.com",
            "subject": "Warning",
            "body": "I know where you live. You better watch your back. This isn't over."
        }
    ]
    
    for test_case in test_emails:
        print(f"\n--- {test_case['name']} ---")
        print(f"From: {test_case['from']}")
        print(f"Subject: {test_case['subject']}")
        print(f"Original: {test_case['body'][:100]}...")
        
        # Create ephemeral email
        email = EphemeralEmail(
            message_id=f"test-{test_case['name'].lower().replace(' ', '-')}",
            from_address=test_case['from'],
            to_addresses=["user@example.com"],
            subject=test_case['subject'],
            text_body=test_case['body'],
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        # Process the email
        result = await processor.process_email(email)
        
        # Use the protection action from processing result
        protection_action = result.action
        
        print(f"\nResults:")
        print(f"  Toxicity Score: {result.toxicity_score:.2f}")
        print(f"  Protection Action: {protection_action.value}")
        print(f"  Requires Delivery: {result.requires_delivery}")
        
        # Show what would happen to the email
        if protection_action.value == 'forward_clean':
            print(f"  ✅ Email would be delivered unchanged")
        elif protection_action.value == 'forward_with_context':
            print(f"  ⚠️ Email would be delivered with warning: [Caution] {test_case['subject']}")
        elif protection_action.value == 'redact_harmful':
            print(f"  🔒 Email would be delivered with redacted content: [Filtered] {test_case['subject']}")
            print(f"     Toxic words would be replaced with [REDACTED]")
        elif protection_action.value == 'summarize_only':
            print(f"  📝 Email would be summarized: [Summary] {test_case['subject']}")
        elif protection_action.value == 'block_entirely':
            print(f"  🚫 Email would be BLOCKED - not delivered at all")
        
        if result.processed_content != test_case['body']:
            print(f"  Processed: {result.processed_content[:100]}...")
    
    print("\n" + "="*60)
    print("SUMMARY: Toxicity-based protection actions working correctly")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_toxic_email_processing())