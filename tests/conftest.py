"""Pytest configuration for CellophoneMail tests."""

import os
import pytest
from typing import AsyncGenerator
from litestar.testing import AsyncTestClient
from cellophanemail.app import create_app

# Set testing environment variable
os.environ["TESTING"] = "true"


@pytest.fixture(scope="function")
async def test_client() -> AsyncGenerator[AsyncTestClient, None]:
    """Create a test client for the application."""
    app = create_app()
    async with AsyncTestClient(app=app) as client:
        yield client


@pytest.fixture(autouse=True)
def set_testing_env():
    """Automatically set testing environment for all tests."""
    os.environ["TESTING"] = "true"
    yield
    # Clean up after test
    if "TESTING" in os.environ:
        del os.environ["TESTING"]