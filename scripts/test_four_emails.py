#!/usr/bin/env python3
"""
Test set of 4 emails with varying levels of harmful content.
Tests the Four Horsemen detection and filtering capabilities.
"""

import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(from_addr, subject, body, email_num):
    """Send a single test email."""
    print(f"\n📧 Sending Email #{email_num}: {subject}")
    
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = 'recipient@cellophanemail.com'
    msg['Subject'] = subject
    msg['Message-ID'] = f'<test-{email_num}-{int(time.time())}@cellophanemail.com>'
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('localhost', 2525)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email #{email_num} sent successfully")
        print(f"   From: {from_addr}")
        print(f"   Subject: {subject}")
        return True
    except Exception as e:
        print(f"❌ Email #{email_num} failed: {e}")
        return False

def main():
    """Send 4 test emails with different levels of harmful content."""
    print("🧪 Testing CellophoneMail with 4 different email types")
    print("   Watch your SMTP server logs to see Four Horsemen analysis")
    print("=" * 60)
    
    emails = [
        # Email 1: SAFE - Normal professional communication
        {
            'from': 'colleague@company.com',
            'subject': 'Meeting Notes from Today',
            'body': '''Hi there,

Here are the notes from today's meeting:

- Discussed the quarterly budget
- Reviewed project timeline
- Scheduled follow-up for next week

Let me know if you have any questions.

Best regards,
John'''
        },
        
        # Email 2: WARNING - Mild criticism but not abusive
        {
            'from': 'manager@company.com',
            'subject': 'Project Feedback',
            'body': '''Hi,

I reviewed your latest report and wanted to provide some feedback.

The analysis could be more thorough, and some of the conclusions seem rushed. Please take more time to review your work before submission.

We should discuss this further.

Thanks'''
        },
        
        # Email 3: HARMFUL - Contains criticism + defensiveness
        {
            'from': 'angry.client@company.com', 
            'subject': 'This is completely unacceptable',
            'body': '''This is absolutely ridiculous!

Your team completely failed to deliver what was promised. This kind of incompetence is exactly why I never should have trusted your company in the first place.

I'm not going to waste any more time explaining what should be obvious to anyone with basic professional skills.

Fix this immediately or we're done.'''
        },
        
        # Email 4: ABUSIVE - Multiple horsemen (contempt, criticism, stonewalling)
        {
            'from': 'toxic.person@example.com',
            'subject': 'You are worthless',
            'body': '''You disgust me. 

Your pathetic attempts at being helpful are laughable. You never listen to anything I say, you always make excuses, and you're too stupid to understand basic concepts.

I'm done trying to explain things to someone as incompetent as you. Don't bother responding - I won't read it.

You're a waste of time and completely worthless.'''
        }
    ]
    
    successful_sends = 0
    
    for i, email in enumerate(emails, 1):
        success = send_email(
            email['from'],
            email['subject'], 
            email['body'],
            i
        )
        
        if success:
            successful_sends += 1
            
        # Wait between emails to see analysis in logs
        if i < len(emails):
            print("   ⏳ Waiting 2 seconds for processing...")
            time.sleep(2)
    
    print(f"\n📊 Results: {successful_sends}/{len(emails)} emails sent successfully")
    print("   Check your SMTP server logs to see:")
    print("   - Four Horsemen analysis for each email") 
    print("   - Toxicity scores")
    print("   - Forward/block decisions")
    print("   - Database logging")

if __name__ == "__main__":
    main()