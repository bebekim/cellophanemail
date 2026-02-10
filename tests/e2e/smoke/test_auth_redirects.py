"""Smoke tests for auth-protected routes and webhook endpoints."""

import pytest


PROTECTED_ROUTES = [
    "/api/v1/auth/dashboard",
    "/api/v1/auth/profile",
]


@pytest.mark.parametrize("path", PROTECTED_ROUTES)
def test_protected_route_requires_auth(staging_url, http_session, path):
    """Protected routes should redirect to login or return 401/403."""
    resp = http_session.get(
        f"{staging_url}{path}", timeout=10, allow_redirects=False
    )
    # Accept redirect (302/303) to login, or 401/403
    assert resp.status_code in (
        302, 303, 401, 403
    ), f"{path} returned {resp.status_code}, expected auth challenge"


WEBHOOK_ENDPOINTS = [
    ("/webhooks/postmark", "POST"),
    ("/webhooks/stripe/", "POST"),
]


@pytest.mark.parametrize("path,method", WEBHOOK_ENDPOINTS)
def test_webhook_endpoint_exists(staging_url, http_session, path, method):
    """Webhook endpoints should exist (not 404). 400/405 is acceptable."""
    if method == "POST":
        resp = http_session.post(f"{staging_url}{path}", timeout=10, json={})
    else:
        resp = http_session.get(f"{staging_url}{path}", timeout=10)
    # The endpoint exists as long as it doesn't 404
    assert resp.status_code != 404, f"{path} returned 404 - endpoint not found"
