# Email Delivery Setup Guide

This guide shows how to configure and switch between SMTP and Postmark for outbound email delivery in CellophoneMail.

## 🏗️ Architecture Overview

The email delivery system uses a plugin architecture with 90% code reuse:

```
EmailProcessor → EmailSenderFactory → [SMTPEmailSender OR PostmarkEmailSender] → User
```

**Shared functionality (90%):**
- Shield address mapping (`yh.kim@cellophanemail.com` → `goldenfermi@gmail.com`)
- Email threading headers (Gmail conversation preservation)
- Anti-spoofing headers (proper From/Reply-To)
- Content formatting (SAFE vs HARMFUL email templates)

**Plugin-specific (10%):**
- SMTPEmailSender: Uses `aiosmtplib.send()`
- PostmarkEmailSender: Uses `httpx.post()` to Postmark API

## 📧 Email Flow

```
1. abusiveparent@gmail.com → goldenfermi@gmail.com (original email)
2. Gmail forwards → yh.kim@cellophanemail.com (user's shield address)
3. CellophoneMail processes → AI analysis (Four Horsemen)
4. System sends back → goldenfermi@gmail.com (filtered result)
```

**Key insight:** All outbound emails use:
```
From: CellophoneMail Shield <noreply@cellophanemail.com>
To: goldenfermi@gmail.com
Reply-To: reply-[conversation-id]@cellophanemail.com  # Future: reply routing
```

This preserves email threading and enables reply routing back to original senders.

## ⚙️ Configuration

### Option 1: SMTP Delivery (Default)

Add to your `.env` file:

```bash
# Basic email settings
EMAIL_DELIVERY_METHOD=smtp
SMTP_DOMAIN=cellophanemail.com
EMAIL_USERNAME=goldenfermi@gmail.com
EMAIL_PASSWORD=your_app_password_here

# Outbound SMTP settings
OUTBOUND_SMTP_HOST=smtp.gmail.com
OUTBOUND_SMTP_PORT=587
OUTBOUND_SMTP_USE_TLS=true
```

### Option 2: Postmark API Delivery

Add to your `.env` file:

```bash
# Basic email settings
EMAIL_DELIVERY_METHOD=postmark
SMTP_DOMAIN=cellophanemail.com
EMAIL_USERNAME=goldenfermi@gmail.com

# Postmark settings
POSTMARK_API_TOKEN=your_postmark_server_token_here
POSTMARK_FROM_EMAIL=noreply@cellophanemail.com
```

**Getting Postmark credentials:**
1. Sign up at [postmark.com](https://postmarkapp.com)
2. Create a server
3. Get your Server API Token from the "API Tokens" tab
4. Verify your sender email address (`noreply@cellophanemail.com`)

## 🚀 Usage

### Initialize EmailProcessor with Config

```python
from cellophanemail.config.settings import get_settings
from cellophanemail.core.email_processor import EmailProcessor

# Get configuration
settings = get_settings()
config = settings.email_delivery_config

# Create processor with email delivery
processor = EmailProcessor(config)

# Process emails (automatically uses configured delivery method)
result = await processor.process(email_message)
```

### Direct Plugin Usage

```python
from cellophanemail.core.email_delivery import EmailSenderFactory

# Create SMTP sender
smtp_sender = EmailSenderFactory.create_sender('smtp', {
    'SMTP_DOMAIN': 'cellophanemail.com',
    'EMAIL_USERNAME': 'goldenfermi@gmail.com',
    'EMAIL_PASSWORD': 'your_password',
    'OUTBOUND_SMTP_HOST': 'smtp.gmail.com',
    'OUTBOUND_SMTP_PORT': 587,
    'OUTBOUND_SMTP_USE_TLS': True
})

# Create Postmark sender
postmark_sender = EmailSenderFactory.create_sender('postmark', {
    'SMTP_DOMAIN': 'cellophanemail.com', 
    'EMAIL_USERNAME': 'goldenfermi@gmail.com',
    'POSTMARK_API_TOKEN': 'your_token',
    'POSTMARK_FROM_EMAIL': 'noreply@cellophanemail.com'
})

# Send filtered email (both have identical interface)
success = await sender.send_filtered_email(
    recipient_shield_address='yh.kim@cellophanemail.com',
    ai_result={'ai_classification': 'SAFE'},
    original_email_data={
        'original_subject': 'Hello',
        'original_sender': 'friend@example.com',
        'original_body': 'Nice message',
        'message_id': '<abc@example.com>'
    }
)
```

## 🔄 Switching Providers

To switch from SMTP to Postmark (or vice versa):

1. **Update `.env` file:**
   ```bash
   # Change this line
   EMAIL_DELIVERY_METHOD=postmark  # was: smtp
   
   # Add Postmark credentials
   POSTMARK_API_TOKEN=your_token_here
   POSTMARK_FROM_EMAIL=noreply@cellophanemail.com
   ```

2. **Restart your application** - no code changes needed!

3. **Verify in logs:**
   ```
   INFO: Initialized postmark email sender
   ```

## 🧪 Testing

Run the email delivery tests:

```bash
# Test individual plugins
pytest tests/test_smtp_sender.py -v
pytest tests/test_postmark_sender.py -v

# Test factory
pytest tests/test_email_sender_factory.py -v

# Test base functionality
pytest tests/test_base_email_sender.py -v
```

## 📊 Benefits

### SMTP Delivery
✅ **Simple setup** - just email credentials  
✅ **No external dependencies**  
✅ **Works with any SMTP provider**  
❌ Lower deliverability than specialized services  
❌ No advanced tracking  

### Postmark Delivery  
✅ **Better deliverability** - specialized email service  
✅ **Advanced tracking** - opens, clicks, bounces  
✅ **Better reputation management**  
✅ **Scalable** - handles high volume  
❌ Requires Postmark account  
❌ Additional API dependency  

## 🚦 Production Recommendations

**For development:** Use SMTP with Gmail App Passwords
**For production:** Use Postmark for better deliverability and tracking

**DNS Setup for Postmark:**
- Set up SPF, DKIM, and DMARC records
- Verify your sender domain
- Use a dedicated subdomain (e.g., `mail.cellophanemail.com`)

## 🔮 Future Enhancements

The plugin architecture makes it easy to add:
- **Gmail API sender** - Direct Gmail API integration
- **SendGrid sender** - Another email service option  
- **AWS SES sender** - Amazon email service
- **Reply routing** - Route replies back to original senders

Just implement the `BaseEmailSender` interface and register with `EmailSenderFactory`!

## ❓ Troubleshooting

**"No email sender configured":**
- Check `.env` file has correct EMAIL_DELIVERY_METHOD
- Verify required credentials are set
- Check logs for initialization errors

**Emails not being sent:**
- Check `should_forward=True` in processing results
- Verify email sender initialization succeeded
- Check network connectivity to SMTP/Postmark servers

**Threading broken in Gmail:**
- Verify `In-Reply-To` and `References` headers are set
- Check original email has valid `Message-ID`
- Ensure consistent thread management