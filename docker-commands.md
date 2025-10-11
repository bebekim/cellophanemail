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
