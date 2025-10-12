"""Pytest configuration for unit tests.

Unit tests should be independent of the main application and database.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src directory to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Mock problematic imports before they're loaded
sys.modules['llama_cpp'] = MagicMock()
sys.modules['llama_cpp.llama_cpp'] = MagicMock()


@pytest.fixture(autouse=True)
def mock_settings():
    """Mock Settings to avoid loading .env file in unit tests."""
    from cellophanemail.config.settings import get_settings

    # Create a mock settings object
    mock_settings_obj = MagicMock()
    mock_settings_obj.stripe_api_key = "sk_test_fake_key_for_testing"
    mock_settings_obj.stripe_webhook_secret = "whsec_fake_secret_for_testing"
    mock_settings_obj.database_url = "postgresql://test:test@localhost:5432/test"
    mock_settings_obj.jwt_secret = "test_secret_key_minimum_32_chars_long"
    mock_settings_obj.anthropic_api_key = "sk-test-fake-key"
    mock_settings_obj.postmark_api_key = "test-postmark-key"
    mock_settings_obj.testing = True
    mock_settings_obj.debug = False

    # Patch get_settings to return our mock
    with patch('cellophanemail.config.settings.get_settings', return_value=mock_settings_obj):
        # Also patch it in the stripe_service module
        with patch('cellophanemail.services.stripe_service.get_settings', return_value=mock_settings_obj):
            yield mock_settings_obj
