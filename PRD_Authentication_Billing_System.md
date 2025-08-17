# Product Requirements Document
## User Authentication & Billing System
### OutForOrangeJuice Platform

**Version:** 1.0  
**Date:** August 2025  
**Status:** Implementation Complete (Phase 1-3)

---

## 1. Executive Summary

OutForOrangeJuice is a SaaS platform that provides users with on-demand AI-powered phone call services. The platform requires robust user authentication, flexible billing mechanisms, and viral growth capabilities through a referral system.

### Current Implementation Status
- ✅ Phone-based authentication with SMS verification
- ✅ Password authentication system
- ✅ Stripe billing integration (payments & subscriptions)
- ✅ Viral referral system with waitlist mechanics
- ✅ Multi-tier service levels (Free, Plus, Pro)
- 🔄 Google OAuth authentication (planned)

---

## 2. User Authentication System

### 2.1 Current Authentication Methods

#### 2.1.1 Phone Number + Password Authentication
**Status:** ✅ Implemented

**User Flow:**
1. User enters phone number in international format (+1, +61, +44)
2. System sends SMS verification code via Twilio
3. User enters verification code (5-minute expiry)
4. User sets password (minimum requirements enforced)
5. Session created with Flask-Login

**Technical Implementation:**
- **Models:** `User`, `PhoneVerification`
- **Services:** `AuthService`, `TwilioService`
- **Routes:** `/auth/login`, `/auth/verify`, `/auth/set-password`
- **Security:** 
  - Password hashing with Werkzeug
  - CSRF protection on all forms
  - Rate limiting on verification attempts (3 max)
  - VoIP number blocking for fraud prevention

#### 2.1.2 API Token Authentication
**Status:** ✅ Implemented

**Use Case:** Apple Shortcuts integration for automated emergency calls

**Implementation:**
- 48-character secure token generation
- Token stored in `User.api_token`
- Header-based authentication: `X-API-Token`
- Revocable through user dashboard

### 2.2 Planned Authentication Methods

#### 2.2.1 Google OAuth 2.0
**Status:** 🔄 Planned

**Proposed Implementation:**
```python
# Models Extension
class User(db.Model):
    # Existing fields...
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    google_email = db.Column(db.String(255), nullable=True)
    google_profile_pic = db.Column(db.Text, nullable=True)
    auth_provider = db.Column(db.Enum('phone', 'google', 'apple'), default='phone')
    
# OAuth Service
class GoogleAuthService:
    def authenticate(self, oauth_token):
        # Verify with Google
        # Create/update user
        # Link to existing phone account if email matches
        pass
```

**User Flow:**
1. User clicks "Sign in with Google"
2. Redirect to Google OAuth consent
3. Callback receives user data
4. System checks for existing account (by email/phone)
5. Creates new account or links to existing
6. Session created

**Benefits:**
- Reduced friction for new users
- No SMS costs for verification
- Access to user email for communications
- Profile picture for personalization

#### 2.2.2 Apple Sign In
**Status:** 🔮 Future Consideration

**Rationale:** iOS app deployment would benefit from Apple Sign In requirement

### 2.3 Session Management

**Current Implementation:**
- Flask-Session with secure cookies
- 30-day remember me option
- Redis session store (production)
- CSRF tokens on all state-changing operations

**Security Measures:**
- Session rotation on privilege escalation
- IP address validation (optional)
- User agent fingerprinting
- Automatic logout on suspicious activity

---

## 3. Billing & Payment System

### 3.1 Pricing Structure

#### 3.1.1 Service Tiers

**Free Tier:**
- 2 base minutes/month
- +1 minute per successful referral
- Maximum 30 minutes/month cap
- Access to basic scenarios
- Shared phone number pool

**Plus Tier ($4.99/month):**
- Unlimited minutes
- Priority queue (30-second wait max)
- Dedicated regional phone numbers
- All scenario types
- Email support

**Pro Tier ($20.00/month):**
- Everything in Plus
- Instant call connection (5-second max)
- Premium AI assistants
- Custom scenarios (coming soon)
- Priority support
- API access for automation

#### 3.1.2 Minute Packages (One-time)
```python
MINUTES_PACKAGES = {
    5: 199,    # $1.99 for 5 minutes
    15: 499,   # $4.99 for 15 minutes  
    30: 899,   # $8.99 for 30 minutes
    60: 1699   # $16.99 for 60 minutes
}
```

### 3.2 Payment Processing

#### 3.2.1 Stripe Integration
**Status:** ✅ Implemented

**Components:**
- Payment Intent API for one-time purchases
- Checkout Sessions for subscriptions
- Webhook processing for payment events
- Apple Pay & Google Pay support

**Key Features:**
- PCI-compliant card processing
- Automatic retry for failed payments
- Subscription lifecycle management
- Invoice generation
- Tax calculation (coming soon)

**Webhook Events Handled:**
- `payment_intent.succeeded`
- `payment_intent.failed`
- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

#### 3.2.2 Payment Service Architecture

```python
class PaymentService:
    def create_checkout_session(user, package):
        # Creates Stripe checkout
        # Returns session URL
        
    def process_webhook(event):
        # Validates signature
        # Processes payment events
        # Updates user credits
        
    def handle_subscription(user, tier):
        # Creates/updates subscription
        # Manages tier transitions
```

### 3.3 Usage Tracking & Billing

#### 3.3.1 Credit System
**Current Implementation:**
- Seconds-based precise tracking
- Legacy minutes compatibility
- Real-time deduction during calls
- Automatic top-up for subscriptions

**Database Schema:**
```sql
-- User credits
seconds_remaining INTEGER
total_seconds_purchased INTEGER
minutes_remaining INTEGER  -- Legacy
total_minutes_purchased INTEGER  -- Legacy

-- Call tracking
CallSession:
  duration_seconds INTEGER
  minutes_used INTEGER
  call_status VARCHAR
```

#### 3.3.2 Billing Accuracy
- Per-second billing calculation
- Round-up to nearest minute for display
- Audit trail for all transactions
- Reconciliation with Stripe records

---

## 4. User Signup & Onboarding

### 4.1 Registration Flow

#### 4.1.1 Standard Registration
**Status:** ✅ Implemented

1. **Phone Number Entry**
   - International format validation
   - Country detection from prefix
   - VoIP blocking (anti-fraud)

2. **Verification**
   - SMS OTP via Twilio
   - 5-minute code expiry
   - 3 attempt limit
   - Rate limiting by IP

3. **Profile Setup**
   - Password creation
   - Preferred name (optional)
   - Terms acceptance
   - Age verification

4. **Consent Collection**
   - TCPA compliance for calls
   - SMS consent separate
   - GDPR consent (EU users)
   - Stored with timestamp & IP

#### 4.1.2 Referral Registration
**Status:** ✅ Implemented

**Enhanced Flow:**
1. User clicks referral link
2. Invitation code stored in session
3. Standard registration process
4. Automatic referral attribution
5. Bonus minutes awarded to both parties

**Fraud Prevention:**
- Phone number similarity detection
- IP address matching
- Time pattern analysis
- VoIP number blocking
- Manual review for high scores

### 4.2 Waitlist System

**Status:** ✅ Implemented

**Viral Mechanics:**
- Queue position based on signup time
- Position improvement for referrals
- Skip-the-line social sharing
- Milestone rewards (5, 10, 25 referrals)

**Implementation:**
```python
class WaitlistEntry:
    queue_position: int
    priority_score: int
    referrals_made: int
    position_improvement: int
    estimated_activation_date: datetime
```

### 4.3 User Activation

**Triggers:**
- Manual admin activation
- Automatic batch processing
- Referral threshold reached
- Payment completion (Pro/Plus)

**Post-Activation:**
- Welcome SMS with instructions
- Initial credits allocation
- Dashboard access enabled
- Referral code generation

---

## 5. Security & Compliance

### 5.1 Authentication Security

**Implemented Measures:**
- Bcrypt password hashing
- CSRF token validation
- Session hijacking prevention
- Rate limiting on all auth endpoints
- VoIP number blocking
- Suspicious pattern detection

**Audit Trail:**
- All login attempts logged
- IP address tracking
- User agent recording
- Geolocation analysis (planned)

### 5.2 Payment Security

**PCI Compliance:**
- No card data stored locally
- Stripe handles all sensitive data
- Webhook signature validation
- HTTPS enforcement

**Fraud Prevention:**
- Referral fraud scoring
- Payment velocity checks
- Chargeback monitoring
- Manual review queue

### 5.3 Regulatory Compliance

**TCPA (US):**
- Explicit consent for automated calls
- Opt-out mechanism (STOP SMS)
- Consent timestamp recording
- Do Not Call list integration (planned)

**GDPR (EU):**
- Consent management
- Data portability
- Right to deletion
- Privacy policy acceptance

**Age Verification:**
- Birthdate collection
- Minimum age enforcement (13+)
- Parental consent framework (unused)

---

## 6. Admin Interface

### 6.1 User Management
**Status:** ✅ Implemented

**Features:**
- User search and filtering
- Credit adjustment
- Account suspension
- Tier management
- Referral oversight

### 6.2 Billing Management
**Status:** ✅ Implemented

**Features:**
- Payment history
- Subscription management
- Refund processing
- Invoice generation
- Revenue analytics

### 6.3 Referral Management
**Status:** ✅ Implemented

**Features:**
- Waitlist queue management
- Referral tracking
- Fraud detection dashboard
- Reward processing
- Campaign analytics

---

## 7. API & Integrations

### 7.1 External Services

**Twilio:**
- SMS verification
- Phone number provisioning
- Call initiation
- Webhook callbacks

**Stripe:**
- Payment processing
- Subscription management
- Invoice generation
- Tax calculation (future)

**VAPI:**
- AI assistant management
- Call orchestration
- Real-time call events

### 7.2 Internal APIs

**Authentication API:**
```
POST /api/auth/token - Generate API token
POST /api/auth/verify - Verify token
DELETE /api/auth/revoke - Revoke token
```

**User API:**
```
GET /api/user/profile - Get user details
PUT /api/user/profile - Update profile
GET /api/user/credits - Check balance
```

**Billing API:**
```
POST /api/billing/charge - One-time payment
POST /api/billing/subscribe - Start subscription
DELETE /api/billing/cancel - Cancel subscription
```

---

## 8. Database Schema

### 8.1 Core Tables

**Users Table:**
- Authentication credentials
- Profile information
- Billing details
- Usage tracking
- Consent records

**Purchases Table:**
- Transaction history
- Stripe references
- Credit allocations

**CallSessions Table:**
- Call records
- Duration tracking
- Assistant allocation

**Referrals Table:**
- Referral relationships
- Fraud scoring
- Status tracking

### 8.2 Supporting Tables

- PhoneVerification
- RateLimitTracker
- WaitlistEntry
- ReferralInvitation
- ReferralReward
- ReferralAudit

---

## 9. Future Enhancements

### 9.1 Authentication
- [ ] Google OAuth integration
- [ ] Apple Sign In
- [ ] Two-factor authentication
- [ ] Biometric authentication (mobile)
- [ ] Magic link authentication
- [ ] Social login (Facebook, Twitter)

### 9.2 Billing
- [ ] Cryptocurrency payments
- [ ] Regional pricing
- [ ] Family plans
- [ ] Enterprise accounts
- [ ] Usage-based pricing tiers
- [ ] Prepaid card support

### 9.3 User Experience
- [ ] Progressive web app
- [ ] Native mobile apps
- [ ] Multi-language support
- [ ] Accessibility improvements
- [ ] Dark mode
- [ ] Email notifications

### 9.4 Security
- [ ] Advanced fraud detection ML
- [ ] Behavioral analytics
- [ ] Zero-trust architecture
- [ ] End-to-end encryption
- [ ] SOC 2 compliance

---

## 10. Success Metrics

### 10.1 Authentication KPIs
- Signup conversion rate: >60%
- Verification success rate: >90%
- Password reset rate: <5%
- Session duration: >15 minutes
- Login success rate: >95%

### 10.2 Billing KPIs
- Payment success rate: >95%
- Chargeback rate: <0.5%
- Subscription retention: >80%
- Average revenue per user: $8+
- Free to paid conversion: >5%

### 10.3 Referral KPIs
- Viral coefficient: >1.2
- Referral conversion: >30%
- Fraud detection accuracy: >90%
- Waitlist activation rate: >70%

---

## 11. Technical Architecture

### 11.1 Technology Stack
- **Backend:** Python/Flask
- **Database:** PostgreSQL
- **Cache:** Redis
- **Queue:** Celery (planned)
- **Hosting:** Replit/AWS
- **CDN:** Cloudflare

### 11.2 Scalability Considerations
- Database connection pooling
- Redis session caching
- CDN for static assets
- Horizontal scaling ready
- Microservices architecture (future)

### 11.3 Monitoring
- Application performance (New Relic)
- Error tracking (Sentry)
- User analytics (Mixpanel)
- Payment monitoring (Stripe Dashboard)
- Uptime monitoring (Pingdom)

---

## Appendix A: Environment Variables

```bash
# Authentication
SECRET_KEY=<flask-secret>
TWILIO_VERIFY_SERVICE_SID=<twilio-verify>

# Billing
STRIPE_PUBLISHABLE_KEY=<stripe-public>
STRIPE_SECRET_KEY=<stripe-secret>
STRIPE_WEBHOOK_SECRET=<webhook-secret>

# OAuth (Future)
GOOGLE_CLIENT_ID=<google-oauth-id>
GOOGLE_CLIENT_SECRET=<google-oauth-secret>

# Database
DATABASE_URL=postgresql://...

# Services
TWILIO_ACCOUNT_SID=<twilio-sid>
TWILIO_AUTH_TOKEN=<twilio-token>
VAPI_API_KEY=<vapi-key>
```

---

## Appendix B: API Response Formats

### Success Response
```json
{
  "success": true,
  "data": {
    "user_id": 123,
    "credits": 300,
    "tier": "plus"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "AUTH_FAILED",
    "message": "Invalid credentials",
    "details": {}
  }
}
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Aug 2025 | System | Initial PRD based on current implementation |

---

**End of Document**