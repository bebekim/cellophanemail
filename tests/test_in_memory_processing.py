"""Tests for in-memory email processing system."""

import time
import pytest
from datetime import datetime, timedelta

# This is our RED phase - these imports will fail until we implement the classes


def test_ephemeral_email_creation():
    """RED TEST: Test basic EphemeralEmail creation with required fields."""
    from src.cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
    
    # Test email creation with minimal required fields
    email = EphemeralEmail(
        message_id="msg-123",
        from_address="sender@example.com",
        to_addresses=["user@example.com"],
        subject="Test",
        text_body="Hello",
        user_email="real@user.com",
        ttl_seconds=300
    )
    
    # Verify basic properties are set correctly
    assert email.message_id == "msg-123"
    assert email.from_address == "sender@example.com"
    assert email.to_addresses == ["user@example.com"]
    assert email.subject == "Test"
    assert email.text_body == "Hello"
    assert email.user_email == "real@user.com"
    assert email.ttl_seconds == 300
    
    # Email should not be expired immediately after creation
    assert not email.is_expired


def test_ephemeral_email_expiration():
    """Test TTL expiration detection."""
    from src.cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
    
    # Create email with very short TTL
    email = EphemeralEmail(
        message_id="msg-456",
        from_address="test@example.com",
        to_addresses=["user@example.com"],
        subject="Expires quickly",
        text_body="This will expire",
        user_email="user@example.com",
        ttl_seconds=0
    )
    
    # Sleep briefly to let it expire
    time.sleep(0.1)
    
    # Should now be expired
    assert email.is_expired


def test_get_content_for_analysis():
    """Test content extraction for LLM analysis."""
    from src.cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
    
    email = EphemeralEmail(
        message_id="msg-789",
        from_address="sender@example.com",
        to_addresses=["user@example.com"],
        subject="Meeting",
        text_body="Please join the meeting",
        user_email="user@example.com",
        ttl_seconds=300
    )
    
    content = email.get_content_for_analysis()
    assert "Subject: Meeting" in content
    assert "Please join the meeting" in content


# Phase 2: MemoryManager Tests

def test_memory_manager_store_and_retrieve():
    """RED TEST: Test basic MemoryManager storage and retrieval."""
    from src.cellophanemail.features.email_protection.memory_manager import MemoryManager
    from src.cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
    
    manager = MemoryManager(max_concurrent=2)
    email = EphemeralEmail(
        message_id="test-1",
        from_address="test@example.com",
        to_addresses=["user@example.com"],
        subject="Test Storage",
        text_body="Test message",
        user_email="user@example.com",
        ttl_seconds=300
    )
    
    # Test storage
    assert manager.store_email(email) == True
    
    # Test retrieval
    retrieved = manager.get_email("test-1")
    assert retrieved == email
    assert retrieved.message_id == "test-1"


def test_memory_manager_capacity_limit():
    """Test that MemoryManager respects capacity limits."""
    from src.cellophanemail.features.email_protection.memory_manager import MemoryManager
    from src.cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
    
    manager = MemoryManager(max_concurrent=2)
    
    email1 = EphemeralEmail(
        message_id="test-1",
        from_address="test@example.com",
        to_addresses=["user@example.com"],
        subject="Test 1",
        text_body="Message 1",
        user_email="user@example.com",
        ttl_seconds=300
    )
    
    email2 = EphemeralEmail(
        message_id="test-2",
        from_address="test@example.com",
        to_addresses=["user@example.com"],
        subject="Test 2",
        text_body="Message 2",
        user_email="user@example.com",
        ttl_seconds=300
    )
    
    email3 = EphemeralEmail(
        message_id="test-3",
        from_address="test@example.com",
        to_addresses=["user@example.com"],
        subject="Test 3",
        text_body="Message 3",
        user_email="user@example.com",
        ttl_seconds=300
    )
    
    # First two should succeed
    assert manager.store_email(email1) == True
    assert manager.store_email(email2) == True
    
    # Third should fail (at capacity)
    assert manager.store_email(email3) == False


@pytest.mark.asyncio
async def test_memory_manager_cleanup_expired():
    """Test that MemoryManager cleans up expired emails."""
    from src.cellophanemail.features.email_protection.memory_manager import MemoryManager
    from src.cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
    
    manager = MemoryManager()
    
    # Create an expired email (TTL = 0)
    expired_email = EphemeralEmail(
        message_id="expired",
        from_address="test@example.com",
        to_addresses=["user@example.com"],
        subject="Expired",
        text_body="This expired",
        user_email="user@example.com",
        ttl_seconds=0
    )
    
    # Create an active email
    active_email = EphemeralEmail(
        message_id="active",
        from_address="test@example.com",
        to_addresses=["user@example.com"],
        subject="Active",
        text_body="This is active",
        user_email="user@example.com",
        ttl_seconds=300
    )
    
    # Store both
    manager.store_email(expired_email)
    manager.store_email(active_email)
    
    # Wait for expiration
    time.sleep(0.1)
    
    # Run cleanup
    cleaned = await manager.cleanup_expired()
    
    # Should have cleaned 1 expired email
    assert cleaned == 1
    assert manager.get_email("expired") is None
    assert manager.get_email("active") is not None


# Phase 3: InMemoryProcessor Tests

@pytest.mark.asyncio
async def test_in_memory_processor_clean_email():
    """RED TEST: Test InMemoryProcessor processing clean email."""
    from src.cellophanemail.features.email_protection.in_memory_processor import InMemoryProcessor
    from src.cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
    from src.cellophanemail.features.email_protection.graduated_decision_maker import ProtectionAction
    
    processor = InMemoryProcessor()
    email = EphemeralEmail(
        message_id="clean-1",
        from_address="sender@example.com",
        to_addresses=["user@example.com"],
        subject="Meeting tomorrow",
        text_body="Let's meet at 2pm",
        user_email="user@example.com",
        ttl_seconds=300
    )
    
    result = await processor.process_email(email)
    
    # Test result structure
    assert hasattr(result, 'action')
    assert hasattr(result, 'toxicity_score')
    assert hasattr(result, 'requires_delivery')
    assert hasattr(result, 'delivery_targets')
    
    # Test clean email behavior
    assert result.action == ProtectionAction.FORWARD_CLEAN
    assert result.toxicity_score < 0.30
    assert result.requires_delivery == True
    assert result.delivery_targets == ["user@example.com"]


@pytest.mark.asyncio
async def test_in_memory_processor_toxic_email():
    """Test InMemoryProcessor processing toxic email."""
    from src.cellophanemail.features.email_protection.in_memory_processor import InMemoryProcessor
    from src.cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
    from src.cellophanemail.features.email_protection.graduated_decision_maker import ProtectionAction
    
    processor = InMemoryProcessor()
    email = EphemeralEmail(
        message_id="toxic-1",
        from_address="sender@example.com",
        to_addresses=["user@example.com"],
        subject="You're terrible",
        text_body="I hate everything about you, you stupid idiot",
        user_email="user@example.com",
        ttl_seconds=300
    )
    
    result = await processor.process_email(email)
    
    # Test toxic email behavior
    assert result.action == ProtectionAction.BLOCK_ENTIRELY
    assert result.toxicity_score > 0.90
    assert result.requires_delivery == False
    assert result.delivery_targets == []


# Phase 4: ImmediateDeliveryManager Tests

@pytest.mark.asyncio
async def test_immediate_delivery_success():
    """RED TEST: Test ImmediateDeliveryManager successful delivery."""
    from src.cellophanemail.features.email_protection.immediate_delivery import ImmediateDeliveryManager
    from src.cellophanemail.features.email_protection.in_memory_processor import ProcessingResult
    from src.cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
    from src.cellophanemail.features.email_protection.graduated_decision_maker import ProtectionAction
    
    delivery_manager = ImmediateDeliveryManager()
    
    # Create a processing result that requires delivery
    processing_result = ProcessingResult(
        action=ProtectionAction.FORWARD_CLEAN,
        toxicity_score=0.1,
        requires_delivery=True,
        delivery_targets=["user@example.com"],
        processed_content="Meeting at 2pm",
        processing_time_ms=150,
        reasoning="Clean content"
    )
    
    email = EphemeralEmail(
        message_id="del-1",
        from_address="sender@example.com",
        to_addresses=["user@example.com"],
        subject="Meeting tomorrow",
        text_body="Let's meet at 2pm",
        user_email="user@example.com",
        ttl_seconds=300
    )
    
    delivery_result = await delivery_manager.deliver_email(processing_result, email)
    
    # Test delivery result structure
    assert hasattr(delivery_result, 'success')
    assert hasattr(delivery_result, 'attempts')
    assert hasattr(delivery_result, 'error_message')
    
    # Test successful delivery
    assert delivery_result.success == True
    assert delivery_result.attempts == 1
    assert delivery_result.error_message is None


@pytest.mark.asyncio
async def test_immediate_delivery_retry_on_failure():
    """Test ImmediateDeliveryManager retry logic on failures."""
    from src.cellophanemail.features.email_protection.immediate_delivery import ImmediateDeliveryManager
    from src.cellophanemail.features.email_protection.in_memory_processor import ProcessingResult
    from src.cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
    from src.cellophanemail.features.email_protection.graduated_decision_maker import ProtectionAction
    
    delivery_manager = ImmediateDeliveryManager(max_retries=3)
    
    # Create a processing result that may fail delivery (not FORWARD_CLEAN)
    processing_result = ProcessingResult(
        action=ProtectionAction.FORWARD_WITH_CONTEXT,
        toxicity_score=0.35,
        requires_delivery=True,
        delivery_targets=["user@example.com"],
        processed_content="Some content with context",
        processing_time_ms=150,
        reasoning="Minor toxicity detected"
    )
    
    email = EphemeralEmail(
        message_id="retry-test",
        from_address="sender@example.com",
        to_addresses=["user@example.com"],
        subject="Test with retries",
        text_body="Test message",
        user_email="user@example.com",
        ttl_seconds=300
    )
    
    delivery_result = await delivery_manager.deliver_email(processing_result, email)
    
    # Should eventually succeed (with retries if needed)
    assert delivery_result.success == True
    assert delivery_result.attempts >= 1
    assert delivery_result.attempts <= 3


@pytest.mark.asyncio
async def test_immediate_delivery_no_delivery_required():
    """Test ImmediateDeliveryManager when no delivery is required."""
    from src.cellophanemail.features.email_protection.immediate_delivery import ImmediateDeliveryManager
    from src.cellophanemail.features.email_protection.in_memory_processor import ProcessingResult
    from src.cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
    from src.cellophanemail.features.email_protection.graduated_decision_maker import ProtectionAction
    
    delivery_manager = ImmediateDeliveryManager()
    
    # Create a processing result that doesn't require delivery (BLOCK_ENTIRELY)
    processing_result = ProcessingResult(
        action=ProtectionAction.BLOCK_ENTIRELY,
        toxicity_score=0.95,
        requires_delivery=False,
        delivery_targets=[],
        processed_content="",
        processing_time_ms=150,
        reasoning="Extreme toxicity - blocked"
    )
    
    email = EphemeralEmail(
        message_id="no-delivery-test",
        from_address="sender@example.com",
        to_addresses=["user@example.com"],
        subject="Blocked email",
        text_body="Blocked content",
        user_email="user@example.com",
        ttl_seconds=300
    )
    
    delivery_result = await delivery_manager.deliver_email(processing_result, email)
    
    # Should succeed immediately without delivery attempts
    assert delivery_result.success == True
    assert delivery_result.attempts == 0
    assert "No delivery required" in delivery_result.error_message