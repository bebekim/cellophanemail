---
date: 2025-10-13T07:28:45+0000
researcher: Claude (Sonnet 4.5)
git_commit: f2a6055cc50a5246d2a4cdda7092f67963b9da3e
branch: main
repository: cellophanemail
topic: "Why is there src/ with cellophanemail nested within it?"
tags: [research, codebase, project-structure, src-layout, python-packaging, dual-license]
status: complete
last_updated: 2025-10-13
last_updated_by: Claude (Sonnet 4.5)
---

# Research: Code Structure - src/ and cellophanemail Nesting

**Date**: 2025-10-13T07:28:45+0000
**Researcher**: Claude (Sonnet 4.5)
**Git Commit**: f2a6055cc50a5246d2a4cdda7092f67963b9da3e
**Branch**: main
**Repository**: cellophanemail

## Research Question

Why is there a `src/` directory with `cellophanemail` nested within it? What is the purpose of this structure?

## Summary

The `src/cellophanemail/` structure implements the **"src layout"** Python packaging pattern to solve two critical challenges:

1. **Import Safety & Testing Accuracy** - Forces explicit PYTHONPATH configuration, preventing tests from accidentally importing from the wrong location
2. **Dual-License Distribution** - Enables a monorepo architecture where a single codebase builds both open source (`cellophanemail`) and commercial (`cellophanemail-pro`) packages through path-based inclusion/exclusion rules

This architecture allows comfortable monorepo development while maintaining clean separation for distribution via two separate `pyproject.toml` files in the `packages/` directory, both pointing to the same `src/` source tree.

## Detailed Findings

### 1. Directory Structure Overview

```
cellophanemail/                          # Project root
├── src/                                # Source code (src-layout pattern)
│   ├── __init__.py                     # Package marker
│   └── cellophanemail/                 # Main application package
│       ├── __init__.py
│       ├── app.py                      # Application entry point
│       ├── config/                     # Configuration management
│       ├── core/                       # Core email processing
│       ├── features/                   # Feature modules
│       │   ├── email_protection/       # Four Horsemen Analysis (OSS)
│       │   ├── shield_addresses/       # Email aliasing (OSS)
│       │   ├── user_accounts/          # Account management (OSS)
│       │   ├── security/               # Security features (OSS)
│       │   └── monitoring/             # Observability (OSS)
│       ├── providers/                  # Email provider integrations
│       │   ├── smtp/                   # SMTP provider (OSS)
│       │   ├── gmail/                  # Gmail API (OSS)
│       │   └── postmark/               # Postmark (Commercial)
│       ├── routes/                     # API routes (HTTP layer)
│       ├── services/                   # Business logic layer
│       ├── models/                     # Database models (Piccolo ORM)
│       ├── middleware/                 # HTTP middleware (JWT auth)
│       ├── plugins/                    # Plugin system
│       └── templates/                  # Jinja2 HTML templates
├── packages/                           # Distribution configurations
│   ├── cellophanemail/                 # Open source package
│   │   └── pyproject.toml              # → package-dir = {"" = "../../src"}
│   └── cellophanemail-pro/             # Commercial package
│       └── pyproject.toml              # → package-dir = {"" = "../../src"}
├── tests/                              # Test suite
│   └── conftest.py                     # sys.path.insert(0, src_path)
├── bin/                                # Development scripts
│   ├── dev-litestar                    # export PYTHONPATH="src:${PYTHONPATH}"
│   └── dev                             # Development utilities
├── docs/                               # Documentation
│   ├── ONBOARDING.md                   # Explains src-layout
│   └── DEVELOPMENT_WORKFLOW.md         # Development guide
├── pyproject.toml                      # Root config (dev dependencies only)
└── README.md                           # Main documentation
```

### 2. The src-layout Pattern

**What it is:**
The src-layout (or "src directory layout") is a Python packaging best practice where application code lives in `src/` rather than the project root.

**Why it's used:**

#### Import Safety
Without src-layout (code at root):
```
cellophanemail/
├── cellophanemail/     # Could import from here (wrong!)
└── tests/              # Tests might import from local dir
```

With src-layout:
```
cellophanemail/
├── src/cellophanemail/ # Only way to import is via PYTHONPATH
└── tests/              # Must explicitly add src/ to path
```

**Problem prevented:** Tests accidentally importing from development directory instead of installed package, leading to "works on my machine" bugs.

**Evidence from codebase:**

`bin/dev-litestar:8`:
```bash
export PYTHONPATH="src:${PYTHONPATH}"
```

`README.md:163`:
```bash
PYTHONPATH=src uvicorn cellophanemail.app:app --host 0.0.0.0 --port 8000 --reload
```

`Dockerfile:34`:
```dockerfile
ENV PYTHONPATH=/app/src
```

`tests/conftest.py:11`:
```python
sys.path.insert(0, str(src_path))
```

#### Testing Accuracy
Forces tests to import from the package as it would be installed, not from arbitrary file paths. This ensures:
- Import paths work the same in development and production
- Tests can't pass locally but fail when package is installed
- Developers must properly configure PYTHONPATH

### 3. Dual-License Distribution Architecture

**The Business Problem:**
CellophoneMail needs to:
1. Distribute an open source version (MIT license)
2. Distribute a commercial version with additional features
3. Develop both in a single comfortable monorepo
4. Prevent code duplication or manual synchronization

**The Solution:**
A monorepo that uses **path-based rules** to build two separate packages from the same source tree.

#### Package Configuration Structure

**Open Source Package** (`packages/cellophanemail/pyproject.toml:68-79`):
```toml
[tool.setuptools]
package-dir = {"" = "../../src"}       # Points to shared source

[tool.setuptools.packages.find]
where = ["../../src"]
include = [
    "cellophanemail*",                # Include everything
]
exclude = [
    "cellophanemail.providers.postmark*",      # Commercial only
    "cellophanemail.features.ai_advanced*",    # Commercial only
]
```

**Commercial Package** (`packages/cellophanemail-pro/pyproject.toml:67-74`):
```toml
[tool.setuptools]
package-dir = {"" = "../../src"}       # Same source!

[tool.setuptools.packages.find]
where = ["../../src"]
include = [
    "cellophanemail_pro*",            # Separate namespace
]
```

**Key insight:** Both `pyproject.toml` files point to `../../src` (relative to their location in `packages/`), but use different `include`/`exclude` rules to package different subsets of code.

#### How It Works

**Development Phase:**
Developer works in internal monorepo at `src/cellophanemail/`:
```bash
# Edit OSS feature
vim src/cellophanemail/providers/smtp/provider.py

# Edit commercial feature
vim src/cellophanemail/providers/postmark/provider.py

# Run everything together
PYTHONPATH=src uvicorn cellophanemail.app:app --reload
```

**Distribution Phase:**
Each package builds independently from the same source:
```bash
# Build OSS package
python -m build --outdir dist/ packages/cellophanemail/
# Result: cellophanemail-0.1.0.tar.gz
#         includes: smtp, gmail providers
#         excludes: postmark provider

# Build commercial package
python -m build --outdir dist/ packages/cellophanemail-pro/
# Result: cellophanemail-pro-0.1.0.tar.gz
#         includes: postmark provider
#         separate namespace: cellophanemail_pro
```

**User Installation:**
```bash
# OSS users
pip install cellophanemail

# Commercial users
pip install cellophanemail cellophanemail-pro
```

#### Entry Points for Plugin Discovery

**Open Source Entry Points** (`packages/cellophanemail/pyproject.toml:61-66`):
```toml
[project.scripts]
cellophanemail = "cellophanemail.cli:main"

[project.entry-points."cellophanemail.providers"]
smtp = "cellophanemail.providers.smtp:SMTPProvider"
gmail = "cellophanemail.providers.gmail:GmailProvider"
```

**Commercial Entry Points** (`packages/cellophanemail-pro/pyproject.toml:54-65`):
```toml
[project.scripts]
cellophanemail-pro = "cellophanemail_pro.cli:main"

[project.entry-points."cellophanemail.providers"]
postmark = "cellophanemail_pro.providers.postmark:PostmarkProvider"
sendgrid = "cellophanemail_pro.providers.sendgrid:SendGridProvider"
aws_ses = "cellophanemail_pro.providers.aws_ses:SESProvider"

[project.entry-points."cellophanemail.analyzers"]
ai_advanced = "cellophanemail_pro.features.ai_advanced:AdvancedAnalyzer"
sentiment = "cellophanemail_pro.features.sentiment:SentimentAnalyzer"
threat_intel = "cellophanemail_pro.features.threat_intel:ThreatIntelligence"
```

The application uses Python's entry points mechanism to discover available providers/analyzers at runtime, enabling the commercial package to extend the OSS package without modifying core code.

### 4. Application Architecture

**Three-layer pattern** within `src/cellophanemail/`:

```
routes/        → HTTP layer (request/response handling)
    ↓ calls
services/      → Business logic layer (reusable across routes)
    ↓ calls
models/        → Data access layer (Piccolo ORM)
```

**Cross-cutting concerns:**
- `middleware/` - JWT auth, CORS, rate limiting
- `config/` - Settings, environment variables, secrets
- `core/` - Shared utilities (email parsing, sending)

**Feature modules** (`features/`):
- Self-contained business capabilities
- Each feature has its own models, services, analyzers
- Plugin architecture for extensibility

### 5. Import Patterns

**Correct imports** (from application code):
```python
from cellophanemail.app import create_app
from cellophanemail.core.email_message import EmailMessage
from cellophanemail.services.email_delivery import EmailDeliveryService
from cellophanemail.features.email_protection import EphemeralEmail
```

**Incorrect imports** (never used):
```python
from src.cellophanemail.app import create_app  # Wrong!
```

All imports use absolute paths starting with `cellophanemail`, never including `src` in the import path. The `PYTHONPATH=src` configuration makes this work by adding `src/` to the Python module search path.

### 6. Development Workflow

**Running the application:**
```bash
# Litestar web API (port 8000)
PYTHONPATH=src uvicorn cellophanemail.app:app --host 0.0.0.0 --port 8000 --reload

# Or use the dev script
./bin/dev-litestar

# SMTP server (port 8025)
PYTHONPATH=src python -m cellophanemail.plugins.smtp
```

**Running tests:**
```bash
# PYTHONPATH automatically set by conftest.py
pytest tests/

# Or with explicit PYTHONPATH
PYTHONPATH=src pytest tests/
```

**Database migrations:**
```bash
PYTHONPATH=src uv run piccolo migrations forwards cellophanemail
```

**Package building:**
```bash
# Build OSS package
cd packages/cellophanemail
python -m build

# Build commercial package
cd packages/cellophanemail-pro
python -m build
```

## Code References

- `src/cellophanemail/app.py:1-100` - Main application factory and Litestar app setup
- `packages/cellophanemail/pyproject.toml:68-79` - OSS package configuration with exclusions
- `packages/cellophanemail-pro/pyproject.toml:67-74` - Commercial package configuration
- `bin/dev-litestar:8` - PYTHONPATH configuration in dev scripts
- `tests/conftest.py:11` - PYTHONPATH configuration in test suite
- `Dockerfile:34` - PYTHONPATH configuration in Docker
- `README.md:163` - Documentation of PYTHONPATH usage
- `README.md:441-495` - File organization rules

## Architecture Insights

### Key Patterns

1. **Shared Source, Split Distribution**
   - Pattern: Multiple package definitions point to same source tree
   - Implementation: `package-dir = {"" = "../../src"}` in both configs
   - Benefit: Single codebase, different distributions without code duplication

2. **Path-Based Feature Gating**
   - Pattern: Package inclusion/exclusion by file path patterns
   - OSS excludes: `cellophanemail.providers.postmark*`, `cellophanemail.features.ai_advanced*`
   - Commercial includes: `cellophanemail_pro*` (separate namespace)
   - Benefit: Automated code splitting, no manual synchronization

3. **Entry Point Plugin System**
   - Pattern: Packages register providers/analyzers via entry points
   - Discovery: Python's `importlib.metadata` discovers installed plugins
   - Extensibility: Commercial package extends OSS without modifying core

4. **Development PYTHONPATH Discipline**
   - Pattern: All dev scripts explicitly set `PYTHONPATH=src`
   - Enforcement: src-layout makes it impossible to import without proper config
   - Safety: Tests can't accidentally import from uninstalled development directory

### Design Decisions

**Why not use a multi-repo approach?**
- Monorepo provides better developer experience
- Shared infrastructure changes happen once
- Integration testing across OSS and commercial features
- Automated tooling handles distribution splitting

**Why not use git submodules or vendoring?**
- Submodules add complexity and synchronization issues
- This approach keeps development simple (single repo)
- Distribution complexity is handled by packaging tools (setuptools)
- Changes to shared code automatically reflected in both packages

**Why not use a single package with feature flags?**
- Path-based exclusion ensures commercial code never ships in OSS
- Licensing is clearer (separate packages = separate licenses)
- Users can't accidentally access commercial features
- Namespace separation (`cellophanemail_pro`) makes boundaries explicit

## Historical Context (from thoughts/)

**Most relevant prior research:**
- `thoughts/shared/research/2025-10-08-application-entry-points-configuration-architecture.md` - Comprehensive analysis of entry points, configuration, and OSS/commercial separation
- `thoughts/shared/research/2025-09-15-architecture-analysis.md` - CellophoneMail architecture overview including dual-service architecture
- `thoughts/shared/research/2025-09-24-entry-points-configuration-workflow-analysis.md` - Entry points and startup sequence analysis
- `thoughts/shared/research/2025-09-21-application-entry-points-startup-guide.md` - Practical guide to entry points and PYTHONPATH patterns
- `thoughts/shared/til/2025-10-13-routes-services-middleware-architecture.md` - Three-layer architecture pattern explanation

**Documentation references:**
- `docs/ONBOARDING.md` - Explains repository structure and src-layout rationale
- `docs/DEVELOPMENT_WORKFLOW.md` - Development workflow and directory organization
- `README.md` - Main documentation with file organization rules

## Related Research

- [Application Entry Points and Configuration Architecture](2025-10-08-application-entry-points-configuration-architecture.md)
- [CellophoneMail Architecture Analysis](2025-09-15-architecture-analysis.md)
- [Entry Points and Configuration Workflow](2025-09-24-entry-points-configuration-workflow-analysis.md)
- [Application Entry Points Startup Guide](2025-09-21-application-entry-points-startup-guide.md)

## Open Questions

1. **Distribution automation**: How is the sync from internal monorepo to public OSS repo automated? (Mentioned `tools/sync-repos.py` but not found in current codebase)

2. **License validation**: How does the OSS package validate commercial licenses at runtime? (Mentioned `licensing/` directory but implementation details not fully explored)

3. **Testing strategy**: How are OSS-only vs commercial-only features tested independently? Are there separate test suites or environment variables that gate tests?

4. **Namespace migration**: Is there a plan to consolidate on a single namespace (e.g., `cellophanemail.pro.*` instead of `cellophanemail_pro.*`)? The underscore vs dot notation creates an asymmetry.

## Conclusion

The `src/cellophanemail/` structure is a sophisticated solution to dual-license distribution that:

1. **Enforces best practices** - Import safety via src-layout prevents common packaging bugs
2. **Enables business model** - Single codebase supports both OSS and commercial offerings
3. **Maintains simplicity** - Monorepo development experience with automated distribution
4. **Follows standards** - Uses modern Python packaging (PEP 517, setuptools, entry points)

This architecture allows CellophoneMail to:
- Develop comfortably in a single repository
- Distribute features separately based on license
- Maintain a plugin ecosystem via entry points
- Ensure import consistency across development and production

The trade-off is increased packaging complexity (two `pyproject.toml` files, PYTHONPATH discipline) for business flexibility (dual-license model) and technical correctness (import safety).
