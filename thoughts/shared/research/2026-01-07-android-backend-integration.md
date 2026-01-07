---
date: 2026-01-07T00:00:00+0000
researcher: claude
git_commit: 33134f03ed2054b51eb3d57158657cb2e00521f2
branch: main
repository: cellophanemail
topic: "How should Android app work with CellophoneMail backend?"
tags: [research, android, integration, text-agnostic, multi-channel, sms]
status: complete
last_updated: 2026-01-07
last_updated_by: claude
---

# Research: How Should Android App Work with CellophoneMail Backend?

**Date**: 2026-01-07
**Researcher**: claude
**Git Commit**: 33134f03ed2054b51eb3d57158657cb2e00521f2
**Branch**: main
**Repository**: cellophanemail

## Research Question

How should the Android app (cellophanesms-android) integrate with the CellophoneMail backend? Is CellophoneMail truly text-agnostic (supporting SMS as well as email)?

## Summary

**Yes, CellophoneMail is designed to be text-agnostic**, not email-focused. The architecture has a clear separation between:

1. **Transport Layer** (email-specific) - handles SMTP, Postmark webhooks, email parsing
2. **Analysis Engine** (text-agnostic) - analyzes any text for "Four Horsemen" toxicity patterns

The `analysis_engine` package was explicitly extracted to be **portable and shared between CellophoneMail web and Android app**. The analysis works with any `content: str` input - email body, SMS, chat messages, etc.

## Detailed Findings

### 1. Analysis Engine is Text-Agnostic

**Location**: `src/analysis_engine/`

The analyzer interface explicitly supports any text:

```python
# src/analysis_engine/analyzer.py:19-31
@abstractmethod
async def analyze(self, content: str, sender: str = "") -> AnalysisResult:
    """
    Analyze content for Four Horseman patterns.

    Args:
        content: Text content to analyze (email body, SMS, etc.)  # <-- Note: "SMS, etc."
        sender: Optional sender identifier for context

    Returns:
        AnalysisResult with toxicity assessment
    """
```

**Package purpose** (from `__init__.py`):
```python
# ABOUTME: Portable Four Horseman analysis engine
# ABOUTME: Shared between CellophoneMail web and Android app
```

### 2. Clean Architecture Boundary

| Layer | Location | Email-Specific? |
|-------|----------|-----------------|
| Transport | `providers/postmark/`, `providers/gmail/`, `plugins/smtp/` | Yes |
| Email Parsing | `core/email_message.py` | Yes |
| **Analysis** | `analysis_engine/` | **No - text-agnostic** |
| **Scoring** | `analysis_engine/scoring.py` | **No - text-agnostic** |
| **Decision Logic** | `analysis_engine/decide_action()` | **No - text-agnostic** |

The boundary point:
```
EmailMessage.text_content  -->  IAnalyzer.analyze(content: str)  -->  AnalysisResult
     (email-specific)              (text-agnostic interface)          (generic result)
```

### 3. Multi-Channel Architecture Plan Exists

**Location**: `thoughts/shared/plans/2025-10-11-multi-channel-b2b-saas-architecture.md`

A comprehensive 7-month implementation plan exists for transforming CellophoneMail into a multi-channel B2B SaaS platform supporting:

- **Email** (current - Postmark, Gmail, SMTP)
- **SMS** (planned - Twilio integration)
- **WhatsApp** (future placeholder)

The plan includes:
- Channel-agnostic `Message` model with `channel_type` discriminator
- Twilio provider implementation
- Android app integration for SMS auto-forwarding
- Unified analysis pipeline for all channels

### 4. Current API Endpoints

**Existing routes that Android can use:**

| Endpoint | Method | Purpose | Android-Ready? |
|----------|--------|---------|----------------|
| `POST /auth/login` | POST | User authentication | Yes |
| `POST /auth/register` | POST | User registration | Yes |
| `POST /auth/refresh` | POST | Token refresh | Yes |
| `GET /auth/profile` | GET | Get user profile | Yes |
| `GET /health/` | GET | Health check | Yes |

**Missing routes for Android SMS:**

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `POST /api/v1/sms/analyze` | POST | SMS cloud analysis | Not implemented |
| `POST /api/v1/archive/sync` | POST | Archive sync | Not implemented |
| `GET /api/v1/archive/export/{format}` | GET | Export reports | Not implemented |
| `GET/POST /api/v1/contacts/monitored` | GET/POST | Contact management | Not implemented |

### 5. Android App Architecture (cellophanesms-android)

**Location**: `~/repositories/cellophanesms-android/`

The Android app is designed with:
- **Local LLM First** - On-device analysis for privacy (Gemma 2B / TinyLlama)
- **Cloud Fallback** - Uses backend when local LLM unavailable
- **Background SMS Forwarding** - WorkManager-based processing

The app expects the `analysis_engine` types to match what the backend returns, ensuring consistent analysis across platforms.

### 6. Integration Points

**How Android should connect:**

1. **Authentication**: Use existing `/auth/login` and `/auth/refresh` endpoints with JWT tokens

2. **SMS Analysis** (when local LLM unavailable):
   ```
   POST /api/v1/messages/analyze
   {
     "channel": "sms",
     "from": "+61412345678",
     "content": "SMS text here",
     "timestamp": 1704585600000
   }
   ```

3. **Response Format** (matches `analysis_engine` types):
   ```json
   {
     "message_id": "uuid",
     "toxicity_score": 0.75,
     "threat_level": "high",
     "action": "REDACT_HARMFUL",
     "processed_content": "...",
     "horsemen_detected": [
       {"horseman": "contempt", "confidence": 0.8, "severity": "high"}
     ]
   }
   ```

## Architecture Insights

### Why It's Text-Agnostic by Design

1. **Four Horsemen Framework** - Gottman's relationship patterns apply to any communication, not just email
2. **LLM Analysis** - The prompts work with any text content
3. **Portable Package** - `analysis_engine` was explicitly extracted for cross-platform use
4. **Abstract Interface** - `IAnalyzer` allows different backends (Anthropic cloud, Llama on-device)

### Implementation Priority

To support the Android app, the backend needs:

1. **Phase 1**: Add `POST /api/v1/messages/analyze` endpoint (minimal - 1-2 days)
2. **Phase 2**: Add Twilio provider for server-side SMS (optional - for orgs that want server-based processing)
3. **Phase 3**: Add archive/export endpoints for case file management

## Code References

- `src/analysis_engine/analyzer.py:19-31` - Text-agnostic analyzer interface
- `src/analysis_engine/__init__.py:1-2` - Package purpose statement
- `src/analysis_engine/types.py:51-68` - Pure Pydantic models (no email dependencies)
- `src/analysis_engine/scoring.py:41-67` - Core `decide_action()` function
- `src/cellophanemail/core/email_message.py:9-41` - Email-specific transport layer
- `src/cellophanemail/providers/contracts.py:34-57` - Provider abstraction

## Historical Context (from thoughts/)

- `thoughts/shared/plans/2025-10-11-multi-channel-b2b-saas-architecture.md` - Comprehensive multi-channel SaaS plan
- `thoughts/shared/plans/2026-01-06-analysis-engine-extraction.md` - Analysis engine extraction for portability

## Related Research

- `thoughts/shared/research/2025-09-15-architecture-analysis.md` - Overall system architecture

## Open Questions

1. **Should Android use local-first analysis?** Yes - the app is designed for local LLM with cloud fallback
2. **What API endpoint format?** Recommend `/api/v1/messages/analyze` (channel-agnostic)
3. **Should we implement the full multi-channel plan?** For MVP, just add the analyze endpoint
