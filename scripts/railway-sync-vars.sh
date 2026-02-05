#!/bin/bash
# Railway Variable Sync Script
# Syncs shared variables across staging and production environments

set -e

echo "🚂 Railway Variable Sync"
echo "========================"

# ============================================
# 1. SHARED VARIABLES (same in both envs)
# ============================================
SHARED_VARS=(
  "AI_PROVIDER=anthropic"
  "AI_MODEL=claude-sonnet-4-5-20250929"
  "SMTP_DOMAIN=cellophanemail.com"
  "LLM_ANALYZER_MODE=privacy"
  "PRIVACY_SAFE_LOGGING=true"
  "HOST=0.0.0.0"
  "OUTBOUND_SMTP_HOST=smtp.gmail.com"
  "OUTBOUND_SMTP_PORT=587"
  "OUTBOUND_SMTP_USE_TLS=true"
  "ENABLED_PLUGINS=smtp"
)

echo ""
echo "📦 Setting SHARED variables in both environments..."
for var in "${SHARED_VARS[@]}"; do
  name="${var%%=*}"
  echo "  → $name"
  railway variables --environment staging --set "$var"
  railway variables --environment production --set "$var"
done

# ============================================
# 2. PER-ENVIRONMENT VARIABLES
# ============================================
echo ""
echo "🔧 Setting STAGING-specific variables..."
STAGING_VARS=(
  "STAGING=true"
  "CELLOPHANEMAIL_STAGING_MODE=true"
  "DEBUG=true"
  "POSTMARK_DRY_RUN=true"
  "POSTMARK_LOG_DRY_RUN=true"
  "CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,https://cellophanemail-staging.up.railway.app"
)
for var in "${STAGING_VARS[@]}"; do
  name="${var%%=*}"
  echo "  → $name"
  railway variables --environment staging --set "$var"
done

echo ""
echo "🚀 Setting PRODUCTION-specific variables..."
PRODUCTION_VARS=(
  "STAGING=false"
  "CELLOPHANEMAIL_STAGING_MODE=false"
  "DEBUG=false"
  "POSTMARK_DRY_RUN=false"
  "POSTMARK_LOG_DRY_RUN=false"
  "CORS_ALLOWED_ORIGINS=https://cellophanemail.com,https://www.cellophanemail.com,https://cellophanemail-production.up.railway.app"
)
for var in "${PRODUCTION_VARS[@]}"; do
  name="${var%%=*}"
  echo "  → $name"
  railway variables --environment production --set "$var"
done

# ============================================
# 3. CLEANUP OLD VARIABLES
# ============================================
echo ""
echo "🧹 Removing OLD variable names..."
OLD_VARS=(
  "TESTING"
  "CELLOPHANEMAIL_TEST_MODE"
)
for var in "${OLD_VARS[@]}"; do
  echo "  → Removing $var"
  railway variables --environment staging --unset "$var" 2>/dev/null || true
  railway variables --environment production --unset "$var" 2>/dev/null || true
done

# ============================================
# 4. REMINDER FOR SECRETS
# ============================================
echo ""
echo "⚠️  MANUAL ACTION REQUIRED - Set these secrets separately:"
echo ""
echo "  STAGING:"
echo "    railway variables --environment staging --set SECRET_KEY=<generate-new>"
echo "    railway variables --environment staging --set ENCRYPTION_KEY=<generate-new>"
echo "    railway variables --environment staging --set STRIPE_API_KEY=sk_test_..."
echo "    railway variables --environment staging --set STRIPE_WEBHOOK_SECRET=whsec_test_..."
echo ""
echo "  PRODUCTION:"
echo "    railway variables --environment production --set SECRET_KEY=<generate-new-different>"
echo "    railway variables --environment production --set ENCRYPTION_KEY=<generate-new-different>"
echo "    railway variables --environment production --set STRIPE_API_KEY=sk_live_..."
echo "    railway variables --environment production --set STRIPE_WEBHOOK_SECRET=whsec_live_..."
echo "    railway variables --environment production --set POSTMARK_API_TOKEN=<real-token>"
echo ""
echo "  Generate keys with:"
echo "    python -c \"import secrets; print(secrets.token_urlsafe(32))\""
echo "    python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
echo ""
echo "✅ Sync complete!"
