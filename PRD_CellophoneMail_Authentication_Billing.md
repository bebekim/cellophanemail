# Product Requirements Document
## CellophoneMail Authentication & Billing System

**Version:** 2.0 (Simplified)  
**Date:** August 2025  
**Status:** MVP Phase

---

## 1. Executive Summary

CellophoneMail is an AI-powered email protection SaaS that provides users with shield email addresses and "Four Horsemen" threat analysis. Tiered pricing model starting at $5/month with 30-day trial period.

### Key Principles
- **Configurable Pricing**: All pricing in settings.py constants
- **Tiered Model**: $5/100, $10/500, $25/unlimited emails
- **Trial with Card**: 30-day free trial requires payment method
- **Add-on Flexibility**: $2 for extra 50 emails when needed
- **Individual Focus First**: Organization features scaffolded for future
- **Shield Addresses**: Every user gets unique protected email addresses

---

## 2. User Signup & Onboarding

### 2.1 MVP User Type
- **Individual Users Only** (organizations scaffolded for future)
- Every user gets unique shield addresses
- Single subscription per user account
- 30-day trial with payment method required

### 2.2 Simplified Signup Flow

#### 2.2.1 Email/Password Signup
```
1. User visits /signup
2. Provides email, password, full name
3. System creates User record
4. Generates unique shield address (username123@cellophanemail.com)
5. Sends email verification
6. User verifies email → proceeds to payment
7. Enters payment details (Stripe)
8. 30-day trial starts immediately
9. Welcome email with trial end date
10. Access to dashboard and shield addresses
```

#### 2.2.2 Google OAuth Signup
```
1. User clicks "Sign up with Google"
2. Authorizes Google account
3. System creates User with Google email
4. Auto-generates secure password (hidden from user)
5. Links Google account for future logins
6. Proceeds to payment flow (steps 6-10 above)
```

### 2.3 Trial & Billing Communication
- **Day 1**: Welcome email with trial end date
- **Day 23**: Reminder that trial ends in 7 days
- **Day 28**: Final reminder - billing starts in 2 days
- **Day 30**: Card charged, subscription active
- Users can cancel anytime during trial

---

## 3. Simplified Authentication System

### 3.1 Authentication Methods

#### 3.1.1 Email/Password (Primary)
- Email + password login
- Email verification required for new accounts
- Minimum password requirements (8 characters)
- Password reset via email link

#### 3.1.2 Google OAuth (Secondary)
- Link Google account after email/password signup
- Or create account via Google (auto-generates password)
- One-click login for linked accounts
- Uses Google email as primary identifier

### 3.2 Session Management
- Simple session tokens (can upgrade to JWT later)
- 30-day "remember me" option
- Basic rate limiting (5 failed attempts = 15 min lockout)
- Password reset tokens expire in 1 hour

### 3.3 Security (MVP Essentials Only)
- Bcrypt password hashing
- HTTPS everywhere
- Rate limiting on auth endpoints
- Email verification for new accounts
- Basic login activity logging

**Deferred for Later:**
- ❌ MFA/2FA (add when enterprise customers need it)
- ❌ Device tracking
- ❌ Suspicious login detection
- ❌ Advanced audit logging
- ❌ Compliance reporting

---

## 4. Billing & Subscription Model

### 4.1 Configurable Pricing Structure

#### Pricing Configuration (settings.py)
```python
# Pricing constants - easily adjustable
PRICING = {
    "STARTER": {
        "price": 5,  # USD per month
        "email_limit": 100,
        "name": "Starter"
    },
    "PROFESSIONAL": {
        "price": 10,  # USD per month
        "email_limit": 500,
        "name": "Professional"
    },
    "UNLIMITED": {
        "price": 25,  # USD per month
        "email_limit": -1,  # -1 means unlimited
        "soft_cap": 5000,  # Soft limit for abuse prevention
        "name": "Unlimited"
    },
    "ADDON_PACK": {
        "price": 2,  # USD per pack
        "emails": 50,
        "name": "Email Add-on Pack"
    },
    "TRIAL_DAYS": 30
}
```

#### Current Tiers (from config)

**Starter: $5/month**
- 100 AI-analyzed emails/month
- Unlimited shield email addresses
- Unlimited basic forwarding (no AI)
- Email support

**Professional: $10/month**
- 500 AI-analyzed emails/month
- Priority email processing
- Advanced analytics
- Priority support

**Unlimited: $25/month**
- Unlimited AI analysis (soft cap: 5000)
- API access (future)
- Custom shield domains (future)
- Dedicated support

**Add-on Packs: $2**
- Extra 50 emails (one-time)
- Available for Starter and Professional tiers
- Expires at month end (no rollover)

### 4.2 Trial & Payment Flow
```
1. User signs up → selects plan → enters payment details
2. Stripe creates subscription with 30-day trial
3. No charge for 30 days
4. Email reminders at day 23 and 28
5. Auto-charge on day 30 unless cancelled
6. Monthly billing thereafter
```

### 4.3 Economics & Unit Costs

#### Pricing Economics (Based on Current Config)
```python
# Cost assumptions (configurable)
AI_COST_PER_EMAIL = 0.015  # $0.015 per email
INFRASTRUCTURE_COST_PER_USER = 0.50  # Monthly

Starter ($5/month, 100 emails):
- Revenue: $5
- AI costs: 100 × $0.015 = $1.50
- Infrastructure: $0.50
- Margin: $3.00 (60%)

Professional ($10/month, 500 emails):
- Revenue: $10
- AI costs: 500 × $0.015 = $7.50
- Infrastructure: $0.50
- Margin: $2.00 (20%)

Unlimited ($25/month):
- Revenue: $25
- Typical usage: 1500-2000 emails
- AI costs: 1500 × $0.015 = $22.50
- Margin: $2.00 (8%) at typical usage

Add-on Pack ($2, 50 emails):
- Revenue: $2
- AI costs: 50 × $0.015 = $0.75
- Margin: $1.25 (62%)
```

### 4.4 Usage Tracking & Limits

#### Monthly Limits & Resets
- Usage resets on billing cycle date
- Real-time usage tracking in dashboard
- Email notifications at 80% and 100% usage
- Add-on packs available via one-click purchase

#### Over-limit Behavior
```
Starter/Professional:
- At 100% usage → prompt to buy add-on or upgrade
- Emails still forwarded but without AI analysis
- User can flag important emails for manual analysis

Unlimited:
- Soft cap at 5,000 emails/month
- Rate limiting to prevent abuse
- Manual review for excessive usage
```

### 4.4 Shield Address Management

#### Address Generation
- Format: `{username}{number}@cellophanemail.com`
- Automatic collision handling with increments
- User can create multiple addresses
- Each address tracked separately

#### Address Features
- Email forwarding to real address
- Optional AI analysis per address
- Enable/disable per address
- Basic analytics (count, last used)

### 4.5 Stripe Integration

#### Payment Processing
- Stripe Checkout for initial signup
- Subscription with trial period
- Webhook handling for payment events
- Card update via Stripe portal
- Automatic retry for failed payments

---

## 5. Database Schema (Simplified)

### 5.1 Updated User Model
```python
class User(Table):
    # Keep existing fields from current model
    # Add these new fields:
    
    # Shield address management
    shield_username = Varchar(length=50, unique=True, null=False)
    
    # Billing
    stripe_subscription_id = Varchar(length=100, null=True)
    subscription_plan = Varchar(choices=["starter", "professional", "unlimited"])
    trial_ends_at = Timestamp(null=True)
    subscription_status = Varchar(choices=["trialing", "active", "cancelled"])
    
    # Usage tracking
    emails_analyzed_month = Integer(default=0)
    email_limit_month = Integer(default=100)  # Set from PRICING config
    addon_emails_remaining = Integer(default=0)  # From add-on packs
    usage_reset_date = Timestamp(null=True)
    
    # Auth
    email_verified = Boolean(default=False)
    password_reset_token = Varchar(length=100, null=True)
    password_reset_expires = Timestamp(null=True)
    google_id = Varchar(length=255, null=True)  # For OAuth
    
    # Keep organization FK for future
    organization = ForeignKey(Organization, null=True)
```

### 5.2 Shield Address Model (Keep existing)

#### Shield Address
```python
class ShieldAddress(Table):
    id = UUID(primary_key=True, default=uuid.uuid4)
    user = ForeignKey(User, null=False)
    organization = ForeignKey(Organization, null=True)
    
    # Address details
    shield_email = Varchar(length=255, unique=True, null=False)
    forward_to = Varchar(length=255, null=False)
    alias = Varchar(length=100, null=True)
    
    # Status & settings
    is_active = Boolean(default=True)
    is_temporary = Boolean(default=False)
    expires_at = Timestamp(null=True)
    
    # Analytics
    emails_received = Integer(default=0)
    emails_forwarded = Integer(default=0)
    threats_blocked = Integer(default=0)
    last_email_at = Timestamp(null=True)
    
    created_at = Timestamp(default=datetime.now)
    updated_at = Timestamp(default=datetime.now)
```

---

## 6. API Design (MVP)

### 6.1 Authentication Endpoints

```python
# Registration & Login
POST /auth/register          # Email/password signup
POST /auth/login             # Email/password login
POST /auth/logout            # End session
POST /auth/google            # Google OAuth
GET  /auth/google/callback   # OAuth callback

# Account Management
POST /auth/verify-email      # Verify email with token
POST /auth/resend-verification
POST /auth/forgot-password   # Request reset
POST /auth/reset-password    # Reset with token
```

### 6.2 User & Shield Endpoints

```python
# Profile
GET  /users/me               # Current user info
PUT  /users/me               # Update profile

# Shield Addresses
GET  /shield-addresses       # List user's addresses
POST /shield-addresses       # Create new address
PUT  /shield-addresses/{id}  # Toggle active/inactive
DELETE /shield-addresses/{id} # Delete address

# Usage
GET  /users/usage            # Current month usage
```

### 6.3 Billing Endpoints

```python
# Subscription
POST /billing/checkout       # Create Stripe checkout session
GET  /billing/subscription   # Current subscription status
POST /billing/upgrade        # Change subscription tier
POST /billing/cancel         # Cancel subscription
POST /billing/portal         # Stripe customer portal link

# Add-ons
POST /billing/addon          # Purchase 100 email add-on pack
GET  /billing/addons         # Available add-ons and pricing

# Webhooks
POST /webhooks/stripe        # Stripe webhook handler
```

---

## 7. Implementation Priorities & Technical Guidance

### Phase 1: Core MVP (Weeks 1-3)
- [x] ✅ **Pricing Configuration** (TDD implemented, 30 tests passing)
- [ ] **Authentication System** using `litestar-users` library
- [ ] **Database Integration** with Piccolo ORM + async connections 
- [ ] **Email verification** flow
- [ ] **Stripe checkout** integration
- [ ] **Trial period** logic with configurable constants

#### Technical Approach Phase 1:
```bash
# Install dependencies
uv add litestar-users
uv add litestar-users[oauth2]  # For Google OAuth later
uv add psycopg[binary]         # Async PostgreSQL
uv add stripe                  # Payment processing

# Test-driven development
uv run python -m pytest tests/ -v
```

### Phase 2: Shield System (Weeks 4-6)
- [ ] **Shield address generation** (using pricing config constants)
- [ ] **Email forwarding** setup (Postmark integration)
- [ ] **Usage tracking** with real-time limits from pricing.py
- [ ] **Address management** UI

### Phase 3: Google OAuth Integration (Week 7)
- [ ] **OAuth2 setup** using `httpx-oauth` (from litestar-oauth2-example)
- [ ] **Account linking** after email/password signup
- [ ] **OAuth-based signup** with auto-password generation

#### Technical Approach Phase 3:
```python
# OAuth2 configuration (from examples)
from httpx_oauth.clients.google import GoogleOAuth2

google_oauth_client = GoogleOAuth2(
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET
)
```

### Phase 4: Polish & Production (Week 8)
- [ ] **Trial reminder emails** (using TRIAL_PERIOD_DAYS constant)
- [ ] **Usage limit enforcement** (using calculate_usage_percentage())
- [ ] **Stripe portal integration**
- [ ] **Analytics dashboard**

### Key Libraries & Patterns to Use:

#### 1. Authentication (litestar-users)
```python
# Multiple auth backends: Session, JWT, JWTCookie
# Pre-built routes for registration, verification, password recovery
# Role-based access control
```

#### 2. Database (Piccolo + Psycopg)
```python
# Async connection pooling
# Dependency injection pattern
# Connection lifecycle management via plugins
```

#### 3. Configuration (Our TDD Pricing Module)
```python
from cellophanemail.config.pricing import (
    STARTER_PRICE, STARTER_EMAILS,
    calculate_email_limit, calculate_usage_percentage
)
```

---

## 8. Success Metrics (MVP)

### Key Metrics
- Trial-to-paid conversion: >40%
- Month 2 retention: >80%
- Payment failure rate: <3%
- Email verification rate: >90%

### Usage & Economics  
- Starter users: 50-80 emails/month average (100 limit)
- Professional users: 200-350 emails/month average (500 limit)
- Unlimited users: 1000-2000 emails/month average
- Add-on purchase rate: 15-25% of Starter users
- Upgrade rate: 20% Starter→Professional, 10% Professional→Unlimited

### Support Targets
- Shield addresses per user: 2-5
- Support tickets: <5% of users/month
- Churn reasons: Track pricing vs features vs competition

---

## 9. Future Expansion (Post-MVP)

### Organization Features (Phase 2)
- Organization signup and management
- Team invitations and roles
- Per-user organization billing
- Domain verification (maybe)
- Admin dashboard

### Advanced Features (Phase 3)
- MFA/2FA for enterprise
- Advanced analytics
- API access for integrations
- Custom email retention policies
- Compliance reporting

### Scaling Considerations
- Move to JWT tokens
- Redis for session management
- Rate limiting improvements
- Usage-based pricing tiers
- White-label options

---

## Appendix B: Environment Configuration

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/cellophanemail

# Authentication
JWT_SECRET_KEY=your-super-secure-jwt-secret
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000

# Email Service
SMTP_HOST=smtp.postmarkapp.com
SMTP_USERNAME=your-postmark-token
SMTP_PASSWORD=your-postmark-token
FROM_EMAIL=noreply@cellophanemail.com

# Stripe Billing
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Application
APP_NAME=CellophoneMail
APP_URL=https://cellophanemail.com
DEBUG=false
ENVIRONMENT=production

# Security
RATE_LIMIT_STORAGE=redis://localhost:6379/0
SESSION_SECRET_KEY=your-session-secret
CORS_ALLOWED_ORIGINS=https://cellophanemail.com,https://app.cellophanemail.com
```

---

**End of Document**