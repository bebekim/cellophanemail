#!/usr/bin/env python3
"""End-to-end test sending email through the complete pipeline."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import time

def send_test_email(subject, content, test_type="SAFE"):
    """Send a test email to trigger the full pipeline."""
    
    # Email configuration
    sender_email = "abusiveparent@gmail.com"  # Simulating the abusive sender
    recipient_email = "goldenfermi@gmail.com"  # Your email that forwards to cellophanemail
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Message-ID"] = f"<test-{datetime.now().timestamp()}@gmail.com>"
    
    # Create the plain-text and HTML version of your message
    text = content
    html = f"""\
    <html>
      <body>
        <p>{content}</p>
      </body>
    </html>
    """
    
    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    
    # Add HTML/plain-text parts to MIMEMultipart message
    message.attach(part1)
    message.attach(part2)
    
    # Send the email
    try:
        # Connect to Gmail SMTP server
        print(f"📤 Connecting to Gmail SMTP server...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        
        # You'll need to use your test sender credentials here
        # For now, let's use your goldenfermi account to simulate
        server.login("goldenfermi@gmail.com", "qgbt gvkc kaom bipo")
        
        text = message.as_string()
        server.sendmail("goldenfermi@gmail.com", recipient_email, text)
        server.quit()
        
        print(f"✅ {test_type} test email sent successfully!")
        print(f"📧 Subject: {subject}")
        print(f"📥 To: {recipient_email}")
        print(f"⏳ Email should be forwarded to yh.kim@cellophanemail.com")
        print(f"🔄 Then processed and sent back filtered\n")
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")


def main():
    print("🚀 CellophoneMail End-to-End Test")
    print("=" * 60)
    print("This test will send emails through the complete pipeline:")
    print("1. Send to goldenfermi@gmail.com")
    print("2. Gmail forwards to yh.kim@cellophanemail.com")
    print("3. Local SMTP server receives and processes")
    print("4. AI analyzes content (Four Horsemen)")
    print("5. Filtered result sent back to goldenfermi@gmail.com")
    print("=" * 60)
    print()
    
    # Test 1: Safe email
    print("📧 Test 1: SAFE Email")
    print("-" * 40)
    send_test_email(
        subject=f"E2E Test - Safe Email - {datetime.now().strftime('%H:%M:%S')}",
        content="Hi! This is a friendly test email. Hope you're having a great day! The weather is nice today.",
        test_type="SAFE"
    )
    
    time.sleep(2)
    
    # Test 2: Critical email (Four Horsemen - Criticism)
    print("📧 Test 2: HARMFUL Email (Criticism)")
    print("-" * 40)
    send_test_email(
        subject=f"E2E Test - Criticism - {datetime.now().strftime('%H:%M:%S')}",
        content="You never do anything right. You're always making mistakes and failing at everything you try.",
        test_type="HARMFUL"
    )
    
    time.sleep(2)
    
    # Test 3: Contempt email (Four Horsemen - Contempt)
    print("📧 Test 3: HARMFUL Email (Contempt)")
    print("-" * 40)
    send_test_email(
        subject=f"E2E Test - Contempt - {datetime.now().strftime('%H:%M:%S')}",
        content="You're pathetic. I can't believe how incompetent you are. You're worthless and everyone knows it.",
        test_type="HARMFUL"
    )
    
    time.sleep(2)
    
    # Test 4: Mixed content
    print("📧 Test 4: Mixed Content Email")
    print("-" * 40)
    send_test_email(
        subject=f"E2E Test - Mixed - {datetime.now().strftime('%H:%M:%S')}",
        content="I wanted to tell you about the meeting tomorrow at 3pm. Also, you're terrible at your job and everyone thinks you're useless.",
        test_type="MIXED"
    )
    
    print("\n" + "=" * 60)
    print("✅ All test emails sent!")
    print("\n📬 Check your Gmail inbox in a few moments for:")
    print("  1. SAFE email - Should arrive with original content + footer")
    print("  2. HARMFUL emails - Should arrive with [Filtered] prefix and warning")
    print("\n🔍 Watch the server logs to see processing in real-time:")
    print("  - Litestar server: Processing logs")
    print("  - SMTP server: Receiving and forwarding logs")
    print("=" * 60)


if __name__ == "__main__":
    main()