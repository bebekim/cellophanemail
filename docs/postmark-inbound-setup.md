# Postmark Inbound Email Setup for CellophoneMail

## Overview
Configure Postmark to receive emails at `@cellophanemail.com` and forward them to your app via webhooks.

## Step 1: Create Inbound Server in Postmark

1. Log into Postmark Dashboard
2. Click "Servers" → "Add Server"
3. Choose "Inbound" server type
4. Name it: "CellophoneMail Inbound"

## Step 2: Configure Inbound Domain

1. In your Inbound Server, go to "Settings" → "Inbound"
2. Add domain: `cellophanemail.com`
3. Set webhook URL: 
   - Development: `https://ngrok-url.ngrok.io/webhooks/postmark`
   - Production: `https://your-app.com/webhooks/postmark`

## Step 3: DNS Configuration

Add these MX records to your domain's DNS:

```
Priority | Host | Value
---------|------|-------
10       | @    | inbound.postmarkapp.com
```

## Step 4: Webhook Configuration

The webhook will receive POST requests with email data:

```json
{
  "From": "sender@example.com",
  "To": "user@cellophanemail.com",
  "Subject": "Test Email",
  "TextBody": "Email content here",
  "MessageID": "unique-id",
  "Headers": [...],
  ...
}
```

## Architecture Comparison

### Traditional SMTP Setup:
```
Internet → Port 25/587 → Your SMTP Server → Your App
```

### Postmark Inbound Setup:
```
Internet → Postmark's MX → Postmark processes → HTTP POST → Your Webhook
```

## Benefits of Postmark Inbound

1. **No SMTP Management**: No ports, no server software
2. **Built-in Spam Filtering**: Postmark filters before forwarding
3. **Automatic Parsing**: Email already parsed into JSON
4. **Attachments Handled**: Base64 encoded in webhook
5. **High Availability**: Postmark handles uptime
6. **Simple Integration**: Just handle HTTP POST requests

## Testing Locally

Use ngrok to expose local webhook:
```bash
ngrok http 8000
```

Then update Postmark webhook URL to ngrok URL.

## Complete Flow

1. User sends email to `yh.kim@cellophanemail.com`
2. MX records route to Postmark
3. Postmark receives and parses email
4. Postmark POSTs to your webhook
5. Your app processes with Four Horsemen
6. Your app sends filtered response via Postmark Outbound API
7. User receives filtered email in Gmail

No SMTP server needed at any point!