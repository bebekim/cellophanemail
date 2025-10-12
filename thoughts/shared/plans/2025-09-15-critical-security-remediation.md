# Critical Security Remediation Implementation Plan

## Overview

Emergency security remediation to address 4 critical vulnerabilities: exposed production credentials in version control, insecure random number generation for usernames, command injection risk in deployment scripts, and weak default secrets in configuration.

## Current State Analysis

The codebase has live production API keys and passwords exposed in `.env`, uses predictable random generation for security-sensitive operations, and has command injection vulnerabilities in deployment tools.

### Key Discoveries:
- `.env` file contains real Anthropic, Postmark, Gmail credentials (must rotate immediately)
- `auth_service.py:66` uses `random.randint()` for username generation (predictable)
- `tools/sync-repos.py:85` uses `subprocess.run(shell=True)` with dynamic commands
- `settings.py:26,36` contains weak default credentials

## Desired End State

A secure configuration system with no exposed credentials, cryptographically secure random generation, safe subprocess execution, and proper secret management with environment validation.

### Verification:
- No real credentials in version control
- All random generation uses `secrets` module
- No `shell=True` in subprocess calls
- Configuration requires explicit secrets with no weak defaults

## What We're NOT Doing

- Implementing full secret management system (HashiCorp Vault, AWS Secrets Manager) - future work
- Adding OAuth providers or MFA - separate feature
- Comprehensive security audit of all endpoints - focused on critical issues only
- Changing authentication architecture - maintaining current JWT approach

## Implementation Approach

Prioritize immediate credential rotation to prevent unauthorized access, then fix code vulnerabilities systematically. Each phase builds on the previous to establish defense in depth.

## Phase 1: Emergency Credential Rotation

### Overview
Immediately rotate all exposed credentials and remove them from version control to prevent unauthorized access.

### Changes Required:

#### 1. Create Secure Template File
**File**: `.env.example`
**Changes**: Create template with placeholder values

```bash
# Application Settings
DEBUG=true
TESTING=false
SECRET_KEY=your-secret-key-here-minimum-32-chars
ENCRYPTION_KEY=generate-with-fernet-generate-key

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0

# AI Services
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
UPSTAGE_API_KEY=up_your-key-here
AI_PROVIDER=anthropic

# Email Delivery
EMAIL_DELIVERY_METHOD=smtp
POSTMARK_API_TOKEN=your-postmark-token
POSTMARK_ACCOUNT_API_TOKEN=your-account-token
POSTMARK_SERVER_ID=your-server-id
POSTMARK_DRY_RUN=false

# SMTP Settings
EMAIL_USERNAME=your-email@example.com
EMAIL_PASSWORD=your-app-password
SMTP_DOMAIN=cellophanemail.com
OUTBOUND_SMTP_HOST=smtp.gmail.com
OUTBOUND_SMTP_PORT=587

# Billing (Optional)
STRIPE_API_KEY=sk_test_your-key
STRIPE_WEBHOOK_SECRET=whsec_your-secret
```

#### 2. Update .gitignore
**File**: `.gitignore`
**Changes**: Ensure .env is properly excluded

```gitignore
# Environment files
.env
.env.local
.env.*.local
!.env.example
!.env.test.example
```

#### 3. Remove Secrets from Git History
**Action**: Clean git history of exposed secrets

```bash
# Remove .env from all commits
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env' \
  --prune-empty --tag-name-filter cat -- --all

# Force push to remote (coordinate with team)
git push origin --force --all
git push origin --force --tags
```

### Success Criteria:

#### Automated Verification:
- [x] `.env.example` file exists: `test -f .env.example`
- [x] `.env` is in .gitignore: `grep -q "^\.env$" .gitignore`
- [x] No .env in git: `! git ls-files | grep -q "^\.env$"`

#### Manual Verification:
- [ ] All API keys rotated in respective services (Anthropic, Postmark, Gmail)
- [ ] Database password changed
- [ ] New credentials working in local development
- [ ] Team notified of credential rotation

---

## Phase 2: Fix Insecure Random Generation

### Overview
Replace predictable random number generation with cryptographically secure alternatives.

### Changes Required:

#### 1. Fix Username Generation
**File**: `src/cellophanemail/services/auth_service.py`
**Changes**: Replace random.randint with secrets module

```python
import secrets  # Add this import at the top

def generate_username_from_email(email: str) -> str:
    """Generate a unique username from email address."""
    local_part = email.split('@')[0]
    # Remove special characters and spaces
    clean_name = ''.join(c for c in local_part if c.isalnum() or c in ['-', '_'])

    # Add random number to ensure uniqueness
    # SECURITY FIX: Use cryptographically secure random
    random_number = secrets.randbelow(900) + 100  # Range: 100-999
    return f"{clean_name}{random_number}"
```

#### 2. Add Security Test
**File**: `tests/test_auth_service.py`
**Changes**: Add test for secure random generation

```python
import secrets
from unittest.mock import patch

def test_username_generation_uses_secure_random():
    """Test that username generation uses cryptographically secure randomness."""
    with patch('cellophanemail.services.auth_service.secrets.randbelow') as mock_secrets:
        mock_secrets.return_value = 500

        username = generate_username_from_email("test@example.com")

        mock_secrets.assert_called_once_with(900)
        assert username == "test600"  # 500 + 100 = 600
```

### Success Criteria:

#### Automated Verification:
- [x] Import added: `grep -q "import secrets" src/cellophanemail/services/auth_service.py`
- [x] No random.randint in auth: `! grep -q "random\.randint" src/cellophanemail/services/auth_service.py`
- [x] Tests pass: `pytest tests/test_auth_service.py -v`
- [x] Type checking passes: `mypy src/cellophanemail/services/auth_service.py`

#### Manual Verification:
- [x] Username generation still works correctly
- [x] No predictable patterns in generated usernames

---

## Phase 3: Eliminate Command Injection

### Overview
Remove shell=True from subprocess calls and implement proper command sanitization.

### Changes Required:

#### 1. Fix Repository Sync Script
**File**: `tools/sync-repos.py`
**Changes**: Remove shell=True and use argument lists

```python
import shlex
from typing import List

def run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> bool:
    """Run shell command with logging (secure version)."""
    self.log(f"Running: {' '.join(cmd)}")
    if self.dry_run:
        return True

    try:
        result = subprocess.run(
            cmd,  # Now expects a list, not a string
            cwd=cwd or self.root_dir,
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout:
            self.log(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        self.log(f"Error: {e.stderr}")
        return False

def sync_repositories(self):
    """Sync changes to OSS and commercial repos."""
    # ... existing code ...

    # Replace string commands with lists
    commands = [
        ["git", "add", "."],
        ["git", "commit", "-m", message],  # message passed as separate arg
        ["git", "push", "origin", "main"]
    ]

    for cmd in commands:
        if not self.run_command(cmd, cwd=repo_path):
            self.log(f"Failed to execute: {' '.join(cmd)}")
            return False
```

#### 2. Add Input Validation
**File**: `tools/sync-repos.py`
**Changes**: Validate commit messages

```python
def validate_commit_message(self, message: str) -> str:
    """Validate and sanitize commit message."""
    # Remove any shell metacharacters
    dangerous_chars = ['$', '`', '\\', '"', "'", '\n', '\r', ';', '&', '|', '>', '<']
    for char in dangerous_chars:
        if char in message:
            message = message.replace(char, '')

    # Truncate to reasonable length
    max_length = 200
    if len(message) > max_length:
        message = message[:max_length] + "..."

    return message
```

### Success Criteria:

#### Automated Verification:
- [x] No shell=True in sync script: `! grep -q "shell=True" tools/sync-repos.py`
- [x] Script runs successfully: `python tools/sync-repos.py --dry-run`
- [x] Validation function exists: `grep -q "validate_commit_message" tools/sync-repos.py`

#### Manual Verification:
- [x] Repository sync still works with safe commands
- [x] Commit messages properly sanitized
- [x] No command injection possible with malicious input

---

## Phase 4: Implement Secure Configuration

### Overview
Remove default credentials from code and require explicit configuration with validation.

### Changes Required:

#### 1. Update Settings Class
**File**: `src/cellophanemail/config/settings.py`
**Changes**: Remove weak defaults and add validation

```python
from pydantic import field_validator, ValidationError
import os

class Settings(BaseSettings):
    """CellophoneMail application settings with security validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Required fields with no defaults (force explicit configuration)
    secret_key: str = Field(
        description="Secret key for JWT and sessions (min 32 chars)"
    )

    database_url: str = Field(
        description="Database URL for Piccolo ORM"
    )

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key strength."""
        if len(v) < 32:
            raise ValueError("secret_key must be at least 32 characters")
        if v == "dev-secret-key-change-in-production":
            raise ValueError("Default secret key not allowed")
        if v.lower() in ['secret', 'password', 'changeme']:
            raise ValueError("Weak secret key detected")
        return v

    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL doesn't contain default password."""
        if 'password@' in v.lower():
            raise ValueError("Default database password not allowed")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug and not self.testing
```

#### 2. Add Startup Validation
**File**: `src/cellophanemail/app.py`
**Changes**: Validate configuration at startup

```python
def validate_configuration(settings: Settings) -> None:
    """Validate configuration for security issues."""
    errors = []

    # Check for required production settings
    if settings.is_production:
        if not settings.encryption_key:
            errors.append("ENCRYPTION_KEY is required in production")
        if not settings.anthropic_api_key and settings.ai_provider == "anthropic":
            errors.append("ANTHROPIC_API_KEY is required for AI features")
        if settings.email_delivery_method == "postmark" and not settings.postmark_api_token:
            errors.append("POSTMARK_API_TOKEN is required for Postmark delivery")

    if errors:
        raise ValueError(f"Configuration errors: {'; '.join(errors)}")

def create_app() -> Litestar:
    """Create CellophoneMail Litestar application."""
    settings = get_settings()

    # Validate configuration before starting
    try:
        validate_configuration(settings)
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise

    # ... rest of app creation
```

### Success Criteria:

#### Automated Verification:
- [x] Validators added: `grep -q "@field_validator" src/cellophanemail/config/settings.py`
- [x] No default secrets: `! grep -q "dev-secret-key-change-in-production" src/cellophanemail/config/settings.py`
- [x] Startup validation: `grep -q "validate_configuration" src/cellophanemail/app.py`
- [x] Tests pass: `pytest tests/unit/test_config_security.py -v`

#### Manual Verification:
- [x] Application refuses to start with weak/default credentials
- [x] Clear error messages for missing configuration
- [x] Production mode enforces stricter validation

---

## Testing Strategy

### Unit Tests:
- Test secure random generation in auth_service
- Test configuration validation with various inputs
- Test command sanitization in sync script

### Integration Tests:
- Verify application starts with valid configuration
- Verify application fails with invalid configuration
- Test credential rotation doesn't break functionality

### Security Tests:
```bash
# Check for exposed secrets
grep -r "sk-ant-api03" . --exclude-dir=.git
grep -r "password" . --include="*.py" | grep -v test | grep -v example

# Verify secure random usage
grep -r "random\.randint\|random\.choice" . --include="*.py" | grep -v test

# Check for shell=True
grep -r "shell=True" . --include="*.py"
```

## Migration Notes

1. **Before deploying**: Ensure all team members have new credentials
2. **Credential rotation order**:
   - Rotate API keys first (immediate effect)
   - Update database password during maintenance window
   - Deploy code changes
   - Verify all services reconnect successfully
3. **Rollback plan**: Keep old credentials active for 24 hours after rotation

## References

- Original security analysis: `thoughts/shared/research/2025-09-15-code-quality-security-analysis.md`
- Pydantic settings docs: https://docs.pydantic.dev/latest/usage/settings/
- Python secrets module: https://docs.python.org/3/library/secrets.html
- Git filter-branch: https://git-scm.com/docs/git-filter-branch