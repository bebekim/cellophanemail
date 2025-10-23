# Railway Deployment Guide for CellophoneMail

## ✅ Railway Compatibility

**YES - CellophoneMail is fully deployable on Railway!**

Railway provides:
- ✅ Docker deployment support
- ✅ PostgreSQL database add-on
- ✅ Automatic HTTPS/SSL certificates
- ✅ Custom domains
- ✅ Environment variable management
- ✅ Automatic deploys from GitHub
- ✅ Built-in monitoring and logging

---

## 🚀 Quick Deployment Steps

### 1. Prerequisites
- GitHub account with CellophoneMail repository
- Railway account (free tier available)
- API keys (Anthropic, Stripe, Postmark)

### 2. Create Railway Project

**Option A: Deploy from GitHub (Recommended)**
```bash
# 1. Push your code to GitHub
git push origin main

# 2. Go to Railway dashboard
https://railway.app/dashboard

# 3. Click "New Project" → "Deploy from GitHub repo"
# 4. Select your cellophanemail repository
# 5. Railway will detect Dockerfile and build automatically
```

**Option B: Deploy with Railway CLI**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to your GitHub repo
railway link

# Deploy
railway up
```

### 3. Add PostgreSQL Database

```bash
# In Railway dashboard
1. Click your project
2. Click "New" → "Database" → "Add PostgreSQL"
3. Railway automatically sets DATABASE_URL environment variable
```

### 4. Configure Environment Variables

In Railway dashboard, go to your service → "Variables" and add:

#### Required Variables
```bash
# Application
SECRET_KEY=<generate-with-python-secrets>
ENCRYPTION_KEY=<generate-with-fernet>
DEBUG=false
PORT=8000

# Database (automatically set by Railway PostgreSQL)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# AI Services
ANTHROPIC_API_KEY=sk-ant-api03-your-key
AI_PROVIDER=anthropic
AI_MODEL=claude-3-5-sonnet-20241022

# Email Delivery
EMAIL_DELIVERY_METHOD=postmark
POSTMARK_API_TOKEN=your-postmark-token
POSTMARK_FROM_ADDRESS=noreply@yourdomain.com
SMTP_DOMAIN=yourdomain.com

# Billing (Stripe)
STRIPE_API_KEY=sk_live_your-key
STRIPE_WEBHOOK_SECRET=whsec_your-secret

# Security
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### Optional Variables
```bash
REDIS_URL=${{Redis.REDIS_URL}}  # If using Redis add-on
POSTMARK_DRY_RUN=false
PRIVACY_SAFE_LOGGING=true
LLM_ANALYZER_MODE=privacy
```

### 5. Run Database Migrations

After first deployment:

```bash
# Via Railway CLI
railway run piccolo migrations forwards cellophanemail

# Or connect to your deployment
railway shell
uv run piccolo migrations forwards cellophanemail
```

### 6. Configure Custom Domain (Optional)

```bash
# In Railway dashboard
1. Go to your service → "Settings"
2. Scroll to "Domains"
3. Click "Custom Domain"
4. Add your domain: cellophanemail.com
5. Update DNS records as shown
```

---

## 🔧 Railway-Specific Configuration

### Environment Variable References

Railway provides variable references for service-to-service communication:

```bash
# PostgreSQL (automatically set when you add PostgreSQL)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (if added)
REDIS_URL=${{Redis.REDIS_URL}}

# Port (Railway assigns dynamically)
PORT=${{PORT}}
```

### Health Checks

Railway uses the `healthcheckPath` in `railway.toml`:
```toml
[deploy]
healthcheckPath = "/health/"
healthcheckTimeout = 100
```

Our `/health/` endpoint returns:
```json
{
  "status": "healthy",
  "service": "CellophoneMail",
  "version": "1.0.0"
}
```

### Start Command

Railway will use the command from `railway.toml`:
```bash
uv run uvicorn cellophanemail.app:app --host 0.0.0.0 --port $PORT
```

Note: Railway provides `$PORT` dynamically, we bind to it.

---

## 📊 Railway Deployment Architecture

```
┌─────────────────────────────────────────────┐
│           Railway Environment               │
│                                             │
│  ┌──────────────┐     ┌─────────────────┐ │
│  │  App Service │────▶│  PostgreSQL DB  │ │
│  │ (Docker)     │     │  (Managed)      │ │
│  │              │     │                 │ │
│  │ Port: $PORT  │     │ Auto-scaled     │ │
│  └──────────────┘     └─────────────────┘ │
│         │                                   │
│         │                                   │
│  ┌──────▼─────┐       ┌─────────────────┐ │
│  │   HTTPS    │       │  Environment    │ │
│  │ (Automatic)│       │   Variables     │ │
│  └────────────┘       └─────────────────┘ │
│                                             │
│  Custom Domain: cellophanemail.com          │
└─────────────────────────────────────────────┘
```

---

## 💰 Railway Pricing

### Free Tier (Hobby Plan)
- $5 free credit per month
- Suitable for development/testing
- Apps sleep after 30min inactivity

### Pro Plan ($20/month)
- $20 in credits included
- Additional usage billed at:
  - CPU: $0.000231/min
  - RAM: $0.000231/GB/min
  - PostgreSQL: ~$5-10/month
- No sleep
- Custom domains
- Priority support

### Estimated Monthly Cost (Pro)
```
App Service:    $10-15
PostgreSQL DB:  $5-10
Total:          $15-25/month
```

---

## 🔒 Security Considerations for Railway

### 1. Environment Variables
- ✅ All secrets stored encrypted
- ✅ Access via ${{VARIABLE_NAME}}
- ✅ Not visible in logs
- ✅ Separate per environment (dev/staging/prod)

### 2. HTTPS
- ✅ Automatic SSL certificates
- ✅ Enforced HTTPS (no manual setup)
- ✅ Renewed automatically

### 3. Database
- ✅ Private network (not public)
- ✅ Automatic backups
- ✅ Encrypted connections

### 4. Webhooks
Railway provides stable URLs for webhooks:
```
https://your-app.up.railway.app/webhooks/postmark
```

---

## 🚦 CI/CD with Railway

### Automatic Deployments

Railway can automatically deploy on:
- Push to main branch
- Pull request creation
- Manual trigger

Configure in Railway dashboard:
```bash
Settings → Deployments → Deploy Triggers
- Branch: main
- Auto-deploy: ON
```

### Environment-Based Deployments

```bash
# Production
railway up --environment production

# Staging
railway up --environment staging
```

---

## 📝 Post-Deployment Checklist

- [ ] Database migrations run successfully
- [ ] Health check endpoint responds (https://your-app.railway.app/health/)
- [ ] Custom domain configured and SSL active
- [ ] Environment variables all set
- [ ] Stripe webhooks configured with Railway URL
- [ ] Postmark webhooks configured with Railway URL
- [ ] Email delivery tested (send test email)
- [ ] User registration flow tested
- [ ] Billing integration tested
- [ ] Monitoring/alerting configured

---

## 🐛 Troubleshooting

### Build Failures
```bash
# Check build logs
railway logs --deployment

# Check Dockerfile
railway run cat Dockerfile
```

### Database Connection Issues
```bash
# Verify DATABASE_URL is set
railway variables

# Test connection
railway run psql $DATABASE_URL
```

### Port Binding Issues
Make sure your app binds to Railway's $PORT:
```python
# In app.py
port = int(os.environ.get("PORT", 8000))
uvicorn.run("app:app", host="0.0.0.0", port=port)
```

### Migration Issues
```bash
# Run migrations manually
railway shell
uv run piccolo migrations forwards cellophanemail

# Check migration status
railway run uv run piccolo migrations check cellophanemail
```

---

## 🔗 Useful Railway Commands

```bash
# View logs (live)
railway logs

# Open shell in deployment
railway shell

# Run one-off command
railway run <command>

# View environment variables
railway variables

# Link local project to Railway
railway link

# Check status
railway status

# Rollback deployment
railway rollback
```

---

## 📞 Support

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Railway Status**: https://railway.app/status
- **CellophoneMail Issues**: GitHub Issues

---

## ✅ Summary

Railway is an **excellent choice** for deploying CellophoneMail because:

1. **Docker Support** - Uses your existing Dockerfile
2. **Managed PostgreSQL** - No database setup needed
3. **Automatic HTTPS** - SSL certificates handled
4. **Simple Pricing** - Predictable costs, free tier available
5. **GitHub Integration** - Auto-deploy on push
6. **Environment Variables** - Secure secrets management
7. **Zero Downtime** - Rolling deployments
8. **Logs & Monitoring** - Built-in observability

**Deployment time**: ~15 minutes from GitHub to production URL

**Total setup cost**: $15-25/month for production deployment
