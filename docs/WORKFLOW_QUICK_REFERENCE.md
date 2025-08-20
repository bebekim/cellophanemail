# CellophoneMail Workflow Quick Reference

## 🚀 Daily Commands

### Development
```bash
# Normal workflow - work in internal repo
vim src/cellophanemail/providers/smtp/provider.py        # OSS code
vim src/cellophanemail/providers/postmark/provider.py    # Commercial code

# Test everything
pytest tests/test_integration_minimal.py    # Fast (30s)
python tests/test_analysis_quality.py       # Quality (2m)

# Commit & push (auto-syncs to both repos)
git add . && git commit -m "feat: message" && git push
```

### Testing
```bash
# Quick tests
pytest tests/test_integration_minimal.py                    # Integration (30s)
python tests/test_analysis_quality.py                       # Quality (1 sample)

# Full tests  
FULL_ANALYSIS=true python tests/test_analysis_quality.py    # All samples (10m)
pytest tests/four_horsemen/                                 # Framework tests
```

### Sync Testing
```bash
python tools/sync-repos.py --dry-run        # Preview changes
python tools/sync-repos.py --target=both    # Test sync locally
```

## 📂 File Organization

### ✅ Open Source (Public)
```
src/cellophanemail/
├── core/                      # Core processing
├── providers/smtp/            # SMTP server
├── providers/gmail/           # Gmail integration  
├── features/email_protection/ # Four Horsemen framework
├── licensing/                 # License checking
└── [models, routes, services, config...]

tests/
├── four_horsemen/            # Complete testing framework
├── test_analysis_quality.py  # Quality validation
└── test_integration_minimal.py # Fast integration
```

### 🏢 Commercial (Private)
```
src/cellophanemail/providers/postmark/     # Postmark integration
scripts/test_webhook_robustness.py         # Enterprise testing
LICENSE.commercial                         # Commercial license
```

## 🎯 Key Rules

### ✅ DO
- Work in `cellophanemail-internal` repo
- Put Four Horsemen in open source paths
- Put Postmark in commercial paths  
- Test before pushing
- Use descriptive commit messages

### ❌ DON'T
- Commit directly to distribution repos
- Put commercial code in OSS paths
- Put OSS code in commercial-only paths
- Push without testing
- Commit secrets or license keys

## 🧪 Four Horsemen Framework

### Detection Patterns
```python
# What we detect
CRITICISM = "You always/never..." + character attacks
CONTEMPT = superiority, mockery, name-calling (most toxic)
DEFENSIVENESS = "It's not my fault...", counter-attacks  
STONEWALLING = silence, withdrawal, "whatever"
```

### Test Samples
```python
from tests.four_horsemen.test_samples import *

# Get samples by type
get_samples_by_classification(ToxicityLevel.HARMFUL)
get_samples_by_horseman(FourHorseman.CONTEMPT)
get_samples_by_language("ko")  # Korean
```

## 🔄 Sync Workflow

### Automatic (GitHub Actions)
```
Push to main → GitHub Actions → Split code → Update both repos → Build packages
```

### Manual (Development)
```bash
python tools/sync-repos.py --target=both
```

### What Goes Where
- **OSS**: SMTP, Gmail, Four Horsemen, core features
- **Commercial**: Postmark, enterprise testing, managed hosting

## 📦 Package Distribution

### Open Source (`cellophanemail`)
```bash
pip install cellophanemail
cellophanemail smtp --port 25  # Self-hosted SMTP
```

### Commercial (`cellophanemail-pro`)  
```bash
pip install cellophanemail cellophanemail-pro
export CELLOPHANEMAIL_LICENSE_KEY="key"
cellophanemail serve  # Enterprise features
```

## 🆘 Troubleshooting

### Sync Issues
```bash
python tools/sync-repos.py --dry-run                    # Check what would sync
ls ../cellophanemail-oss/src/cellophanemail/providers/  # Should show: smtp, gmail
ls ../cellophanemail-pro/src/cellophanemail/providers/  # Should show: postmark
```

### Test Failures
```bash
pytest tests/test_integration_minimal.py -v    # Debug integration
python tests/test_analysis_quality.py          # Check analysis quality
```

### Code in Wrong Repo
```bash
git revert <commit-hash>        # Emergency revert
python tools/sync-repos.py     # Re-sync clean state
```

## 🎯 Business Model Summary

**Open Source Strategy:**
- Four Horsemen framework (differentiator)
- Complete self-hosting solution  
- Real value for developers

**Commercial Strategy:**
- Enterprise providers (Postmark, SendGrid, AWS SES)
- Managed hosting and convenience
- Priority support

**Value Proposition:**
- OSS: Get complete toxicity detection for free
- Pro: Pay for enterprise reliability and support

## 📞 Quick Help

- **Documentation**: `docs/DEVELOPMENT_WORKFLOW.md`
- **Onboarding**: `docs/ONBOARDING.md`  
- **Slack**: #cellophanemail-dev
- **Sync Script**: `python tools/sync-repos.py --help`