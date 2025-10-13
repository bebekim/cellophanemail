"""Test helper utilities for creating mock objects and connections."""

from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any, Optional
from litestar.connection import ASGIConnection


def create_mock_asgi_connection(
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    user: Any = None,
    **kwargs
) -> MagicMock:
    """Create a mock ASGI connection for middleware testing.

    Args:
        headers: HTTP headers dictionary
        cookies: Cookie dictionary
        user: Authenticated user object (or None)
        **kwargs: Additional connection attributes

    Returns:
        Mock ASGI connection object
    """
    connection = MagicMock(spec=ASGIConnection)

    # Set up headers with get() method
    headers_dict = headers or {}
    connection.headers = MagicMock()
    connection.headers.get = lambda key, default="": headers_dict.get(key, default)

    # Set up cookies with get() method
    cookies_dict = cookies or {}
    connection.cookies = MagicMock()
    connection.cookies.get = lambda key, default=None: cookies_dict.get(key, default)

    # Set authenticated user
    connection.user = user

    # Add any additional attributes
    for key, value in kwargs.items():
        setattr(connection, key, value)

    return connection


def create_mock_database_query(return_value: Any = None, returns_list: bool = False):
    """Create a mock database query chain.

    Args:
        return_value: Value to return from final query method
        returns_list: Whether query returns a list or single object

    Returns:
        Mock query object with chained methods
    """
    mock_query = MagicMock()

    if returns_list:
        # For queries that return lists
        mock_query.run = AsyncMock(return_value=return_value or [])
    else:
        # For queries that return single objects
        mock_query.first = AsyncMock(return_value=return_value)
        mock_query.run = AsyncMock(return_value=return_value)

    # Support chaining methods
    mock_where = MagicMock(return_value=mock_query)
    mock_select = MagicMock(return_value=mock_where)

    # Attach chaining methods
    mock_query.where = mock_where
    mock_query.select = mock_select

    return mock_query
