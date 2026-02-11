"""Pytest configuration for CellophoneMail tests."""

import os
import sys
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env.test for testing
env_path = Path(__file__).parent.parent / ".env.test"
load_dotenv(env_path)

# Set testing mode
os.environ["TESTING"] = "true"

# CRITICAL: Set staging environment BEFORE any app imports
# This must happen before settings.py is imported
os.environ["STAGING"] = "true"

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Now safe to import app components
from litestar.testing import AsyncTestClient
from cellophanemail.app import create_app


@pytest_asyncio.fixture(scope="function")
async def test_client() -> AsyncGenerator[AsyncTestClient, None]:
    """Create a test client for the application."""
    # Ensure staging flag is set before creating app
    os.environ["STAGING"] = "true"
    
    # Clear settings cache to ensure testing flag is picked up
    from cellophanemail.config.settings import get_settings
    get_settings.cache_clear()
    
    app = create_app()
    async with AsyncTestClient(app=app) as client:
        yield client


@pytest.fixture(autouse=True)
def set_staging_env():
    """Automatically set staging environment for all tests."""
    # STAGING is already set at module level, but ensure it stays set
    os.environ["STAGING"] = "true"

    # Clear settings cache to ensure staging flag is picked up
    from cellophanemail.config.settings import get_settings
    get_settings.cache_clear()

    yield
    # Don't delete STAGING - keep it for the whole test session
