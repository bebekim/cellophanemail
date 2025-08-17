"""Pytest configuration for CellophoneMail tests."""

import os
import sys
import pytest
from typing import AsyncGenerator
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from litestar.testing import AsyncTestClient
from cellophanemail.app import create_app

# Set testing environment variable
os.environ["TESTING"] = "true"


@pytest.fixture(scope="function")
async def test_client() -> AsyncGenerator[AsyncTestClient, None]:
    """Create a test client for the application."""
    # Ensure testing flag is set before creating app
    os.environ["TESTING"] = "true"
    
    # Clear settings cache to ensure testing flag is picked up
    from cellophanemail.config.settings import get_settings
    get_settings.cache_clear()
    
    app = create_app()
    async with AsyncTestClient(app=app) as client:
        yield client


@pytest.fixture(autouse=True)
def set_testing_env():
    """Automatically set testing environment for all tests."""
    os.environ["TESTING"] = "true"
    
    # Clear settings cache to ensure testing flag is picked up
    from cellophanemail.config.settings import get_settings
    get_settings.cache_clear()
    
    yield
    # Clean up after test
    if "TESTING" in os.environ:
        del os.environ["TESTING"]