# CellophoneMail - Internal Development Repository

**Private monorepo for CellophoneMail development with automated open source and commercial distribution.**

AI-powered email protection using the Four Horsemen framework to filter toxic communication patterns.

## 🏗️ Repository Architecture

This is the **internal development repository** that automatically splits into:

### 📂 Distribution Repositories
- **`cellophanemail/cellophanemail`** (Public) - Open source version  
- **`cellophanemail/cellophanemail-pro`** (Private) - Commercial version

### 🔄 Automated Workflow
When you push to `main`, GitHub Actions automatically:
1. **Splits the code** using file-based rules
2. **Syncs to distribution repos** with appropriate code
3. **Triggers package builds** for PyPI distribution

## 🗂️ Code Organization

### Open Source Features (Public Distribution)
```
src/cellophanemail/
├── core/                    # Core email processing
├── providers/
│   ├── smtp/               # Self-hosted SMTP server
│   ├── gmail/              # Gmail OAuth integration
│   ├── contracts.py        # Provider interfaces
│   └── registry.py         # Provider discovery
├── features/
│   ├── email_protection/   # Four Horsemen analysis
│   ├── shield_addresses/   # Anonymous forwarding
│   └── user_accounts/      # User management
├── licensing/              # License validation framework
└── [core services, models, routes...]

tests/
├── four_horsemen/          # Complete testing framework
├── test_analysis_quality.py # Analysis validation
├── test_integration_minimal.py # Fast integration tests
└── unit/                   # Unit tests
```

### Commercial Features (Private Distribution)
```
src/cellophanemail/providers/
└── postmark/              # Postmark API integration

scripts/
└── test_webhook_robustness.py # Enterprise webhook testing

LICENSE.commercial          # Commercial license terms
```

## 🛠️ Development Workflow

### Daily Development
Work normally in this monorepo - **everything in one place**:

```bash
# Normal development workflow
git clone git@github.com:cellophanemail/cellophanemail-internal.git
cd cellophanemail-internal

# Edit any feature - open source or commercial
vim src/cellophanemail/providers/smtp/provider.py        # OSS
vim src/cellophanemail/providers/postmark/provider.py    # Commercial
vim src/cellophanemail/features/email_protection/analyzer.py # OSS

# Test everything together
pytest tests/integration/

# Commit normally - automation handles the rest
git add .
git commit -m "feat: improve Four Horsemen detection accuracy"
git push  # 🎉 Auto-syncs to both distribution repos
```

### Testing Strategy

#### 1. Integration Testing (Internal)
Test all features together in this monorepo:
```bash
pytest tests/integration/        # Test everything together
pytest tests/four_horsemen/      # Four Horsemen analysis quality
pytest tests/unit/               # Fast unit tests
```

#### 2. Distribution Testing
Each distribution repo has its own focused tests:
- **OSS repo**: SMTP, Gmail, Four Horsemen framework
- **Commercial repo**: Postmark integration, webhook robustness

### Manual Sync (Development/Testing)
```bash
# Test sync locally (dry run)
python tools/sync-repos.py --dry-run

# Sync to local test repos
python tools/sync-repos.py --target=both

# Sync only open source
python tools/sync-repos.py --target=oss

# Sync only commercial
python tools/sync-repos.py --target=commercial
```

## 📦 Package Distribution

### Open Source Package (`cellophanemail`)
**What users get:**
- Complete Four Horsemen toxicity detection framework
- Self-hosted SMTP server with built-in analysis
- Gmail OAuth integration with real-time protection
- Shield address management and user accounts
- Multilingual support (English, Korean)
- Comprehensive testing and analysis tools

**Installation:**
```bash
pip install cellophanemail
cellophanemail smtp --host 0.0.0.0 --port 25
```

### Commercial Package (`cellophanemail-pro`)
**Additional enterprise features:**
- Postmark API integration for reliable delivery
- Enterprise provider ecosystem (SendGrid, AWS SES, Azure)
- Advanced webhook testing and monitoring
- Managed hosting options
- Priority support

**Installation:**
```bash
pip install cellophanemail cellophanemail-pro
export CELLOPHANEMAIL_LICENSE_KEY="your-key"
cellophanemail serve
```

## 🔧 File Organization Rules

### What Goes to Open Source
- ✅ All core email processing (`src/cellophanemail/core/`)
- ✅ SMTP and Gmail providers (`src/cellophanemail/providers/smtp/`, `gmail/`)
- ✅ Complete Four Horsemen framework (`src/cellophanemail/features/email_protection/`)
- ✅ All analysis and testing tools (`tests/four_horsemen/`, `test_analysis_quality.py`)
- ✅ User management and shield addresses
- ✅ Licensing framework (for loading commercial features)

### What Goes to Commercial Only
- 🏢 Postmark provider (`src/cellophanemail/providers/postmark/`)
- 🏢 Enterprise webhook testing (`scripts/test_webhook_robustness.py`)
- 🏢 Commercial license terms (`LICENSE.commercial`)
- 🏢 Future: SendGrid, AWS SES, Azure providers
- 🏢 Future: Advanced analytics and managed hosting features

## 🤖 Automation Details

### GitHub Actions Workflow
**File:** `.github/workflows/sync-repos.yml`

**Triggers:**
- Push to `main` branch
- Manual workflow dispatch

**Process:**
1. Clone both distribution repositories
2. Run `tools/sync-repos.py` to split code
3. Commit and push changes to distribution repos
4. Trigger package builds in each repo

**Requirements:**
- `REPO_SYNC_TOKEN` secret with repository access
- Repository must be `cellophanemail/cellophanemail-internal`

### Sync Script
**File:** `tools/sync-repos.py`

**Features:**
- File-based splitting with configurable rules
- Dry-run mode for testing
- Automatic README generation for each distribution
- Git commit and push automation
- Detailed logging and error handling

**Usage:**
```bash
python tools/sync-repos.py --help
python tools/sync-repos.py --dry-run              # Test without changes
python tools/sync-repos.py --target=oss           # Sync only OSS
python tools/sync-repos.py --target=commercial    # Sync only commercial
python tools/sync-repos.py --target=both          # Sync both (default)
```

## 🚨 Important Guidelines

### DO ✅
- **Develop in this monorepo** for all features
- **Test integrations** before pushing to main
- **Follow file organization rules** (see above)
- **Use descriptive commit messages** (synced to distribution repos)
- **Run tests locally** before pushing

### DON'T ❌
- **Don't commit directly** to distribution repos
- **Don't put commercial code** in open source paths
- **Don't put open source code** in commercial-only paths
- **Don't commit secrets** or license keys
- **Don't bypass the sync workflow**

## 🔐 Security & Access Control

### Repository Access
- **Internal repo**: Private, core team only
- **OSS repo**: Public, community contributions welcome
- **Commercial repo**: Private, licensed users and partners only

### Preventing Code Leaks
1. **Automated splitting** ensures commercial code never reaches public repo
2. **Path-based exclusions** prevent accidents
3. **GitHub Actions restrictions** to internal repo only
4. **License validation** at runtime for commercial features

### License Management
- **Open source**: MIT license for maximum adoption
- **Commercial**: Proprietary license with key validation
- **Runtime checking**: Commercial features require valid license key

## 🔐 Privacy-Focused Architecture

### The Privacy Problem
Current email protection systems violate privacy by:
- **Storing email content in databases** (privacy breach)
- **Sending data to external LLM APIs** (data leaves your control)
- **Keeping emails forever** (unnecessary data retention)

### The Solution: Zero-Persistence Architecture

**Current Flow (PRIVACY VIOLATION):**
```
Email → Webhook → Database (stores content) → LLM API → Database (logs) → Delivery
```

**New Flow (PRIVACY-SAFE):**
```
Email → Webhook → Memory (5 min) → LLM → Immediate Delivery → Auto-Cleanup
         ↓                                                          ↓
    [202 Accepted]                                        [Metadata Only to DB]
```

### Privacy Components (Already Implemented)
- ✅ **EphemeralEmail** - Temporary email container with 5-minute lifetime
- ✅ **MemoryManager** - Manages 50 concurrent emails in RAM only
- ✅ **InMemoryProcessor** - Processes emails without database
- ✅ **ImmediateDeliveryManager** - Delivers and forgets

### Privacy Guarantees
- **Zero Content Persistence** - Email content never touches the database
- **5-Minute Memory Limit** - All emails auto-deleted from memory after 5 minutes
- **Metadata-Only Logging** - Only anonymous statistics stored (no content)
- **No External Data Storage** - Processing happens entirely in your infrastructure

### Implementation Status
- ✅ Privacy components built and tested
- 🚧 Integration with webhook controller in progress
- 🚧 Database migration to remove content fields pending
- 🚧 Background cleanup task implementation pending

## 🧪 Four Horsemen Framework

### Overview
CellophoneMail implements Gottman's Four Horsemen of the Apocalypse framework to detect toxic communication:

1. **Criticism** - Character/personality attacks rather than behavior feedback
2. **Contempt** - Expressions of superiority, disrespect, mockery (most destructive)
3. **Defensiveness** - Playing victim, counter-attacking, excuse-making
4. **Stonewalling** - Emotional withdrawal, communication shutdown

### Analysis Pipeline (Privacy-Safe)
```
Inbound Email → Webhook → Memory Storage → In-Memory Processor → Four Horsemen Analyzer
     ↓              ↓           ↓                ↓                      ↓
[202 Accepted] → [5-min TTL] → [No DB] → [LLM Analysis] → Forward/Block → Cleanup
```

### Testing Framework
Comprehensive testing framework in `tests/four_horsemen/`:

**Components:**
- **Test Samples**: 16+ multilingual samples with ground truth labels
- **Pipeline Tracer**: 13-stage monitoring from receipt to forwarding  
- **Metrics Collector**: Accuracy, performance, cost optimization tracking
- **Analysis Comparator**: Local vs AI method comparison
- **Test Runner**: Configurable evaluation with detailed reporting

**Quick Usage:**
```python
# Test analysis quality
python tests/test_analysis_quality.py

# Full Four Horsemen evaluation
from tests.four_horsemen.test_runner import run_quick_test
result = await run_quick_test()
print(f"Accuracy: {result['overall_accuracy']:.1%}")
```

## 📚 Documentation

### For Developers
- **[Development Workflow](docs/DEVELOPMENT_WORKFLOW.md)** - Detailed workflow guide
- **[API Documentation](docs/api/)** - API reference and examples  
- **[Testing Guide](docs/testing/)** - Testing strategies and frameworks

### For Users
- **OSS Documentation**: Auto-generated in distribution repo
- **Commercial Documentation**: Private documentation for licensed users
- **Self-hosting Guide**: Complete setup instructions for OSS users

## 🚀 Deployment & Release

### Package Release Process
1. **Push to main** in internal repo
2. **Automated sync** to distribution repos
3. **GitHub Actions** build packages in each repo
4. **PyPI publication** (OSS to public PyPI, Commercial to private PyPI)

### Version Management
- **Semantic versioning** across all packages
- **Synchronized releases** between OSS and Commercial
- **Release notes** auto-generated from commit messages

## 🆘 Troubleshooting

### Sync Issues
```bash
# Check sync script
python tools/sync-repos.py --dry-run

# Verify file organization
ls ../cellophanemail-oss/src/cellophanemail/providers/    # Should show: smtp, gmail
ls ../cellophanemail-pro/src/cellophanemail/providers/    # Should show: postmark

# Check GitHub Actions logs
```

### Code in Wrong Repository
```bash
# Emergency: Revert problematic commit
git revert <commit-hash>

# Re-run sync to clean up
python tools/sync-repos.py
```

### Test Failures
```bash
# Test both distributions
cd ../cellophanemail-oss && pytest
cd ../cellophanemail-pro && pytest

# Test internal integration
pytest tests/integration/
```

## 🎯 Business Model

### Open Source Strategy
- **Four Horsemen framework** as the core differentiator
- **Complete self-hosting solution** for developers
- **Real value** that justifies open sourcing vs competitors
- **Community building** around email protection research

### Commercial Strategy  
- **Enterprise providers** (Postmark, SendGrid, AWS SES) for reliability
- **Managed hosting** for convenience and scale
- **Priority support** for business customers
- **Advanced analytics** and reporting tools

### Value Proposition
- **Open source users**: Get complete toxicity detection framework for free
- **Commercial users**: Pay for enterprise reliability, convenience, and support
- **Not feature-gating the core** - adding enterprise convenience layers

---

## 🤝 Contributing

**Internal Development:**
1. Clone this internal repository
2. Create feature branch from `main`
3. Develop and test in monorepo
4. Submit PR for review
5. Merge triggers automatic distribution

**External Contributions:**
- Open source contributions welcome in public repository
- Commercial features require partnership discussion

## 📞 Support

- **Development Team**: Internal Slack #cellophanemail-dev
- **Documentation**: [Development Workflow](docs/DEVELOPMENT_WORKFLOW.md)
- **Issues**: GitHub Issues in appropriate distribution repository

---

**This internal repository enables comfortable monorepo development while maintaining clean separation between open source and commercial offerings. The automated workflow ensures consistency and prevents accidental code leaks between distributions.**