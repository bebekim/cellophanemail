---
date: 2025-09-15T05:34:11+0000
researcher: Claude Code
git_commit: 18bdf3701a28400cc059cd33379083ad0c65de41
branch: feature/email-delivery-integration
repository: cellophanemail
topic: "Architecture analysis: entry points, configuration, workflows, actors, and state management"
tags: [research, codebase, architecture, privacy-pipeline, email-processing, state-management]
status: complete
last_updated: 2025-09-15
last_updated_by: Claude Code
---

# Research: CellophoneMail Architecture Analysis

**Date**: 2025-09-15T05:34:11+0000
**Researcher**: Claude Code
**Git Commit**: 18bdf3701a28400cc059cd33379083ad0c65de41
**Branch**: feature/email-delivery-integration
**Repository**: cellophanemail

## Research Question
Understand the architecture of the code, entry point, configuration, running the program, state diagram, actors/triggers and workflow/dataflow

## Summary
CellophoneMail is a privacy-focused email protection SaaS built with Litestar (ASGI framework) that implements a dual-architecture pattern: persistent database state for user/organization data and ephemeral in-memory processing for email content. The system operates entirely in-memory for email content processing with a 5-minute TTL to ensure privacy compliance, while using PostgreSQL with Piccolo ORM for metadata persistence.

## Detailed Findings

### Application Entry Points and Bootstrapping

#### Primary Entry Points
- **Main ASGI Application**: `src/cellophanemail/app.py:157` - Litestar ASGI application with comprehensive middleware stack
- **SMTP Server**: `src/cellophanemail/plugins/smtp/__main__.py` - Standalone SMTP server for direct email ingestion
- **Development Scripts**: `bin/dev-all`, `bin/dev-litestar`, `bin/dev-smtp` - Service orchestration scripts

#### Application Factory Pattern
The system uses a factory pattern in `app.py:74-149` with:
- **Dependency injection**: Settings singleton via `get_settings()`
- **Middleware stack**: JWT authentication, CORS, CSRF protection, rate limiting
- **Plugin system**: `PluginManager` for email input methods
- **Lifespan management**: Background service startup/shutdown

#### Dual Service Architecture
- **Web API Server**: Litestar on port 8000 (webhooks, authentication, frontend)
- **SMTP Server**: aiosmtpd on port 2525 (direct email ingestion)
- **Coordination**: Shared memory manager singleton for email processing

### Configuration Management

#### Pydantic Settings Architecture
**Primary Configuration**: `src/cellophanemail/config/settings.py:11-125`
- **Type-safe validation**: Pydantic BaseSettings with Field descriptors
- **Environment binding**: Automatic `.env` file loading via `SettingsConfigDict`
- **Cached singleton**: `@lru_cache()` decorator for performance

#### Configuration Categories
- **Application Settings** (lines 20-32): Debug mode, host/port, encryption keys
- **Database Configuration** (lines 34-39): PostgreSQL with Piccolo ORM integration
- **AI Service Integration** (lines 53-61): Anthropic/Upstage API configuration
- **Email Delivery** (lines 63-84): SMTP and Postmark provider switching
- **Security Settings** (lines 86-95): Plugin management, SaaS billing integration

#### Environment Modes
- **Development** (`.env`): Local PostgreSQL, debug enabled, real API keys
- **Testing** (`.env.test`): Dry-run mode, test database, limited API usage
- **Production** (`production_config.py`): HTTPS enforcement, resource limits, deployment profiles

### Core Workflows and Data Flow

#### Privacy-First Email Processing Pipeline
**Entry**: Webhook → `privacy_webhook_orchestrator.py:112-239`

1. **Webhook Reception**: Validation and shield address resolution
2. **Memory Storage**: 5-minute TTL `EphemeralEmail` with capacity limits (100 concurrent)
3. **Async Processing**: Background task with 30-second timeout
4. **LLM Analysis**: Toxicity scoring via Anthropic Claude 3.5 Sonnet
5. **Graduated Actions**: Based on toxicity scores (0.0-1.0):
   - `< 0.30`: Forward clean
   - `< 0.55`: Forward with warning
   - `< 0.70`: Redact harmful content
   - `< 0.90`: Summary only
   - `≥ 0.90`: Block entirely
6. **Email Composition**: Content transformation based on protection action
7. **Delivery**: Via Postmark API or SMTP with retry logic

#### Request/Response Patterns
- **Webhook Processing**: 202 Accepted for async processing
- **Background Tasks**: asyncio task management with lifecycle tracking
- **Memory Cleanup**: Scheduled 60-second background service

### Actors, Triggers, and Event Handlers

#### HTTP Endpoints
- **Health Checks** (`routes/health.py:14-56`): `/health/`, `/health/ready`, `/health/memory`
- **Authentication** (`routes/auth.py:153-371`): Registration, login, JWT token management
- **Webhooks** (`routes/webhooks.py:36-128`): Legacy Postmark, Gmail integration
- **Provider Webhooks** (`providers/postmark/webhook.py:40-159`): New provider architecture

#### Background Services
- **Memory Cleanup** (`background_cleanup.py:20-116`): TTL-based email expiration
- **Privacy Processing** (`privacy_webhook_orchestrator.py`): Async email pipeline
- **Plugin Manager** (`plugins/manager.py:16-156`): Email input plugin lifecycle

#### External Integrations
- **SMTP Protocol Handlers** (`providers/smtp/server.py:18-174`): Real-time email processing
- **JWT Middleware** (`middleware/jwt_auth.py:38-135`): Request authentication
- **OAuth Callbacks** (`providers/gmail/webhook.py:29-207`): Gmail API integration

### State Management and Transitions

#### Dual-State Architecture
**Persistent State (PostgreSQL)**:
- **User Models** (`models/user.py:21-66`): Authentication, subscription status
- **Organization Models** (`models/organization.py:27-75`): Multi-tenant subscription management
- **Email Logs** (`models/email_log.py:29-76`): Processing metadata only (no content)

**Ephemeral State (Memory)**:
- **Email Content** (`memory_manager.py:39-56`): 5-minute TTL with thread safety
- **Processing Cache** (`services/analysis_cache.py:12-44`): Content hash-based caching
- **Background Tasks**: AsyncIO task tracking for pipeline processing

#### State Machine Patterns
**Email Processing Flow**:
```
PENDING → ANALYZED → (BLOCKED|FORWARDED) → (DELIVERED|BOUNCED|REJECTED)
```

**User Subscription Lifecycle**:
```
FREE → TRIAL → ACTIVE → PAST_DUE → CANCELED
```

**Organization Status Transitions**:
```
ACTIVE ⟷ TRIALING → PAST_DUE → UNPAID → CANCELED
```

#### Memory Management
- **Singleton Pattern**: Shared `MemoryManager` instance across services
- **Capacity Limits**: 100 concurrent emails with rejection at capacity
- **Cleanup Strategy**: Background service with grace period (TTL + 1 minute)

## Code References
- `src/cellophanemail/app.py:157` - Main Litestar application factory
- `src/cellophanemail/config/settings.py:11-125` - Pydantic configuration management
- `src/cellophanemail/features/privacy_integration/privacy_webhook_orchestrator.py:112-239` - Core processing pipeline
- `src/cellophanemail/features/email_protection/memory_manager.py:39-56` - Ephemeral state management
- `src/cellophanemail/features/email_protection/in_memory_processor.py:87-155` - LLM analysis pipeline
- `src/cellophanemail/models/email_log.py:29-76` - Persistent state models
- `src/cellophanemail/routes/webhooks.py:36-128` - Webhook entry points
- `src/cellophanemail/providers/postmark/webhook.py:40-159` - Provider architecture

## Architecture Insights

### Privacy by Design
- **Zero Content Persistence**: Email content never stored in database
- **TTL-based Expiration**: Automatic 5-minute content cleanup
- **Memory-only Processing**: All content analysis in RAM

### Scalability Patterns
- **Async Processing**: 202 Accepted pattern for long-running operations
- **Background Services**: Proper lifecycle management with graceful shutdown
- **Plugin Architecture**: Extensible email input methods
- **Provider Abstraction**: Unified interface for multiple email services

### Security Architecture
- **Hybrid Authentication**: JWT tokens + httpOnly cookies
- **CSRF Protection**: State-changing operation protection
- **Rate Limiting**: 100 requests/minute with webhook exclusions
- **Input Validation**: Pydantic models for all webhook payloads

### Operational Excellence
- **Health Monitoring**: Multi-level health checks with memory metrics
- **Error Handling**: Comprehensive exception handling with retry logic
- **Configuration Management**: Environment-driven with validation
- **Testing Strategy**: Two-tier approach (code quality vs analysis quality)

## Historical Context (from thoughts/)
No dedicated thoughts/ directory found, but comprehensive architecture documentation exists:
- `docs/architecture.md` - Multi-User SaaS Data Flow architecture
- `hybrid_pipeline_dataflow.md` - Sequential Pipeline with Smart Routing
- `enhanced_system_flow.md` - Four Horsemen System Data Flow
- `TDD_PRIVACY_INTEGRATION_PLAN.org` - Unified TDD Privacy Integration strategy

## Open Questions
1. **Scaling Strategy**: How does memory management scale beyond 100 concurrent emails?
2. **Plugin Ecosystem**: Roadmap for additional email provider integrations?
3. **AI Model Evolution**: Plans for supporting multiple LLM providers?
4. **Multi-tenant Isolation**: Database sharding strategy for large organizations?
5. **Compliance Audit**: GDPR/CCPA compliance verification for ephemeral processing?