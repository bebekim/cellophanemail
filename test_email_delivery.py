#!/usr/bin/env python3
"""Test email delivery with Postmark API."""

import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cellophanemail.core.email_message import EmailMessage
from cellophanemail.services.email_delivery import EmailDeliveryService


@pytest.mark.asyncio
async def test_postmark_delivery():
    """Test actual Postmark email delivery."""
    try:
        print("🚀 Testing Postmark email delivery...")
        
        # Create test email message (safe email)
        email_message = EmailMessage(
            id=uuid4(),
            from_address="test@example.com",
            to_addresses=["testuser88827346@gmail.com"],  # Use real test user
            subject="Test CellophoneMail Delivery",
            text_content="This is a test email from CellophoneMail delivery service.",
            html_content="<p>This is a test email from CellophoneMail delivery service.</p>",
            message_id=f"test-delivery-{uuid4()}",
            received_at=datetime.now(),
            source_plugin="test"
        )
        
        # Initialize delivery service
        delivery_service = EmailDeliveryService()
        
        # Send the email
        print(f"📧 Sending test email to: {email_message.to_addresses}")
        result = await delivery_service.send_email(email_message)
        
        # Check result
        if result.success:
            print(f"✅ Email sent successfully!")
            print(f"   Postmark Message ID: {result.message_id}")
        else:
            print(f"❌ Email delivery failed: {result.error}")
            
    except Exception as e:
        print(f"❌ Error testing email delivery: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Set required environment variables for testing
    # NOTE: You need to set POSTMARK_API_TOKEN environment variable
    
    if not os.getenv("POSTMARK_API_TOKEN"):
        print("❌ POSTMARK_API_TOKEN environment variable required")
        print("   Get your token from: https://postmarkapp.com/")
        print("   Run: export POSTMARK_API_TOKEN='your-token-here'")
        sys.exit(1)
    
    # Set delivery method to postmark
    os.environ["EMAIL_DELIVERY_METHOD"] = "postmark"
    os.environ["POSTMARK_FROM_EMAIL"] = "noreply@cellophanemail.com"
    
    print("Testing Postmark Email Delivery")
    print("=" * 40)
    asyncio.run(test_postmark_delivery())