"""
Pytest configuration for cellophanemail tests.
"""

import pytest
import asyncio
from typing import Generator, Any


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def real_llm():
    """Provide real LLM analyzer for testing."""
    from src.cellophanemail.features.email_protection.llm_analyzer import SimpleLLMAnalyzer
    return SimpleLLMAnalyzer()


# Mark all async tests with pytest.mark.asyncio automatically
def pytest_collection_modifyitems(items):
    """Automatically mark all async tests."""
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)