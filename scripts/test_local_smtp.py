#!/usr/bin/env python3
"""
Test direct connection to local CellophoneMail SMTP server.
Simple test to verify the server is receiving emails.
"""

import smtplib
from email.mime.text import MIMEText
import time

print("🔍 Testing DIRECT connection to localhost:2525")
print("   This tests the CellophoneMail SMTP server directly")
print()

try:
    # Connect directly to your local server
    print("🤝 Connecting to localhost:2525...")
    server = smtplib.SMTP('localhost', 2525, timeout=30)
    server.set_debuglevel(1)
    
    print('🤝 EHLO...')
    server.ehlo()
    
    print('📧 Creating test message...')
    msg = MIMEText('Direct test: Hello from CellophoneMail test suite!')
    msg['Subject'] = 'CellophoneMail Local Test'
    msg['From'] = 'test@example.com'
    msg['To'] = 'recipient@cellophanemail.com'
    msg['Message-ID'] = f'<test-local-{int(time.time())}@cellophanemail.com>'
    
    print('📬 Sending email...')
    server.send_message(msg)
    
    server.quit()
    print('✅ LOCAL test successful!')
    print('   Check your server logs to see the Four Horsemen analysis')
    
except Exception as e:
    print(f'❌ LOCAL test failed: {e}')
    print('   Make sure ./bin/dev-smtp is running')