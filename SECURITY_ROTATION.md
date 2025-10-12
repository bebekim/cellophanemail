# Emergency Security Credential Rotation Guide

## ⚠️ IMMEDIATE ACTION REQUIRED

Production credentials have been exposed in version control. Follow these steps immediately:

## Step 1: Rotate All API Keys

### Anthropic API Key
1. Go to: https://console.anthropic.com/account/keys
2. Delete the compromised key starting with `sk-ant-api03-mduogs...`
3. Create a new API key
4. Update your local `.env` file with the new key

### Postmark Tokens
1. Go to: https://account.postmarkapp.com/servers
2. Navigate to your server → API Tokens
3. Revoke tokens:
   - Server Token: `06a5003f-1289-49c3-9f54-67958b6a669e`
   - Account Token: `346ebf22-e177-4128-b674-71889e83088d`
4. Generate new tokens
5. Update your local `.env` file

### Gmail App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Revoke the app password for `goldenfermi@gmail.com`
3. Generate a new app password
4. Update your local `.env` file

### Upstage API Key
1. Go to your Upstage dashboard
2. Revoke key: `up_RtNEYoVCqChugwSNDL7tCZWKRYIm3`
3. Generate a new key
4. Update your local `.env` file

## Step 2: Rotate Database Password

```bash
# Connect to PostgreSQL
psql -U postgres

# Change the password for cellophane_user
ALTER USER cellophane_user WITH PASSWORD 'new-secure-password-here';

# Exit
\q
```

Update your `.env` file with the new database URL.

## Step 3: Generate New Application Secrets

```bash
# Generate new SECRET_KEY (for JWT signing)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate new ENCRYPTION_KEY (for data encryption)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Update these in your `.env` file.

## Step 4: Clean Git History

⚠️ **WARNING**: This will rewrite git history. Coordinate with your team!

```bash
# Remove .env from all commits
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env' \
  --prune-empty --tag-name-filter cat -- --all

# Clean up refs
git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d

# Garbage collect
git gc --prune=now --aggressive

# Force push to remote (COORDINATE WITH TEAM)
git push origin --force --all
git push origin --force --tags
```

## Step 5: Verify New Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in all the new credentials

3. Test the application:
   ```bash
   # Run tests
   pytest tests/

   # Start the application
   ./bin/dev
   ```

4. Verify all services connect successfully

## Step 6: Notify Team

Send this message to your team:

> **Security Alert: Credential Rotation Required**
>
> All API keys and passwords have been rotated due to a security incident.
> Please:
> 1. Pull the latest code
> 2. Copy `.env.example` to `.env`
> 3. Request new credentials from the team lead
> 4. Do NOT use old credentials - they have been revoked
>
> If you have any local branches, rebase them after pulling.

## Prevention Measures

1. **Never commit `.env` files** - Always use `.env.example` as a template
2. **Use secret management** - Consider HashiCorp Vault or AWS Secrets Manager
3. **Enable git pre-commit hooks** - Prevent accidental credential commits
4. **Regular rotation** - Rotate credentials every 90 days
5. **Monitor for exposed secrets** - Use tools like GitGuardian or TruffleHog

## Verification Checklist

- [ ] All API keys rotated and working
- [ ] Database password changed
- [ ] Application secrets regenerated
- [ ] Git history cleaned
- [ ] `.env.example` created with placeholders
- [ ] `.gitignore` updated
- [ ] Application tested with new credentials
- [ ] Team notified
- [ ] Old credentials confirmed revoked

## Need Help?

If you encounter issues during rotation:
1. Keep old credentials active until new ones are confirmed working
2. Test in a development environment first
3. Have a rollback plan ready
4. Document any service-specific rotation steps

Remember: It's better to rotate credentials immediately than to wait for a "convenient" time.