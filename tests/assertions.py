"""Shared assertion helpers for testing."""

import jwt
from typing import Dict, Any


def assert_valid_jwt_structure(token: str) -> None:
    """Assert that a token has valid JWT structure.

    Args:
        token: JWT token string

    Raises:
        AssertionError: If token structure is invalid
    """
    assert isinstance(token, str), "Token must be a string"
    parts = token.split('.')
    assert len(parts) == 3, f"JWT must have 3 parts (header.payload.signature), got {len(parts)}"


def assert_jwt_contains_claims(token: str, expected_claims: Dict[str, Any]) -> None:
    """Assert that a JWT token contains expected claims.

    Args:
        token: JWT token string
        expected_claims: Dictionary of expected claim key-value pairs

    Raises:
        AssertionError: If claims don't match
    """
    decoded = jwt.decode(token, options={"verify_signature": False})

    for claim_key, expected_value in expected_claims.items():
        assert claim_key in decoded, f"Token missing claim: {claim_key}"
        if expected_value is not None:
            actual_value = decoded[claim_key]
            assert actual_value == expected_value, \
                f"Claim '{claim_key}' mismatch: expected {expected_value}, got {actual_value}"


def assert_valid_email_routing_context(context, should_be_valid: bool = True) -> None:
    """Assert that an EmailRoutingContext has expected validity.

    Args:
        context: EmailRoutingContext object
        should_be_valid: Whether context should represent valid routing

    Raises:
        AssertionError: If context validity doesn't match expectation
    """
    from cellophanemail.services.email_routing_service import EmailRoutingContext

    assert isinstance(context, EmailRoutingContext), \
        f"Expected EmailRoutingContext, got {type(context)}"

    assert context.shield_address is not None, "Context must have shield_address"

    if should_be_valid:
        assert context.is_active_user is True, "Context should indicate active user"
        assert context.user_id is not None, "Valid context must have user_id"
        assert context.user_email is not None, "Valid context must have user_email"
        assert context.error_code is None, "Valid context should not have error_code"
    else:
        assert context.is_active_user is False, "Invalid context should not have active user"
        assert context.error_code is not None, "Invalid context must have error_code"
        assert context.error_message is not None, "Invalid context must have error_message"


def assert_http_error_response(response, expected_status: int, expected_error_key: str = "error") -> None:
    """Assert that an HTTP response is an error with expected structure.

    Args:
        response: HTTP response object
        expected_status: Expected HTTP status code
        expected_error_key: Key containing error message in response JSON

    Raises:
        AssertionError: If response doesn't match expected error structure
    """
    assert response.status_code == expected_status, \
        f"Expected status {expected_status}, got {response.status_code}"

    data = response.json()
    assert expected_error_key in data, \
        f"Response missing '{expected_error_key}' key: {data}"
    assert data[expected_error_key] is not None, \
        f"Error message should not be None"
