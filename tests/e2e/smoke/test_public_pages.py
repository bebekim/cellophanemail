"""Smoke tests for public pages."""

import pytest


PUBLIC_PAGES = [
    ("/", "CellophoneMail"),
    ("/pricing", "pricing"),
    ("/terms", "terms"),
    ("/privacy", "privacy"),
]


@pytest.mark.parametrize("path,expected_text", PUBLIC_PAGES)
def test_public_page_returns_200(staging_url, http_session, path, expected_text):
    """Public pages should return 200 and contain expected content."""
    resp = http_session.get(f"{staging_url}{path}", timeout=10)
    assert resp.status_code == 200, f"{path} returned {resp.status_code}"
    assert expected_text.lower() in resp.text.lower(), (
        f"{path} missing expected text '{expected_text}'"
    )


def test_login_page(staging_url, http_session):
    """Login page should be accessible."""
    resp = http_session.get(f"{staging_url}/api/v1/auth/login", timeout=10)
    assert resp.status_code == 200


def test_register_page(staging_url, http_session):
    """Register page should be accessible."""
    resp = http_session.get(f"{staging_url}/api/v1/auth/register", timeout=10)
    assert resp.status_code == 200
