# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Files

**NEVER automatically overwrite or modify `.env*` files** (`.env`, `.env.docker`, `.env.local`, etc.). These contain user-configured secrets. If environment changes are needed, inform the user what to change and let them do it manually.

## Build & Run

```bash
# Install dependencies
uv sync --frozen

# Run dev server (hot reload)
uv run uvicorn cellophanemail.app:create_app --factory --host 0.0.0.0 --port 8000 --reload

# Docker (full stack)
docker-compose up db migrate app

# Docker with Redis + async jobs
docker-compose --profile cache up
```

## Testing

```bash
# All tests
uv run pytest tests/ -x

# Single test file
uv run pytest tests/test_auth_routes.py -v

# Single test method
uv run pytest tests/test_auth_routes.py::TestAuthRoutes::test_login -v

# Unit tests only
uv run pytest tests/unit/ -v

# With coverage
uv run pytest tests/ --cov=src/cellophanemail --cov-report=html
```

Tests auto-set `STAGING=true` (via `tests/conftest.py`), which makes the analyzer factory use `MockAnalyzer` instead of calling real LLM APIs.

## Linting

```bash
uv run ruff check src/ tests/
uv run black src/ tests/
uv run mypy src/cellophanemail --ignore-missing-imports
```

## Migrations (Piccolo ORM)

Local dev uses a shared `postgres_dev` Docker container (`postgres:16-alpine` on port 5432). The `cellophanemail` database and password were set up manually — **not** via docker-compose. Credentials match the `piccolo_conf.py` fallback: `postgres:password@localhost:5432/cellophanemail`.

```bash
# Create migration (needs PYTHONPATH for module resolution)
PYTHONPATH=src DATABASE_URL="postgresql://postgres:password@localhost:5432/cellophanemail" \
  uv run piccolo migrations create cellophanemail --auto

# Run migrations
PYTHONPATH=src DATABASE_URL="postgresql://postgres:password@localhost:5432/cellophanemail" \
  uv run piccolo migrations forwards all

# Via Docker
docker-compose run migrate uv run piccolo migrations forwards all
```

## Refactoring Safety Rules

**MANDATORY before any refactor that changes paths, names, or signatures:**

1. Search for test impact first: `grep -r "old_path_or_name" tests/`
2. Update tests BEFORE changing source code (tests should FAIL, proving they hit the code)
3. Make source change
4. Verify: `uv run pytest tests/ -x`

## Architecture

### Application Factory
`src/cellophanemail/app.py` — `create_app()` builds the Litestar app with middleware, CORS, CSRF, compression, templates, and route registration. Test isolation via factory pattern.

### Email Protection Pipeline
The core feature lives in `features/email_protection/`:
- **AnalyzerFactory** selects analyzer by environment: `MockAnalyzer` (staging) / `LlamaAnalyzer` (privacy) / `EmailToxicityAnalyzer` (production via Anthropic)
- **StreamlinedEmailProtectionProcessor** — single-pass LLM analysis replacing the old multi-phase pipeline
- **GraduatedDecisionMaker** — maps `ThreatLevel` enum (SAFE/LOW/MEDIUM/HIGH/CRITICAL) to `ProtectionAction` (FORWARD_CLEAN/FORWARD_WITH_CONTEXT/REDACT_HARMFUL/SUMMARIZE_ONLY/BLOCK_ENTIRELY)
- **Four Horsemen model** — toxicity classification based on Gottman's four horsemen (criticism, contempt, defensiveness, stonewalling). Contempt is the strongest signal.

### Provider/Adapter Pattern
`providers/contracts.py` defines `EmailProvider` protocol. Implementations: Postmark (`providers/postmark/`), Gmail (`providers/gmail/`), SMTP (`providers/smtp/`). Each has a webhook handler.

### Auth
Dual auth strategy — JWT in Bearer headers (API/mobile) + httpOnly cookies (browser). Routes at `/api/v1/auth/`. `middleware/jwt_auth.py` handles both.

### Shield Addresses
UUID-based anonymous forwarding: `{hex}@cellophanemail.com`. Users never expose real email.

### Key Directories
- `routes/` — API endpoints (auth, billing, health, messages, sms, webhooks)
- `services/` — Business logic (auth, JWT, Stripe, email delivery/routing, user)
- `features/` — Domain features (email_protection, security, shield_addresses, monitoring)
- `providers/` — External email provider adapters
- `models/` — Piccolo ORM models and migrations
- `config/settings.py` — Pydantic settings with env var loading

## Android Client

The canonical Android app is at **`C:\Users\yhkim\StudioProjects\cellophanesms-android`** (accessible via WSL at `/mnt/c/Users/yhkim/StudioProjects/cellophanesms-android`). The `/home/yhk/repositories/cellophanesms-android` WSL copy is stale — do not use it.

### Android Build
```bash
cd /mnt/c/Users/yhkim/StudioProjects/cellophanesms-android
./gradlew assembleDebug
./gradlew test                    # Unit tests
./gradlew connectedAndroidTest    # Instrumented tests
```

### Android Architecture
- **Stack**: Kotlin, Jetpack Compose, Hilt DI, Room DB, Retrofit, Material 3
- **Pattern**: MVVM + Clean Architecture
- **Auth flow**: `LoginActivity` → API login → JWT stored in `EncryptedSharedPreferences` → `TokenAuthenticator` auto-refreshes on 401
- **SMS pipeline**: `SmsReceiver` → `MessageProcessingService` → cloud API analysis → `NotificationHelper`
- **Encryption**: AES-256-GCM via Android Keystore for stored SMS content (`MessageEntity.originalContent` is `ByteArray`)
- **`local.properties` keys**: `sdk.dir`, `BACKEND_URL`, `GEMINI_API_KEY` (optional), `DEBUG_JWT_TOKEN` (optional)

### Backend ↔ Android API Contract
- Auth: `POST auth/login`, `POST auth/register`, `POST auth/refresh`
- SMS analysis: `POST api/v1/messages/analyze`, `POST api/v1/sms/analyze:batch`
- Profile: `GET api/v1/user/profile`
