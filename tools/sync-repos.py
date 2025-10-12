#!/usr/bin/env python3
"""
Automated repository splitting tool for CellophoneMail.
Splits monorepo into open source and commercial distributions.
"""

import os
import sys
import shlex
import shutil
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Union


class RepoSyncer:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.root_dir = Path(__file__).parent.parent
        
        # Open source files/directories to include
        self.oss_files = [
            "src/cellophanemail/core/",
            "src/cellophanemail/providers/smtp/",
            "src/cellophanemail/providers/gmail/",
            "src/cellophanemail/providers/contracts.py",
            "src/cellophanemail/providers/registry.py",
            "src/cellophanemail/providers/__init__.py",
            "src/cellophanemail/features/email_protection/",
            "src/cellophanemail/features/shield_addresses/",
            "src/cellophanemail/features/user_accounts/",
            "src/cellophanemail/licensing/",
            "src/cellophanemail/config/",
            "src/cellophanemail/middleware/",
            "src/cellophanemail/models/",
            "src/cellophanemail/routes/",
            "src/cellophanemail/services/",
            "src/cellophanemail/app.py",
            "src/cellophanemail/__init__.py",
            "tests/open_source/",
            "tests/test_integration_minimal.py",
            "tests/test_analysis_quality.py",
            "tests/four_horsemen/",
            "tests/test_auth_*.py",
            "tests/unit/",
            "tests/__init__.py",
            "tests/conftest.py",
            "docs/",
            "scripts/run_tests.py",
            "scripts/test_dry_run.py",
            "packages/cellophanemail/",
            "pytest.ini",
            "README.md",
            "LICENSE",
            ".gitignore",
        ]
        
        # Commercial files/directories to include
        self.commercial_files = [
            "src/cellophanemail/providers/postmark/",
            "src/cellophanemail/features/ai_advanced/",
            "src/cellophanemail_pro/",
            "tests/commercial/",
            "packages/cellophanemail-pro/",
            "scripts/test_webhook_robustness.py",
            "LICENSE.commercial",
        ]
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        prefix = "🔍 DRY RUN" if self.dry_run else "🚀 EXEC"
        print(f"[{timestamp}] {prefix} {level}: {message}")
    
    def run_command(self, cmd: Union[str, List[str]], cwd: Optional[Path] = None) -> bool:
        """Run shell command with logging (secure version)."""
        # Convert string commands to lists for security
        if isinstance(cmd, str):
            cmd_list = shlex.split(cmd)
        else:
            cmd_list = cmd

        self.log(f"Running: {' '.join(cmd_list)}")
        if self.dry_run:
            return True

        try:
            result = subprocess.run(
                cmd_list,  # No shell=True - much safer
                cwd=cwd or self.root_dir,
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout:
                self.log(f"Output: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {e}", "ERROR")
            if e.stderr:
                self.log(f"Error: {e.stderr.strip()}", "ERROR")
            return False
    
    def copy_files(self, files: List[str], dest_dir: Path, 
                   exclude_patterns: List[str] = None) -> None:
        """Copy files from source to destination."""
        exclude_patterns = exclude_patterns or []
        
        for file_path in files:
            src = self.root_dir / file_path
            
            # Skip if source doesn't exist
            if not src.exists():
                self.log(f"Skipping non-existent: {file_path}", "WARN")
                continue
            
            # Skip if matches exclude pattern
            if any(pattern in str(src) for pattern in exclude_patterns):
                self.log(f"Excluding: {file_path}")
                continue
            
            dst = dest_dir / file_path
            
            self.log(f"Copying: {src} -> {dst}")
            
            if not self.dry_run:
                # Create parent directories
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                if src.is_file():
                    shutil.copy2(src, dst)
                elif src.is_dir():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst, dirs_exist_ok=True)
    
    def create_oss_readme(self, dest_dir: Path) -> None:
        """Create README for open source repo."""
        readme_content = '''# CellophoneMail 🛡️

Open source email protection with Four Horsemen toxicity detection framework.

## 🚀 Features

- **Four Horsemen Detection**: Advanced toxic email analysis based on relationship psychology
- **SMTP Server**: Self-hosted email protection with built-in analysis
- **Gmail Integration**: OAuth-based Gmail forwarding with real-time protection
- **Shield Addresses**: Anonymous email forwarding with toxicity filtering
- **User Management**: Complete user account system
- **Multilingual Support**: English and Korean toxic pattern detection

## 📦 Installation

```bash
pip install cellophanemail
```

## 🔧 Quick Start

### Self-Hosted SMTP
```bash
# Start SMTP server
cellophanemail smtp --host 0.0.0.0 --port 25

# Configure your email client to use localhost:25
```

### Gmail Integration
```bash
# Set up Gmail OAuth
cellophanemail gmail setup

# Start protection service
cellophanemail serve
```

## 🏢 Commercial Features

For enterprise providers, managed hosting, and priority support, check out [CellophoneMail Pro](https://cellophanemail.com/pro).

| Feature | Open Source | Pro |
|---------|-------------|-----|
| Four Horsemen Detection | ✅ | ✅ |
| SMTP Server | ✅ | ✅ |
| Gmail Integration | ✅ | ✅ |
| Analysis Quality Testing | ✅ | ✅ |
| Postmark Integration | ❌ | ✅ |
| Enterprise Providers | ❌ | ✅ |
| Managed Hosting | ❌ | ✅ |
| Priority Support | ❌ | ✅ |

## 📚 Documentation

- [Self-hosting Guide](https://docs.cellophanemail.com/self-hosting)
- [API Reference](https://docs.cellophanemail.com/api)
- [Gmail Setup](https://docs.cellophanemail.com/gmail)

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

Made with ❤️ by the CellophoneMail team
'''
        
        readme_path = dest_dir / "README.md"
        self.log(f"Creating OSS README: {readme_path}")
        
        if not self.dry_run:
            with open(readme_path, 'w') as f:
                f.write(readme_content)
    
    def create_commercial_readme(self, dest_dir: Path) -> None:
        """Create README for commercial repo."""
        readme_content = '''# CellophoneMail Pro 🛡️✨

Commercial email protection features with enterprise providers and managed hosting.

## 🚀 Pro Features

- **Postmark Integration**: Direct API integration with Postmark for reliable delivery
- **Enterprise Providers**: SendGrid, AWS SES, Azure Email (coming soon)
- **Managed Hosting**: Cloud-hosted Four Horsemen analysis with 99.9% uptime
- **Advanced Analytics**: Detailed toxicity reports and trend analysis
- **Webhook Testing**: Robust endpoint testing and monitoring
- **Priority Support**: Direct access to our engineering team

## 🔧 Built on Open Source

CellophoneMail Pro extends the open source [Four Horsemen detection framework](https://github.com/cellophanemail/cellophanemail) with enterprise-grade providers and managed services.

## 📦 Installation

```bash
# Install both packages
pip install cellophanemail cellophanemail-pro

# Set your license key
export CELLOPHANEMAIL_LICENSE_KEY="your-license-key-here"
```

## 🔧 Configuration

```python
from cellophanemail import CellophoneMail
from cellophanemail_pro import enable_pro_features

# Enable commercial features
app = CellophoneMail()
enable_pro_features(app, license_key="your-key")

# Use Postmark provider
app.add_provider("postmark", api_key="your-postmark-key")
```

## 🏢 License

This software requires a valid commercial license. 
Visit [cellophanemail.com/pricing](https://cellophanemail.com/pricing) to purchase.

## 📞 Support

- Email: support@cellophanemail.com
- Priority Support Portal: https://cellophanemail.com/support
- Documentation: https://docs.cellophanemail.com/pro

---

© 2024 CellophoneMail. All rights reserved.
'''
        
        readme_path = dest_dir / "README.md"
        self.log(f"Creating Pro README: {readme_path}")
        
        if not self.dry_run:
            with open(readme_path, 'w') as f:
                f.write(readme_content)
    
    def sync_to_oss_repo(self, repo_path: str) -> bool:
        """Sync open source files to OSS repository."""
        dest_dir = Path(repo_path)
        
        self.log(f"Syncing to OSS repo: {dest_dir}")
        
        # Clear destination (but preserve .git)
        if not self.dry_run and dest_dir.exists():
            for item in dest_dir.iterdir():
                if item.name != '.git':
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
        
        # Copy OSS files
        self.copy_files(
            self.oss_files, 
            dest_dir,
            exclude_patterns=["postmark", "commercial", "ai_advanced"]
        )
        
        # Create OSS-specific README
        self.create_oss_readme(dest_dir)
        
        # Copy package config
        if not self.dry_run:
            shutil.copy2(
                self.root_dir / "packages/cellophanemail/pyproject.toml",
                dest_dir / "pyproject.toml"
            )
        
        return True
    
    def sync_to_commercial_repo(self, repo_path: str) -> bool:
        """Sync commercial files to commercial repository."""
        dest_dir = Path(repo_path)
        
        self.log(f"Syncing to commercial repo: {dest_dir}")
        
        # Clear destination (but preserve .git)
        if not self.dry_run and dest_dir.exists():
            for item in dest_dir.iterdir():
                if item.name != '.git':
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
        
        # Copy commercial files
        self.copy_files(self.commercial_files, dest_dir)
        
        # Create commercial-specific README
        self.create_commercial_readme(dest_dir)
        
        # Copy package config
        if not self.dry_run:
            shutil.copy2(
                self.root_dir / "packages/cellophanemail-pro/pyproject.toml",
                dest_dir / "pyproject.toml"
            )
        
        return True
    
    def validate_commit_message(self, message: str) -> str:
        """Validate and sanitize commit message."""
        # Remove dangerous shell characters
        dangerous_chars = ['$', '`', '\\', '\n', '\r', ';', '&', '|', '>', '<']
        sanitized = message
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')

        # Truncate to reasonable length
        max_length = 200
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."

        # Ensure not empty after sanitization
        if not sanitized.strip():
            sanitized = "Repository sync"

        return sanitized.strip()

    def commit_and_push(self, repo_path: str, message: str) -> bool:
        """Commit changes and push to remote."""
        repo_dir = Path(repo_path)

        self.log(f"Committing changes in {repo_dir}")

        # Sanitize commit message
        safe_message = self.validate_commit_message(message)

        # Use secure command lists
        commands = [
            ["git", "add", "."],
            ["git", "commit", "-m", safe_message],  # Safe: message as separate argument
            ["git", "push", "origin", "main"]
        ]

        for cmd in commands:
            # Skip commit if no changes (check status first for commit command)
            if cmd[0] == "git" and cmd[1] == "commit":
                # Check if there are changes to commit
                status_result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True
                )
                if not status_result.stdout.strip():
                    self.log("No changes to commit, skipping commit")
                    continue

            if not self.run_command(cmd, repo_dir):
                # Don't fail if commit has no changes
                if cmd[0] == "git" and cmd[1] == "commit":
                    self.log("Commit failed (likely no changes), continuing")
                    continue
                return False

        return True


def main():
    parser = argparse.ArgumentParser(description="Sync CellophoneMail repositories")
    parser.add_argument("--target", choices=["oss", "commercial", "both"], 
                       default="both", help="Target repository to sync")
    parser.add_argument("--oss-repo", default="../cellophanemail-oss",
                       help="Path to OSS repository")
    parser.add_argument("--commercial-repo", default="../cellophanemail-pro",
                       help="Path to commercial repository")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without executing")
    parser.add_argument("--commit-message", default=None,
                       help="Commit message (uses git SHA if not provided)")
    
    args = parser.parse_args()
    
    # Get commit message
    if args.commit_message:
        commit_msg = args.commit_message
    else:
        git_sha = os.getenv("GITHUB_SHA", "manual-sync")[:8]
        commit_msg = f"Sync from internal repo: {git_sha}"
    
    syncer = RepoSyncer(dry_run=args.dry_run)
    
    success = True
    
    if args.target in ["oss", "both"]:
        syncer.log("Starting OSS sync...")
        if syncer.sync_to_oss_repo(args.oss_repo):
            if not args.dry_run:
                success &= syncer.commit_and_push(args.oss_repo, commit_msg)
        else:
            success = False
    
    if args.target in ["commercial", "both"]:
        syncer.log("Starting commercial sync...")
        if syncer.sync_to_commercial_repo(args.commercial_repo):
            if not args.dry_run:
                success &= syncer.commit_and_push(args.commercial_repo, commit_msg)
        else:
            success = False
    
    if success:
        syncer.log("✅ Sync completed successfully!")
    else:
        syncer.log("❌ Sync failed!", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()