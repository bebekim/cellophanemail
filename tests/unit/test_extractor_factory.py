"""Tests for ExtractorFactory — environment-based extractor selection.

STAGING=true → MockExtractor, ANTHROPIC_API_KEY set → AnthropicExtractor,
no key → fallback to MockExtractor.
"""

import os

import pytest

from cellophanemail.features.entity_extraction.anthropic_extractor import (
    AnthropicExtractor,
)
from cellophanemail.features.entity_extraction.extractor_factory import (
    ExtractorFactory,
)
from cellophanemail.features.entity_extraction.extractor_interface import (
    IEntityExtractor,
)
from cellophanemail.features.entity_extraction.mock_extractor import MockExtractor


class TestExtractorFactoryStaging:
    """STAGING=true should return MockExtractor."""

    def test_staging_returns_mock_extractor(self, monkeypatch):
        monkeypatch.setenv("STAGING", "true")
        extractor = ExtractorFactory.create_extractor()
        assert isinstance(extractor, MockExtractor)

    def test_staging_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("STAGING", "True")
        extractor = ExtractorFactory.create_extractor()
        assert isinstance(extractor, MockExtractor)

    def test_staging_accepts_1(self, monkeypatch):
        monkeypatch.setenv("STAGING", "1")
        extractor = ExtractorFactory.create_extractor()
        assert isinstance(extractor, MockExtractor)


class TestExtractorFactoryExplicitType:
    """Explicit type override bypasses environment detection."""

    def test_explicit_mock(self):
        extractor = ExtractorFactory.create_extractor(extractor_type="mock")
        assert isinstance(extractor, MockExtractor)

    def test_explicit_mock_case_insensitive(self):
        extractor = ExtractorFactory.create_extractor(extractor_type="Mock")
        assert isinstance(extractor, MockExtractor)

    def test_explicit_anthropic_with_key(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake")
        extractor = ExtractorFactory.create_extractor(extractor_type="anthropic")
        assert isinstance(extractor, AnthropicExtractor)

    def test_explicit_anthropic_no_key_falls_back(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        extractor = ExtractorFactory.create_extractor(extractor_type="anthropic")
        assert isinstance(extractor, MockExtractor)

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown extractor type"):
            ExtractorFactory.create_extractor(extractor_type="nonexistent")


class TestExtractorFactoryInterface:
    """Factory always returns IEntityExtractor."""

    def test_returns_interface_compliant(self, monkeypatch):
        monkeypatch.setenv("STAGING", "true")
        extractor = ExtractorFactory.create_extractor()
        assert isinstance(extractor, IEntityExtractor)


class TestExtractorFactoryEnvironmentDetection:
    """detect_environment() returns correct environment string."""

    def test_detect_staging(self, monkeypatch):
        monkeypatch.setenv("STAGING", "true")
        assert ExtractorFactory.detect_environment() == "staging"

    def test_detect_production(self, monkeypatch):
        monkeypatch.delenv("STAGING", raising=False)
        monkeypatch.delenv("PRIVACY_MODE", raising=False)
        assert ExtractorFactory.detect_environment() == "production"

    def test_detect_privacy(self, monkeypatch):
        monkeypatch.delenv("STAGING", raising=False)
        monkeypatch.setenv("PRIVACY_MODE", "true")
        assert ExtractorFactory.detect_environment() == "privacy"


class TestExtractorFactoryProduction:
    """Production path: AnthropicExtractor when key present, fallback otherwise."""

    def test_production_with_api_key(self, monkeypatch):
        monkeypatch.delenv("STAGING", raising=False)
        monkeypatch.delenv("PRIVACY_MODE", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake")
        extractor = ExtractorFactory.create_extractor()
        assert isinstance(extractor, AnthropicExtractor)

    def test_production_no_api_key_falls_back(self, monkeypatch):
        monkeypatch.delenv("STAGING", raising=False)
        monkeypatch.delenv("PRIVACY_MODE", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        extractor = ExtractorFactory.create_extractor()
        assert isinstance(extractor, MockExtractor)
