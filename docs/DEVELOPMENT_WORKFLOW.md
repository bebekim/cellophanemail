# CellophoneMail Development Workflow

This document describes the monorepo development workflow with automated splitting to open source and commercial distributions.

## 🏗️ Repository Architecture

### Development Repository (This Repo)
- **Private monorepo** containing all code
- **Single source of truth** for development
- **Automated splitting** to distribution repos

### Distribution Repositories
- `cellophanemail/cellophanemail` (Public) - Open source features
- `cellophanemail/cellophanemail-pro` (Private) - Commercial features

## 📁 Directory Structure

```
cellophanemail-internal/
├── src/cellophanemail/
│   ├── core/                    # → Both repos
│   ├── providers/
│   │   ├── smtp/               # → OSS only
│   │   ├── gmail/              # → OSS only
│   │   └── postmark/           # → Commercial only
│   ├── features/
│   │   ├── email_protection/   # → OSS only
│   │   └── ai_advanced/        # → Commercial only (future)
│   └── licensing/              # → OSS only
├── packages/
│   ├── cellophanemail/         # OSS package config
│   └── cellophanemail-pro/     # Commercial package config
├── tests/
│   ├── integration/            # All features (internal only)
│   ├── open_source/           # → OSS repo
│   └── commercial/            # → Commercial repo
└── tools/
    └── sync-repos.py          # Automated splitting script
```

## 🔄 Development Workflow

### 1. Normal Development
Work in this monorepo as usual:

```bash
# Clone the internal monorepo
git clone git@github.com:cellophanemail/cellophanemail-internal.git
cd cellophanemail-internal

# Work on any feature - open source or commercial
vim src/cellophanemail/providers/smtp/provider.py        # OSS feature
vim src/cellophanemail/providers/postmark/provider.py    # Commercial feature

# Test everything together
pytest tests/integration/

# Commit normally
git add .
git commit -m "feat: improve email analysis"
git push
```

### 2. Automated Distribution
When you push to `main`, GitHub Actions automatically:

1. **Splits the code** using `tools/sync-repos.py`
2. **Pushes to distribution repos**:
   - Open source code → `cellophanemail/cellophanemail`
   - Commercial code → `cellophanemail/cellophanemail-pro`
3. **Triggers package builds** for PyPI

### 3. Manual Sync (If Needed)
```bash
# Test sync locally (dry run)
python tools/sync-repos.py --dry-run

# Sync to local test repos
python tools/sync-repos.py --target=both

# Sync only OSS
python tools/sync-repos.py --target=oss

# Sync only commercial
python tools/sync-repos.py --target=commercial
```

## 📦 Package Structure

### Open Source Package (`cellophanemail`)
- **Features**: SMTP server, Gmail integration, basic toxicity detection
- **Installation**: `pip install cellophanemail`
- **License**: MIT
- **Repository**: Public

### Commercial Package (`cellophanemail-pro`)
- **Features**: Postmark integration, AI analysis, premium support
- **Installation**: `pip install cellophanemail cellophanemail-pro`
- **License**: Commercial (requires license key)
- **Repository**: Private

## 🚀 User Installation Experience

### Open Source Users
```bash
pip install cellophanemail
cellophanemail smtp --host 0.0.0.0 --port 25
```

### Commercial Users
```bash
pip install cellophanemail cellophanemail-pro
export CELLOPHANEMAIL_LICENSE_KEY="your-key"
cellophanemail serve
```

## 🧪 Testing Strategy

### Integration Tests (Internal)
Test all features together in this monorepo:
```bash
pytest tests/integration/  # Tests everything together
```

### Distribution Tests
Each distribution repo has its own tests:
```bash
# OSS repo tests
pytest tests/open_source/

# Commercial repo tests  
pytest tests/commercial/
```

## 📋 What Goes Where

### Open Source (`cellophanemail`)
- ✅ Core email processing
- ✅ SMTP server
- ✅ Gmail OAuth integration
- ✅ Basic pattern-based toxicity detection
- ✅ Shield address management
- ✅ User account system
- ✅ Licensing framework (for loading commercial features)

### Commercial (`cellophanemail-pro`)
- ✅ Postmark API integration
- ✅ Advanced AI analysis (Four Horsemen framework)
- ✅ Webhook robustness testing
- 🔄 Future: SendGrid, AWS SES, Azure Email
- 🔄 Future: Advanced sentiment analysis
- 🔄 Future: Threat intelligence feeds

## 🔧 Configuration Files

### Open Source Package
```toml
# packages/cellophanemail/pyproject.toml
[project.entry-points."cellophanemail.providers"]
smtp = "cellophanemail.providers.smtp:SMTPProvider"
gmail = "cellophanemail.providers.gmail:GmailProvider"
```

### Commercial Package
```toml
# packages/cellophanemail-pro/pyproject.toml
[project.entry-points."cellophanemail.providers"]
postmark = "cellophanemail_pro.providers.postmark:PostmarkProvider"

[project.entry-points."cellophanemail.analyzers"]
ai_advanced = "cellophanemail_pro.features.ai:AdvancedAnalyzer"
```

## 🤖 GitHub Actions

### Sync Workflow (`.github/workflows/sync-repos.yml`)
- **Trigger**: Push to `main`
- **Action**: Sync code to distribution repos
- **Requirements**: `REPO_SYNC_TOKEN` secret with repo access

### Distribution Repo Workflows
- **OSS**: Build and publish to PyPI
- **Commercial**: Build and publish to private PyPI

## 🔐 Security Considerations

### Preventing Code Leaks
1. **Automated splitting** ensures commercial code never reaches public repo
2. **Path-based exclusions** in sync script
3. **GitHub Actions restrictions** to internal repo only
4. **License validation** at runtime

### Access Control
- **Internal repo**: Private, team access only
- **OSS repo**: Public, community contributions welcome
- **Commercial repo**: Private, licensed users only

## 🚨 Important Rules

### DO ✅
- Work in this internal monorepo for all development
- Test features together before pushing
- Use the automated sync workflow
- Follow the file organization structure

### DON'T ❌
- Don't commit directly to distribution repos
- Don't put commercial code in OSS-designated paths
- Don't push secrets or license keys
- Don't bypass the sync workflow

## 🆘 Troubleshooting

### Sync Failed
```bash
# Check sync script locally
python tools/sync-repos.py --dry-run

# Check GitHub Actions logs
# Look for repository access issues
```

### Commercial Code in OSS Repo
```bash
# Emergency: Revert the commit
git revert <commit-hash>

# Re-run sync to clean up
python tools/sync-repos.py --target=oss
```

### Tests Failing After Sync
```bash
# Check what was excluded
python tools/sync-repos.py --dry-run --target=oss

# Test both distributions locally
cd ../cellophanemail-oss && pytest
cd ../cellophanemail-pro && pytest
```

## 📚 Related Documentation

- [Sync Script Documentation](../tools/sync-repos.py)
- [Package Configuration](../packages/)
- [GitHub Actions](../.github/workflows/)
- [Contributing Guidelines](CONTRIBUTING.md)

## 🎯 Next Steps

1. **Set up actual GitHub repositories**
2. **Configure GitHub secrets** (`REPO_SYNC_TOKEN`)
3. **Test full workflow** with real repos
4. **Document commercial license management**
5. **Set up PyPI publishing**

---

**Questions?** Contact the development team or check the internal documentation.