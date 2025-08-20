# Testing Without Burning Through Email Quota

## Problem
During development and testing, it's easy to accidentally burn through your Postmark server quota by sending real emails. This document explains how to test safely without using your quota.

## Solution: Dry-Run Mode

The Postmark provider now supports a **dry-run mode** that simulates sending emails without making actual API calls.

## How to Enable Dry-Run Mode

### Method 1: Environment Variables (Recommended)
```bash
# Enable dry-run for Postmark
export POSTMARK_DRY_RUN=true

# Or enable test mode for all providers
export CELLOPHANEMAIL_TEST_MODE=true

# Optional: Log dry-run emails to file
export POSTMARK_LOG_DRY_RUN=true
```

### Method 2: Configuration
```python
config = ProviderConfig(
    enabled=True,
    config={
        "server_token": "your-token",
        "from_address": "test@cellophanemail.com",
        "dry_run": True  # Enable dry-run
    }
)
```

### Method 3: Use Test Environment File
```bash
# Copy the test environment template
cp .env.test .env

# This automatically enables:
# - POSTMARK_DRY_RUN=true
# - CELLOPHANEMAIL_TEST_MODE=true
# - Local SMTP as fallback
```

## Testing Script

Run the provided test script to verify dry-run mode:

```bash
# Test without using any quota
python scripts/test_dry_run.py

# Output will show:
# 🚫 Postmark running in DRY-RUN mode - no emails will be sent!
# 🔵 [DRY-RUN] Postmark send #1
# ✨ Test complete! No quota was used.
```

## What Happens in Dry-Run Mode

1. **No API Calls**: The provider skips all Postmark API calls
2. **Success Simulation**: All sends return `True` (success)
3. **Detailed Logging**: Full details logged to console
4. **Optional File Logging**: With `POSTMARK_LOG_DRY_RUN=true`, creates `postmark_dry_run_YYYYMMDD.jsonl`
5. **Send Counter**: Tracks number of simulated sends

## Dry-Run Log Format

When file logging is enabled, each simulated send creates a JSON entry:

```json
{
  "timestamp": "2024-01-20T10:30:00.000Z",
  "to": ["user@example.com"],
  "subject": "Test Email",
  "from": "noreply@cellophanemail.com",
  "message_id": "test-001",
  "dry_run": true
}
```

## Visual Indicators

The logs use clear visual indicators:

- 🚫 **DRY-RUN mode active** - Warning at initialization
- 🔵 **[DRY-RUN]** - Prefix for simulated sends
- ⚠️ **Real sending not implemented** - When attempting real send
- ✅ **Success** - Simulated success
- 📊 **Statistics** - Send count summary

## Alternative: Use SMTP for Testing

Instead of Postmark, use the local SMTP provider for testing:

```bash
# Set in .env or environment
EMAIL_DELIVERY_METHOD=smtp
SMTP_HOST=localhost
SMTP_PORT=1025

# Run local SMTP server
python -m cellophanemail.providers.smtp.server
```

## Checking Your Postmark Quota

Before switching back to live mode, check your quota:

1. Log into Postmark dashboard
2. Check Server > Statistics
3. View monthly sending limit
4. Consider upgrading if needed

## Switching to Live Mode

When ready for production:

```bash
# Disable dry-run
export POSTMARK_DRY_RUN=false

# Or remove from config
config = ProviderConfig(
    config={
        "dry_run": False  # or omit entirely
    }
)
```

## Safety Tips

1. **Always test with dry-run first** when developing new features
2. **Use test environment files** (`.env.test`) for development
3. **Monitor the logs** - look for [DRY-RUN] indicators
4. **Check quota regularly** in Postmark dashboard
5. **Use SMTP for integration tests** to avoid Postmark entirely
6. **Review dry-run logs** before going live

## Provider Registry with Licensing

The new provider registry also helps control provider access:

```python
from cellophanemail.providers.registry import get_provider_registry

# Without license, Postmark won't be available
registry = get_provider_registry()
providers = registry.get_available_providers()
# Returns: ['gmail', 'smtp'] (no 'postmark' without commercial license)
```

This prevents accidental Postmark usage in open-source deployments.