#!/usr/bin/env python3
"""
Send a single test email with custom content.
Useful for quick testing of specific content.
"""

import smtplib
import sys
from email.mime.text import MIMEText
import time

def send_test_email(subject="Test Email", body="Hello, this is a test message!", from_addr="test@example.com"):
    """Send a single test email."""
    print(f"📧 Sending test email to CellophoneMail SMTP server")
    print(f"   Subject: {subject}")
    print(f"   From: {from_addr}")
    print()
    
    msg = MIMEText(body)
    msg['From'] = from_addr
    msg['To'] = 'recipient@cellophanemail.com'
    msg['Subject'] = subject
    msg['Message-ID'] = f'<single-test-{int(time.time())}@cellophanemail.com>'
    
    try:
        server = smtplib.SMTP('localhost', 2525, timeout=30)
        server.send_message(msg)
        server.quit()
        
        print("✅ Email sent successfully!")
        print("   Check your SMTP server logs for Four Horsemen analysis")
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        print("   Make sure ./bin/dev-smtp is running")
        return False

def main():
    """Main function with command line argument support."""
    if len(sys.argv) > 1:
        # Custom message from command line
        body = " ".join(sys.argv[1:])
        send_test_email(body=body, subject="Custom Test Message")
    else:
        # Default test message
        send_test_email()

if __name__ == "__main__":
    main()