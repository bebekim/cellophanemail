---
date: 2025-10-11T09:06:33+0000
researcher: claude
git_commit: bc3628957155c373b4b2a71c1a074f9a8f973320
branch: feature/email-delivery-integration
repository: cellophanemail
topic: "Multi-Channel B2B SaaS Architecture for Social Worker Protection"
tags: [plan, architecture, multi-channel, b2b-saas, twilio, stripe, android, refactoring]
status: draft
last_updated: 2025-10-11
last_updated_by: claude
---

# Multi-Channel B2B SaaS Architecture Implementation Plan

**Date**: 2025-10-11T09:06:33+0000
**Repository**: cellophanemail
**Branch**: feature/email-delivery-integration
**Git Commit**: bc3628957155c373b4b2a71c1a074f9a8f973320

## Overview

This plan details the transformation of CellophoneMail from an email-only protection service into a multi-channel B2B SaaS platform serving social workers who receive abusive communications (email and SMS) from clients. The system will provide real-time toxicity detection, case file generation, and cross-platform support via web and Android applications.

**Target Users**: Social workers handling abusive client communications
**Pricing Model**: Self-service subscription with organization upgrade path
**Channels**: Email (current) + SMS (new via Twilio)
**Clients**: Web app (signup/admin) + Android app (SMS forwarding)

## Current State Analysis

### What Exists Today

#### ✅ Backend Infrastructure
- **JWT Authentication**: 15-minute access tokens, 7-day refresh tokens
- **User/Organization Models**: Multi-tenant architecture ready
- **Toxic Content Detection**: LLM-powered analysis via Anthropic Claude
- **Email Processing Pipeline**: Postmark/SMTP webhook handling
- **Privacy-Focused Architecture**: In-memory processing with 5-minute TTL
- **CORS Configuration**: Ready for web clients

#### ✅ Data Models
- `User` table with organization FK, Stripe customer ID fields
- `Organization` table with subscription plan, usage limits
- `Subscription` table (Stripe-compatible schema)
- `EmailLog` table (privacy-safe, no content storage)
- `ShieldAddress` table for email forwarding

#### ❌ Critical Gaps
- **No SMS channel support**: Email-only processing
- **No Stripe integration**: Models exist, zero implementation
- **No case file management**: No API to create/export cases
- **Dual EmailMessage classes**: Architectural conflict (`core` vs `providers`)
- **No organization joining flow**: Users can't join existing orgs
- **No PDF/export functionality**: No document generation
- **Tight email coupling**: Delivery services assume email structure

### Key Discoveries from Research

#### Twilio Integration Patterns (from garasade repository)
Located at: `~/repositories/individuals/garasade`

**Best Practices Found**:
1. **Database-managed phone numbers** (not env vars) - `garasade/app/models.py:529-643`
2. **Service layer pattern** - Routes delegate to service classes - `garasade/app/services/`
3. **Tuple return pattern** - `(success: bool, result_or_error: Any)` for error handling
4. **TCPA compliance** - STOP/START command handling with consent tracking
5. **LLM-powered intent analysis** - Natural language SMS processing
6. **Phone number normalization** - Google's phonenumbers library for E.164
7. **No webhook signature verification** - Security gap to avoid

**Key Integration Point**:
- `garasade/app/sms/routes.py:11-129` - SMS webhook handler pattern
- `garasade/app/services/sms_service.py:13-75` - Service layer abstraction

#### EmailMessage Architectural Conflict
Two competing implementations:
- `src/cellophanemail/core/email_message.py` - Core version with UUIDs, factory methods
- `src/cellophanemail/providers/contracts.py` - Provider version with simpler structure

**Field naming inconsistency**:
- Core: `text_content`, `html_content`
- Providers: `text_body`, `html_body`

**Impact**: Feature layer uses `getattr()` fallbacks to handle both - `features/email_protection/streamlined_processor.py:174-175`

#### Channel-Agnostic Components (Ready for Reuse)
- `IEmailAnalyzer` - Works with pure strings - `features/email_protection/analyzer_interface.py:12-46`
- `GraduatedDecisionMaker` - Content-agnostic - `features/email_protection/graduated_decision_maker.py:39-225`
- `EmailCompositionStrategy` - Generic result handling - `features/email_protection/email_composition_strategy.py:41-217`
- `IntegratedDeliveryManager` - Abstract sender interface - `features/email_protection/integrated_delivery_manager.py:42-187`

#### Tight Coupling Points (Need Refactoring)
- `EmailDeliveryService.send_email()` - Requires specific EmailMessage structure - `services/email_delivery.py:35-81`
- `PostmarkDeliveryService._prepare_postmark_payload()` - Direct field access - `services/email_delivery.py:83-122`
- `PrivacyWebhookOrchestrator` - Postmark-specific payload - `features/privacy_integration/privacy_webhook_orchestrator.py:114-158`

## Desired End State

### System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                  BACKEND API (cellophanemail)                    │
│  - Channel-agnostic message analysis                             │
│  - Unified Message model (email/SMS)                             │
│  - Stripe billing integration                                    │
│  - Case file management (JSON + PDF export)                      │
│  - Organization management with member invites                   │
│  - Usage tracking and quota enforcement                          │
└──────────────────────────────────────────────────────────────────┘
                           │
                           │ REST API
                           │
         ┌─────────────────┴─────────────────┐
         │                                   │
         │                                   │
┌────────▼─────────┐               ┌─────────▼───────────┐
│   WEB APP        │               │   ANDROID APP       │
│ (cellophane-web) │               │ (cellophane-android)│
├──────────────────┤               ├─────────────────────┤
│ - Org signup     │               │ - SMS auto-forward  │
│ - Stripe checkout│               │ - Toxicity alerts   │
│ - User invites   │               │ - Case file viewer  │
│ - Email forward  │               │ - JWT auth          │
│ - Dashboard      │               │ - Background service│
│ - Case mgmt      │               │ - Social worker UI  │
│ - Analytics      │               │                     │
└──────────────────┘               └─────────────────────┘
```

### User Flows

#### Flow 1: Social Worker Self-Service Signup
1. Worker visits web app → Signup page
2. Enters email, password, organization name (creates new org)
3. Redirected to Stripe Checkout for plan selection
4. After payment: Returns to dashboard with shield email address
5. Downloads Android app → Authenticates with same credentials
6. Enables SMS auto-forwarding in Android app

#### Flow 2: Worker Joins Existing Organization
1. Worker visits web app → Signup page
2. Enters email, password, selects "Join existing organization"
3. Searches for organization by name
4. Sends join request (optional: requires org admin approval)
5. After approval: Inherits organization's subscription
6. Downloads Android app → Individual authentication

#### Flow 3: SMS Protection
1. Android app receives SMS in background
2. Forwards SMS to backend: `POST /api/v1/messages/analyze`
3. Backend analyzes toxicity (same LLM pipeline as email)
4. Returns: `{ "toxicity_score": 0.85, "action": "REDACT_HARMFUL", "processed_content": "..." }`
5. Android app displays local notification with threat level
6. Worker views full analysis in app, adds to case file

#### Flow 4: Case File Generation
1. Worker selects messages from dashboard (web/mobile)
2. Clicks "Export Case File"
3. Backend aggregates: message content, toxicity scores, timestamps, sender info
4. Generates: JSON (API response) + PDF (downloadable report)
5. Worker downloads PDF for legal/administrative use

### Verification Criteria

**The system is complete when**:
1. Social worker can sign up via web app and pay via Stripe
2. Social worker can download Android app and authenticate
3. SMS received on Android is automatically forwarded and analyzed
4. Toxicity analysis works identically for email and SMS
5. Case files can be exported as JSON and PDF
6. Organization admins can invite members
7. Usage quotas are enforced (messages/month)
8. Add-on packs can be purchased ($2 for 50 messages)

## What We're NOT Doing

- **No multi-admin organizations**: Single admin per organization (for MVP)
- **No real-time web push notifications**: Email/SMS notifications only
- **No video/image content analysis**: Text-only toxicity detection
- **No voice call analysis**: SMS and email only
- **No third-party integrations**: No Slack, Teams, case management systems (future feature)
- **No custom LLM training**: Use existing Anthropic models
- **No mobile iOS app**: Android only for MVP
- **No end-to-end encryption**: Privacy via in-memory processing, not E2EE

## Implementation Phases

---

## Phase 1: Backend Channel-Agnostic Refactoring (6-8 weeks)

### Overview
Transform the email-centric backend into a channel-agnostic messaging platform that can handle email, SMS, and future channels uniformly. This is the foundation for all other features.

### Changes Required

#### 1.1 Consolidate EmailMessage Models

**Problem**: Two competing EmailMessage classes cause confusion and require runtime workarounds.

**Files to Modify**:

**A. Update Core EmailMessage** (`src/cellophanemail/core/email_message.py:10-149`)

Add channel_type discriminator:

```python
from enum import Enum

class ChannelType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"  # Future

@dataclass
class Message:  # Renamed from EmailMessage
    """Channel-agnostic message format."""

    # Core identification
    id: UUID = field(default_factory=uuid4)
    channel: ChannelType = ChannelType.EMAIL

    # Sender/recipients (generalized)
    from_address: str = ""  # Email address or phone number
    to_addresses: List[str] = field(default_factory=list)

    # Content (unified naming)
    subject: str = ""  # For email, empty for SMS
    content: str = ""  # Renamed from text_content (plain text)
    rich_content: str = ""  # Renamed from html_content (HTML for email, media URL for SMS)

    # Metadata
    message_id: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    attachments: List[Dict[str, Any]] = field(default_factory=list)

    # Processing context
    received_at: datetime = field(default_factory=datetime.now)
    source_plugin: str = ""
    raw_message: Optional[bytes] = None

    # Organization routing
    organization_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    shield_address: Optional[str] = None

    @classmethod
    def from_postmark_webhook(cls, webhook_data: Dict[str, Any]) -> "Message":
        """Create Message from Postmark email webhook."""
        # ... existing logic but with channel=ChannelType.EMAIL
        return cls(
            channel=ChannelType.EMAIL,
            from_address=webhook_data.get("From", ""),
            to_addresses=[addr.strip() for addr in to_field.split(",") if addr.strip()],
            subject=webhook_data.get("Subject", ""),
            content=webhook_data.get("TextBody") or "",
            rich_content=webhook_data.get("HtmlBody") or "",
            # ... rest of fields
        )

    @classmethod
    def from_twilio_webhook(cls, webhook_data: Dict[str, Any]) -> "Message":
        """Create Message from Twilio SMS webhook."""
        return cls(
            channel=ChannelType.SMS,
            from_address=webhook_data.get("From", ""),  # Phone number
            to_addresses=[webhook_data.get("To", "")],
            subject="",  # SMS has no subject
            content=webhook_data.get("Body", ""),
            rich_content="",  # Future: MMS media URL
            message_id=webhook_data.get("MessageSid", ""),
            source_plugin="twilio",
            shield_address=webhook_data.get("To")
        )

    def get_content_for_analysis(self) -> str:
        """Extract content for toxicity analysis."""
        parts = []
        if self.channel == ChannelType.EMAIL and self.subject:
            parts.append(f"Subject: {self.subject}")
        parts.append(self.content)
        return "\n".join(parts)

# Create alias for backward compatibility during migration
EmailMessage = Message
```

**B. Remove Duplicate from Provider Contracts** (`src/cellophanemail/providers/contracts.py:9-24`)

Delete the duplicate EmailMessage class entirely, import from core instead:

```python
from ..core.email_message import Message as EmailMessage, ChannelType

# Update Protocol to use core Message
class ChannelProvider(Protocol):  # Renamed from EmailProvider
    """Contract that all channel providers must implement."""

    async def initialize(self, config: ProviderConfig) -> None:
        ...

    async def receive_message(self, raw_data: Dict[str, Any]) -> EmailMessage:
        """Parse provider-specific webhook into Message format."""
        ...

    async def send_message(self, message: EmailMessage) -> bool:
        """Send message through this channel provider."""
        ...
```

**C. Update All Imports** (15+ files)

Files to update:
- `src/cellophanemail/routes/webhooks.py:12`
- `src/cellophanemail/services/email_delivery.py:8`
- `src/cellophanemail/plugins/base/plugin.py:7`
- `src/cellophanemail/providers/*/provider.py` (3 files)
- `src/cellophanemail/features/email_protection/streamlined_processor.py:20`
- `src/cellophanemail/features/email_protection/storage.py:9`

Change:
```python
# Old
from ..providers.contracts import EmailMessage

# New
from ..core.email_message import Message as EmailMessage, ChannelType
```

#### 1.2 Add Channel Type to Database Models

**A. Update EmailLog Model** (`src/cellophanemail/models/email_log.py:29-76`)

```python
class EmailLog(Table):
    # ... existing fields

    # Add channel discrimination
    channel_type = Varchar(length=20, default="email", null=False, index=True)

    # Rename for generalization (migration required)
    # from_address → sender_identifier
    # to_addresses → recipient_identifiers

    # But for backward compatibility, keep both during migration
    channel_type = Varchar(20, default="email")
```

**B. Create Migration** (`migrations/`)

```python
# migrations/cellophanemail_2025_10_11_add_channel_support.py

from piccolo.apps.migrations.auto.migration_manager import MigrationManager

ID = "2025-10-11T09:00:00:000000"

async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="cellophanemail", description="Add channel type support"
    )

    # Add channel_type column
    manager.add_column(
        table_class_name="EmailLog",
        tablename="email_logs",
        column_name="channel_type",
        column_class_name="Varchar",
        params={
            "length": 20,
            "default": "email",
            "null": False,
            "index": True
        }
    )

    return manager
```

#### 1.3 Create SMS Provider (Twilio Integration)

**A. Create Twilio Provider** (`src/cellophanemail/providers/twilio/provider.py` - NEW FILE)

```python
"""Twilio SMS provider implementation."""
from typing import Dict, Any, Optional
import phonenumbers
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from ..contracts import ChannelProvider, EmailMessage, ProviderConfig, ChannelType

class TwilioProvider(ChannelProvider):
    """Twilio SMS channel provider."""

    def __init__(self):
        self.client: Optional[Client] = None
        self.account_sid: str = ""
        self.auth_token: str = ""
        self.phone_number: str = ""
        self.validator: Optional[RequestValidator] = None

    async def initialize(self, config: ProviderConfig) -> None:
        """Initialize Twilio client with credentials."""
        self.account_sid = config.account_sid
        self.auth_token = config.auth_token
        self.phone_number = config.phone_number

        # Use API key if available (recommended for production)
        if config.api_key and config.api_secret:
            self.client = Client(config.api_key, config.api_secret, self.account_sid)
        else:
            self.client = Client(self.account_sid, self.auth_token)

        # Initialize request validator for webhook verification
        self.validator = RequestValidator(self.auth_token)

    async def receive_message(self, raw_data: Dict[str, Any]) -> EmailMessage:
        """Parse Twilio SMS webhook into Message format."""

        # Normalize phone numbers to E.164 format
        from_phone = self._normalize_phone(raw_data.get("From", ""))
        to_phone = self._normalize_phone(raw_data.get("To", ""))

        return EmailMessage(
            channel=ChannelType.SMS,
            from_address=from_phone,
            to_addresses=[to_phone],
            subject="",  # SMS has no subject
            content=raw_data.get("Body", ""),
            rich_content="",  # Future: MMS media
            message_id=raw_data.get("MessageSid", ""),
            headers={
                "NumMedia": raw_data.get("NumMedia", "0"),
                "FromCity": raw_data.get("FromCity", ""),
                "FromState": raw_data.get("FromState", ""),
                "FromCountry": raw_data.get("FromCountry", "")
            },
            source_plugin="twilio",
            shield_address=to_phone
        )

    async def send_message(self, message: EmailMessage) -> bool:
        """Send SMS via Twilio."""
        if not self.client:
            raise RuntimeError("Twilio provider not initialized")

        try:
            twilio_message = self.client.messages.create(
                body=message.content,
                from_=self.phone_number,
                to=message.to_addresses[0]  # SMS is one-to-one
            )
            return True
        except Exception as e:
            logger.error(f"Twilio SMS send failed: {e}")
            return False

    async def validate_webhook(self, request_data: Dict[str, Any], headers: Dict[str, str], url: str) -> bool:
        """Validate Twilio webhook signature."""
        if not self.validator:
            return False

        signature = headers.get("X-Twilio-Signature", "")
        return self.validator.validate(url, request_data, signature)

    def _normalize_phone(self, phone: str, region: str = "AU") -> str:
        """Normalize phone number to E.164 format."""
        try:
            parsed = phonenumbers.parse(phone, region)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            return phone
        except:
            return phone
```

**B. Create Twilio Webhook Handler** (`src/cellophanemail/providers/twilio/webhook.py` - NEW FILE)

```python
"""Twilio SMS webhook handler."""
from litestar import Controller, post, Request, Response
from litestar.status_codes import HTTP_200_OK, HTTP_403_FORBIDDEN
from litestar.exceptions import PermissionDeniedException

from .provider import TwilioProvider
from ...features.email_processing_strategy import ProcessingStrategyManager

class TwilioWebhookHandler(Controller):
    path = "/providers/twilio"
    tags = ["webhooks", "sms"]

    @post("/inbound")
    async def handle_sms_inbound(self, request: Request) -> Response:
        """Handle Twilio SMS webhook."""

        # Parse Twilio POST data (form-encoded)
        data = dict(request.form())

        # Validate webhook signature (security)
        provider = TwilioProvider()
        is_valid = await provider.validate_webhook(
            request_data=data,
            headers=dict(request.headers),
            url=str(request.url)
        )

        if not is_valid:
            raise PermissionDeniedException("Invalid Twilio signature")

        # Convert to Message
        message = await provider.receive_message(data)

        # Process through unified pipeline
        strategy = ProcessingStrategyManager()
        result = await strategy.process_message(message)  # New method

        # Return TwiML response
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            status_code=HTTP_200_OK,
            media_type="application/xml"
        )
```

**C. Add Twilio Configuration** (`src/cellophanemail/config/settings.py:94-95`)

```python
# Add after Stripe settings
twilio_account_sid: str = Field(default="", description="Twilio Account SID")
twilio_auth_token: str = Field(default="", description="Twilio Auth Token")
twilio_api_key: str = Field(default="", description="Twilio API Key (recommended)")
twilio_api_secret: str = Field(default="", description="Twilio API Secret")
twilio_phone_number: str = Field(default="", description="Twilio phone number for sending")

@field_validator('twilio_account_sid')
@classmethod
def validate_twilio_sid(cls, v: str) -> str:
    """Validate Twilio Account SID format."""
    if v and not v.startswith('AC'):
        raise ValueError("Twilio Account SID must start with 'AC'")
    return v
```

**D. Update Environment Template** (`.env.example`)

```bash
# ============================================
# Twilio SMS Configuration
# ============================================
# Twilio Account (https://console.twilio.com/)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_API_KEY=SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_API_SECRET=your_api_secret
TWILIO_PHONE_NUMBER=+61412345678
```

**E. Add Twilio Dependency** (`pyproject.toml`)

```toml
dependencies = [
    # ... existing dependencies
    "twilio>=9.0.0",  # SMS provider
    "phonenumbers>=8.13.0",  # Phone validation
]
```

#### 1.4 Refactor Processing Pipeline

**A. Update ProcessingStrategyManager** (`src/cellophanemail/features/email_processing_strategy.py:25-68`)

Make it channel-agnostic:

```python
class ProcessingStrategyManager:
    """Manages message processing strategy (privacy-focused in-memory processing)."""

    def __init__(self):
        self.orchestrator = PrivacyWebhookOrchestrator()

    async def process_message(self, message: EmailMessage, user_email: str) -> Response:
        """Process message through privacy-focused pipeline (channel-agnostic)."""

        # Log channel type
        logger.info(f"Processing {message.channel.value} message {message.message_id}")

        # Convert to EphemeralEmail (already channel-agnostic)
        ephemeral = self._convert_to_ephemeral(message, user_email)

        # Process through orchestrator
        result = await self.orchestrator.process_webhook(
            payload=message.to_dict(),  # Add to_dict() method to Message
            user_email=user_email
        )

        return Response(
            content={"status": "accepted", "channel": message.channel.value},
            status_code=202
        )

    def _convert_to_ephemeral(self, message: EmailMessage, user_email: str):
        """Convert Message to EphemeralEmail."""
        return EphemeralEmail(
            message_id=message.message_id,
            from_address=message.from_address,
            to_addresses=message.to_addresses,
            subject=message.subject,
            text_body=message.content,
            html_body=message.rich_content,
            user_email=user_email,
            channel_type=message.channel.value  # Add this field
        )
```

**B. Update InMemoryProcessor** (`src/cellophanemail/features/email_protection/in_memory_processor.py:87-155`)

Already channel-agnostic! Just verify:

```python
async def process_email(self, ephemeral_email: EphemeralEmail) -> ProcessingResult:
    """Process ephemeral email (or SMS) through toxicity analysis."""

    # Extract content (works for both email and SMS)
    content = ephemeral_email.get_content_for_analysis()

    # Analyze toxicity (channel-agnostic)
    analysis = self.analyzer.analyze_email_toxicity(content, ephemeral_email.from_address)

    # Make decision (channel-agnostic)
    decision = self._make_protection_decision(analysis)

    # No changes needed - already works for SMS!
    return ProcessingResult(...)
```

### Success Criteria

#### Automated Verification:
- [ ] Database migration applies cleanly: `piccolo migrations forwards cellophanemail`
- [ ] All imports resolve: `python -m py_compile src/cellophanemail/**/*.py`
- [ ] Unit tests pass: `pytest tests/unit/test_message_model.py`
- [ ] Type checking passes: `mypy src/cellophanemail/`
- [ ] Provider tests pass: `pytest tests/unit/test_twilio_provider.py`

#### Manual Verification:
- [ ] Can receive Postmark webhook → processes as EMAIL channel
- [ ] Can receive Twilio webhook → processes as SMS channel
- [ ] Both channels route through same LLM analysis
- [ ] EmailLog table shows channel_type correctly
- [ ] Twilio webhook signature validation blocks invalid requests
- [ ] Phone numbers normalized to E.164 format

---

## Phase 2: Stripe Billing Integration (2-3 weeks)

### Overview
Implement complete Stripe integration for subscription management, checkout flows, webhook handling, and usage tracking.

### Changes Required

#### 2.1 Create Stripe Service Layer

**A. Stripe Service** (`src/cellophanemail/services/stripe_service.py` - NEW FILE)

```python
"""Stripe billing service."""
import stripe
from typing import Optional, Dict, Any
from ..config.settings import get_settings

class StripeService:
    """Handle all Stripe API interactions."""

    def __init__(self):
        settings = get_settings()
        stripe.api_key = settings.stripe_api_key
        self.webhook_secret = settings.stripe_webhook_secret

    async def create_customer(self, user_id: str, email: str, name: str) -> stripe.Customer:
        """Create Stripe customer."""
        return stripe.Customer.create(
            email=email,
            name=name,
            metadata={"user_id": user_id}
        )

    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        trial_days: int = 30
    ) -> stripe.checkout.Session:
        """Create Stripe Checkout session."""
        return stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            subscription_data={"trial_period_days": trial_days},
            allow_promotion_codes=True
        )

    async def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> stripe.Subscription:
        """Cancel subscription."""
        return stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=at_period_end
        )

    async def create_portal_session(self, customer_id: str, return_url: str) -> stripe.billing_portal.Session:
        """Create Stripe Customer Portal session."""
        return stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url
        )

    def verify_webhook_signature(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Verify Stripe webhook signature."""
        return stripe.Webhook.construct_event(
            payload, sig_header, self.webhook_secret
        )
```

#### 2.2 Create Billing Routes

**B. Billing Routes** (`src/cellophanemail/routes/billing.py` - NEW FILE)

```python
"""Billing and subscription routes."""
from litestar import Controller, get, post, Request, Response
from litestar.status_codes import HTTP_303_SEE_OTHER, HTTP_200_OK
from ..services.stripe_service import StripeService
from ..middleware.jwt_auth import jwt_auth_required

class BillingController(Controller):
    path = "/billing"
    tags = ["billing"]

    @post("/create-checkout", guards=[jwt_auth_required])
    async def create_checkout(self, request: Request, data: Dict[str, Any]) -> Response:
        """Create Stripe Checkout session."""
        user = request.user
        stripe_service = StripeService()

        # Create or get customer
        if not user.stripe_customer_id:
            customer = await stripe_service.create_customer(
                user_id=str(user.id),
                email=user.email,
                name=f"{user.first_name} {user.last_name}"
            )
            # Update user
            user.stripe_customer_id = customer.id
            await user.save()

        # Create checkout session
        session = await stripe_service.create_checkout_session(
            customer_id=user.stripe_customer_id,
            price_id=data["price_id"],
            success_url=f"{request.base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{request.base_url}/billing/cancel",
            trial_days=30
        )

        return Response(
            content={"checkout_url": session.url},
            status_code=HTTP_200_OK
        )

    @get("/portal", guards=[jwt_auth_required])
    async def customer_portal(self, request: Request) -> Response:
        """Redirect to Stripe Customer Portal."""
        user = request.user
        stripe_service = StripeService()

        session = await stripe_service.create_portal_session(
            customer_id=user.stripe_customer_id,
            return_url=f"{request.base_url}/auth/dashboard"
        )

        return Response(
            content={"portal_url": session.url},
            status_code=HTTP_303_SEE_OTHER,
            headers={"Location": session.url}
        )
```

#### 2.3 Stripe Webhook Handler

**C. Stripe Webhooks** (`src/cellophanemail/routes/stripe_webhooks.py` - NEW FILE)

```python
"""Stripe webhook event handler."""
from litestar import Controller, post, Request, Response
from litestar.status_codes import HTTP_200_OK
from ..services.stripe_service import StripeService
from ..models.subscription import Subscription
from ..models.user import User

class StripeWebhookHandler(Controller):
    path = "/webhooks/stripe"
    tags = ["webhooks"]

    @post("/")
    async def handle_webhook(self, request: Request) -> Response:
        """Handle Stripe webhook events."""
        stripe_service = StripeService()

        # Verify signature
        payload = await request.body()
        sig_header = request.headers.get("Stripe-Signature")

        try:
            event = stripe_service.verify_webhook_signature(payload, sig_header)
        except Exception as e:
            logger.error(f"Stripe webhook signature verification failed: {e}")
            return Response(content={"error": "Invalid signature"}, status_code=400)

        # Handle events
        event_type = event["type"]
        data_object = event["data"]["object"]

        if event_type == "customer.subscription.created":
            await self._handle_subscription_created(data_object)
        elif event_type == "customer.subscription.updated":
            await self._handle_subscription_updated(data_object)
        elif event_type == "customer.subscription.deleted":
            await self._handle_subscription_deleted(data_object)
        elif event_type == "invoice.payment_succeeded":
            await self._handle_payment_succeeded(data_object)
        elif event_type == "invoice.payment_failed":
            await self._handle_payment_failed(data_object)

        return Response(content={"received": True}, status_code=HTTP_200_OK)

    async def _handle_subscription_created(self, subscription: Dict):
        """Create subscription record in database."""
        # Find user by customer_id
        user = await User.objects().where(
            User.stripe_customer_id == subscription["customer"]
        ).first()

        if user:
            await Subscription.objects().create(
                organization_id=user.organization_id,
                stripe_subscription_id=subscription["id"],
                stripe_customer_id=subscription["customer"],
                stripe_product_id=subscription["plan"]["product"],
                stripe_price_id=subscription["plan"]["id"],
                status=subscription["status"],
                amount=subscription["plan"]["amount"] / 100,  # Convert cents to dollars
                currency=subscription["plan"]["currency"],
                interval=subscription["plan"]["interval"],
                current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
                current_period_end=datetime.fromtimestamp(subscription["current_period_end"]),
                trial_start=datetime.fromtimestamp(subscription["trial_start"]) if subscription.get("trial_start") else None,
                trial_end=datetime.fromtimestamp(subscription["trial_end"]) if subscription.get("trial_end") else None
            )

            # Update user subscription status
            user.subscription_status = "active"
            await user.save()
```

#### 2.4 Update Registration Flow

**D. Update Auth Routes** (`src/cellophanemail/routes/auth.py:182`)

Replace TODO with actual Stripe checkout:

```python
# OLD (line 182):
# TODO: Create Stripe checkout session for trial

# NEW:
stripe_service = StripeService()

# Create Stripe customer
customer = await stripe_service.create_customer(
    user_id=str(user.id),
    email=user.email,
    name=f"{user.first_name or ''} {user.last_name or ''}".strip()
)

# Store customer ID
user.stripe_customer_id = customer.id
await user.save()

# Return checkout URL in response
return Response(
    content={
        "status": "registered",
        "user_id": str(user.id),
        "email": user.email,
        "shield_address": shield_address,
        "checkout_url": f"/billing/create-checkout?user_id={user.id}",
        "message": "Registration successful. Complete payment to activate your account."
    },
    status_code=HTTP_201_CREATED
)
```

### Success Criteria

#### Automated Verification:
- [x] Stripe Service created with all methods (customer, checkout, portal, webhooks)
- [x] Billing Controller created with checkout and portal endpoints
- [x] Stripe Webhook Handler created with subscription event handlers
- [x] Auth registration flow updated to create Stripe customers
- [x] Routes registered in app.py
- [ ] Stripe checkout session created successfully: `pytest tests/integration/test_stripe_checkout.py`
- [ ] Webhook signature verification passes: `stripe trigger customer.subscription.created`
- [ ] Subscription record created in database after webhook
- [ ] User subscription_status updated correctly

#### Manual Verification:
- [ ] User can complete signup and reach Stripe Checkout page
- [ ] After payment, user is redirected back with active subscription
- [ ] Stripe Customer Portal link works from dashboard
- [ ] Subscription cancellation updates database correctly
- [ ] Trial period expires after 30 days and charges first payment
- [ ] Failed payment updates user status to "past_due"

---

## Phase 3: Case File Management API (2-3 weeks)

### Overview
Build API endpoints for creating, managing, and exporting case files in both JSON (structured data) and PDF (legal documents) formats.

### Changes Required

#### 3.1 Create Case File Data Model

**A. CaseFile Model** (`src/cellophanemail/models/case_file.py` - NEW FILE)

```python
"""Case file model for documenting abusive communications."""
from piccolo.table import Table
from piccolo.columns import (
    UUID, Varchar, Text, JSON, Timestamp, ForeignKey, Boolean, Integer
)
from datetime import datetime
import uuid

class CaseFile(Table):
    """Case file aggregating multiple messages for legal/administrative use."""

    id = UUID(primary_key=True, default=uuid.uuid4)
    user = ForeignKey("User", null=False, index=True)
    organization = ForeignKey("Organization", null=True, index=True)

    # Case metadata
    title = Varchar(length=500, null=False)
    description = Text(null=True)
    case_number = Varchar(length=100, unique=True, null=True, index=True)

    # Status
    status = Varchar(length=50, default="draft")  # draft, finalized, submitted

    # Timestamps
    created_at = Timestamp(default=datetime.now, null=False, index=True)
    updated_at = Timestamp(default=datetime.now, null=False)
    finalized_at = Timestamp(null=True)

    # Export tracking
    pdf_generated = Boolean(default=False)
    pdf_generated_at = Timestamp(null=True)
    last_exported_at = Timestamp(null=True)

    # Statistics (cached)
    total_messages = Integer(default=0)
    high_toxicity_count = Integer(default=0)
    date_range_start = Timestamp(null=True)
    date_range_end = Timestamp(null=True)

class CaseFileMessage(Table):
    """Link table between case files and communication logs."""

    id = UUID(primary_key=True, default=uuid.uuid4)
    case_file = ForeignKey(CaseFile, null=False, index=True)
    email_log = ForeignKey("EmailLog", null=True, index=True)  # Links to EmailLog

    # Message snapshot (for immutability after finalization)
    message_snapshot = JSON(null=True)  # Full message data frozen at finalization

    # Ordering
    order = Integer(default=0)

    # Metadata
    added_at = Timestamp(default=datetime.now, null=False)
    added_by = ForeignKey("User", null=False)
    notes = Text(null=True)  # User notes about this message
```

**B. Create Migration** (`migrations/cellophanemail_2025_10_11_case_files.py`)

```python
from piccolo.apps.migrations.auto.migration_manager import MigrationManager

ID = "2025-10-11T10:00:00:000000"

async def forwards():
    manager = MigrationManager(
        migration_id=ID,
        app_name="cellophanemail",
        description="Add case file tables"
    )

    # Create case_files table
    # Create case_file_messages table
    # ... (Piccolo auto-generates from Table definitions)

    return manager
```

#### 3.2 Case File Service

**C. Case File Service** (`src/cellophanemail/services/case_file_service.py` - NEW FILE)

```python
"""Case file management service."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..models.case_file import CaseFile, CaseFileMessage
from ..models.email_log import EmailLog

class CaseFileService:
    """Handle case file operations."""

    async def create_case(
        self,
        user_id: str,
        title: str,
        description: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> CaseFile:
        """Create new case file."""
        case = await CaseFile.objects().create(
            user_id=user_id,
            organization_id=organization_id,
            title=title,
            description=description,
            case_number=self._generate_case_number()
        )
        return case

    async def add_message_to_case(
        self,
        case_id: str,
        email_log_id: str,
        user_id: str,
        notes: Optional[str] = None
    ) -> CaseFileMessage:
        """Add message to case file."""

        # Get email log
        email_log = await EmailLog.objects().where(
            EmailLog.id == email_log_id
        ).first()

        if not email_log:
            raise ValueError("Email log not found")

        # Get current message count for ordering
        count = await CaseFileMessage.count().where(
            CaseFileMessage.case_file == case_id
        )

        # Add to case
        case_message = await CaseFileMessage.objects().create(
            case_file_id=case_id,
            email_log_id=email_log_id,
            order=count,
            added_by=user_id,
            notes=notes
        )

        # Update case statistics
        await self._update_case_stats(case_id)

        return case_message

    async def finalize_case(self, case_id: str) -> CaseFile:
        """Finalize case file (make immutable)."""
        case = await CaseFile.objects().where(CaseFile.id == case_id).first()

        # Snapshot all messages
        messages = await CaseFileMessage.objects().where(
            CaseFileMessage.case_file == case_id
        ).all()

        for msg in messages:
            email_log = await EmailLog.objects().where(
                EmailLog.id == msg.email_log_id
            ).first()

            # Store snapshot
            msg.message_snapshot = {
                "from_address": email_log.from_address,
                "to_addresses": email_log.to_addresses,
                "received_at": email_log.received_at.isoformat(),
                "toxicity_score": str(email_log.toxicity_score),
                "horsemen_detected": email_log.horsemen_detected,
                "channel_type": email_log.channel_type
            }
            await msg.save()

        # Mark case as finalized
        case.status = "finalized"
        case.finalized_at = datetime.now()
        await case.save()

        return case

    async def export_case_json(self, case_id: str) -> Dict[str, Any]:
        """Export case file as structured JSON."""
        case = await self._get_case_with_messages(case_id)

        return {
            "case_file": {
                "id": str(case.id),
                "case_number": case.case_number,
                "title": case.title,
                "description": case.description,
                "status": case.status,
                "created_at": case.created_at.isoformat(),
                "finalized_at": case.finalized_at.isoformat() if case.finalized_at else None,
                "statistics": {
                    "total_messages": case.total_messages,
                    "high_toxicity_count": case.high_toxicity_count,
                    "date_range": {
                        "start": case.date_range_start.isoformat() if case.date_range_start else None,
                        "end": case.date_range_end.isoformat() if case.date_range_end else None
                    }
                }
            },
            "messages": [
                {
                    "order": msg.order,
                    "data": msg.message_snapshot,
                    "notes": msg.notes,
                    "added_at": msg.added_at.isoformat()
                }
                for msg in case.messages
            ]
        }

    def _generate_case_number(self) -> str:
        """Generate unique case number."""
        timestamp = datetime.now().strftime("%Y%m%d")
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f"CASE-{timestamp}-{random_suffix}"

    async def _update_case_stats(self, case_id: str):
        """Update case file statistics."""
        # Aggregate stats from messages
        # ... (implementation details)
```

#### 3.3 PDF Generation Service

**D. PDF Generator** (`src/cellophanemail/services/pdf_generator.py` - NEW FILE)

```python
"""PDF report generation service."""
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Dict, Any
import tempfile

class PDFGenerator:
    """Generate PDF reports from case files."""

    def __init__(self):
        template_dir = Path(__file__).parent.parent / "templates" / "reports"
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

    async def generate_case_pdf(self, case_data: Dict[str, Any]) -> bytes:
        """Generate PDF from case file data."""

        # Render HTML template
        template = self.jinja_env.get_template("case_file_report.html")
        html_content = template.render(case=case_data)

        # Generate PDF
        pdf_bytes = HTML(string=html_content).write_pdf()

        return pdf_bytes
```

**E. PDF Template** (`src/cellophanemail/templates/reports/case_file_report.html` - NEW FILE)

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Case File Report: {{ case.case_file.case_number }}</title>
    <style>
        @page {
            size: A4;
            margin: 2cm;
            @bottom-right {
                content: "Page " counter(page) " of " counter(pages);
            }
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
        }
        .header {
            text-align: center;
            margin-bottom: 2cm;
            border-bottom: 2px solid #333;
            padding-bottom: 1cm;
        }
        .case-info {
            margin-bottom: 1cm;
        }
        .message {
            border: 1px solid #ddd;
            padding: 1cm;
            margin-bottom: 0.5cm;
            page-break-inside: avoid;
        }
        .toxicity-high {
            background-color: #ffe0e0;
        }
        .metadata {
            font-size: 9pt;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Case File Report</h1>
        <p><strong>Case Number:</strong> {{ case.case_file.case_number }}</p>
        <p><strong>Generated:</strong> {{ now().strftime('%Y-%m-%d %H:%M') }}</p>
    </div>

    <div class="case-info">
        <h2>{{ case.case_file.title }}</h2>
        <p>{{ case.case_file.description }}</p>

        <p><strong>Total Messages:</strong> {{ case.case_file.statistics.total_messages }}</p>
        <p><strong>High Toxicity Messages:</strong> {{ case.case_file.statistics.high_toxicity_count }}</p>
        <p><strong>Date Range:</strong>
            {{ case.case_file.statistics.date_range.start }} to
            {{ case.case_file.statistics.date_range.end }}
        </p>
    </div>

    <h2>Messages</h2>
    {% for message in case.messages %}
    <div class="message {% if message.data.toxicity_score|float > 0.7 %}toxicity-high{% endif %}">
        <h3>Message #{{ message.order + 1 }}</h3>
        <p class="metadata">
            <strong>From:</strong> {{ message.data.from_address }}<br>
            <strong>To:</strong> {{ message.data.to_addresses|join(', ') }}<br>
            <strong>Date:</strong> {{ message.data.received_at }}<br>
            <strong>Channel:</strong> {{ message.data.channel_type|upper }}<br>
            <strong>Toxicity Score:</strong> {{ message.data.toxicity_score }}
        </p>

        {% if message.data.horsemen_detected %}
        <p><strong>Threats Detected:</strong>
            {{ message.data.horsemen_detected|join(', ') }}
        </p>
        {% endif %}

        {% if message.notes %}
        <p><strong>Notes:</strong> {{ message.notes }}</p>
        {% endif %}
    </div>
    {% endfor %}

    <div style="margin-top: 2cm; padding-top: 1cm; border-top: 1px solid #ddd;">
        <p style="font-size: 9pt; color: #666;">
            This report was generated by CellophoneMail automated case file system.
            Report ID: {{ case.case_file.id }}
        </p>
    </div>
</body>
</html>
```

#### 3.4 Case File API Routes

**F. Case File Routes** (`src/cellophanemail/routes/case_files.py` - NEW FILE)

```python
"""Case file management API routes."""
from litestar import Controller, get, post, delete, Request, Response
from litestar.status_codes import HTTP_201_CREATED, HTTP_200_OK
from ..services.case_file_service import CaseFileService
from ..services.pdf_generator import PDFGenerator
from ..middleware.jwt_auth import jwt_auth_required

class CaseFileController(Controller):
    path = "/api/v1/cases"
    tags = ["case-files"]
    guards = [jwt_auth_required]

    @post("/")
    async def create_case(self, request: Request, data: Dict[str, Any]) -> Response:
        """Create new case file."""
        user = request.user
        service = CaseFileService()

        case = await service.create_case(
            user_id=str(user.id),
            title=data["title"],
            description=data.get("description"),
            organization_id=str(user.organization_id) if user.organization_id else None
        )

        return Response(
            content={
                "id": str(case.id),
                "case_number": case.case_number,
                "title": case.title,
                "created_at": case.created_at.isoformat()
            },
            status_code=HTTP_201_CREATED
        )

    @post("/{case_id:uuid}/messages")
    async def add_message(self, request: Request, case_id: str, data: Dict[str, Any]) -> Response:
        """Add message to case file."""
        user = request.user
        service = CaseFileService()

        case_message = await service.add_message_to_case(
            case_id=case_id,
            email_log_id=data["email_log_id"],
            user_id=str(user.id),
            notes=data.get("notes")
        )

        return Response(
            content={"id": str(case_message.id), "order": case_message.order},
            status_code=HTTP_201_CREATED
        )

    @post("/{case_id:uuid}/finalize")
    async def finalize_case(self, request: Request, case_id: str) -> Response:
        """Finalize case file (make immutable)."""
        service = CaseFileService()
        case = await service.finalize_case(case_id)

        return Response(
            content={"status": "finalized", "finalized_at": case.finalized_at.isoformat()},
            status_code=HTTP_200_OK
        )

    @get("/{case_id:uuid}/export/json")
    async def export_json(self, request: Request, case_id: str) -> Response:
        """Export case as JSON."""
        service = CaseFileService()
        case_data = await service.export_case_json(case_id)

        return Response(
            content=case_data,
            status_code=HTTP_200_OK,
            headers={"Content-Disposition": f'attachment; filename="case_{case_data["case_file"]["case_number"]}.json"'}
        )

    @get("/{case_id:uuid}/export/pdf")
    async def export_pdf(self, request: Request, case_id: str) -> Response:
        """Export case as PDF."""
        service = CaseFileService()
        pdf_gen = PDFGenerator()

        case_data = await service.export_case_json(case_id)
        pdf_bytes = await pdf_gen.generate_case_pdf(case_data)

        return Response(
            content=pdf_bytes,
            status_code=HTTP_200_OK,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="case_{case_data["case_file"]["case_number"]}.pdf"'}
        )
```

#### 3.5 Add Dependencies

**G. Update pyproject.toml**

```toml
dependencies = [
    # ... existing
    "weasyprint>=61.0.0",  # PDF generation
]
```

### Success Criteria

#### Automated Verification:
- [ ] Database migrations apply: `piccolo migrations forwards cellophanemail`
- [ ] Case file CRUD tests pass: `pytest tests/unit/test_case_file_service.py`
- [ ] PDF generation test passes: `pytest tests/unit/test_pdf_generator.py`
- [ ] API endpoint tests pass: `pytest tests/integration/test_case_api.py`

#### Manual Verification:
- [ ] Can create case file via API
- [ ] Can add email/SMS messages to case
- [ ] Case statistics update automatically
- [ ] Finalized cases become immutable
- [ ] JSON export contains complete case data
- [ ] PDF export is readable and properly formatted
- [ ] Downloaded PDF includes all messages with metadata
- [ ] High toxicity messages are visually highlighted in PDF

---

## Phase 4: Organization Management & User Flows (2 weeks)

### Overview
Implement organization joining, member management, and improved signup flows.

### Changes Required

#### 4.1 Organization Invitation System

**A. Organization Invitation Model** (`src/cellophanemail/models/organization_invitation.py` - NEW FILE)

```python
"""Organization invitation model."""
from piccolo.table import Table
from piccolo.columns import UUID, Varchar, ForeignKey, Timestamp, Boolean
from datetime import datetime, timedelta
import uuid

class OrganizationInvitation(Table):
    """Invitation to join an organization."""

    id = UUID(primary_key=True, default=uuid.uuid4)
    organization = ForeignKey("Organization", null=False, index=True)
    invited_by = ForeignKey("User", null=False)

    # Invitee details
    email = Varchar(length=255, null=False, index=True)

    # Invitation token
    token = Varchar(length=255, unique=True, null=False, index=True)

    # Status
    status = Varchar(length=50, default="pending")  # pending, accepted, expired, revoked

    # Timestamps
    created_at = Timestamp(default=datetime.now, null=False)
    expires_at = Timestamp(null=False)  # 7 days from creation
    accepted_at = Timestamp(null=True)

    @classmethod
    async def create_invitation(cls, org_id: str, invited_by_id: str, email: str):
        """Create new invitation with token and expiry."""
        token = uuid.uuid4().hex
        expires_at = datetime.now() + timedelta(days=7)

        return await cls.objects().create(
            organization_id=org_id,
            invited_by=invited_by_id,
            email=email,
            token=token,
            expires_at=expires_at
        )
```

#### 4.2 Organization Service

**B. Organization Service** (`src/cellophanemail/services/organization_service.py` - NEW FILE)

```python
"""Organization management service."""
from typing import List, Optional
from ..models.organization import Organization
from ..models.organization_invitation import OrganizationInvitation
from ..models.user import User

class OrganizationService:
    """Handle organization operations."""

    async def create_organization(
        self,
        name: str,
        slug: str,
        created_by_user_id: str
    ) -> Organization:
        """Create new organization."""
        org = await Organization.objects().create(
            name=name,
            slug=slug
        )

        # Update user to be part of org
        user = await User.objects().where(User.id == created_by_user_id).first()
        user.organization_id = org.id
        await user.save()

        return org

    async def search_organizations(self, query: str, limit: int = 10) -> List[Organization]:
        """Search organizations by name."""
        return await Organization.objects().where(
            Organization.name.ilike(f"%{query}%")
        ).limit(limit).all()

    async def invite_member(
        self,
        org_id: str,
        invited_by_user_id: str,
        email: str
    ) -> OrganizationInvitation:
        """Send invitation to join organization."""

        # Check if user already in org
        existing_user = await User.objects().where(
            User.email == email,
            User.organization_id == org_id
        ).first()

        if existing_user:
            raise ValueError("User already in organization")

        # Create invitation
        invitation = await OrganizationInvitation.create_invitation(
            org_id=org_id,
            invited_by_id=invited_by_user_id,
            email=email
        )

        # Send invitation email (TODO: implement email service)
        # await self._send_invitation_email(invitation)

        return invitation

    async def accept_invitation(self, token: str, user_id: str) -> Organization:
        """Accept organization invitation."""
        invitation = await OrganizationInvitation.objects().where(
            OrganizationInvitation.token == token,
            OrganizationInvitation.status == "pending"
        ).first()

        if not invitation:
            raise ValueError("Invalid or expired invitation")

        if invitation.expires_at < datetime.now():
            invitation.status = "expired"
            await invitation.save()
            raise ValueError("Invitation has expired")

        # Add user to organization
        user = await User.objects().where(User.id == user_id).first()
        user.organization_id = invitation.organization_id
        await user.save()

        # Update invitation
        invitation.status = "accepted"
        invitation.accepted_at = datetime.now()
        await invitation.save()

        return await Organization.objects().where(
            Organization.id == invitation.organization_id
        ).first()
```

#### 4.3 Organization API Routes

**C. Organization Routes** (`src/cellophanemail/routes/organizations.py` - NEW FILE)

```python
"""Organization management API routes."""
from litestar import Controller, get, post, Request, Response
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED
from ..services.organization_service import OrganizationService
from ..middleware.jwt_auth import jwt_auth_required

class OrganizationController(Controller):
    path = "/api/v1/organizations"
    tags = ["organizations"]

    @get("/search")
    async def search_organizations(self, request: Request, q: str) -> Response:
        """Search organizations by name (public endpoint for signup)."""
        service = OrganizationService()
        orgs = await service.search_organizations(query=q, limit=10)

        return Response(
            content={
                "results": [
                    {"id": str(org.id), "name": org.name, "slug": org.slug}
                    for org in orgs
                ]
            },
            status_code=HTTP_200_OK
        )

    @post("/", guards=[jwt_auth_required])
    async def create_organization(self, request: Request, data: Dict[str, Any]) -> Response:
        """Create new organization."""
        user = request.user
        service = OrganizationService()

        org = await service.create_organization(
            name=data["name"],
            slug=data["slug"],
            created_by_user_id=str(user.id)
        )

        return Response(
            content={"id": str(org.id), "name": org.name, "slug": org.slug},
            status_code=HTTP_201_CREATED
        )

    @post("/{org_id:uuid}/invitations", guards=[jwt_auth_required])
    async def invite_member(self, request: Request, org_id: str, data: Dict[str, Any]) -> Response:
        """Invite user to organization."""
        user = request.user
        service = OrganizationService()

        # Verify user is in org
        if str(user.organization_id) != org_id:
            return Response(content={"error": "Not authorized"}, status_code=403)

        invitation = await service.invite_member(
            org_id=org_id,
            invited_by_user_id=str(user.id),
            email=data["email"]
        )

        return Response(
            content={
                "invitation_id": str(invitation.id),
                "token": invitation.token,
                "expires_at": invitation.expires_at.isoformat()
            },
            status_code=HTTP_201_CREATED
        )

    @post("/invitations/{token}/accept", guards=[jwt_auth_required])
    async def accept_invitation(self, request: Request, token: str) -> Response:
        """Accept organization invitation."""
        user = request.user
        service = OrganizationService()

        org = await service.accept_invitation(token=token, user_id=str(user.id))

        return Response(
            content={"organization": {"id": str(org.id), "name": org.name}},
            status_code=HTTP_200_OK
        )
```

#### 4.4 Update Registration Flow

**D. Enhanced Registration** (`src/cellophanemail/routes/auth.py`)

Update registration endpoint to support organization joining:

```python
class EnhancedUserRegistration(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    # Organization options
    create_organization: bool = False
    organization_name: Optional[str] = None
    join_organization_id: Optional[str] = None
    invitation_token: Optional[str] = None

@post("/register")
async def register_enhanced(self, data: EnhancedUserRegistration) -> Response:
    """Enhanced registration with organization support."""

    # Create user (existing logic)
    user = await auth_service.create_user(...)

    # Handle organization
    org_service = OrganizationService()

    if data.invitation_token:
        # Accept invitation
        org = await org_service.accept_invitation(data.invitation_token, str(user.id))
    elif data.create_organization and data.organization_name:
        # Create new organization
        org = await org_service.create_organization(
            name=data.organization_name,
            slug=data.organization_name.lower().replace(" ", "-"),
            created_by_user_id=str(user.id)
        )
    elif data.join_organization_id:
        # Join existing organization (send join request)
        # ... implementation

    # Continue with Stripe checkout...
```

### Success Criteria

#### Automated Verification:
- [ ] Organization CRUD tests pass: `pytest tests/unit/test_organization_service.py`
- [ ] Invitation creation/acceptance tests pass
- [ ] Organization search returns correct results

#### Manual Verification:
- [ ] Can create new organization during signup
- [ ] Can search for existing organizations
- [ ] Can send invitation to email address
- [ ] Invitation link works and adds user to org
- [ ] Expired invitations are rejected
- [ ] Users in same org share subscription quota

---

## Phase 5: Web App (cellophane-web) (4-6 weeks)

### Overview
Build Next.js web application for organization signup, billing, dashboard, and administration.

**Technology Stack**:
- Next.js 14 (App Router)
- React 18
- TypeScript
- TailwindCSS
- shadcn/ui components
- Stripe Elements for checkout

### Repository Structure

```
cellophane-web/
├── app/
│   ├── (auth)/
│   │   ├── signup/
│   │   │   └── page.tsx
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   ├── cases/
│   │   │   ├── page.tsx
│   │   │   └── [id]/
│   │   │       └── page.tsx
│   │   ├── organization/
│   │   │   └── page.tsx
│   │   └── layout.tsx
│   ├── api/
│   │   └── webhooks/
│   │       └── stripe/
│   │           └── route.ts
│   └── layout.tsx
├── components/
│   ├── ui/  # shadcn components
│   ├── auth/
│   │   ├── SignupForm.tsx
│   │   └── LoginForm.tsx
│   ├── dashboard/
│   │   ├── MessageList.tsx
│   │   ├── ToxicityChart.tsx
│   │   └── UsageStats.tsx
│   └── cases/
│       ├── CaseFileList.tsx
│       └── CreateCaseDialog.tsx
├── lib/
│   ├── api.ts  # Backend API client
│   ├── auth.ts  # Auth helpers
│   └── stripe.ts  # Stripe integration
├── types/
│   └── api.ts  # TypeScript types
└── package.json
```

### Key Implementation Files

#### 5.1 API Client

**File**: `lib/api.ts`

```typescript
/**
 * Backend API client with JWT authentication
 */
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem('access_token', data.access_token);
          // Retry original request
          return api.request(error.config);
        } catch {
          // Refresh failed, logout
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

#### 5.2 Signup Form with Organization

**File**: `app/(auth)/signup/page.tsx`

```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';

export default function SignupPage() {
  const router = useRouter();
  const [mode, setMode] = useState<'create' | 'join'>('create');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    organization_name: '',
    join_organization_id: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const { data } = await api.post('/auth/register', {
        ...formData,
        create_organization: mode === 'create',
      });

      // Store tokens
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);

      // Redirect to Stripe checkout
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        router.push('/dashboard');
      }
    } catch (error) {
      console.error('Signup failed:', error);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-lg shadow-md">
      <h1 className="text-2xl font-bold mb-6">Sign Up for CellophoneMail</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label>Organization Setup</Label>
          <RadioGroup value={mode} onValueChange={(v) => setMode(v as any)}>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="create" id="create" />
              <Label htmlFor="create">Create new organization</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="join" id="join" />
              <Label htmlFor="join">Join existing organization</Label>
            </div>
          </RadioGroup>
        </div>

        <div>
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            required
          />
        </div>

        <div>
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            required
          />
        </div>

        {mode === 'create' && (
          <div>
            <Label htmlFor="org_name">Organization Name</Label>
            <Input
              id="org_name"
              value={formData.organization_name}
              onChange={(e) => setFormData({ ...formData, organization_name: e.target.value })}
              required
            />
          </div>
        )}

        <Button type="submit" className="w-full">
          Continue to Payment
        </Button>
      </form>
    </div>
  );
}
```

#### 5.3 Dashboard with Message List

**File**: `app/(dashboard)/dashboard/page.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { MessageList } from '@/components/dashboard/MessageList';
import { UsageStats } from '@/components/dashboard/UsageStats';

export default function DashboardPage() {
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      const [userRes, statsRes] = await Promise.all([
        api.get('/auth/profile'),
        api.get('/api/v1/stats'),
      ]);
      setUser(userRes.data);
      setStats(statsRes.data);
    };
    fetchData();
  }, []);

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>

      {stats && <UsageStats data={stats} />}

      <div className="mt-8">
        <MessageList userId={user?.user_id} />
      </div>
    </div>
  );
}
```

### Success Criteria

#### Automated Verification:
- [ ] Web app builds successfully: `npm run build`
- [ ] TypeScript checks pass: `npm run type-check`
- [ ] Unit tests pass: `npm test`
- [ ] E2E tests pass: `npm run test:e2e`

#### Manual Verification:
- [ ] Can signup and create organization
- [ ] Stripe checkout flow completes
- [ ] Dashboard loads with user data
- [ ] Message list displays correctly
- [ ] Case file creation works
- [ ] PDF export downloads successfully

---

## Phase 6: Android App (cellophane-android) (6-8 weeks)

### Overview
Build native Android app in Kotlin for SMS forwarding, toxicity alerts, and case management.

**Technology Stack**:
- Kotlin
- Jetpack Compose (UI)
- Hilt (Dependency Injection)
- Retrofit (API client)
- Room (Local database)
- WorkManager (Background tasks)
- Firebase Cloud Messaging (Push notifications)

### Repository Structure

```
cellophane-android/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/cellophanemail/
│   │   │   │   ├── MainActivity.kt
│   │   │   │   ├── data/
│   │   │   │   │   ├── api/
│   │   │   │   │   │   └── CellophaneApi.kt
│   │   │   │   │   ├── repository/
│   │   │   │   │   │   └── MessageRepository.kt
│   │   │   │   │   └── local/
│   │   │   │   │       └── AppDatabase.kt
│   │   │   │   ├── ui/
│   │   │   │   │   ├── auth/
│   │   │   │   │   │   └── LoginScreen.kt
│   │   │   │   │   ├── dashboard/
│   │   │   │   │   │   └── DashboardScreen.kt
│   │   │   │   │   └── cases/
│   │   │   │   │       └── CaseListScreen.kt
│   │   │   │   ├── service/
│   │   │   │   │   └── SMSForwardingService.kt
│   │   │   │   └── worker/
│   │   │   │       └── SMSWorker.kt
│   │   │   └── AndroidManifest.xml
│   │   └── test/
│   └── build.gradle.kts
├── gradle/
└── settings.gradle.kts
```

### Key Implementation Files

#### 6.1 SMS Receiver

**File**: `app/src/main/java/com/cellophanemail/service/SMSReceiver.kt`

```kotlin
package com.cellophanemail.service

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import android.util.Log
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.workDataOf
import com.cellophanemail.worker.SMSWorker

class SMSReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Telephony.Sms.Intents.SMS_RECEIVED_ACTION) {
            val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)

            messages.forEach { message ->
                val sender = message.originatingAddress ?: "Unknown"
                val body = message.messageBody ?: ""

                Log.d("SMSReceiver", "Received SMS from $sender")

                // Queue background work to forward SMS
                val workRequest = OneTimeWorkRequestBuilder<SMSWorker>()
                    .setInputData(
                        workDataOf(
                            "sender" to sender,
                            "body" to body,
                            "timestamp" to System.currentTimeMillis()
                        )
                    )
                    .build()

                WorkManager.getInstance(context).enqueue(workRequest)
            }
        }
    }
}
```

#### 6.2 SMS Worker (Background Forwarding)

**File**: `app/src/main/java/com/cellophanemail/worker/SMSWorker.kt`

```kotlin
package com.cellophanemail.worker

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.cellophanemail.data.api.CellophaneApi
import com.cellophanemail.data.repository.MessageRepository
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject

@HiltWorker
class SMSWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val messageRepository: MessageRepository,
    private val api: CellophaneApi
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val sender = inputData.getString("sender") ?: return Result.failure()
        val body = inputData.getString("body") ?: return Result.failure()
        val timestamp = inputData.getLong("timestamp", System.currentTimeMillis())

        return try {
            // Forward SMS to backend
            val response = api.analyzeMessage(
                channel = "sms",
                from = sender,
                content = body,
                timestamp = timestamp
            )

            // Store result locally
            messageRepository.saveMessage(
                sender = sender,
                content = body,
                toxicityScore = response.toxicity_score,
                action = response.action,
                processedContent = response.processed_content
            )

            // Show notification if high toxicity
            if (response.toxicity_score > 0.7) {
                showHighToxicityNotification(sender, response.toxicity_score)
            }

            Result.success()
        } catch (e: Exception) {
            Log.e("SMSWorker", "Failed to forward SMS", e)
            Result.retry()
        }
    }

    private fun showHighToxicityNotification(sender: String, score: Float) {
        // ... notification implementation
    }
}
```

#### 6.3 API Client

**File**: `app/src/main/java/com/cellophanemail/data/api/CellophaneApi.kt`

```kotlin
package com.cellophanemail.data.api

import retrofit2.http.*

data class AnalyzeRequest(
    val channel: String,
    val from: String,
    val content: String,
    val timestamp: Long
)

data class AnalyzeResponse(
    val message_id: String,
    val toxicity_score: Float,
    val action: String,
    val processed_content: String,
    val threat_level: String
)

data class LoginRequest(
    val email: String,
    val password: String
)

data class LoginResponse(
    val access_token: String,
    val refresh_token: String,
    val user: User
)

data class User(
    val id: String,
    val email: String,
    val organization_id: String?
)

interface CellophaneApi {
    @POST("/auth/login")
    suspend fun login(@Body request: LoginRequest): LoginResponse

    @POST("/api/v1/messages/analyze")
    suspend fun analyzeMessage(@Body request: AnalyzeRequest): AnalyzeResponse

    @GET("/api/v1/cases")
    suspend fun getCases(): List<CaseFile>

    @POST("/api/v1/cases")
    suspend fun createCase(@Body request: CreateCaseRequest): CaseFile
}
```

#### 6.4 Dashboard Screen

**File**: `app/src/main/java/com/cellophanemail/ui/dashboard/DashboardScreen.kt`

```kotlin
package com.cellophanemail.ui.dashboard

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun DashboardScreen(
    viewModel: DashboardViewModel = hiltViewModel()
) {
    val messages by viewModel.messages.collectAsState()
    val stats by viewModel.stats.collectAsState()

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Dashboard", style = MaterialTheme.typography.headlineLarge)

        Spacer(modifier = Modifier.height(16.dp))

        // Usage stats card
        stats?.let { StatsCard(it) }

        Spacer(modifier = Modifier.height(16.dp))

        // Recent messages
        Text("Recent Messages", style = MaterialTheme.typography.titleMedium)

        LazyColumn {
            items(messages) { message ->
                MessageCard(message)
            }
        }
    }
}

@Composable
fun MessageCard(message: Message) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
        colors = CardDefaults.cardColors(
            containerColor = when {
                message.toxicityScore > 0.7 -> MaterialTheme.colorScheme.errorContainer
                message.toxicityScore > 0.5 -> MaterialTheme.colorScheme.warningContainer
                else -> MaterialTheme.colorScheme.surfaceVariant
            }
        )
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("From: ${message.sender}", style = MaterialTheme.typography.bodyMedium)
            Text("Toxicity: ${(message.toxicityScore * 100).toInt()}%",
                style = MaterialTheme.typography.bodySmall)
            Spacer(modifier = Modifier.height(8.dp))
            Text(message.content, style = MaterialTheme.typography.bodySmall)
        }
    }
}
```

#### 6.5 AndroidManifest.xml Permissions

**File**: `app/src/main/AndroidManifest.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <!-- SMS Permissions -->
    <uses-permission android:name="android.permission.RECEIVE_SMS" />
    <uses-permission android:name="android.permission.READ_SMS" />

    <!-- Network Permissions -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

    <!-- Background Work -->
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />

    <application
        android:name=".CellophoneMailApp"
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:theme="@style/Theme.CellophoneMail">

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <!-- SMS Receiver -->
        <receiver
            android:name=".service.SMSReceiver"
            android:exported="true"
            android:permission="android.permission.BROADCAST_SMS">
            <intent-filter android:priority="999">
                <action android:name="android.provider.Telephony.SMS_RECEIVED" />
            </intent-filter>
        </receiver>

    </application>
</manifest>
```

### Success Criteria

#### Automated Verification:
- [ ] App builds successfully: `./gradlew assembleDebug`
- [ ] Unit tests pass: `./gradlew test`
- [ ] Lint checks pass: `./gradlew lint`
- [ ] Instrumentation tests pass: `./gradlew connectedAndroidTest`

#### Manual Verification:
- [ ] Can login with backend credentials
- [ ] SMS permissions requested and granted
- [ ] Incoming SMS triggers background forwarding
- [ ] High toxicity SMS shows notification
- [ ] Dashboard displays analyzed messages
- [ ] Can create and view case files
- [ ] JWT token refresh works automatically
- [ ] Offline mode queues SMS for later upload

---

## Testing Strategy

### Backend Testing

**Unit Tests**:
- Message model factory methods
- Channel provider implementations
- Toxicity analysis logic
- Case file generation
- PDF rendering

**Integration Tests**:
- Twilio webhook to analysis pipeline
- Stripe webhook to database updates
- Case file export (JSON + PDF)
- Organization invitation flow

**Manual Testing**:
- Send test SMS via Twilio → verify analysis
- Complete Stripe checkout → verify subscription
- Export case file → verify PDF format
- Invite user to org → verify join flow

### Web App Testing

**Unit Tests** (Jest + React Testing Library):
- Component rendering
- Form validation
- API client error handling

**E2E Tests** (Playwright):
- Complete signup flow
- Stripe checkout completion
- Dashboard interaction
- Case file export

### Android App Testing

**Unit Tests** (JUnit):
- API client
- Repository layer
- ViewModel logic

**Instrumentation Tests** (Espresso):
- SMS receiver triggers
- Background worker execution
- Notification display
- UI navigation

---

## Performance Considerations

### Backend Optimization
- **Message processing**: Keep in-memory with 5-minute TTL (existing)
- **Database queries**: Index on `channel_type`, `user_id`, `organization_id`
- **PDF generation**: Cache templates, generate async via Celery (optional)
- **Rate limiting**: Per-channel limits (email vs SMS)

### Android Optimization
- **Battery usage**: Use WorkManager for background SMS forwarding
- **Network usage**: Batch SMS uploads every 5 minutes or 10 messages
- **Storage**: Purge local messages after 30 days
- **Notifications**: Group by sender to avoid spam

---

## Migration Strategy

### Backward Compatibility

**Phase 1 Deployment** (Channel-Agnostic Refactoring):
- Keep `EmailMessage` as alias to `Message` for 2 releases
- Dual-write to `channel_type` column (default: "email")
- All existing email routes continue working

**Phase 2 Deployment** (Billing):
- No breaking changes, additive only
- Existing users default to "free" tier

**Phase 3-4 Deployment** (Case Files + Organizations):
- All new tables, no migrations
- Optional features, no impact on existing users

**Web/Android Launch**:
- New clients, no migration needed

### Rollback Plans

**Phase 1 Rollback**:
- Revert Message model changes
- Remove `channel_type` column migration

**Phase 2 Rollback**:
- Stripe webhooks fail silently
- Users can still use email protection

**Phase 3-6 Rollback**:
- Disable new routes
- No impact on existing features

---

## Timeline Summary

| Phase | Duration | Estimated Completion | Key Deliverable |
|-------|----------|---------------------|-----------------|
| Phase 1: Channel-Agnostic Backend | 6-8 weeks | Week 8 | SMS support live |
| Phase 2: Stripe Billing | 2-3 weeks | Week 11 | Payment functional |
| Phase 3: Case Files | 2-3 weeks | Week 14 | PDF export works |
| Phase 4: Organizations | 2 weeks | Week 16 | Multi-user orgs |
| Phase 5: Web App | 4-6 weeks | Week 22 | Signup/dashboard live |
| Phase 6: Android App | 6-8 weeks | Week 30 | SMS auto-forward |

**Total Estimated Time**: 22-30 weeks (5.5-7.5 months)

---

## Open Questions

1. **SMS Rate Limiting**: Should we implement per-user SMS limits separate from email?
   - Recommendation: Unified "messages/month" quota

2. **Organization Admin Permissions**: How granular should permissions be?
   - Recommendation: Single admin role for MVP, expand later

3. **Case File Approval**: Should finalized cases require admin approval?
   - Recommendation: No approval for MVP, self-finalization

4. **Android Background Restrictions**: How to handle Android 12+ battery optimization?
   - Recommendation: Request "Unrestricted" battery permission, fallback to manual forwarding

5. **Twilio Phone Number Provisioning**: Auto-provision or manual setup?
   - Recommendation: Manual setup for MVP, auto-provision in Phase 7

6. **Multi-Channel Analysis**: Should email + SMS from same sender be linked?
   - Recommendation: Phase 7 feature, separate for MVP

---

## References

### Codebase Analysis Documents
- Channel-agnostic refactoring analysis (this document, Phase 1 research)
- Twilio integration patterns from garasade repository
- EmailMessage architectural conflict analysis
- Current authentication and billing infrastructure analysis

### External Documentation
- Twilio SMS API: https://www.twilio.com/docs/sms
- Stripe Checkout: https://stripe.com/docs/checkout
- Stripe Webhooks: https://stripe.com/docs/webhooks
- WeasyPrint PDF: https://doc.courtbouillon.org/weasyprint/
- Android SMS: https://developer.android.com/reference/android/provider/Telephony.Sms
- Jetpack Compose: https://developer.android.com/jetpack/compose

### Implementation Examples
- garasade SMS webhook handler: `~/repositories/individuals/garasade/app/sms/routes.py:11-129`
- garasade Twilio provider: `~/repositories/individuals/garasade/app/services/sms_service.py`
- cellophanemail privacy pipeline: `src/cellophanemail/features/privacy_integration/privacy_webhook_orchestrator.py`
- cellophanemail LLM analysis: `src/cellophanemail/core/content_analyzer.py`

---

**End of Implementation Plan**
