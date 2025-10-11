# 🐳 Docker Quick Start

**TL;DR: Get started with Docker in 30 seconds**

## One-time Setup

```bash
# Copy environment configuration
cp .env.docker .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start everything
./bin/docker-dev
```

## What You Get

- **PostgreSQL** on port 5433 with persistent data
- **Litestar API** on port 8000 with hot reload
- **SMTP Server** on port 2525
- **Redis** (optional) on port 6379 with `--profile cache`

## Common Commands

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

## Migration from Native Python

Docker is now the recommended development method. To migrate:

1. Stop native services: `./bin/kill`
2. Copy environment: `cp .env.docker .env`
3. Start Docker: `./bin/docker-dev`

Native Python development still works but Docker provides:
- Consistent environment across team
- No PostgreSQL installation needed
- Easy database reset and backups
- Simplified onboarding
