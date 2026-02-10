"""Smoke test markers."""

import pytest


def pytest_collection_modifyitems(items):
    """Add 'smoke' marker to all tests in this directory."""
    for item in items:
        item.add_marker(pytest.mark.smoke)
