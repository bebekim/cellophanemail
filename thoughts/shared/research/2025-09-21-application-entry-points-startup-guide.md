---
date: 2025-09-21T20:16:10+1000
researcher: Claude Code
git_commit: bc3628957155c373b4b2a71c1a074f9a8f973320
branch: feature/email-delivery-integration
repository: cellophanemail
topic: "Application entry points and startup guide for CellophoneMail"
tags: [research, codebase, startup, entry-points, development, litestar, uvicorn]
status: complete
last_updated: 2025-09-21
last_updated_by: Claude Code
---

# Research: Application Entry Points and Startup Guide for CellophoneMail

**Date**: 2025-09-21T20:16:10+1000
**Researcher**: Claude Code
**Git Commit**: bc3628957155c373b4b2a71c1a074f9a8f973320
**Branch**: feature/email-delivery-integration
**Repository**: cellophanemail

## Research Question
Show the entry point and how to start up the CellophoneMail application, including development scripts, configuration, and deployment options.

## Summary
CellophoneMail is a Litestar-based privacy-focused email protection SaaS with multiple entry points and startup methods. The application uses an application factory pattern with comprehensive dependency injection, supports both development and production deployment modes, and provides separate entry points for web API and SMTP email processing servers. Development is streamlined through shell scripts in the `bin/` directory, while production deployment supports uvicorn, systemd, supervisord, and PM2 configurations.

## Detailed Findings

### Primary Entry Points

#### 1. Main Application File (`src/cellophanemail/app.py:195-208`)
**Primary Entry Point**: The core Litestar ASGI application
```python
# Entry point for uvicorn
app = create_app()

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "cellophanemail.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else 4,
    )
```

**Key Features**:
- Dynamic worker count based on debug mode (1 for development, 4 for production)
- Configuration-driven host/port binding
- Hot reloading in development mode
- ASGI-compliant application instance

#### 2. Root-Level Entry Point (`main.py`)
**Secondary Entry Point**: Root-level convenience script
- Provides simplified startup interface
- Imports and delegates to main application

#### 3. SMTP Server Entry Point (`src/cellophanemail/plugins/smtp/__main__.py`)
**Specialized Entry Point**: Dedicated SMTP email processing server
- Independent async server for email ingestion
- Can run separately from web API
- Integrates with same configuration system

### Development Startup Scripts

#### Quick Start - Full Development Stack (`bin/dev`)
**Recommended for most development work**
```bash
./bin/dev
```

**What it does**:
- Checks and starts Docker PostgreSQL container on port 5433
- Runs database migrations via Piccolo ORM
- Creates development user if needed
- Starts Litestar application on http://localhost:8000 with hot reloading
- Configures development environment variables

#### Individual Service Scripts

**1. API Server Only (`bin/dev-litestar`)**
```bash
./bin/dev-litestar
```
- Starts only the web API server
- Uses uvicorn with hot reloading
- Port availability validation
- Database connectivity checks

**2. SMTP Server Only (`bin/dev-smtp`)**
```bash
./bin/dev-smtp
```
- Starts only the email processing server on port 2525
- Async entry point via inline Python execution
- Service isolation for testing email flows

**3. Full Stack Orchestration (`bin/dev-all`)**
```bash
./bin/dev-all
```
- Runs both API and SMTP servers concurrently
- Process management with graceful shutdown
- Background job coordination
- Color-coded logging and status

**4. Service Management (`bin/kill`)**
```bash
./bin/kill
```
- Stops all CellophoneMail services
- Process pattern matching
- Port-based cleanup (8000, 2525)
- Graceful failure handling

### Application Factory Pattern

#### Bootstrap Sequence (`src/cellophanemail/app.py:104-189`)

**1. Configuration Initialization (Lines 106-115)**
- Loads settings via cached `get_settings()` from `config/settings.py:182`
- Validates configuration through `validate_configuration()` (lines 33-61)
- Checks production requirements, security settings, database credentials

**2. Plugin System Setup (Line 117)**
- Creates `PluginManager` instance from `plugins/manager.py:16`
- Maintains registry of available email input plugins
- Currently supports SMTP with planned Postmark/Gmail support

**3. Security Middleware Configuration (Lines 120-147)**
- **CORS**: Configurable origins from environment variables
- **CSRF Protection**: Disabled in testing mode
- **Rate Limiting**: 100 requests/minute, excludes health/webhook endpoints
- **JWT Authentication**: Token-based auth via custom middleware

**4. Dependency Injection (Lines 182-185)**
- Provides `plugin_manager` singleton with thread safety
- Provides `settings` singleton across application
- Litestar's DI system manages component lifecycle

**5. Background Services Lifecycle (Lines 63-96)**
- Lifespan manager initializes memory manager singleton
- Starts background cleanup service (60-second intervals)
- Cleanup service manages ephemeral email memory (5-minute TTL)
- Graceful shutdown with service cleanup

### Configuration Management

#### Environment Variables (`.env` file)
```bash
# Application Settings
DEBUG=true
TESTING=false
HOST=0.0.0.0
PORT=8000

# Security (REQUIRED)
SECRET_KEY=your-secret-key-minimum-32-chars
ENCRYPTION_KEY=fernet-generated-key

# Database
DATABASE_URL=postgresql://user:password@localhost:5433/cellophanemail
REDIS_URL=redis://localhost:6379/0

# AI Services
ANTHROPIC_API_KEY=sk-ant-api03-your-key
AI_PROVIDER=anthropic
AI_MODEL=claude-3-5-sonnet-20241022

# Email Delivery
EMAIL_DELIVERY_METHOD=smtp  # or postmark
EMAIL_USERNAME=your-email@example.com
EMAIL_PASSWORD=your-app-password
SMTP_DOMAIN=cellophanemail.com
```

#### Configuration Validation (`src/cellophanemail/config/settings.py:102-149`)
- **Secret Key Validation**: Minimum 32 characters, entropy checks
- **Database URL Validation**: Prevents default passwords
- **API Key Validation**: Format and length verification
- **Production Mode Detection**: Security requirement enforcement

### Production Deployment Options

#### 1. Direct Uvicorn
```bash
# Basic production startup
uvicorn cellophanemail.app:app --host 0.0.0.0 --port 8000

# With workers
uvicorn cellophanemail.app:app --workers 4 --host 0.0.0.0 --port 8000
```

#### 2. Systemd Service
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
RestartSec=3
Environment=PATH=/opt/cellophanemail/.venv/bin
EnvironmentFile=/opt/cellophanemail/.env

[Install]
WantedBy=multi-user.target
```

#### 3. Supervisord Configuration
```ini
[program:cellophanemail]
command=/opt/cellophanemail/.venv/bin/uvicorn cellophanemail.app:app --host 0.0.0.0 --port 8000
directory=/opt/cellophanemail
user=cellophanemail
autostart=true
autorestart=true
stdout_logfile=/var/log/cellophanemail/stdout.log
stderr_logfile=/var/log/cellophanemail/stderr.log
environment=PATH="/opt/cellophanemail/.venv/bin"
```

#### 4. PM2 Process Manager
```json
{
  "name": "cellophanemail",
  "script": "/opt/cellophanemail/.venv/bin/uvicorn",
  "args": ["cellophanemail.app:app", "--host", "0.0.0.0", "--port", "8000"],
  "cwd": "/opt/cellophanemail",
  "env_file": "/opt/cellophanemail/.env",
  "instances": 1,
  "exec_mode": "fork",
  "autorestart": true
}
```

### Database Management

#### Migration Commands
```bash
# Apply migrations (development)
PYTHONPATH=src uv run piccolo migrations forwards cellophanemail

# Create new migration
PYTHONPATH=src uv run piccolo migrations new cellophanemail --auto

# Production migration
piccolo migrations forwards cellophanemail
```

#### Database Setup
- **Development**: Docker PostgreSQL on port 5433
- **Production**: External PostgreSQL with connection pooling
- **ORM**: Piccolo with automatic migration management

### Testing and Validation

#### Test Runners (`scripts/run_tests.py`)
```bash
# All tests
python scripts/run_tests.py all

# Code functionality only
python scripts/run_tests.py code

# AI analysis quality
python scripts/run_tests.py analysis
```

#### Health Checks
- **API Health**: `GET /health/` - Basic application health
- **Readiness**: `GET /health/ready` - Database connectivity
- **Memory Status**: `GET /health/memory` - Email processing capacity

## Code References
- `src/cellophanemail/app.py:195-208` - Main application entry point
- `src/cellophanemail/app.py:104-189` - Application factory function
- `bin/dev` - Primary development startup script
- `bin/dev-all` - Full stack development orchestration
- `src/cellophanemail/config/settings.py:12-184` - Configuration management
- `src/cellophanemail/plugins/manager.py:16-57` - Plugin system setup
- `main.py` - Root-level convenience entry point
- `src/cellophanemail/plugins/smtp/__main__.py` - SMTP server entry point

## Architecture Insights

### Dual-Service Architecture
- **Web API Server**: Litestar on port 8000 (webhooks, authentication, frontend)
- **SMTP Server**: aiosmtpd on port 2525 (direct email ingestion)
- **Shared Memory**: Singleton memory manager for email processing coordination

### Security-First Design
- **Configuration Validation**: Startup fails if security requirements not met
- **Secret Management**: Environment-driven with validation
- **Rate Limiting**: Request throttling with webhook exceptions
- **CSRF Protection**: State-changing operation protection

### Privacy Architecture
- **Zero Persistence**: Email content stored in memory only (5-minute TTL)
- **Background Cleanup**: Scheduled service ensures memory limits
- **Metadata Logging**: No content logging, privacy-safe operation tracking

### Development Workflow
- **Hot Reloading**: Automatic code reload in development
- **Service Isolation**: Separate scripts for API vs email processing
- **Database Management**: Automated migration handling
- **Process Orchestration**: Graceful startup/shutdown coordination

## Historical Context (from thoughts/)
- [2025-09-15 Architecture Analysis](thoughts/shared/research/2025-09-15-architecture-analysis.md) - Complete architectural documentation
- [2025-09-19 CORS Configuration Fix](thoughts/shared/research/2025-09-19-cors-pydantic-settings-parsing-issue.md) - Configuration parsing issues
- [2025-09-15 Security Remediation](thoughts/shared/plans/2025-09-15-critical-security-remediation.md) - Security startup validation

## Quick Reference Commands

### Development
```bash
# Start everything (recommended)
./bin/dev-all

# API only
./bin/dev-litestar

# SMTP only
./bin/dev-smtp

# Stop all services
./bin/kill
```

### Production
```bash
# Direct uvicorn
uvicorn cellophanemail.app:app --host 0.0.0.0 --port 8000 --workers 4

# With systemd
sudo systemctl start cellophanemail
sudo systemctl enable cellophanemail

# With supervisord
sudo supervisorctl start cellophanemail

# With PM2
pm2 start cellophanemail.json
```

### Database
```bash
# Run migrations
PYTHONPATH=src uv run piccolo migrations forwards cellophanemail

# Create migration
PYTHONPATH=src uv run piccolo migrations new cellophanemail --auto
```

### Testing
```bash
# Full test suite
python scripts/run_tests.py all

# Quick validation
python scripts/run_tests.py code
```

## Open Questions
1. **Container Deployment**: Docker/Kubernetes deployment patterns for production scaling?
2. **Load Balancing**: Configuration for multiple worker instances and session management?
3. **Monitoring Integration**: Integration patterns for APM tools and health monitoring?
4. **Database Scaling**: Connection pooling and read replica configuration for high traffic?
5. **SSL/TLS Configuration**: Reverse proxy setup and certificate management patterns?

The CellophoneMail application provides a comprehensive, security-focused startup system suitable for both development and production deployment with extensive configuration validation and monitoring capabilities.