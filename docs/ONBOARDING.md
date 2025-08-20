# CellophoneMail Developer Onboarding

Welcome to the CellophoneMail development team! This guide will get you up and running with our dual open source/commercial development workflow.

## 🎯 Quick Overview

**What makes us unique:**
- **Monorepo development** - Everything in one place for easy development
- **Automated splitting** - Code automatically distributed to open source and commercial repos
- **Four Horsemen framework** - Psychology-based toxic email detection (our secret sauce!)

## 🚀 Quick Start (5 minutes)

### 1. Clone the Internal Repository
```bash
git clone git@github.com:cellophanemail/cellophanemail-internal.git
cd cellophanemail-internal
```

### 2. Set Up Environment
```bash
# Install dependencies with uv
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# ANTHROPIC_API_KEY=your-key-here
```

### 3. Run Tests
```bash
# Quick functionality test (30 seconds)
pytest tests/test_integration_minimal.py -v

# Four Horsemen analysis test (2 minutes)
python tests/test_analysis_quality.py
```

### 4. Test the Sync (Optional)
```bash
# See how code splitting works (dry run)
python tools/sync-repos.py --dry-run
```

**🎉 You're ready to develop!**

## 🧠 Understanding the Architecture

### Repository Structure
```
cellophanemail-internal/           # ← You work here (everything)
├── src/cellophanemail/
│   ├── providers/
│   │   ├── smtp/                 # → Goes to open source
│   │   ├── gmail/                # → Goes to open source
│   │   └── postmark/             # → Goes to commercial only
│   └── features/
│       └── email_protection/     # → Goes to open source (Four Horsemen!)
└── tests/
    └── four_horsemen/            # → Goes to open source (complete framework)

cellophanemail/cellophanemail      # ← Auto-generated (public)
cellophanemail/cellophanemail-pro  # ← Auto-generated (private)
```

### What Users Get

**Open Source Users (`pip install cellophanemail`):**
- ✅ Complete Four Horsemen toxicity detection
- ✅ Self-hosted SMTP server
- ✅ Gmail integration
- ✅ Full analysis framework and testing tools

**Commercial Users (`pip install cellophanemail-pro`):**
- ✅ Everything above PLUS
- ⭐ Postmark integration for reliable delivery
- ⭐ Enterprise webhook testing
- ⭐ Priority support

## 🛠️ Daily Development Workflow

### Normal Development
```bash
# Edit any code - open source or commercial
vim src/cellophanemail/providers/smtp/provider.py        # OSS
vim src/cellophanemail/providers/postmark/provider.py    # Commercial
vim tests/four_horsemen/test_samples.py                  # OSS

# Test everything together (this is the magic!)
pytest tests/integration/

# Commit normally
git add .
git commit -m "feat: improve Four Horsemen accuracy for Korean text"
git push  # 🎉 Auto-syncs to both repos
```

### When You Push to Main
GitHub Actions automatically:
1. **Splits your code** based on file paths
2. **Updates both distribution repos** with appropriate pieces
3. **Builds packages** for PyPI distribution

### Testing Strategy
```bash
# Fast tests (run frequently)
pytest tests/test_integration_minimal.py    # 30 seconds

# Quality tests (run before important commits)
python tests/test_analysis_quality.py       # 2 minutes, 1 email sample

# Full analysis tests (run weekly/for releases)
FULL_ANALYSIS=true python tests/test_analysis_quality.py  # 10 minutes, all samples
```

## 🧪 Understanding Four Horsemen

### The Psychology Framework
Based on Dr. John Gottman's relationship research - the 4 patterns that predict relationship failure:

1. **Criticism** - "You always..." vs "When you..."
2. **Contempt** - Eye-rolling, name-calling, mockery (most toxic)
3. **Defensiveness** - "It's not my fault because..."
4. **Stonewalling** - Silent treatment, emotional withdrawal

### Our Implementation
```python
# Example of what we detect
email_content = "You're so stupid, you never do anything right"
# → Classification: HARMFUL
# → Horsemen: [CRITICISM, CONTEMPT]
# → Action: BLOCK

email_content = "I noticed the report had some issues. Could we review it together?"
# → Classification: SAFE  
# → Horsemen: []
# → Action: FORWARD
```

### Testing Your Changes
```python
# Quick test
python tests/test_analysis_quality.py

# Test specific patterns
from tests.four_horsemen.test_samples import get_samples_by_horseman, FourHorseman
contempt_samples = get_samples_by_horseman(FourHorseman.CONTEMPT)
```

## 📂 File Organization Rules

### ✅ What Goes to Open Source
- **Core email processing** (`src/cellophanemail/core/`)
- **SMTP & Gmail providers** (`src/cellophanemail/providers/smtp/`, `gmail/`)  
- **Four Horsemen framework** (`src/cellophanemail/features/email_protection/`)
- **All testing tools** (`tests/four_horsemen/`, `test_analysis_quality.py`)
- **User management** (`src/cellophanemail/features/user_accounts/`)

### 🏢 What Goes to Commercial Only
- **Postmark provider** (`src/cellophanemail/providers/postmark/`)
- **Enterprise testing** (`scripts/test_webhook_robustness.py`)
- **Future enterprise providers** (SendGrid, AWS SES, etc.)

### 🎯 Rule of Thumb
- **If it's core functionality** → Open source
- **If it's enterprise convenience** → Commercial
- **Four Horsemen = open source** (our differentiator!)
- **Postmark integration = commercial** (enterprise reliability)

## 🚨 Common Mistakes to Avoid

### ❌ DON'T
```bash
# Don't put commercial code in OSS paths
vim src/cellophanemail/providers/smtp/postmark_helper.py  # ❌ Wrong!

# Don't commit directly to distribution repos
git clone git@github.com:cellophanemail/cellophanemail.git  # ❌ Wrong repo!

# Don't bypass testing
git push  # without running tests ❌
```

### ✅ DO
```bash
# Put commercial code in commercial paths
vim src/cellophanemail/providers/postmark/provider.py  # ✅ Correct!

# Always work in internal repo
git clone git@github.com:cellophanemail/cellophanemail-internal.git  # ✅ Correct!

# Test before pushing
pytest tests/test_integration_minimal.py && git push  # ✅ Correct!
```

## 🧪 Testing Examples

### Test Four Horsemen Detection
```python
# Add a new test sample
from tests.four_horsemen.test_samples import EmailTestSample, ToxicityLevel, FourHorseman

new_sample = EmailTestSample(
    id="test_new_001",
    language="en",
    sender="test@example.com",
    subject="Test Email",
    content="Your proposal is interesting. Could we discuss the timeline?",
    expected_classification=ToxicityLevel.SAFE,
    expected_horsemen=[],
    category="business_communication",
    description="Polite business inquiry"
)

# Test your changes
python tests/test_analysis_quality.py
```

### Test Provider Integration
```python
# Test SMTP provider (open source)
pytest tests/test_integration_minimal.py::TestCodeFunctionality::test_smtp_provider_pipeline

# Test Postmark provider (commercial)
pytest tests/test_integration_minimal.py::TestCodeFunctionality::test_postmark_provider_pipeline
```

## 🔧 Useful Development Commands

### Sync Testing
```bash
# See what would be synced (no changes)
python tools/sync-repos.py --dry-run

# Test sync to local directories
python tools/sync-repos.py --target=both

# Check what ended up where
ls ../cellophanemail-oss/src/cellophanemail/providers/     # Should show: smtp, gmail
ls ../cellophanemail-pro/src/cellophanemail/providers/     # Should show: postmark
```

### Running Tests
```bash
# Super fast (30 seconds)
pytest tests/test_integration_minimal.py

# Quality check (2 minutes, 1 sample)
python tests/test_analysis_quality.py

# Full analysis (10 minutes, all 15 samples)
FULL_ANALYSIS=true python tests/test_analysis_quality.py

# Specific provider tests
pytest tests/unit/test_postmark_webhook_simple.py
```

### Four Horsemen Testing
```bash
# Run comprehensive Four Horsemen evaluation
cd tests/four_horsemen
python test_runner.py

# Quick accuracy check
python -c "
from tests.four_horsemen.test_runner import run_quick_test
import asyncio
result = asyncio.run(run_quick_test())
print(f'Accuracy: {result[\"overall_accuracy\"]:.1%}')
"
```

## 📚 Key Files to Know

### Core Files
- **`src/cellophanemail/features/email_protection/analyzer.py`** - Four Horsemen detection logic
- **`src/cellophanemail/providers/registry.py`** - Provider loading with license checking
- **`tests/four_horsemen/test_samples.py`** - All test cases with ground truth
- **`tests/test_analysis_quality.py`** - Main quality validation

### Configuration
- **`packages/cellophanemail/pyproject.toml`** - Open source package config
- **`packages/cellophanemail-pro/pyproject.toml`** - Commercial package config
- **`tools/sync-repos.py`** - Repository splitting automation

### Automation
- **`.github/workflows/sync-repos.yml`** - Auto-sync GitHub Actions
- **`docs/DEVELOPMENT_WORKFLOW.md`** - Detailed workflow documentation

## 🎯 Your First Contribution

Good first tasks:
1. **Add a test sample** in `tests/four_horsemen/test_samples.py`
2. **Improve accuracy** by tuning patterns in the analyzer
3. **Add Korean language patterns** for better multilingual support
4. **Optimize performance** in the analysis pipeline

## 🆘 Getting Help

### Internal Resources
- **Slack**: #cellophanemail-dev
- **Documentation**: `docs/DEVELOPMENT_WORKFLOW.md`
- **Architecture**: This README.md

### External Resources  
- **Four Horsemen Research**: Dr. John Gottman's relationship studies
- **Toxic Communication**: Academic papers on online toxicity detection
- **Psychology Patterns**: Communication psychology research

## 🎉 Welcome to the Team!

You're now ready to work on **CellophoneMail** - the first email protection system based on relationship psychology research!

**Key things to remember:**
- **Work in the internal monorepo** - everything in one place
- **Four Horsemen framework is open source** - our main differentiator  
- **Test your changes** before pushing
- **Trust the automation** - it handles distribution for you

**Your first week goals:**
- [ ] Run all tests successfully
- [ ] Understand the Four Horsemen framework
- [ ] Make a small improvement or add a test
- [ ] See the sync workflow in action

**Happy coding!** 🚀