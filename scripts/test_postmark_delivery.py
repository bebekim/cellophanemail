#!/usr/bin/env python3
"""Test script for Postmark email delivery."""

import asyncio
import sys
import os
from pathlib import Path
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cellophanemail.config.settings import get_settings
from cellophanemail.core.email_delivery import EmailSenderFactory


@pytest.mark.asyncio
async def test_postmark_connection():
    """Test basic Postmark connection and email sending."""
    print("🧪 Testing Postmark Email Delivery")
    print("=" * 50)
    
    # Get settings
    settings = get_settings()
    config = settings.email_delivery_config
    
    print(f"📧 Email delivery method: {config['EMAIL_DELIVERY_METHOD']}")
    print(f"📮 Postmark API URL: https://api.postmarkapp.com/email")
    print(f"🔑 API token: {config['POSTMARK_API_TOKEN'][:8]}...")
    print(f"📤 From email: {config['POSTMARK_FROM_EMAIL']}")
    print()
    
    try:
        # Create Postmark sender
        print("🔧 Creating Postmark email sender...")
        sender = EmailSenderFactory.create_sender('postmark', config)
        print("✅ Postmark sender created successfully")
        print()
        
        # Test basic email sending
        print("📨 Sending test email...")
        
        # Test data (simulating a SAFE email)
        ai_result = {'ai_classification': 'SAFE'}
        original_email_data = {
            'original_subject': 'Postmark Test Email',
            'original_sender': 'test@example.com',
            'original_body': 'This is a test email to verify Postmark delivery is working.',
            'message_id': '<postmark-test123@example.com>',
            'content': 'This is a test email to verify Postmark delivery is working.'
        }
        
        success = await sender.send_filtered_email(
            recipient_shield_address='test@cellophanemail.com',  # Maps to goldenfermi@gmail.com
            ai_result=ai_result,
            original_email_data=original_email_data
        )
        
        if success:
            print("✅ Email sent successfully!")
            print("📬 Check your Gmail inbox for the test email")
            print("📧 Subject: Postmark Test Email")
            print("📤 From: CellophoneMail Shield <noreply@cellophanemail.com>")
            print("📥 To: goldenfermi@gmail.com")
        else:
            print("❌ Email sending failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()


@pytest.mark.asyncio
async def test_harmful_email():
    """Test sending a HARMFUL email (should show filtered message)."""
    print("\n" + "=" * 50)
    print("🧪 Testing HARMFUL Email Filtering")
    print("=" * 50)
    
    settings = get_settings()
    config = settings.email_delivery_config
    sender = EmailSenderFactory.create_sender('postmark', config)
    
    # Test data (simulating a HARMFUL email)
    ai_result = {
        'ai_classification': 'ABUSIVE',
        'horsemen_detected': ['criticism', 'contempt']
    }
    original_email_data = {
        'original_subject': 'You are terrible',
        'original_sender': 'abusiveparent@gmail.com',
        'original_body': 'You are incompetent and useless.',
        'message_id': '<postmark-harmful456@gmail.com>',
        'content': 'You are incompetent and useless.'
    }
    
    print("🚨 Sending harmful email test (should be filtered)...")
    
    success = await sender.send_filtered_email(
        recipient_shield_address='yh.kim@cellophanemail.com',
        ai_result=ai_result,
        original_email_data=original_email_data
    )
    
    if success:
        print("✅ Filtered email sent successfully!")
        print("📬 Check your Gmail inbox for the filtered notification")
        print("📧 Subject: [Filtered] You are terrible")
        print("📤 From: CellophoneMail Shield <noreply@cellophanemail.com>")
        print("🚨 Content: Should show filtering warning")
    else:
        print("❌ Email sending failed")


if __name__ == "__main__":
    print("🚀 CellophoneMail Postmark Delivery Test")
    print()
    
    # Run tests
    asyncio.run(test_postmark_connection())
    asyncio.run(test_harmful_email())
    
    print("\n" + "=" * 50)
    print("✨ Testing completed!")
    print("📧 Check your Gmail inbox: goldenfermi@gmail.com")
    print("🔍 Look for emails from: CellophoneMail Shield")
    print("=" * 50)