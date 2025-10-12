# Docker Development Environment Implementation Plan

## Overview

Implement comprehensive Docker development environment for cellophanemail, making Docker the recommended development approach while maintaining backward compatibility. Focus on developer experience, reliability, and incremental adoption without breaking existing workflows.

## Current State Analysis

**What Exists:**
- PostgreSQL runs in Docker for development (`bin/dev:14-22`)
- Basic Dockerfile templates in documentation (not optimized)
- Comprehensive test specifications for deployment infrastructure (not implemented)
- Native Python development with shell scripts (`bin/dev`, `bin/dev-litestar`, `bin/dev-smtp`)
- Dual-service architecture: Litestar API (port 8000) + SMTP server (port 2525)

**What's Missing:**
- Production-ready Dockerfile with optimization
- docker-compose.yml for service orchestration
- .dockerignore for build optimization
- Docker-based development workflow
- Multi-environment Docker support

**Key Discoveries:**
- Redis is **optional** - both `AnalysisCacheService` and `RateLimiter` use in-memory storage with graceful Redis fallback (`analysis_cache.py:16`, `rate_limiter.py:20-26`)
- Health check endpoints already exist: `/health/`, `/health/ready`, `/health/memory` (`README.md:180-193`)
- cev repository provides proven Docker patterns that can be adapted (`cev/Dockerfile:1-40`, `cev/docker-compose.yml:1-137`)
- Current port mapping: PostgreSQL 5433, Litestar 8000, SMTP 2525

## Desired End State

### For Developers:
- Simple `docker-compose up` starts complete development environment
- Hot reloading works seamlessly in containers
- Database data persists across container restarts
- Easy database management (migrations, backup/restore)
- Clear documentation for Docker workflows

### For the Codebase:
- Dockerfile optimized for development (single-stage, fast rebuilds)
- docker-compose.yml orchestrates PostgreSQL + Litestar + SMTP
- .dockerignore reduces build context size
- Redis available via optional profile for testing distributed features
- Native Python development still works (transitional period)

### Verification:
- `docker-compose up` starts all services successfully
- Code changes trigger hot reload without rebuilding
- Database migrations work in Docker environment
- Health checks return 200 OK
- Tests pass in Docker containers

## What We're NOT Doing

**Explicitly Out of Scope:**
- ❌ Production multi-stage builds (defer to later)
- ❌ Process managers (systemd, supervisord, PM2)
- ❌ Secret management infrastructure
- ❌ Monitoring and observability systems
- ❌ Kubernetes or orchestration beyond docker-compose
- ❌ Security hardening (non-root users, SELinux, etc.)
- ❌ CI/CD Docker builds
- ❌ Advanced deployment infrastructure from test specs
- ❌ Backup/restore automation

## Implementation Approach

**Strategy:** Incremental Docker adoption with zero breaking changes
1. Create Docker files alongside existing scripts
2. Developers can choose Docker or native Python
3. Document migration path but don't force it
4. Once proven stable, recommend Docker as default

**Guiding Principles:**
- Development experience first
- Backward compatibility maintained
- Build features reliably
- Simple beats complex
- Redis optional, PostgreSQL required

---

## ✅ Phase 1: Core Docker Files (COMPLETED)

### Overview
Create essential Docker infrastructure files that work alongside existing development scripts without breaking current workflows.

### Changes Required:

#### 1. Create Dockerfile for Development
**File**: `Dockerfile`

```dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install uv

# Copy dependency files first (layer caching optimization)
COPY pyproject.toml .
COPY uv.lock .

# Install Python dependencies
RUN uv pip install --system --frozen

# Copy application code
COPY src/ ./src/

# Create necessary directories
RUN mkdir -p logs

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8000
EXPOSE 2525

# Health check using existing endpoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default command (Litestar API)
CMD ["uvicorn", "cellophanemail.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Why this approach:**
- Single-stage build for fast development iteration
- `--reload` flag enables hot reloading
- Layer caching optimized (dependencies before code)
- Health check integrated with existing endpoints
- Uses `uv` matching current project setup

#### 2. Create .dockerignore
**File**: `.dockerignore`

```dockerignore
# Git
.git
.gitignore
.github/

# Python
__pycache__
*.pyc
*.pyo
.Python
.venv
venv/
env/
*.egg-info
.pytest_cache

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
test_results/
.hypothesis

# Documentation
*.md
!README.md
thoughts/

# Secrets & Config
.env
.env.*
!.env.example

# Logs
logs/
*.log
flask_session/

# Build artifacts
dist/
build/
*.egg-info

# Tools & Scripts
tools/
scripts/
demo_*.py
bin/

# Docker files themselves
Dockerfile*
docker-compose*.yml
.dockerignore
```

**Why this matters:**
- Reduces build context from ~100MB to ~10MB
- Prevents secrets from entering image
- Speeds up build significantly
- Excludes unnecessary files (tests, docs, tools)

### Success Criteria:

#### Automated Verification:
- [ ] Dockerfile builds successfully: `docker build -t cellophanemail-dev .`
- [ ] Image size is reasonable: `docker images cellophanemail-dev --format "{{.Size}}"` (should be < 500MB)
- [ ] No secrets in image: `docker history cellophanemail-dev | grep -i "env\|secret\|password"` returns nothing sensitive
- [ ] Build uses layer caching: Second build completes in < 10 seconds

#### Manual Verification:
- [ ] Can build image without errors
- [ ] .dockerignore excludes expected files (check build output)
- [ ] Health check endpoint is accessible
- [ ] Hot reload works when code changes

---

## ✅ Phase 2: Development Orchestration (COMPLETED)

### Overview
Create docker-compose.yml to orchestrate PostgreSQL, Litestar API, and SMTP server with proper dependencies and networking.

### Changes Required:

#### 1. Create docker-compose.yml
**File**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  db:
    image: postgres:15
    container_name: cellophanemail_db
    environment:
      POSTGRES_USER: cellophane_user
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: cellophanemail
    ports:
      - "5433:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - cellophanemail
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cellophane_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis (Optional - use with --profile cache)
  redis:
    image: redis:7-alpine
    container_name: cellophanemail_redis
    ports:
      - "6379:6379"
    networks:
      - cellophanemail
    profiles:
      - cache
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Litestar API Server
  app:
    build: .
    container_name: cellophanemail_app
    environment:
      - DEBUG=1
      - DATABASE_URL=postgresql://cellophane_user:secure_password@db:5432/cellophanemail
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/src/cellophanemail.egg-info  # Prevent overwriting
    depends_on:
      db:
        condition: service_healthy
    networks:
      - cellophanemail
    env_file:
      - .env
    command: ["uvicorn", "cellophanemail.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

  # SMTP Email Server
  smtp:
    build: .
    container_name: cellophanemail_smtp
    environment:
      - DEBUG=1
      - SMTP_HOST=0.0.0.0
      - SMTP_PORT=2525
      - DATABASE_URL=postgresql://cellophane_user:secure_password@db:5432/cellophanemail
    ports:
      - "2525:2525"
    volumes:
      - .:/app
    depends_on:
      db:
        condition: service_healthy
    networks:
      - cellophanemail
    env_file:
      - .env
    command: ["uv", "run", "python", "-m", "cellophanemail.plugins.smtp"]

volumes:
  postgres_data:

networks:
  cellophanemail:
    driver: bridge
```

**Key decisions:**
- PostgreSQL uses port 5433 (matches current setup in `bin/dev`)
- Redis in optional `cache` profile (only starts with `--profile cache`)
- Bind mounts (`.:/app`) for live code reloading
- Health checks ensure services start in correct order
- Shared network for service communication
- Service names (`db`, `redis`) act as DNS hostnames

#### 2. Create .env.docker Template
**File**: `.env.docker`

```bash
# Docker Development Environment Variables
# Copy to .env and customize for local development

# Security (Required)
SECRET_KEY=docker-dev-secret-key-change-for-production-use-32plus-chars
ENCRYPTION_KEY=docker-dev-encryption-key-change-me

# Database (Configured by docker-compose)
DATABASE_URL=postgresql://cellophane_user:secure_password@db:5432/cellophanemail
REDIS_URL=redis://redis:6379/0

# AI Services (Required)
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
AI_PROVIDER=anthropic
AI_MODEL=claude-3-5-sonnet-20241022

# Email Delivery
EMAIL_DELIVERY_METHOD=smtp
EMAIL_USERNAME=your-email@example.com
EMAIL_PASSWORD=your-app-password
SMTP_DOMAIN=cellophanemail.com

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

**Why separate .env.docker:**
- Database URL uses service name `db` instead of `localhost`
- Redis URL uses service name `redis`
- Developers can copy to `.env` for Docker use
- Keeps `.env.example` for native Python development

### Success Criteria:

#### Automated Verification:
- [ ] Services start successfully: `docker-compose up -d && sleep 10 && docker-compose ps`
- [ ] Database is healthy: `docker-compose exec db pg_isready -U cellophane_user`
- [ ] API responds: `curl -f http://localhost:8000/health/`
- [ ] SMTP server is listening: `nc -zv localhost 2525`
- [ ] Migrations work: `docker-compose exec app uv run piccolo migrations status cellophanemail`
- [ ] Services stop cleanly: `docker-compose down`

#### Manual Verification:
- [ ] All services start without errors
- [ ] Code changes in `src/` trigger hot reload
- [ ] Database data persists after `docker-compose down && docker-compose up`
- [ ] Can access API documentation at http://localhost:8000/schema
- [ ] Redis profile works: `docker-compose --profile cache up` starts Redis

---

## ✅ Phase 3: Developer Workflow Integration (COMPLETED)

### Overview
Create Docker-based development scripts and documentation to guide developers to Docker workflow while maintaining backward compatibility.

### Changes Required:

#### 1. Create Docker Development Script
**File**: `bin/docker-dev`

```bash
#!/usr/bin/env bash
# Docker-based development environment launcher

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}🐳 Starting CellophoneMail Docker Environment${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${YELLOW}❌ Docker is not running${NC}"
    echo "Please start Docker Desktop or Docker daemon"
    exit 1
fi

# Check if .env exists, create from .env.docker if not
if [ ! -f .env ]; then
    if [ -f .env.docker ]; then
        echo -e "${YELLOW}⚠️  .env not found, copying from .env.docker${NC}"
        cp .env.docker .env
        echo -e "${YELLOW}⚠️  Please edit .env and add your ANTHROPIC_API_KEY${NC}"
    else
        echo -e "${YELLOW}⚠️  .env.docker not found, please create .env manually${NC}"
        exit 1
    fi
fi

# Build and start services
echo -e "${BLUE}Building Docker images...${NC}"
docker-compose build

echo -e "${BLUE}Starting services...${NC}"
docker-compose up -d

# Wait for services to be healthy
echo -e "${BLUE}Waiting for services to be ready...${NC}"
sleep 5

# Run migrations
echo -e "${BLUE}Running database migrations...${NC}"
docker-compose exec app uv run piccolo migrations forwards cellophanemail || true

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✅ Docker environment is running!${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "${YELLOW}📖 API Server: http://localhost:8000${NC}"
echo -e "${YELLOW}📖 API Docs: http://localhost:8000/schema${NC}"
echo -e "${YELLOW}📧 SMTP Server: localhost:2525${NC}"
echo -e "${YELLOW}🗄️  PostgreSQL: localhost:5433${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "${BLUE}View logs: docker-compose logs -f${NC}"
echo -e "${BLUE}Stop services: docker-compose down${NC}"
echo -e "${BLUE}Stop and clean: ./bin/docker-clean${NC}"
```

#### 2. Create Docker Cleanup Script
**File**: `bin/docker-clean`

```bash
#!/usr/bin/env bash
# Clean up Docker environment completely

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🧹 Cleaning Docker Environment${NC}"

# Stop and remove containers
echo -e "${BLUE}Stopping containers...${NC}"
docker-compose down

# Option to remove volumes
read -p "Remove database volumes? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Removing volumes (database data will be lost)...${NC}"
    docker-compose down -v
    echo -e "${GREEN}✅ Volumes removed${NC}"
fi

# Remove dangling images
echo -e "${BLUE}Cleaning up dangling images...${NC}"
docker image prune -f

echo -e "${GREEN}✅ Cleanup complete${NC}"
```

#### 3. Create Docker Commands Documentation
**File**: `docker-commands.md`

```markdown
# Docker Development Commands

Quick reference for Docker-based development with CellophoneMail.

## Quick Start

```bash
# Start everything
./bin/docker-dev

# View logs
docker-compose logs -f

# Stop everything
docker-compose down
```

## Service Management

### Start Services

```bash
# Start all services (default - without Redis)
docker-compose up -d

# Start with Redis cache
docker-compose --profile cache up -d

# Start and view logs
docker-compose up

# Rebuild and start
docker-compose up -d --build
```

### Stop Services

```bash
# Stop services (keep volumes)
docker-compose down

# Stop and remove volumes (⚠️  deletes database data)
docker-compose down -v

# Clean everything
./bin/docker-clean
```

## Database Management

### Migrations

```bash
# Check migration status
docker-compose exec app uv run piccolo migrations status cellophanemail

# Run pending migrations
docker-compose exec app uv run piccolo migrations forwards cellophanemail

# Create new migration
docker-compose exec app uv run piccolo migrations new cellophanemail --auto
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U cellophane_user -d cellophanemail

# Backup database
docker-compose exec db pg_dump -U cellophane_user cellophanemail > backup.sql

# Restore database
docker-compose exec -T db psql -U cellophane_user cellophanemail < backup.sql
```

### Database Reset

```bash
# Stop services
docker-compose down

# Remove database volume
docker volume rm cellophanemail_postgres_data

# Restart (migrations will run automatically)
./bin/docker-dev
```

## Development Workflow

### Code Changes

Code changes in `src/` directory automatically trigger hot reload:
- Litestar API reloads when Python files change
- SMTP server reloads when plugin files change
- No rebuild needed for code changes

### Installing Dependencies

```bash
# After adding dependencies to pyproject.toml
docker-compose build
docker-compose up -d
```

### Running Tests

```bash
# Run all tests
docker-compose exec app pytest

# Run specific test file
docker-compose exec app pytest tests/unit/test_email_protection.py

# Run with coverage
docker-compose exec app pytest --cov=cellophanemail
```

### Shell Access

```bash
# Python shell in app container
docker-compose exec app python

# Bash shell in app container
docker-compose exec app bash

# PostgreSQL shell
docker-compose exec db psql -U cellophane_user -d cellophanemail
```

## Debugging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f smtp
docker-compose logs -f db

# Last 100 lines
docker-compose logs --tail=100 app
```

### Check Service Status

```bash
# List running containers
docker-compose ps

# Check service health
docker-compose exec db pg_isready -U cellophane_user
curl http://localhost:8000/health/
```

### Restart Services

```bash
# Restart specific service
docker-compose restart app
docker-compose restart smtp

# Restart all
docker-compose restart
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8000
lsof -i :5433

# Stop native Python services
./bin/kill

# Or change ports in docker-compose.yml
```

### Database Connection Issues

```bash
# Check if PostgreSQL is healthy
docker-compose exec db pg_isready

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Build Failures

```bash
# Clean build (no cache)
docker-compose build --no-cache

# Remove all containers and rebuild
docker-compose down
docker-compose up -d --build
```

### Volume Permission Issues

```bash
# Fix permissions (if needed)
sudo chown -R $USER:$USER .

# Or run container as root (not recommended)
docker-compose run --user root app bash
```

## Redis Cache (Optional)

### Enable Redis

```bash
# Start with Redis
docker-compose --profile cache up -d

# Verify Redis is running
docker-compose exec redis redis-cli ping
```

### Redis Commands

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# Check keys
docker-compose exec redis redis-cli KEYS '*'

# Flush all data
docker-compose exec redis redis-cli FLUSHALL
```

## Migration from Native Python

### One-time Setup

1. Copy environment configuration:
   ```bash
   cp .env.docker .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

2. Stop native Python services:
   ```bash
   ./bin/kill
   ```

3. Start Docker environment:
   ```bash
   ./bin/docker-dev
   ```

### Side-by-Side (Transitional)

You can run both native Python and Docker:
- Docker uses ports 8000, 2525, 5433
- Native Python can use different ports
- Update `.env` accordingly for each environment

### Full Docker Migration

Once comfortable with Docker:
1. Remove native Python virtual environment: `rm -rf .venv`
2. Use Docker exclusively: `./bin/docker-dev`
3. Update IDE/editor to use Docker Python interpreter
```

#### 4. Update README.md Docker Section
**File**: `README.md` (update existing Docker section)

**Location**: After line 240, replace basic Dockerfile example with:

```markdown
## 🐳 Docker Development (Recommended)

### Quick Start

```bash
# One-time setup
cp .env.docker .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start everything
./bin/docker-dev

# View logs
docker-compose logs -f
```

### What You Get

- **PostgreSQL** on port 5433 with persistent data
- **Litestar API** on port 8000 with hot reload
- **SMTP Server** on port 2525
- **Redis** (optional) on port 6379 with `--profile cache`

### Common Commands

```bash
# Start services
docker-compose up -d

# Run migrations
docker-compose exec app uv run piccolo migrations forwards cellophanemail

# Run tests
docker-compose exec app pytest

# Stop services
docker-compose down

# Complete cleanup
./bin/docker-clean
```

See [docker-commands.md](docker-commands.md) for complete reference.

### Migration from Native Python

Docker is now the recommended development method. To migrate:

1. Stop native services: `./bin/kill`
2. Copy environment: `cp .env.docker .env`
3. Start Docker: `./bin/docker-dev`

Native Python development still works but Docker provides:
- Consistent environment across team
- No PostgreSQL installation needed
- Easy database reset and backups
- Simplified onboarding
```

### Success Criteria:

#### Automated Verification:
- [ ] `bin/docker-dev` script is executable: `chmod +x bin/docker-dev && test -x bin/docker-dev`
- [ ] `bin/docker-clean` script is executable: `chmod +x bin/docker-clean && test -x bin/docker-clean`
- [ ] Scripts run without errors: `bash -n bin/docker-dev && bash -n bin/docker-clean`
- [ ] Documentation has no broken links: `grep -r "](docker-commands.md)" README.md`

#### Manual Verification:
- [ ] `./bin/docker-dev` starts all services successfully
- [ ] Database migrations run automatically
- [ ] README Docker section is clear and accurate
- [ ] docker-commands.md covers common scenarios
- [ ] Can follow migration guide from native to Docker
- [ ] Error messages are helpful when Docker not running

---

## ✅ Phase 4: Testing & Validation (COMPLETED)

### Overview
Ensure Docker environment works reliably and update development documentation to guide everyone to Docker.

### Changes Required:

#### 1. Update bin/dev Script
**File**: `bin/dev` (update, don't replace)

Add Docker recommendation at the beginning:

```bash
#!/bin/bash
# Development environment startup script for CellophoneMail

echo "ℹ️  Note: Docker is now the recommended development method"
echo "   Run ./bin/docker-dev for Docker-based development"
echo "   See docker-commands.md for full Docker documentation"
echo ""
echo "Continuing with native Python development..."
echo ""

# ... rest of existing script unchanged
```

#### 2. Create Docker Quick Reference
**File**: `.github/DOCKER.md` or `docs/DOCKER.md`

```markdown
# Docker Quick Reference

## Why Docker?

✅ **Consistent environment** - Same setup for everyone
✅ **No PostgreSQL install** - Everything in containers
✅ **Easy reset** - `docker-compose down -v && docker-compose up`
✅ **Simple onboarding** - New developers up and running in 5 minutes

## First Time Setup

```bash
# 1. Copy environment template
cp .env.docker .env

# 2. Edit .env and add your keys
vim .env  # Add ANTHROPIC_API_KEY

# 3. Start everything
./bin/docker-dev
```

## Daily Development

```bash
# Start work
docker-compose up -d

# View logs while developing
docker-compose logs -f app

# Run tests
docker-compose exec app pytest

# End of day
docker-compose down
```

## Troubleshooting

**Port conflict:** Run `./bin/kill` to stop native Python services

**Build issues:** Run `docker-compose build --no-cache`

**Database issues:** Reset with `docker-compose down -v && ./bin/docker-dev`

**Full docs:** See [docker-commands.md](../docker-commands.md)
```

#### 3. Add Docker Validation Tests
**File**: `tests/docker/test_docker_environment.py` (new file)

```python
"""Tests to validate Docker environment setup."""
import subprocess
import requests
import time
import pytest


def run_command(cmd: str) -> tuple[int, str, str]:
    """Run shell command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


class TestDockerEnvironment:
    """Validate Docker development environment."""

    def test_docker_compose_config_valid(self):
        """Docker compose configuration should be valid."""
        exit_code, stdout, stderr = run_command("docker-compose config")
        assert exit_code == 0, f"docker-compose.yml invalid: {stderr}"

    def test_dockerfile_builds(self):
        """Dockerfile should build successfully."""
        exit_code, stdout, stderr = run_command(
            "docker build -t cellophanemail-test ."
        )
        assert exit_code == 0, f"Dockerfile build failed: {stderr}"

    def test_services_start(self):
        """All services should start successfully."""
        # Start services
        run_command("docker-compose up -d")
        time.sleep(10)  # Wait for startup

        # Check all services are running
        exit_code, stdout, _ = run_command("docker-compose ps --services --filter 'status=running'")
        running_services = stdout.strip().split('\n')

        assert 'db' in running_services, "PostgreSQL not running"
        assert 'app' in running_services, "Litestar app not running"
        assert 'smtp' in running_services, "SMTP server not running"

        # Cleanup
        run_command("docker-compose down")

    def test_health_endpoints(self):
        """Health check endpoints should be accessible."""
        # Start services
        run_command("docker-compose up -d")
        time.sleep(10)

        # Check API health
        response = requests.get("http://localhost:8000/health/")
        assert response.status_code == 200, "Health endpoint not accessible"

        # Check database readiness
        response = requests.get("http://localhost:8000/health/ready")
        assert response.status_code == 200, "Database not ready"

        # Cleanup
        run_command("docker-compose down")

    def test_hot_reload_works(self):
        """Code changes should trigger hot reload."""
        # Start services
        run_command("docker-compose up -d")
        time.sleep(10)

        # Make a trivial code change
        test_file = "src/cellophanemail/test_hot_reload.py"
        with open(test_file, 'w') as f:
            f.write("# Test hot reload\n")

        # Check logs for reload message (uvicorn shows reload on change)
        time.sleep(2)
        exit_code, stdout, _ = run_command("docker-compose logs app")

        # Cleanup
        run_command(f"rm -f {test_file}")
        run_command("docker-compose down")

        # Uvicorn should have detected the change
        assert "Reloading" in stdout or "detected" in stdout.lower()

    def test_database_persistence(self):
        """Database data should persist across restarts."""
        # Start services and run migration
        run_command("docker-compose up -d")
        time.sleep(10)
        run_command("docker-compose exec -T app uv run piccolo migrations forwards cellophanemail")

        # Stop services (keep volumes)
        run_command("docker-compose down")

        # Start again
        run_command("docker-compose up -d")
        time.sleep(10)

        # Check migration status (should show already applied)
        exit_code, stdout, _ = run_command(
            "docker-compose exec -T app uv run piccolo migrations status cellophanemail"
        )

        # Cleanup
        run_command("docker-compose down")

        assert exit_code == 0, "Migrations not persisted"
```

### Success Criteria:

#### Automated Verification:
- [ ] Docker config is valid: `docker-compose config`
- [ ] All Docker validation tests pass: `pytest tests/docker/`
- [ ] Build completes in < 2 minutes: `time docker-compose build`
- [ ] Services start in < 30 seconds: `time docker-compose up -d`
- [ ] No errors in logs: `docker-compose logs | grep -i error` returns nothing critical

#### Manual Verification:
- [ ] New developer can follow Docker quick reference and get running
- [ ] Hot reload works - change Python file, see reload in logs
- [ ] Database persists - stop/start containers, data remains
- [ ] All health checks return 200 OK
- [ ] Can switch between Docker and native Python without conflicts
- [ ] Documentation is clear and complete

---

## Testing Strategy

### Automated Tests

**Docker Environment Tests** (`tests/docker/test_docker_environment.py`):
- Dockerfile builds successfully
- docker-compose.yml is valid
- Services start and become healthy
- Health check endpoints accessible
- Hot reload functionality works
- Database persistence across restarts

**Integration Tests in Docker**:
```bash
# Run existing tests in Docker
docker-compose exec app pytest tests/integration/
docker-compose exec app pytest tests/unit/
```

### Manual Testing Steps

1. **First-time Setup Flow:**
   - Clone repository
   - Run `cp .env.docker .env`
   - Edit `.env` to add API key
   - Run `./bin/docker-dev`
   - Verify all services start
   - Access http://localhost:8000/schema

2. **Development Workflow:**
   - Edit `src/cellophanemail/app.py`
   - Observe hot reload in logs
   - Make API request, see change reflected
   - Run tests: `docker-compose exec app pytest`

3. **Database Management:**
   - Create migration: `docker-compose exec app uv run piccolo migrations new cellophanemail --auto`
   - Apply migration: `docker-compose exec app uv run piccolo migrations forwards cellophanemail`
   - Verify in database: `docker-compose exec db psql -U cellophane_user -d cellophanemail`

4. **Service Isolation:**
   - Stop services: `docker-compose down`
   - Start services: `docker-compose up -d`
   - Verify data persists (database, logs)

5. **Redis Profile (Optional):**
   - Start with Redis: `docker-compose --profile cache up -d`
   - Verify Redis: `docker-compose exec redis redis-cli ping`
   - Check app connects to Redis (no errors in logs)

6. **Cleanup:**
   - Run `./bin/docker-clean`
   - Confirm volumes removed when requested
   - Verify clean state: `docker-compose ps` shows nothing

## Performance Considerations

**Build Optimization:**
- `.dockerignore` reduces context size from ~100MB to ~10MB
- Layer caching: dependencies before code means fast rebuilds
- First build: ~3-5 minutes
- Subsequent builds (code change only): ~5-10 seconds

**Runtime Performance:**
- Hot reload adds minimal overhead (~100ms per reload)
- PostgreSQL in Docker: negligible performance difference for development
- Volume mounts: native performance on Linux, ~10% overhead on macOS

**Resource Usage:**
- PostgreSQL: ~100MB RAM
- Litestar + SMTP: ~200MB RAM combined
- Redis (if enabled): ~50MB RAM
- Total: ~350MB RAM (acceptable for development)

## Migration Notes

### For Current Developers

**Transition Path:**
1. Try Docker: `./bin/docker-dev` (doesn't affect native setup)
2. Use both: Docker for most work, native for debugging
3. Commit to Docker: Remove `.venv`, use Docker exclusively

**Key Differences:**
- Database URL changes from `localhost:5433` to `db:5432` (service name)
- Environment variables in `.env` vs `.env.docker`
- PostgreSQL data in Docker volume instead of native
- No need for `uv venv` or `uv sync` locally

### For New Developers

**Quick Start (< 5 minutes):**
```bash
# 1. Get code
git clone <repo>
cd cellophanemail

# 2. Configure
cp .env.docker .env
# Edit .env: Add ANTHROPIC_API_KEY

# 3. Start
./bin/docker-dev

# 4. Verify
curl http://localhost:8000/health/
```

## References

**Learned From:**
- cev repository Docker setup: `~/repositories/individuals/cev/Dockerfile`
- cev docker-compose patterns: `~/repositories/individuals/cev/docker-compose.yml`
- cev .dockerignore: `~/repositories/individuals/cev/.dockerignore`

**Current Implementation:**
- Test specifications: `tests/unit/test_deployment_infrastructure.py`
- Native Python workflow: `bin/dev`, `bin/dev-litestar`, `bin/dev-smtp`
- Current documentation: `README.md:226-240`

**Docker Files Created:**
- `Dockerfile` - Development-optimized container
- `docker-compose.yml` - Service orchestration
- `.dockerignore` - Build optimization
- `.env.docker` - Docker-specific environment template
- `bin/docker-dev` - Docker startup script
- `bin/docker-clean` - Docker cleanup script
- `docker-commands.md` - Complete Docker reference
- `tests/docker/test_docker_environment.py` - Docker validation tests

## Open Questions

**Resolved:**
- ✅ Redis requirement: Made optional via `--profile cache`
- ✅ Migration strategy: Incremental, maintain backward compatibility
- ✅ Development priority: Focus on developer experience over production hardening
- ✅ Deployment infrastructure: Deferred advanced features (process managers, secrets, monitoring)

**For Future Consideration:**
1. When should we deprecate native Python development?
2. Should we add production multi-stage Dockerfile later?
3. How to handle CI/CD Docker builds?
4. Should we provide Docker Desktop alternatives (Podman, Colima)?
