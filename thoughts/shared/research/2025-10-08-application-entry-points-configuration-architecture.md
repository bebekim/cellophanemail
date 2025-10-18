---
date: 2025-10-08T10:18:59+0000
researcher: Claude
git_commit: bc3628957155c373b4b2a71c1a074f9a8f973320
branch: feature/email-delivery-integration
repository: cellophanemail
topic: "Application Entry Points, Configuration, and Open Source/Commercial Separation"
tags: [research, codebase, entry-points, configuration, architecture, monorepo, open-source, commercial-separation]
status: complete
last_updated: 2025-10-08
last_updated_by: Claude
---

# Research: Application Entry Points, Configuration, and Open Source/Commercial Separation

**Date**: 2025-10-08T10:18:59+0000
**Researcher**: Claude
**Git Commit**: bc3628957155c373b4b2a71c1a074f9a8f973320
**Branch**: feature/email-delivery-integration
**Repository**: cellophanemail

## Research Question

How does CellophoneMail manage:
1. Application entry points and startup workflows
2. Configuration system and settings management
3. Open source and commercial code separation
4. Different methods to start the application

## Summary

CellophoneMail uses a **dual-service architecture** with independent Litestar web API and SMTP email servers that can run standalone or together. The application employs an **application factory pattern** for initialization, **Pydantic-based settings** loaded from `.env` files, and a sophisticated **monorepo-to-multirepo distribution strategy** that automatically splits code into open source and commercial repositories using file-based rules, package configuration exclusions, and runtime license validation through a provider registry pattern.

## Detailed Findings

### Application Entry Points

CellophoneMail has **17+ entry points** organized by purpose:

#### Main Application Entry Points

**1. Litestar Web API** (`src/cellophanemail/app.py:195`)
- Primary production entry point: `app = create_app()`
- Application factory pattern with dependency injection
- Serves HTTP API, webhooks, authentication, and frontend
- Access: `http://localhost:8000`
- API docs: `http://localhost:8000/schema`

**2. SMTP Email Server** (`src/cellophanemail/plugins/smtp/__main__.py:6-7`)
- Standalone email processing server
- Module entry point: `python -m cellophanemail.plugins.smtp`
- Uses aiosmtpd on port 2525 (development)
- Processes emails with Four Horsemen AI analysis

**3. Root-level Entry** (`main.py`)
- Simple "Hello World" placeholder
- Minimal test entry point

#### Development Scripts (`bin/` directory)

**4. Unified Development Script** (`bin/dev`)
- Starts full CellophoneMail environment
- Manages: PostgreSQL Docker → Migrations → Development user → Litestar server
- Uses Litestar CLI: `litestar --app cellophanemail.app:app run --reload`

**5. Web API Only** (`bin/dev-litestar:55-59`)
- Starts only Litestar web server
- Command: `uv run uvicorn src.cellophanemail.app:app --host 0.0.0.0 --port 8000 --reload`
- Includes pre-flight checks: database connection, port availability

**6. SMTP Server Only** (`bin/dev-smtp:50-56`)
- Starts only email processing server
- Runs: `python -c "from cellophanemail.plugins.smtp.server import main; asyncio.run(main())"`
- Port 2525 for development, configurable via `SMTP_PORT`

**7. Full Stack Launcher** (`bin/dev-all`)
- Starts both API and SMTP servers in parallel
- Process lifecycle management with cleanup on exit

**8. Service Management** (`bin/kill`)
- Stops all CellophoneMail processes
- Kills processes on ports 8000 (Litestar) and 2525 (SMTP)

**9. Development Tunneling** (`bin/ngrok`)
- Exposes local services via ngrok tunnels
- For webhook testing with external services

#### Utility & Demo Scripts (13+ additional scripts)

Located in `scripts/` directory:
- `create_test_user.py` - User creation utility
- `configure_postmark.py` - Postmark configuration
- `test_smtp_delivery.py`, `test_postmark_delivery.py` - Delivery testing
- `test_end_to_end.py` - Complete workflow testing
- `run_tests.py` - Test runner with argparse CLI
- `switch_delivery.py` - Switch email delivery methods
- Demo scripts: `demo_email_delivery.py`, `demo_simple_delivery.py`

### Application Startup Sequence

#### Phase 1: Configuration Loading

**1.1 Settings Initialization** (`src/cellophanemail/config/settings.py:182-184`)

```python
@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

**Process:**
- Pydantic BaseSettings reads from `.env` file (line 15-19)
- Validates `secret_key` (32+ chars, no defaults) (line 102-117)
- Validates `database_url` (no default passwords) (line 119-129)
- Validates `anthropic_api_key` format (line 131-141)
- Parses comma-separated lists for CORS origins and plugins (line 143-149)
- Singleton instance cached via `@lru_cache()`

**1.2 Configuration Validation** (`src/cellophanemail/app.py:33-61`)

Comprehensive validation before startup:
- Production requires `encryption_key` (line 39-40)
- AI provider requires `anthropic_api_key` (line 41-42)
- Postmark delivery requires `postmark_api_token` (line 43-44)
- SMTP delivery requires `email_password` (line 45-46)
- Detects default/weak secrets (line 50-51, 54-55)
- **Failure:** Raises `ValueError` with detailed error messages

#### Phase 2: Database Connection

**2.1 Piccolo ORM Configuration** (`piccolo_conf.py:9-51`)

- Loads settings via `get_settings()` (line 10-12)
- Falls back to `DATABASE_URL` environment variable (line 14-17)
- Parses PostgreSQL URL with regex (line 26-38)
- Creates `PostgresEngine` with connection config (line 30-38)
- SQLite fallback for non-postgres URLs (line 42-51)

**2.2 Database Migrations** (`bin/dev-litestar:34-43`)

```bash
PYTHONPATH=src uv run piccolo migrations forwards cellophanemail
```

Runs before application starts in development scripts.

#### Phase 3: Litestar Application Factory

**3.1 Application Creation** (`src/cellophanemail/app.py:104-191`)

Entry point: `create_app()` function

**Step 1: Plugin Manager** (line 117)
```python
plugin_manager = PluginManager()
```
Empty registry, plugins registered on-demand from `AVAILABLE_PLUGINS` dict.

**Step 2: Security Configuration** (line 120-147)
- **CORS:** Allows configured origins, all methods, credentials (line 120-125)
- **CSRF:** Disabled in testing; excludes `/webhooks/*`, `/health/*`, `/providers/*` (line 129-137)
- **Compression:** Gzip for responses >1024 bytes (line 139-142)
- **Rate Limiting:** 100 requests/minute, excludes health/webhooks (line 144-147)

**Step 3: API Documentation** (line 149-154)
- OpenAPI config at `/docs`
- Title: "CellophoneMail API" v1.0.0

**Step 4: Template Engine** (line 156-160)
- Jinja2 templates from `src/cellophanemail/templates`

**Step 5: Litestar Application** (line 163-189)

**Route Handlers** (line 164-172):
1. `favicon` handler
2. `frontend.router` - Landing pages, pricing
3. `health.router` - Health checks
4. `webhooks.router` - Legacy webhooks
5. `auth.router` - Authentication
6. `PostmarkWebhookHandler` - Postmark provider webhook
7. `GmailWebhookHandler` - Gmail provider webhook

**Middleware Stack** (line 179-181):
- `JWTAuthenticationMiddleware` - Token extraction from Authorization header/cookies

**Dependencies** (line 182-185):
- `plugin_manager`: PluginManager instance
- `settings`: Settings instance

**Lifespan Management** (line 178):
- Background services initialization/cleanup

#### Phase 4: Background Services

**4.1 Lifespan Manager** (`src/cellophanemail/app.py:63-96`)

**Startup Phase** (line 71-86):

**Step 1: Memory Manager Singleton** (line 75)
```python
memory_manager = get_memory_manager()
```
- Creates singleton `MemoryManager(capacity=100)` (`memory_manager_singleton.py:22`)
- Shared across privacy orchestrator and cleanup service
- **Purpose:** In-memory storage for ephemeral emails during analysis

**Step 2: Background Cleanup Service** (line 78-81)
```python
_cleanup_service = BackgroundCleanupService(
    memory_manager=memory_manager,
    grace_period_minutes=1
)
```
- Initializes from `background_cleanup.py:20-33`
- 1-minute grace period before cleanup

**Step 3: Start Scheduled Cleanup** (line 84)
```python
await _cleanup_service.start_scheduled_cleanup(interval_seconds=60)
```
- Creates asyncio task running cleanup loop (`background_cleanup.py:95-116`)
- Runs every 60 seconds
- Removes expired emails (max 100 per cycle)

**Shutdown Phase** (line 90-95):
- Stops cleanup task
- Cancels asyncio task and waits for cleanup

#### Phase 5: Server Launch

**5.1 Web Application** (multiple methods)

**Direct Python:**
```python
# src/cellophanemail/app.py:199-208
uvicorn.run(
    "cellophanemail.app:app",
    host=settings.host,
    port=settings.port,
    reload=settings.debug,
    workers=1 if settings.debug else 4,
)
```

**Development Script:**
```bash
# bin/dev-litestar:55-59
uv run uvicorn src.cellophanemail.app:app \
    --host 0.0.0.0 \
    --port ${LITESTAR_PORT} \
    --reload \
    --log-level info
```

**Litestar CLI:**
```bash
# bin/dev:83
PYTHONPATH=src uv run litestar --app cellophanemail.app:app run --host 0.0.0.0 --port 8000 --reload
```

**Process:**
1. Uvicorn imports `app` (triggers `create_app()`)
2. Creates ASGI server
3. Binds to host:port (default: 127.0.0.1:8000)
4. Spawns workers (4 production, 1 debug)
5. Calls lifespan startup handler
6. Begins accepting HTTP requests

#### Phase 6: SMTP Server (Standalone)

**6.1 Entry Point** (`src/cellophanemail/plugins/smtp/__main__.py:6-7`)

```python
if __name__ == "__main__":
    asyncio.run(main())
```

**Server Initialization** (`server.py:117-127`):

1. **Logging Setup** (line 120-123)
2. **Server Creation** (line 126): `server = SMTPServerRunner()`
   - Reads `SMTP_HOST` (default: localhost) and `SMTP_PORT` (default: 2525)
3. **Launch** (line 127): `await server.run_forever()`

**Handler Setup** (`server.py:81-95`):
```python
handler = SMTPHandler()
self.controller = Controller(
    handler,
    hostname=self.host,
    port=self.port
)
self.controller.start()
```

**Handler Components** (`server.py:20-23`):
- `EmailProtectionProcessor()` - Four Horsemen analysis
- `ShieldAddressManager()` - Shield address lookup

**Run Loop** (line 108-110):
```python
while True:
    await asyncio.sleep(1)
```
Keeps event loop alive, handles KeyboardInterrupt for graceful shutdown.

### Configuration System

#### Configuration Files

**Core Settings:**
- `src/cellophanemail/config/settings.py` - Main settings class (Pydantic BaseSettings)
- `src/cellophanemail/config/privacy.py` - Privacy configuration
- `src/cellophanemail/config/pricing.py` - Billing configuration

**Feature-Specific:**
- `src/cellophanemail/features/email_protection/analysis_config.py` - Email analysis settings
- `src/cellophanemail/features/email_protection/production_config.py` - Multiple config classes:
  - `SecurityConfig` (line 36)
  - `APIConfig` (line 55)
  - `LoggingConfig` (line 73)
  - `ProductionConfig` (line 126)
  - `ConfigurationValidator` (line 490)

**Environment Files:**
- `.env` - Active configuration (not committed)
- `.env.example` - Configuration template with all options
- `.env.test` - Testing environment configuration

**Database:**
- `piccolo_conf.py` - Piccolo ORM configuration

**Package:**
- `pyproject.toml` - Project dependencies and metadata
- `packages/cellophanemail/pyproject.toml` - OSS package config
- `packages/cellophanemail-pro/pyproject.toml` - Commercial package config

#### Key Settings Categories

**Security** (`settings.py:26-32`):
- `SECRET_KEY`: JWT signing (min 32 chars, validated)
- `ENCRYPTION_KEY`: Sensitive data encryption
- Validation prevents default/weak values

**Database** (`settings.py:35-38`):
- `DATABASE_URL`: PostgreSQL connection string
- `DATABASE_ECHO`: SQL query logging
- Validation prevents default passwords

**Redis** (`settings.py:41-44`):
- `REDIS_URL`: Caching and rate limiting
- Default: `redis://localhost:6379/0`

**CORS** (`settings.py:47-50`):
- `CORS_ALLOWED_ORIGINS`: Comma-separated list
- Parsed into `List[str]` by field validator (line 143-149)
- Default: `["http://localhost:3000", "https://cellophanemail.com"]`

**AI Services** (`settings.py:53-60`):
- `ANTHROPIC_API_KEY`: Claude API key (validated format)
- `UPSTAGE_API_KEY`: Upstage API key (optional)
- `AI_PROVIDER`: "anthropic" or "upstage"
- `AI_MODEL`: Default "claude-3-5-sonnet-20241022"
- `AI_MAX_TOKENS`: Max tokens per request

**Email Delivery** (`settings.py:63-85`):
- `EMAIL_DELIVERY_METHOD`: "smtp" or "postmark"
- **SMTP Settings:**
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USE_TLS`
  - `EMAIL_USERNAME`, `EMAIL_PASSWORD`
  - `SMTP_DOMAIN`: Service domain
  - `OUTBOUND_SMTP_HOST`, `OUTBOUND_SMTP_PORT`, `OUTBOUND_SMTP_USE_TLS`
- **Postmark Settings:**
  - `POSTMARK_API_TOKEN`, `POSTMARK_SERVER_ID`
  - `POSTMARK_ACCOUNT_API_TOKEN`
  - `POSTMARK_FROM_EMAIL`, `POSTMARK_FROM_ADDRESS`
  - `POSTMARK_DRY_RUN`: Testing mode

**Plugins** (`settings.py:88-91`):
- `ENABLED_PLUGINS`: Comma-separated list
- Default: `["smtp", "postmark"]`

**SaaS** (`settings.py:94-95`):
- `STRIPE_API_KEY`: Stripe integration
- `STRIPE_WEBHOOK_SECRET`: Webhook validation

**Privacy** (`settings.py:98-99`):
- `PRIVACY_SAFE_LOGGING`: Enable privacy-safe logging
- `LLM_ANALYZER_MODE`: LLM analyzer mode

#### Configuration Properties

**Production Check** (`settings.py:152-154`):
```python
@property
def is_production(self) -> bool:
    return not self.debug and not self.testing
```

**Piccolo Config** (`settings.py:157-162`):
```python
@property
def piccolo_config(self):
    return {
        "database_url": self.database_url,
        "app_name": "cellophanemail",
    }
```

**Email Delivery Config** (`settings.py:165-178`):
```python
@property
def email_delivery_config(self):
    return {
        'EMAIL_DELIVERY_METHOD': self.email_delivery_method,
        'SMTP_DOMAIN': self.smtp_domain,
        'EMAIL_USERNAME': self.email_username,
        'EMAIL_PASSWORD': self.email_password,
        'OUTBOUND_SMTP_HOST': self.outbound_smtp_host,
        'OUTBOUND_SMTP_PORT': self.outbound_smtp_port,
        'OUTBOUND_SMTP_USE_TLS': self.outbound_smtp_use_tls,
        'POSTMARK_API_TOKEN': self.postmark_api_token,
        'POSTMARK_FROM_EMAIL': self.postmark_from_email or f'noreply@{self.smtp_domain}',
        'SERVICE_CONSTANTS': {}
    }
```

#### Configuration Loading Priority

From `settings.py:15-19`:

1. `.env` file in project root
2. System environment variables (override .env)
3. Pydantic field defaults (fallback)

Case-insensitive environment variable names.

### Open Source and Commercial Separation

CellophoneMail uses a **monorepo-to-multirepo distribution strategy** that automatically splits code into public open source and private commercial repositories.

#### Separation Mechanisms

**1. Automated Repository Splitting** (`tools/sync-repos.py:17-68`)

**Open Source Files** (line 23-57):
```python
self.oss_files = [
    "src/cellophanemail/core/",
    "src/cellophanemail/providers/smtp/",
    "src/cellophanemail/providers/gmail/",
    "src/cellophanemail/providers/contracts.py",
    "src/cellophanemail/providers/registry.py",
    "src/cellophanemail/features/email_protection/",
    "src/cellophanemail/features/shield_addresses/",
    "src/cellophanemail/features/user_accounts/",
    "src/cellophanemail/licensing/",
    # ... more OSS files
]
```

**Commercial Files** (line 60-68):
```python
self.commercial_files = [
    "src/cellophanemail/providers/postmark/",
    "src/cellophanemail/features/ai_advanced/",
    "src/cellophanemail_pro/",
    "tests/commercial/",
    "packages/cellophanemail-pro/",
    "scripts/test_webhook_robustness.py",
    "LICENSE.commercial",
]
```

**Exclusion Pattern Enforcement** (`tools/sync-repos.py:302-306`):
```python
self.copy_files(
    self.oss_files,
    dest_dir,
    exclude_patterns=["postmark", "commercial", "ai_advanced"]
)
```

**2. GitHub Actions Automation** (`.github/workflows/sync-repos.yml`)

**Trigger Configuration** (line 3-11):
- Push to `main` branch
- Ignores docs and tool changes
- Manual workflow dispatch with target selection

**Workflow Process** (line 26-94):
1. Clone internal repository (line 31-35)
2. Clone distribution repositories (line 42-50)
3. Configure git credentials (line 52-64)
4. Execute sync script (line 66-75)
5. Trigger package builds (line 77-94)

**Security Restriction** (line 28):
```yaml
if: github.repository == 'cellophanemail/cellophanemail-internal'
```

**3. Package Configuration Separation**

**Open Source Exclusions** (`packages/cellophanemail/pyproject.toml:76-79`):
```toml
[tool.setuptools.packages.find]
where = ["../../src"]
include = ["cellophanemail*"]
exclude = [
    "cellophanemail.providers.postmark*",
    "cellophanemail.features.ai_advanced*",
]
```

**Open Source Entry Points** (line 64-66):
```toml
[project.entry-points."cellophanemail.providers"]
smtp = "cellophanemail.providers.smtp:SMTPProvider"
gmail = "cellophanemail.providers.gmail:GmailProvider"
```

**Commercial Package** (`packages/cellophanemail-pro/pyproject.toml:27-35`):
```toml
dependencies = [
    "cellophanemail>=0.1.0",  # Depends on OSS base
    "anthropic>=0.8.1",
    "openai>=1.3.0",
    "postmark>=1.0.0",
    "sendgrid>=6.10.0",
    "boto3>=1.34.0",
    "azure-communication-email>=1.0.0",
]
```

**Commercial Entry Points** (line 57-65):
```toml
[project.entry-points."cellophanemail.providers"]
postmark = "cellophanemail_pro.providers.postmark:PostmarkProvider"
sendgrid = "cellophanemail_pro.providers.sendgrid:SendGridProvider"
aws_ses = "cellophanemail_pro.providers.aws_ses:SESProvider"

[project.entry-points."cellophanemail.analyzers"]
ai_advanced = "cellophanemail_pro.features.ai_advanced:AdvancedAnalyzer"
```

**4. Provider Registry Pattern** (`src/cellophanemail/providers/registry.py`)

**License-Based Access Control** (line 20-49):

```python
_providers: Dict[str, Dict[str, Any]] = {
    "gmail": {
        "module": "cellophanemail.providers.gmail.provider",
        "class": "GmailProvider",
        "license": LicenseType.OPEN_SOURCE,  # Always available
    },
    "smtp": {
        "module": "cellophanemail.providers.smtp.provider",
        "class": "SMTPProvider",
        "license": LicenseType.OPEN_SOURCE,  # Always available
    },
    "postmark": {
        "module": "cellophanemail.providers.postmark.provider",
        "class": "PostmarkProvider",
        "license": LicenseType.COMMERCIAL,  # Requires license
    }
}
```

**License Validation** (line 62-75):
```python
def _determine_license_type(self) -> LicenseType:
    """Determine current license type based on license key."""
    if not self.license_key:
        return LicenseType.OPEN_SOURCE

    if self.license_key.startswith("ENT-"):
        return LicenseType.ENTERPRISE
    elif self.license_key.startswith("COM-"):
        return LicenseType.COMMERCIAL
    else:
        logger.warning(f"Invalid license key format")
        return LicenseType.OPEN_SOURCE
```

**Runtime Access Control** (line 95-122):
```python
def get_provider(self, name: str, config: Optional[ProviderConfig] = None):
    # Check license
    if not self._is_provider_licensed(provider_info["license"]):
        raise ValueError(
            f"Provider '{name}' requires {provider_info['license'].value} license. "
            f"Current license: {self.license_type.value}. "
            f"Visit https://cellophanemail.com/pricing to upgrade."
        )
```

**License Hierarchy** (line 159-170):
```python
def _is_provider_licensed(self, required_license: LicenseType) -> bool:
    if required_license == LicenseType.OPEN_SOURCE:
        return True  # Always available

    if self.license_type == LicenseType.ENTERPRISE:
        return True  # Enterprise can access everything

    if self.license_type == LicenseType.COMMERCIAL:
        return required_license in [LicenseType.COMMERCIAL, LicenseType.OPEN_SOURCE]

    return False  # Open source can't access commercial/enterprise
```

**Dynamic Import** (line 128-154):
```python
try:
    module = import_module(provider_info["module"])
    provider_class = getattr(module, provider_info["class"])
    provider = provider_class()
    # ...
except ImportError as e:
    logger.error(f"Failed to import provider {name}: {e}")
    raise ValueError(f"Provider {name} not installed or import failed: {e}")
```

#### User Journey Comparison

**Open Source User:**
1. Install: `pip install cellophanemail`
2. Package contains: SMTP, Gmail providers only
3. Registry: `ProviderRegistry(license_key=None)` → `LicenseType.OPEN_SOURCE`
4. `get_provider("smtp")` → ✅ Available
5. `get_provider("postmark")` → ❌ Raises `ValueError` with upgrade message
6. Import fails: `ImportError` (Postmark not in package)

**Commercial User:**
1. Install: `pip install cellophanemail cellophanemail-pro`
2. Package contains: All providers including Postmark
3. Set: `export CELLOPHANEMAIL_LICENSE_KEY="COM-xxx-yyy"`
4. Registry: `ProviderRegistry(license_key="COM-xxx-yyy")` → `LicenseType.COMMERCIAL`
5. `get_provider("postmark")` → ✅ Available
6. Import succeeds: `import_module("cellophanemail.providers.postmark.provider")`

#### Security Guarantees

**File-Level:**
1. Explicit include lists per distribution
2. Exclusion patterns prevent commercial keywords
3. Old files deleted before sync

**Package-Level:**
1. setuptools exclusions even if files copied
2. Entry point isolation (OSS providers only)
3. Dependency separation (commercial depends on OSS)

**Runtime:**
1. License enforcement before loading provider
2. Dynamic imports fail gracefully
3. Helpful error messages with upgrade URLs

### How to Start the Application

#### Quick Start (Recommended)

```bash
# Full development environment (API + SMTP)
./bin/dev-all
```

Starts:
- Web API on http://localhost:8000
- SMTP Server on localhost:2525
- PostgreSQL via Docker
- Hot reloading enabled

#### Individual Services

```bash
# Web API server only
./bin/dev-litestar

# SMTP email server only
./bin/dev-smtp

# Stop all services
./bin/kill
```

#### Manual Startup Options

**Option 1: Direct uvicorn (production-like)**
```bash
PYTHONPATH=src uvicorn cellophanemail.app:app --host 0.0.0.0 --port 8000 --reload
```

**Option 2: Python directly**
```bash
PYTHONPATH=src python src/cellophanemail/app.py
```

**Option 3: Litestar CLI**
```bash
PYTHONPATH=src litestar --app cellophanemail.app:app run --reload
```

**Option 4: SMTP Module**
```bash
PYTHONPATH=src python -m cellophanemail.plugins.smtp
```

#### Prerequisites

1. **Python 3.12+**
2. **PostgreSQL** (Docker recommended):
```bash
docker run --name cellophanemail-postgres \
  -e POSTGRES_USER=cellophane_user \
  -e POSTGRES_PASSWORD=secure_password \
  -e POSTGRES_DB=cellophanemail \
  -p 5433:5432 -d postgres:15
```

3. **Environment Variables** (`.env` file):
```bash
# Security (Required)
SECRET_KEY=your-secret-key-minimum-32-characters
ENCRYPTION_KEY=fernet-generated-encryption-key

# Database (Required)
DATABASE_URL=postgresql://user:password@localhost:5433/cellophanemail
REDIS_URL=redis://localhost:6379/0

# AI Services (Required)
ANTHROPIC_API_KEY=sk-ant-api03-your-anthropic-key
AI_PROVIDER=anthropic
AI_MODEL=claude-3-5-sonnet-20241022

# Email Delivery
EMAIL_DELIVERY_METHOD=smtp  # or 'postmark'
EMAIL_USERNAME=your-email@example.com
EMAIL_PASSWORD=your-app-password
SMTP_DOMAIN=cellophanemail.com
```

4. **Generate Secure Keys**:
```bash
# SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

5. **Database Migrations**:
```bash
PYTHONPATH=src uv run piccolo migrations forwards cellophanemail
```

#### Health Checks

```bash
# Application health
curl http://localhost:8000/health/

# Database readiness
curl http://localhost:8000/health/ready

# Memory status
curl http://localhost:8000/health/memory

# API documentation
curl http://localhost:8000/schema
```

#### Production Deployment

**Using Uvicorn:**
```bash
uvicorn cellophanemail.app:app --host 0.0.0.0 --port 8000 --workers 4
```

**Systemd Service:**
```ini
[Unit]
Description=CellophoneMail Application
After=network.target

[Service]
Type=exec
ExecStart=/opt/cellophanemail/.venv/bin/uvicorn cellophanemail.app:app --host 0.0.0.0 --port 8000
WorkingDirectory=/opt/cellophanemail
User=cellophanemail
Restart=always
Environment=PYTHONPATH=/opt/cellophanemail/src
EnvironmentFile=/opt/cellophanemail/.env

[Install]
WantedBy=multi-user.target
```

**Using Docker:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY .env .

ENV PYTHONPATH=/app/src

EXPOSE 8000
CMD ["uvicorn", "cellophanemail.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Code References

### Entry Points
- `src/cellophanemail/app.py:195` - Main Litestar application entry point
- `src/cellophanemail/app.py:104-191` - Application factory (`create_app()`)
- `src/cellophanemail/plugins/smtp/__main__.py:6-7` - SMTP module entry point
- `src/cellophanemail/plugins/smtp/server.py:117-132` - SMTP server implementation
- `bin/dev:1-83` - Unified development script
- `bin/dev-litestar:1-59` - Web API development script
- `bin/dev-smtp:1-56` - SMTP development script
- `main.py` - Root-level placeholder entry point

### Configuration
- `src/cellophanemail/config/settings.py:12-184` - Main settings class
- `src/cellophanemail/config/settings.py:102-117` - SECRET_KEY validation
- `src/cellophanemail/config/settings.py:119-129` - DATABASE_URL validation
- `src/cellophanemail/config/settings.py:131-141` - ANTHROPIC_API_KEY validation
- `src/cellophanemail/config/settings.py:143-149` - Comma-separated list parsing
- `src/cellophanemail/config/settings.py:152-178` - Configuration properties
- `piccolo_conf.py:9-51` - Piccolo ORM configuration
- `.env.example` - Configuration template

### Startup Sequence
- `src/cellophanemail/app.py:33-61` - Configuration validation
- `src/cellophanemail/app.py:63-96` - Lifespan manager (background services)
- `src/cellophanemail/app.py:117` - Plugin manager initialization
- `src/cellophanemail/app.py:120-147` - Security configuration (CORS, CSRF, compression, rate limiting)
- `src/cellophanemail/app.py:163-189` - Litestar application construction
- `src/cellophanemail/features/email_protection/memory_manager_singleton.py:9-24` - Memory manager singleton
- `src/cellophanemail/features/email_protection/background_cleanup.py:20-116` - Background cleanup service

### Open Source/Commercial Separation
- `tools/sync-repos.py:17-68` - File-based splitting (OSS vs commercial files)
- `tools/sync-repos.py:302-306` - Exclusion pattern enforcement
- `.github/workflows/sync-repos.yml:3-94` - GitHub Actions automation
- `packages/cellophanemail/pyproject.toml:64-79` - OSS package config and entry points
- `packages/cellophanemail-pro/pyproject.toml:27-65` - Commercial package config and entry points
- `src/cellophanemail/providers/registry.py:20-49` - Provider metadata with license types
- `src/cellophanemail/providers/registry.py:62-75` - License key validation
- `src/cellophanemail/providers/registry.py:95-122` - Runtime access control
- `src/cellophanemail/providers/registry.py:159-170` - License hierarchy enforcement
- `src/cellophanemail/providers/postmark/provider.py:21-164` - Commercial provider implementation

## Architecture Insights

### Key Patterns

**1. Application Factory Pattern**
- `create_app()` function constructs configured Litestar instance
- Enables testing with different configurations
- Module-level `app = create_app()` for production deployment

**2. Singleton Pattern**
- Settings cached via `@lru_cache()` for performance
- Memory manager singleton ensures single shared state
- Prevents multiple instances of critical services

**3. Dependency Injection**
- Plugin manager and settings injected into route handlers
- Accessed via Litestar's DI container
- Facilitates testing and modularity

**4. Plugin Architecture**
- Registry-based plugin system
- Lifecycle methods: `initialize()`, `start()`, `stop()`
- Currently SMTP plugin implemented
- Designed for future Postmark, Gmail API plugins

**5. Provider Contract Pattern**
- All providers implement same `EmailProvider` protocol
- OSS and commercial providers interchangeable
- Core application agnostic to licensing
- New commercial providers addable without core changes

**6. Registry Pattern**
- Centralizes provider discovery and access control
- Single point of license validation
- Dynamic provider loading
- Metadata-driven configuration

**7. Monorepo Development**
- All features developed in single codebase
- Integration tests across OSS and commercial
- Consistency between distributions
- Automated splitting prevents human error

**8. Dual Package Distribution**
- `cellophanemail`: Standalone OSS package (MIT)
- `cellophanemail-pro`: Commercial add-on extending base
- Users choose licensing at installation time

**9. Lifespan Context Manager**
- `@asynccontextmanager` pattern
- Startup: Initialize background services
- Yield: Application runs
- Shutdown: Cleanup services gracefully

**10. Middleware Chain**
- JWT authentication middleware on all requests
- Token extraction from header or cookies
- Sets `connection.user` for authenticated requests

### Dual-Service Architecture

**Web API Server (Litestar):**
- Port 8000 (configurable)
- Handles webhooks, authentication, frontend
- Background services (memory cleanup)
- Hot reloading in development

**SMTP Server (aiosmtpd):**
- Port 2525 (development), 25 (production)
- Direct email ingestion
- Four Horsemen AI analysis
- Shield address management

**Shared Components:**
- Database connection (PostgreSQL via Piccolo)
- Configuration settings (loaded identically)
- Email protection services
- Shield address management
- Memory manager (singleton)

**Independence:**
- Can run standalone or together
- `bin/dev-litestar` - API only
- `bin/dev-smtp` - SMTP only
- `bin/dev-all` - Both services

### Privacy-First Design

**Zero-Persistence Architecture:**
- Email content stored in memory only (5-minute TTL)
- `EphemeralEmail` temporary containers
- `MemoryManager` handles 100 concurrent emails
- `BackgroundCleanupService` scheduled cleanup (60s intervals)
- Metadata-only database logging (no content)
- LLM processing in-infrastructure

**Flow:**
```
Email → Webhook → Memory (5 min) → LLM → Delivery → Auto-Cleanup
         ↓                                              ↓
    [202 Accepted]                            [Metadata Only]
```

### Configuration Architecture

**Layered Configuration:**
1. **Pydantic BaseSettings** - Type-safe, validated
2. **Environment Variables** - `.env` file + system env
3. **Field Validators** - Custom validation logic
4. **Computed Properties** - Derived configurations

**Validation Strategy:**
- Fail-fast on startup with detailed errors
- Prevent weak secrets and default passwords
- Format validation (API keys, URLs)
- Character variety checks for entropy

**Configuration Categories:**
- Security (SECRET_KEY, ENCRYPTION_KEY)
- Database (DATABASE_URL, REDIS_URL)
- AI Services (ANTHROPIC_API_KEY, AI_MODEL)
- Email Delivery (SMTP, Postmark settings)
- CORS and plugins
- Privacy and logging

### Startup Dependencies

**Critical Path (Web Application):**
1. `.env` file with required variables
2. PostgreSQL accessible
3. Database schema migrated
4. Valid Anthropic API key
5. Secret key configured (32+ chars)

**Critical Path (SMTP Server):**
1. `.env` file with database URL
2. PostgreSQL accessible
3. Port 2525 available
4. Valid Anthropic API key

**Shared:**
- Database connection
- Configuration settings
- Email protection services
- Shield address management

## Historical Context (from thoughts/)

### Related Research Documents

**Recent Entry Points and Configuration Research:**
- `thoughts/shared/research/2025-09-24-entry-points-configuration-workflow-analysis.md` - Entry Points, Configuration, and Workflow Architecture Analysis
- `thoughts/shared/research/2025-09-21-application-entry-points-startup-guide.md` - Application Entry Points and Startup Guide
- `thoughts/shared/research/2025-09-19-cors-pydantic-settings-parsing-issue.md` - CORS Configuration Parsing Issue

**Architecture and Security:**
- `thoughts/shared/research/2025-09-15-architecture-analysis.md` - CellophoneMail Architecture Analysis
- `thoughts/shared/research/2025-09-15-code-quality-security-analysis.md` - Code Quality and Security Analysis
- `thoughts/shared/plans/2025-09-15-critical-security-remediation.md` - Security Remediation Plan

These documents provide historical context on architectural decisions, configuration challenges (particularly CORS parsing with Pydantic), and security improvements made to the codebase.

## Open Questions

1. **Entry Point Consolidation:** Should `main.py` be expanded or removed? Currently just a placeholder.

2. **Plugin System:** Plugin architecture is defined but only SMTP plugin implemented. What's the roadmap for:
   - Gmail API plugin
   - Postmark plugin as actual plugin vs direct integration
   - Plugin discovery mechanism
   - Plugin hot-reloading

3. **Configuration Overrides:** Should there be a programmatic config override mechanism for testing beyond `.env.test`?

4. **Commercial Provider Distribution:** How will future commercial providers (SendGrid, AWS SES, Azure) be packaged? Separate packages or bundled in `cellophanemail-pro`?

5. **License Key Infrastructure:** Is there a license key validation service/API, or is the current prefix-based validation (`ENT-`, `COM-`) sufficient?

6. **Production Deployment:** Best practices for:
   - Running both services in production (separate containers vs single process)
   - Handling service interdependencies
   - Monitoring and health checks for both services
   - Log aggregation across dual services

7. **Database Migration Strategy:** How are migrations handled in production with dual services? Does SMTP server need database access or only API server?

8. **Background Services:** Current cleanup service runs on API server. Should it be:
   - Separate service?
   - Run on SMTP server instead?
   - Shared responsibility?

9. **SMTP Port Configuration:** Development uses 2525, production typically uses 25. Is there a deployment guide for port configuration and firewall rules?

10. **Sync Testing:** How are the repo sync rules tested? Is there a staging environment for testing distribution before production sync?
