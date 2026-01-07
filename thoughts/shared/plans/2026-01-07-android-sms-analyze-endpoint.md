# Android SMS Analyze Endpoint - Implementation Plan

## Overview

Add a `POST /api/v1/sms/analyze` endpoint to CellophoneMail backend that enables the Android app to use cloud LLM analysis when local on-device LLM is unavailable. This is the MVP integration point between cellophanesms-android and the backend.

## Current State Analysis

### What Exists
- **Text-agnostic analysis engine** at `src/analysis_engine/` - already supports any text content including SMS
- **JWT authentication middleware** at `src/cellophanemail/middleware/jwt_auth.py` - ready to protect new endpoints
- **Analyzer implementations**: `AnthropicAnalyzer` (cloud), `MockAnalyzer` (testing)
- **Response types**: `AnalysisResult`, `HorsemanDetection`, `ThreatLevel` in `analysis_engine/types.py`

### What's Missing
- SMS-specific API route (`/api/v1/sms/analyze`)
- Request/response DTOs matching Android app contract
- Route registration in app factory

### Key Discoveries
- `analysis_engine/analyzer.py:19-31` - `IAnalyzer.analyze(content: str, sender: str)` already accepts any text
- `analysis_engine/types.py:51-68` - `AnalysisResult` contains all fields Android needs
- `middleware/jwt_auth.py:104-117` - `jwt_auth_required` guard ready for use

## Desired End State

After implementation:
1. Android app can call `POST /api/v1/sms/analyze` with SMS text
2. Backend analyzes using Anthropic Claude API (same as email)
3. Response matches Android app's expected contract from `docs/API.md`
4. Endpoint is protected by JWT authentication
5. Processing time and model used are tracked in response

### Verification
- `curl -X POST http://localhost:8000/api/v1/sms/analyze` with valid JWT returns analysis
- Response format matches Android `docs/API.md` contract exactly
- Unauthorized requests return 401

## What We're NOT Doing

- Rate limiting (future enhancement)
- Archive sync endpoints
- Monitored contacts management
- Device registration
- Organization stats
- Database persistence of SMS content (privacy-first)
- New database models

## Implementation Approach

Minimal changes leveraging existing infrastructure:
1. Create new route file for SMS API
2. Define request/response DTOs matching Android contract
3. Wire up existing `IAnalyzer` to process requests
4. Register route in app factory

## Phase 1: Create SMS API Route

### Overview
Add the `/api/v1/sms/analyze` endpoint with proper authentication and response mapping.

### Changes Required:

#### 1. Create Request/Response DTOs
**File**: `src/cellophanemail/routes/sms.py` (new file)

```python
# ABOUTME: SMS analysis API for Android app cloud LLM fallback
# ABOUTME: Leverages existing text-agnostic analysis_engine

from typing import List, Optional

from litestar import Controller, post
from litestar.di import Provide
from litestar.params import Body
from pydantic import BaseModel, Field

from analysis_engine import IAnalyzer
from analysis_engine.types import AnalysisResult, HorsemanDetection
from cellophanemail.middleware.jwt_auth import jwt_auth_required


# Request DTO - matches Android app contract
class SmsAnalyzeRequest(BaseModel):
    """SMS analysis request from Android app."""

    message_text: str = Field(..., min_length=1, max_length=10000)
    sender_phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{7,15}$")
    sender_label: Optional[str] = Field(None, max_length=100)


# Response DTO - matches Android app contract from docs/API.md
class HorsemanDetected(BaseModel):
    """Single horseman detection in response."""

    type: str  # criticism, contempt, defensiveness, stonewalling
    confidence: float
    severity: str  # low, medium, high
    indicators: List[str]


class SmsAnalyzeResponse(BaseModel):
    """SMS analysis response for Android app."""

    toxicity_score: float
    threat_level: str  # safe, low, medium, high, critical
    is_toxic: bool
    horsemen_detected: List[HorsemanDetected]
    filtered_summary: Optional[str] = None
    processing_time_ms: int
    model_used: str


def _map_analysis_to_response(
    analysis: AnalysisResult,
    model_name: str
) -> SmsAnalyzeResponse:
    """Map internal AnalysisResult to Android-compatible response."""
    return SmsAnalyzeResponse(
        toxicity_score=analysis.toxicity_score,
        threat_level=analysis.threat_level.value,
        is_toxic=not analysis.safe,
        horsemen_detected=[
            HorsemanDetected(
                type=h.horseman,
                confidence=h.confidence,
                severity=h.severity,
                indicators=h.indicators,
            )
            for h in analysis.horsemen_detected
        ],
        filtered_summary=analysis.reasoning if not analysis.safe else None,
        processing_time_ms=analysis.processing_time_ms,
        model_used=model_name,
    )


class SmsController(Controller):
    """SMS analysis endpoints for Android app."""

    path = "/api/v1/sms"
    tags = ["SMS"]
    guards = [jwt_auth_required]

    @post("/analyze")
    async def analyze_sms(
        self,
        data: SmsAnalyzeRequest,
        analyzer: IAnalyzer,
    ) -> SmsAnalyzeResponse:
        """
        Analyze SMS text for Four Horsemen toxicity patterns.

        Used by Android app when local LLM is unavailable.
        """
        # Build sender context string
        sender_context = ""
        if data.sender_label:
            sender_context = data.sender_label
        elif data.sender_phone:
            sender_context = data.sender_phone

        # Use existing text-agnostic analyzer
        analysis = await analyzer.analyze(
            content=data.message_text,
            sender=sender_context,
        )

        # Get model name from analyzer (implementation-specific)
        model_name = getattr(analyzer, "model_name", "anthropic-claude")

        return _map_analysis_to_response(analysis, model_name)
```

#### 2. Register Route in App Factory
**File**: `src/cellophanemail/app.py`

**Changes**: Add SmsController to route_handlers

```python
# Add import at top of file
from cellophanemail.routes.sms import SmsController

# In create_app() function, add to route_handlers list:
route_handlers=[
    # ... existing handlers ...
    SmsController,
]
```

#### 3. Add model_name to Analyzers (optional enhancement)
**File**: `src/analysis_engine/anthropic_analyzer.py`

Add `model_name` property to track which model was used:

```python
@property
def model_name(self) -> str:
    """Return the model identifier for response tracking."""
    return self._model  # e.g., "claude-3-5-sonnet-20241022"
```

### Success Criteria:

#### Automated Verification:
- [ ] Server starts without errors: `docker compose up`
- [ ] Type checking passes: `PYTHONPATH=src mypy src/cellophanemail/routes/sms.py`
- [ ] Linting passes: `ruff check src/cellophanemail/routes/sms.py`
- [ ] Unit test passes: `PYTHONPATH=src pytest tests/unit/test_sms_route.py -v`
- [ ] Health check works: `curl http://localhost:8000/health/`

#### Manual Verification:
- [ ] Unauthenticated request returns 401:
  ```bash
  curl -X POST http://localhost:8000/api/v1/sms/analyze \
    -H "Content-Type: application/json" \
    -d '{"message_text": "test"}'
  # Expected: 401 Unauthorized
  ```

- [ ] Authenticated request returns analysis:
  ```bash
  # First login to get token
  TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "password": "testpass"}' \
    | jq -r '.access_token')

  # Then analyze
  curl -X POST http://localhost:8000/api/v1/sms/analyze \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{
      "message_text": "You are completely useless, why did you not call me back?!",
      "sender_phone": "+1234567890",
      "sender_label": "Client - John D."
    }'
  ```

- [ ] Response matches Android contract:
  ```json
  {
    "toxicity_score": 0.78,
    "threat_level": "high",
    "is_toxic": true,
    "horsemen_detected": [...],
    "filtered_summary": "...",
    "processing_time_ms": 1250,
    "model_used": "claude-3-5-sonnet-20241022"
  }
  ```

---

## Phase 2: Add Unit Tests

### Overview
Add unit tests for the new SMS endpoint using MockAnalyzer.

### Changes Required:

#### 1. Create Test File
**File**: `tests/unit/test_sms_route.py` (new file)

```python
"""Unit tests for SMS analysis endpoint."""

import pytest
from litestar.testing import TestClient

from analysis_engine import MockAnalyzer
from cellophanemail.app import create_app


@pytest.fixture
def test_client():
    """Create test client with mock analyzer."""
    app = create_app()
    # Override analyzer dependency with mock
    app.dependency_overrides[IAnalyzer] = lambda: MockAnalyzer()
    return TestClient(app)


@pytest.fixture
def auth_headers(test_client):
    """Get auth headers for authenticated requests."""
    # Create test user and login
    # ... implementation depends on test fixtures
    return {"Authorization": "Bearer test-token"}


class TestSmsAnalyzeEndpoint:
    """Tests for POST /api/v1/sms/analyze."""

    def test_requires_authentication(self, test_client):
        """Unauthenticated requests should return 401."""
        response = test_client.post(
            "/api/v1/sms/analyze",
            json={"message_text": "Hello world"},
        )
        assert response.status_code == 401

    def test_analyzes_toxic_message(self, test_client, auth_headers):
        """Toxic message should return high toxicity score."""
        response = test_client.post(
            "/api/v1/sms/analyze",
            json={
                "message_text": "You're completely useless!",
                "sender_phone": "+1234567890",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_toxic"] is True
        assert data["toxicity_score"] > 0.5
        assert "horsemen_detected" in data

    def test_analyzes_safe_message(self, test_client, auth_headers):
        """Safe message should return low toxicity score."""
        response = test_client.post(
            "/api/v1/sms/analyze",
            json={"message_text": "Thanks for your help today!"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_toxic"] is False
        assert data["toxicity_score"] < 0.3

    def test_validates_message_text_required(self, test_client, auth_headers):
        """Empty message_text should return 400."""
        response = test_client.post(
            "/api/v1/sms/analyze",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_response_matches_android_contract(self, test_client, auth_headers):
        """Response should match Android app expected format."""
        response = test_client.post(
            "/api/v1/sms/analyze",
            json={"message_text": "Test message"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Verify all expected fields present
        assert "toxicity_score" in data
        assert "threat_level" in data
        assert "is_toxic" in data
        assert "horsemen_detected" in data
        assert "processing_time_ms" in data
        assert "model_used" in data

        # Verify types
        assert isinstance(data["toxicity_score"], float)
        assert isinstance(data["threat_level"], str)
        assert isinstance(data["is_toxic"], bool)
        assert isinstance(data["horsemen_detected"], list)
        assert isinstance(data["processing_time_ms"], int)
```

### Success Criteria:

#### Automated Verification:
- [ ] All unit tests pass: `PYTHONPATH=src pytest tests/unit/test_sms_route.py -v`
- [ ] Test coverage for new route: `PYTHONPATH=src pytest tests/unit/test_sms_route.py --cov=cellophanemail.routes.sms`

#### Manual Verification:
- [ ] Tests run in under 5 seconds (no real API calls)

---

## Testing Strategy

### Unit Tests
- Mock the `IAnalyzer` dependency with `MockAnalyzer`
- Test authentication guard (401 for unauthenticated)
- Test request validation (400 for invalid input)
- Test response format matches Android contract
- Test toxic vs safe message detection

### Integration Tests
- Real API call with test user
- Verify Anthropic API integration works
- End-to-end from HTTP request to response

### Manual Testing Steps
1. Start server: `docker compose up`
2. Create test user via `/auth/register`
3. Login via `/auth/login` to get token
4. Call `/api/v1/sms/analyze` with toxic message
5. Verify response matches expected format

## Performance Considerations

- Analysis uses same LLM as email - expect 1-3 second response times
- No database writes (privacy-first - content not persisted)
- Consider adding response caching for repeated identical messages (future)

## Migration Notes

No database migrations required - this endpoint is stateless.

## References

- Android API contract: `/home/yhk/repositories/cellophanesms-android/docs/API.md`
- Existing research: `thoughts/shared/research/2026-01-07-android-backend-integration.md`
- Analysis engine interface: `src/analysis_engine/analyzer.py:19-31`
- JWT auth guard: `src/cellophanemail/middleware/jwt_auth.py:104-117`
