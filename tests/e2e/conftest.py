"""E2E test configuration - fixtures for testing against a live staging URL."""

import os

import pytest
import requests


@pytest.fixture(scope="session")
def staging_url():
    """Staging base URL from STAGING_URL env var."""
    url = os.environ.get("STAGING_URL", "https://cellophanemail-staging.up.railway.app")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def http_session():
    """Shared requests session for the test run."""
    session = requests.Session()
    session.headers.update({"User-Agent": "cellophanemail-smoke-tests/1.0"})
    yield session
    session.close()


@pytest.fixture(scope="session", autouse=True)
def staging_available(staging_url, http_session):
    """Skip all E2E tests if staging is unreachable."""
    try:
        resp = http_session.get(f"{staging_url}/health/", timeout=10)
        resp.raise_for_status()
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError):
        pytest.skip(f"Staging unavailable at {staging_url}")
