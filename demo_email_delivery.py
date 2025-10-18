#!/usr/bin/env python3
"""Demonstrate the email delivery system flow."""

import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
from cellophanemail.features.email_protection.in_memory_processor import ProcessingResult
from cellophanemail.features.email_protection.graduated_decision_maker import ProtectionAction
from cellophanemail.features.email_protection.integrated_delivery_manager import IntegratedDeliveryManager
from cellophanemail.features.email_protection.email_composition_strategy import DeliveryConfiguration


async def demo_email_delivery():
    """Demonstrate the email delivery pipeline."""

    print("🚀 CellophoneMail Email Delivery Demo")
    print("=" * 60)
    print("This demo shows the email delivery flow:")
    print("1. Receive email (simulated)")
    print("2. Process through AI analysis (simulated)")
    print("3. Apply delivery decision")
    print("4. Compose appropriate response")
    print("5. Attempt delivery (dry-run mode)")
    print("=" * 60)
    print()

    # Create a sample email that would come from the webhook
    print("📨 Step 1: Creating sample incoming email...")
    email = EphemeralEmail(
        message_id=str(uuid4()),
        from_address="sender@example.com",
        to_addresses=["user@cellophanemail.com"],
        subject="Important message about your project",
        text_body="Your work on this project has been disappointing and below standards.",
        html_body=None,
        ttl_seconds=300,
        user_email="actualuser@gmail.com"
    )
    print(f"   From: {email.from_address}")
    print(f"   To: {email.to_addresses[0]}")
    print(f"   Subject: {email.subject}")
    print()

    # Simulate AI processing result (HARMFUL email detected)
    print("🤖 Step 2: Simulating AI analysis...")
    processing_result = ProcessingResult(
        email_id=email.message_id,
        action=ProtectionAction.FORWARD_WITH_CONTEXT,
        toxicity_score=0.85,
        requires_delivery=True,
        delivery_targets=["actualuser@gmail.com"],
        analysis_summary="Detected criticism and contempt (Four Horsemen)",
        horsemen_detected=["criticism", "contempt"]
    )
    print(f"   Toxicity Score: {processing_result.toxicity_score}")
    print(f"   Action: {processing_result.action.value}")
    print(f"   Horsemen Detected: {', '.join(processing_result.horsemen_detected)}")
    print()

    # Configure delivery (dry-run mode for demo)
    print("⚙️ Step 3: Configuring delivery manager...")
    config = DeliveryConfiguration(
        sender_type="smtp",  # or "postmark"
        max_retries=3,
        dry_run=True,  # Don't actually send emails
        from_address="noreply@cellophanemail.com",
        config={
            "SMTP_DOMAIN": "cellophanemail.com",
            "EMAIL_USERNAME": "demo@cellophanemail.com",
            "OUTBOUND_SMTP_HOST": "smtp.gmail.com",
            "OUTBOUND_SMTP_PORT": "587",
            "EMAIL_PASSWORD": "dummy-password-for-demo"
        }
    )
    print(f"   Sender Type: {config.sender_type}")
    print(f"   Dry Run Mode: {config.dry_run}")
    print(f"   Max Retries: {config.max_retries}")
    print()

    # Initialize delivery manager
    try:
        print("📬 Step 4: Processing delivery...")
        delivery_manager = IntegratedDeliveryManager(config)

        # Attempt delivery
        result = await delivery_manager.deliver_email(processing_result, email)

        print()
        print("📊 Delivery Result:")
        print(f"   Success: {'✅' if result.success else '❌'}")
        print(f"   Protection Action: {result.protection_action.value}")
        print(f"   Toxicity Score: {result.toxicity_score}")
        print(f"   Attempts: {result.attempts}")
        if result.delivery_time_ms:
            print(f"   Delivery Time: {result.delivery_time_ms}ms")
        if result.error_message:
            print(f"   Error: {result.error_message}")
        print(f"   Sender Used: {result.email_sender_used}")

    except Exception as e:
        print(f"❌ Error during delivery: {e}")

    print()
    print("=" * 60)
    print("✨ Demo completed!")
    print()
    print("In production, this would:")
    print("• Actually send the email via SMTP or Postmark")
    print("• Include warning headers and modified content")
    print("• Track delivery metrics and success rates")
    print("=" * 60)


async def demo_safe_email():
    """Demo a SAFE email flow."""
    print("\n\n")
    print("📧 SAFE Email Demo")
    print("-" * 40)

    email = EphemeralEmail(
        message_id=str(uuid4()),
        from_address="friend@example.com",
        to_addresses=["user@cellophanemail.com"],
        subject="Great job on the presentation!",
        text_body="Your presentation was excellent. The team loved your ideas!",
        html_body=None,
        ttl_seconds=300,
        user_email="actualuser@gmail.com"
    )

    processing_result = ProcessingResult(
        email_id=email.message_id,
        action=ProtectionAction.FORWARD_CLEAN,
        toxicity_score=0.1,
        requires_delivery=True,
        delivery_targets=["actualuser@gmail.com"],
        analysis_summary="No harmful content detected",
        horsemen_detected=[]
    )

    print(f"From: {email.from_address}")
    print(f"Subject: {email.subject}")
    print(f"Toxicity: {processing_result.toxicity_score} (SAFE)")
    print(f"Action: {processing_result.action.value}")
    print("Result: Email would be forwarded without modification ✅")


if __name__ == "__main__":
    print("CellophoneMail Email Delivery System Demo")
    print("=========================================\n")

    # Run the harmful email demo
    asyncio.run(demo_email_delivery())

    # Run the safe email demo
    asyncio.run(demo_safe_email())