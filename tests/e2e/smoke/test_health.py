"""Smoke tests for the health endpoint."""

import time


def test_health_returns_200(staging_url, http_session):
    """Health endpoint should return 200 with JSON status."""
    resp = http_session.get(f"{staging_url}/health/", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") in ("ok", "healthy")


def test_health_response_time(staging_url, http_session):
    """Health endpoint should respond within 5 seconds."""
    start = time.monotonic()
    resp = http_session.get(f"{staging_url}/health/", timeout=10)
    elapsed = time.monotonic() - start
    assert resp.status_code == 200
    assert elapsed < 5, f"Health check took {elapsed:.1f}s (limit: 5s)"


def test_readiness_probe(staging_url, http_session):
    """Readiness probe should return 200."""
    resp = http_session.get(f"{staging_url}/health/ready", timeout=10)
    assert resp.status_code == 200


def test_liveness_probe(staging_url, http_session):
    """Liveness probe should return 200."""
    resp = http_session.get(f"{staging_url}/health/live", timeout=10)
    assert resp.status_code == 200
