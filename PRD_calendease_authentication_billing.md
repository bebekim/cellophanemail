# Product Requirements Document: Authentication & Billing System

## Overview
This document outlines the authentication and billing system for CalendEase, a calendar management application that extracts events from images and syncs them with Google Calendar.

## 1. User Registration & Sign Up

### 1.1 Core Features
- **Email-based registration** with username and password
- **Email verification** required before account activation
- **Tier-based onboarding** supporting free, plus, and pro plans
- **Plan selection during signup** with seamless checkout flow

### 1.2 User Registration Flow
1. User visits signup page (`/auth/signup`)
2. Provides username (3-64 chars, alphanumeric + underscore/dash), email, and password (min 8 chars)
3. System validates input and checks for existing accounts
4. Creates user with `email_verified: false` status
5. Generates secure verification token with expiry
6. Sends verification email with confirmation link
7. User clicks verification link to activate account
8. Redirects to verified confirmation page

### 1.3 Data Model - User
```python
User:
- id: Integer (Primary Key)
- username: String(64), unique, nullable
- email: String(120), unique, required, indexed
- password_hash: String(256)
- email_verified: Boolean, default False
- verification_token: String(256), indexed
- verification_token_expiry: DateTime with timezone
- tier: String(20), default "free" (free/plus/pro)
- subscription_end_date: DateTime with timezone
- monthly_upload_limit: Integer, default 10
- uploads_remaining: Integer, default 10
- created_at: DateTime, default current time
- last_login: DateTime
- is_active: Boolean, default True
- avatar_url: String(500)
```

### 1.4 Validation Rules
- **Username**: 3-64 characters, letters, numbers, underscores, dashes only
- **Email**: Valid email format, automatically normalized to lowercase
- **Password**: Minimum 8 characters, hashed with Werkzeug
- **Tier**: Must be one of ["free", "plus", "pro"]

## 2. User Authentication & Login

### 2.1 Sign-In Methods
- **Email/password authentication**
- **Google OAuth integration**
- **Session management** via Flask-Login
- **Email verification enforcement**

### 2.2 Login Flow
1. User visits signin page (`/auth/signin`)
2. Chooses between Google OAuth or email/password
3. For email: validates credentials and email verification status
4. Blocks login if email not verified, shows verification message
5. Updates last login timestamp on successful authentication
6. Handles pending plan upgrades from session storage
7. Redirects to intended destination or dashboard

### 2.3 Password Management
- **Password reset** via email tokens with expiry
- **Secure password hashing** with Werkzeug (generate_password_hash)
- **Token-based reset flow** with signature verification
- **Password strength requirements** (minimum 8 characters)
- **Password change tracking** with last_password_change timestamp

### 2.4 Security Features
- **CSRF protection** on all authentication forms
- **Session permanence** for OAuth flows
- **Rate limiting** considerations for verification email resends
- **Generic error messages** to prevent user enumeration

## 3. Google OAuth Authentication

### 3.1 OAuth Configuration
- **Provider**: Google OAuth 2.0
- **Scopes**: 
  - `https://www.googleapis.com/auth/calendar` (Full calendar access)
  - `https://www.googleapis.com/auth/userinfo.email` (User email)
  - `https://www.googleapis.com/auth/userinfo.profile` (User profile)
- **Storage**: Custom SQLAlchemy storage for tokens
- **Consent**: Reprompt consent enabled for fresh permissions

### 3.2 OAuth Features
- **Account linking** for existing authenticated users
- **New user creation** from Google profile data
- **Avatar synchronization** from Google profile picture
- **Calendar access verification** during authentication flow
- **Token management** with automatic refresh capabilities
- **Duplicate account prevention** (one Google account per local user)

### 3.3 OAuth Flow
1. User clicks "Sign in with Google" button
2. Redirects to Google OAuth with calendar scopes
3. User grants permissions (calendar, email, profile)
4. System receives OAuth callback with access tokens
5. Fetches user profile information from Google API
6. Verifies calendar list access to confirm permissions
7. Determines flow based on authentication state:
   - **If logged in**: Links Google account to current user
   - **If not logged in**: 
     - Finds existing user by Google email
     - Creates new user if no match found
     - Prevents signup, redirects to registration if no local account

### 3.4 Data Model - OAuth
```python
OAuth:
- id: Integer (Primary Key)
- provider: String (e.g., "google")
- provider_user_id: String(256), unique (Google user ID)
- provider_user_login: String(256) (Google email)
- token: JSON (access_token, refresh_token, expires, etc.)
- user_id: Foreign Key to User
- created_at: DateTime
- updated_at: DateTime
```

### 3.5 OAuth Error Handling
- **Access denied**: Redirects to signup with OAuth context
- **Invalid tokens**: Graceful error handling with user notification
- **API failures**: Fallback behavior with logging
- **Token revocation**: Clean database cleanup on logout

## 4. Billing & Subscription Management

### 4.1 Pricing Tiers
| Tier | Price | Upload Limit | Features |
|------|-------|--------------|----------|
| **Free** | $0/month | 10 uploads | Basic event extraction, Manual calendar download |
| **Plus** | $2/month | 100 uploads | Google Calendar sync, Priority support |
| **Pro** | $10/month | 1000 uploads | API access, All Plus features |

### 4.2 Payment Integration
- **Payment processor**: Stripe
- **Billing model**: Subscription-based with automatic renewal
- **Checkout**: Stripe Checkout Sessions for secure payment
- **Webhooks**: Real-time subscription status updates
- **Currency**: USD with card payments

### 4.3 Billing Features
- **Plan upgrades/downgrades** with immediate tier updates
- **Refund processing** within 14-day window
- **Subscription cancellation** with end-of-period access
- **Usage tracking** with monthly upload limit enforcement
- **Proration handling** for mid-cycle plan changes
- **Failed payment handling** via Stripe webhooks

### 4.4 Data Model - Subscription
```python
Subscription:
- id: Integer (Primary Key)
- user_id: Foreign Key to User, required
- stripe_subscription_id: String(255), unique
- stripe_customer_id: String(255), unique
- plan_id: String(255) (Stripe price ID)
- status: String(50) (active, canceled, past_due, etc.)
- current_period_start: DateTime
- current_period_end: DateTime
- created_at: DateTime
- updated_at: DateTime
```

### 4.5 Payment Flow
1. User selects plan on pricing page (`/payments/pricing`)
2. Redirects to plan confirmation page (`/payments/confirm-plan`)
3. User confirms plan details and submits payment form
4. Creates Stripe checkout session with:
   - Price ID for selected plan
   - User metadata (user_id, email, plan)
   - Success/cancel URLs
5. User completes payment in Stripe hosted checkout
6. Stripe webhook (`/payments/webhook`) updates subscription:
   - Creates/updates Subscription record
   - Updates User tier immediately
   - Sets subscription period dates
7. Redirects to success page with plan features overview

### 4.6 Subscription Management
- **Plan switching**: Cancel current + create new subscription
- **Cancellation**: Stripe subscription deletion with immediate tier downgrade
- **Refunds**: Automatic refund of latest invoice for recent subscriptions
- **Billing portal**: Integration with Stripe Customer Portal (planned)

## 5. Usage & Tier Management

### 5.1 Upload Limits
- **Monthly reset**: Upload counts reset on the first day of each month
- **Tier enforcement**: Upload blocked when limit reached
- **Limit tracking**: `uploads_remaining` decremented on each upload
- **Automatic reset**: Background process resets limits monthly

### 5.2 Tier Benefits
```python
TIER_LIMITS = {
    "free": {
        "uploads": 10,
        "can_sync": False,
        "features": ["Basic event extraction", "Manual calendar download"]
    },
    "plus": {
        "uploads": 100,
        "can_sync": True,
        "features": ["Increased event extraction", "Google Calendar sync", "Priority support"]
    },
    "pro": {
        "uploads": 1000,
        "can_sync": True,
        "features": ["Everything in Plus", "API access"]
    }
}
```

## 6. Security & Compliance

### 6.1 Security Measures
- **Password hashing**: Werkzeug PBKDF2 with salt
- **Email verification**: Mandatory before account activation
- **Token security**: Cryptographically secure token generation
- **Session management**: Flask-Login with secure session handling
- **CSRF protection**: Enabled on all forms
- **Input validation**: Server-side validation with pattern matching

### 6.2 Data Protection
- **Email normalization**: Automatic lowercase conversion
- **Token expiry**: Time-limited verification and reset tokens
- **OAuth token encryption**: Secure storage of OAuth credentials
- **Webhook verification**: Stripe signature validation
- **Error handling**: Generic error messages to prevent enumeration

### 6.3 Privacy Considerations
- **Google permissions**: Clear consent for calendar access
- **Data retention**: Subscription data retained per business requirements
- **User deletion**: Cascade deletion of related OAuth and subscription data
- **Audit logging**: Authentication events logged for security monitoring

## 7. API Endpoints

### 7.1 Authentication Routes
- `GET/POST /auth/signup` - User registration
- `GET/POST /auth/signin` - User login
- `GET /auth/logout` - User logout
- `GET /auth/verify/<token>` - Email verification
- `POST /auth/resend-verification` - Resend verification email
- `GET/POST /auth/reset-password` - Password reset request
- `GET/POST /auth/reset-password/<token>` - Password reset execution
- `POST /auth/disconnect-google` - Disconnect Google account

### 7.2 OAuth Routes
- `GET /auth/google` - Initiate Google OAuth
- `GET /auth/google/authorized` - OAuth callback handler
- `POST /auth/google/logout` - OAuth logout with token revocation

### 7.3 Payment Routes
- `GET /payments/pricing` - Pricing page
- `GET /payments/confirm-plan` - Plan confirmation
- `GET/POST /payments/checkout` - Checkout session creation
- `POST /payments/webhook` - Stripe webhook handler
- `GET /payments/success` - Payment success page
- `GET /payments/cancelled` - Payment cancellation page
- `GET /payments/manage` - Subscription management
- `GET/POST /payments/refund` - Refund processing

## 8. Integration Points

### 8.1 External Services
- **Google OAuth API**: User authentication and authorization
- **Google Calendar API**: Calendar access via OAuth tokens
- **Stripe API**: Payment processing and subscription management
- **Email service**: Verification and password reset emails

### 8.2 Internal Dependencies
- **Flask-Login**: Session management
- **Flask-Dance**: OAuth integration
- **SQLAlchemy**: Database ORM
- **Werkzeug**: Password hashing
- **Flask-WTF**: CSRF protection

## 9. Error Handling & Edge Cases

### 9.1 Authentication Errors
- **Invalid credentials**: Generic error message
- **Unverified email**: Clear verification prompt
- **Expired tokens**: Automatic cleanup and new token generation
- **OAuth failures**: Graceful fallback with error logging

### 9.2 Billing Errors
- **Payment failures**: Webhook handling with user notification
- **Subscription conflicts**: Prevention of duplicate subscriptions
- **Refund failures**: Error logging with manual intervention
- **Plan limits**: Clear usage limit messaging

## 10. Future Enhancements

### 10.1 Planned Features
- **Multi-factor authentication** (MFA)
- **Social login expansion** (GitHub, Microsoft)
- **Enterprise SSO** integration
- **Advanced billing portal** with Stripe Customer Portal
- **Usage analytics** and reporting
- **API rate limiting** for Pro tier

### 10.2 Technical Improvements
- **Rate limiting** on authentication endpoints
- **Advanced session management** with Redis
- **Audit logging** enhancement
- **Automated testing** for payment flows
- **Performance monitoring** for OAuth flows