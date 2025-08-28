"""
TDD RED PHASE: Email Composition Strategy Tests
Tests for composing emails based on protection actions with proper attribution and transparency.
"""

import pytest
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
from cellophanemail.features.email_protection.in_memory_processor import ProcessingResult, ProtectionAction

# Try to import components (should fail initially - RED phase)
try:
    from cellophanemail.features.email_protection.email_composition_strategy import (
        EmailCompositionStrategy,
        EmailComposition,
        DeliveryConfiguration
    )
    COMPOSITION_AVAILABLE = True
except ImportError:
    COMPOSITION_AVAILABLE = False


class TestEmailCompositionStrategy:
    """Test email composition strategy for different protection actions."""
    
    def test_composition_modules_exist(self):
        """
        RED TEST: Email composition modules should exist
        """
        assert COMPOSITION_AVAILABLE, \
            "EmailCompositionStrategy modules must exist"
    
    @pytest.mark.skipif(not COMPOSITION_AVAILABLE, reason="Composition modules not available")
    def test_compose_forward_clean_email(self):
        """
        RED TEST: Should compose clean forwarded email with transparency footer
        """
        # Create test data
        original_email = EphemeralEmail(
            message_id="test-001",
            from_address="alice@example.com",
            to_addresses=["user@example.com"],
            subject="Project Update",
            text_body="Meeting at 3pm tomorrow",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        processing_result = ProcessingResult(
            action=ProtectionAction.FORWARD_CLEAN,
            toxicity_score=0.15,
            processed_content="Meeting at 3pm tomorrow",
            requires_delivery=True,
            delivery_targets=["user@example.com"],
            processing_time_ms=150
        )
        
        config = DeliveryConfiguration(
            service_domain="cellophanemail.com",
            add_transparency_headers=True
        )
        
        strategy = EmailCompositionStrategy()
        
        # Test composition
        composition = strategy.compose_email(processing_result, original_email, config)
        
        # Assertions
        assert isinstance(composition, EmailComposition)
        assert composition.subject == "Project Update"
        assert "Meeting at 3pm tomorrow" in composition.body
        assert "Protected by CellophoneMail" in composition.body
        assert composition.from_address == "noreply@cellophanemail.com"
        assert composition.reply_to == "alice@example.com"
        assert composition.headers["X-Original-From"] == "alice@example.com"
        assert composition.headers["X-Protection-Action"] == "forward_clean"
        assert "X-Toxicity-Score" in composition.headers
    
    @pytest.mark.skipif(not COMPOSITION_AVAILABLE, reason="Composition modules not available")
    def test_compose_redacted_email(self):
        """
        RED TEST: Should compose redacted email with filtering notice
        """
        original_email = EphemeralEmail(
            message_id="test-002",
            from_address="bob@example.com",
            to_addresses=["user@example.com"],
            subject="Urgent Issue",
            text_body="This message had inappropriate content",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        processing_result = ProcessingResult(
            action=ProtectionAction.REDACT_HARMFUL,
            toxicity_score=0.65,
            processed_content="This message had [REDACTED] content",
            requires_delivery=True,
            delivery_targets=["user@example.com"],
            processing_time_ms=200
        )
        
        config = DeliveryConfiguration(
            service_domain="cellophanemail.com",
            add_transparency_headers=True
        )
        
        strategy = EmailCompositionStrategy()
        composition = strategy.compose_email(processing_result, original_email, config)
        
        # Assertions
        assert composition.subject == "[Filtered] Urgent Issue"
        assert "This message had [REDACTED] content" in composition.body
        assert "Content filtered by CellophoneMail" in composition.body
        assert "toxicity: 0.65" in composition.body
        assert composition.from_address == "protection@cellophanemail.com"
        assert composition.reply_to == "bob@example.com"
        assert composition.headers["X-Protection-Action"] == "redact_harmful"
        assert float(composition.headers["X-Toxicity-Score"]) == 0.65
    
    @pytest.mark.skipif(not COMPOSITION_AVAILABLE, reason="Composition modules not available")
    def test_compose_summary_only_email(self):
        """
        RED TEST: Should compose summary-only email with original sender info
        """
        original_email = EphemeralEmail(
            message_id="test-003",
            from_address="charlie@example.com",
            to_addresses=["user@example.com"],
            subject="Long Newsletter",
            text_body="Very long newsletter content...",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        processing_result = ProcessingResult(
            action=ProtectionAction.SUMMARIZE_ONLY,
            toxicity_score=0.25,
            processed_content="Summary: Newsletter about product updates and company news.",
            requires_delivery=True,
            delivery_targets=["user@example.com"],
            processing_time_ms=300
        )
        
        config = DeliveryConfiguration(service_domain="cellophanemail.com")
        
        strategy = EmailCompositionStrategy()
        composition = strategy.compose_email(processing_result, original_email, config)
        
        # Assertions
        assert composition.subject == "[Summary] Long Newsletter"
        assert "Summary: Newsletter about product updates" in composition.body
        assert "Summarized by CellophoneMail" in composition.body
        assert composition.from_address == "summary@cellophanemail.com"
        assert composition.reply_to == "charlie@example.com"
        assert composition.headers["X-Protection-Action"] == "summarize_only"
    
    @pytest.mark.skipif(not COMPOSITION_AVAILABLE, reason="Composition modules not available")
    def test_compose_forward_with_context_email(self):
        """
        RED TEST: Should compose email with warning context
        """
        original_email = EphemeralEmail(
            message_id="test-004",
            from_address="sender@suspicious-domain.com",
            to_addresses=["user@example.com"],
            subject="Important Update",
            text_body="Click this link for updates",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        processing_result = ProcessingResult(
            action=ProtectionAction.FORWARD_WITH_CONTEXT,
            toxicity_score=0.45,
            processed_content="Click this link for updates",
            requires_delivery=True,
            delivery_targets=["user@example.com"],
            processing_time_ms=180
        )
        
        config = DeliveryConfiguration(service_domain="cellophanemail.com")
        
        strategy = EmailCompositionStrategy()
        composition = strategy.compose_email(processing_result, original_email, config)
        
        # Assertions
        assert composition.subject == "[Caution] Important Update"
        assert "Click this link for updates" in composition.body
        assert "CAUTION: This email may contain" in composition.body
        assert composition.from_address == "caution@cellophanemail.com"
        assert composition.reply_to == "sender@suspicious-domain.com"
        assert composition.headers["X-Protection-Action"] == "forward_with_context"
    
    @pytest.mark.skipif(not COMPOSITION_AVAILABLE, reason="Composition modules not available")
    def test_preserve_threading_headers(self):
        """
        RED TEST: Should preserve threading headers for conversation continuity
        """
        original_email = EphemeralEmail(
            message_id="thread-test-001",
            from_address="alice@example.com",
            to_addresses=["user@example.com"],
            subject="Re: Project Discussion",
            text_body="Thanks for the update!",
            user_email="user@example.com",
            ttl_seconds=300,
            message_id_header="<original-123@example.com>",
            in_reply_to="<parent-456@example.com>",
            references="<parent-456@example.com> <grandparent-789@example.com>"
        )
        
        processing_result = ProcessingResult(
            action=ProtectionAction.FORWARD_CLEAN,
            toxicity_score=0.10,
            processed_content="Thanks for the update!",
            requires_delivery=True,
            delivery_targets=["user@example.com"],
            processing_time_ms=120
        )
        
        config = DeliveryConfiguration(
            service_domain="cellophanemail.com",
            preserve_threading=True
        )
        
        strategy = EmailCompositionStrategy()
        composition = strategy.compose_email(processing_result, original_email, config)
        
        # Threading headers should be preserved
        assert composition.headers["Message-ID"] == "<original-123@example.com>"
        assert composition.headers["In-Reply-To"] == "<parent-456@example.com>"
        assert composition.headers["References"] == "<parent-456@example.com> <grandparent-789@example.com>"
    
    @pytest.mark.skipif(not COMPOSITION_AVAILABLE, reason="Composition modules not available")
    def test_transparency_headers_optional(self):
        """
        RED TEST: Should respect transparency headers configuration
        """
        original_email = EphemeralEmail(
            message_id="config-test-001",
            from_address="sender@example.com",
            to_addresses=["user@example.com"],
            subject="Test Message",
            text_body="Test content",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        processing_result = ProcessingResult(
            action=ProtectionAction.FORWARD_CLEAN,
            toxicity_score=0.20,
            processed_content="Test content",
            requires_delivery=True,
            delivery_targets=["user@example.com"],
            processing_time_ms=100
        )
        
        # Test with transparency headers disabled
        config_no_transparency = DeliveryConfiguration(
            service_domain="cellophanemail.com",
            add_transparency_headers=False
        )
        
        strategy = EmailCompositionStrategy()
        composition = strategy.compose_email(processing_result, original_email, config_no_transparency)
        
        # Should not include transparency headers
        assert "X-Protection-Action" not in composition.headers
        assert "X-Toxicity-Score" not in composition.headers
        # But should still have attribution
        assert composition.headers["X-Original-From"] == "sender@example.com"
        assert composition.reply_to == "sender@example.com"
    
    @pytest.mark.skipif(not COMPOSITION_AVAILABLE, reason="Composition modules not available")
    def test_delivery_configuration_data_structure(self):
        """
        RED TEST: DeliveryConfiguration should have expected structure
        """
        config = DeliveryConfiguration(
            sender_type="postmark",
            config={"POSTMARK_API_TOKEN": "test-token"},
            service_domain="cellophanemail.com",
            max_retries=3,
            add_transparency_headers=True,
            preserve_threading=True
        )
        
        assert config.sender_type == "postmark"
        assert config.config["POSTMARK_API_TOKEN"] == "test-token"
        assert config.service_domain == "cellophanemail.com"
        assert config.max_retries == 3
        assert config.add_transparency_headers == True
        assert config.preserve_threading == True
    
    @pytest.mark.skipif(not COMPOSITION_AVAILABLE, reason="Composition modules not available")
    def test_email_composition_data_structure(self):
        """
        RED TEST: EmailComposition should have expected structure
        """
        composition = EmailComposition(
            subject="Test Subject",
            body="Test body content",
            headers={"X-Test": "value"},
            from_address="test@example.com",
            reply_to="original@example.com"
        )
        
        assert composition.subject == "Test Subject"
        assert composition.body == "Test body content"
        assert composition.headers["X-Test"] == "value"
        assert composition.from_address == "test@example.com"
        assert composition.reply_to == "original@example.com"