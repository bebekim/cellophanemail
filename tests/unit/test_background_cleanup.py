"""
TDD CYCLE 4 - RED PHASE: Test background cleanup of expired emails from memory
This should fail initially because no cleanup task exists yet
"""
import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from cellophanemail.features.email_protection.memory_manager import MemoryManager
from cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
from cellophanemail.features.email_protection.background_cleanup import BackgroundCleanupService


class TestBackgroundCleanup:
    """Test automated cleanup of expired emails from memory"""
    
    @pytest.mark.asyncio
    async def test_background_cleanup_removes_expired_emails(self):
        """
        RED TEST: Background cleanup should remove emails older than 5 minutes
        """
        memory_manager = MemoryManager(capacity=100)
        cleanup_service = BackgroundCleanupService(memory_manager)
        
        # Create expired email (using 5 minute TTL)
        expired_email = EphemeralEmail(
            message_id="expired-001",
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            subject="Old email",
            text_body="This should be cleaned up",
            user_email="user@example.com",
            ttl_seconds=300  # 5 minutes
        )
        # Manually set creation time to make it expired (6 minutes ago)
        expired_email._created_at = time.time() - 360  # 6 minutes ago
        
        # Create fresh email (2 minutes old) 
        fresh_email = EphemeralEmail(
            message_id="fresh-001", 
            from_address="sender2@example.com",
            to_addresses=["recipient2@example.com"],
            subject="Recent email",
            text_body="This should remain",
            user_email="user2@example.com",
            ttl_seconds=300  # 5 minutes
        )
        # Manually set creation time to make it fresh (2 minutes ago)
        fresh_email._created_at = time.time() - 120  # 2 minutes ago
        
        # Add emails to memory
        await memory_manager.store_email_safe(expired_email)
        await memory_manager.store_email_safe(fresh_email)
        
        # Verify both emails are in memory
        assert len(await memory_manager.get_all_emails()) == 2
        assert await memory_manager.get_email_safe("expired-001") is not None
        assert await memory_manager.get_email_safe("fresh-001") is not None
        
        # Run cleanup
        cleaned_count = await cleanup_service.cleanup_expired_emails()
        
        # Verify expired email was removed, fresh email remains
        assert cleaned_count == 1, "Should have cleaned up 1 expired email"
        assert await memory_manager.get_email_safe("expired-001") is None, "Expired email should be removed"
        assert await memory_manager.get_email_safe("fresh-001") is not None, "Fresh email should remain"
        assert len(await memory_manager.get_all_emails()) == 1
    
    @pytest.mark.asyncio
    async def test_background_cleanup_handles_empty_memory(self):
        """
        RED TEST: Cleanup should handle empty memory gracefully
        """
        memory_manager = MemoryManager(capacity=100)
        cleanup_service = BackgroundCleanupService(memory_manager)
        
        # Run cleanup on empty memory
        cleaned_count = await cleanup_service.cleanup_expired_emails()
        
        assert cleaned_count == 0, "Should clean 0 emails from empty memory"
        assert len(await memory_manager.get_all_emails()) == 0
    
    @pytest.mark.asyncio
    async def test_background_cleanup_respects_ttl_grace_period(self):
        """
        RED TEST: Cleanup should respect TTL + grace period before removing emails
        """
        memory_manager = MemoryManager(capacity=100)
        cleanup_service = BackgroundCleanupService(memory_manager, grace_period_minutes=2)
        
        # Create email that's expired but within grace period (6 minutes old, 5 min TTL, 2 min grace)
        borderline_email = EphemeralEmail(
            message_id="borderline-001",
            from_address="sender@example.com", 
            to_addresses=["recipient@example.com"],
            subject="Borderline email",
            text_body="Within grace period",
            user_email="user@example.com",
            ttl_seconds=300  # 5 minutes
        )
        # 6 minutes ago - expired but within grace period
        borderline_email._created_at = time.time() - 360  
        
        # Create email that's truly expired (beyond grace period - 8 minutes old)
        truly_expired_email = EphemeralEmail(
            message_id="truly-expired-001",
            from_address="sender2@example.com",
            to_addresses=["recipient2@example.com"], 
            subject="Very old email",
            text_body="Beyond grace period",
            user_email="user2@example.com",
            ttl_seconds=300  # 5 minutes
        )
        # 8 minutes ago - beyond grace period
        truly_expired_email._created_at = time.time() - 480
        
        await memory_manager.store_email_safe(borderline_email)
        await memory_manager.store_email_safe(truly_expired_email)
        
        # Run cleanup
        cleaned_count = await cleanup_service.cleanup_expired_emails()
        
        # Only truly expired email should be removed
        assert cleaned_count == 1, "Should clean only 1 truly expired email"
        assert await memory_manager.get_email_safe("borderline-001") is not None, "Borderline email should remain in grace period"
        assert await memory_manager.get_email_safe("truly-expired-001") is None, "Truly expired email should be removed"
    
    @pytest.mark.asyncio 
    async def test_background_cleanup_logs_operations(self):
        """
        RED TEST: Cleanup should log operations for monitoring
        """
        memory_manager = MemoryManager(capacity=100)
        cleanup_service = BackgroundCleanupService(memory_manager)
        
        # Create expired email
        expired_email = EphemeralEmail(
            message_id="logging-test-001",
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            subject="Test email",
            text_body="Content",
            user_email="user@example.com",
            ttl_seconds=300  # 5 minutes
        )
        # 6 minutes ago - expired
        expired_email._created_at = time.time() - 360
        
        await memory_manager.store_email_safe(expired_email)
        
        with patch('cellophanemail.features.email_protection.background_cleanup.logger') as mock_logger:
            cleaned_count = await cleanup_service.cleanup_expired_emails()
            
            # Verify cleanup was logged (privacy-safe - no content details)
            assert cleaned_count == 1
            mock_logger.info.assert_called_with(f"Background cleanup completed: removed 1 expired emails from memory")
    
    @pytest.mark.asyncio
    async def test_background_cleanup_scheduled_task_integration(self):
        """
        RED TEST: Cleanup should integrate with Litestar background tasks
        """
        # This tests the Litestar integration layer
        memory_manager = MemoryManager(capacity=100)
        cleanup_service = BackgroundCleanupService(memory_manager)
        
        # Mock Litestar background task scheduler
        with patch('cellophanemail.features.email_protection.background_cleanup.schedule_cleanup_task') as mock_scheduler:
            # Start scheduled cleanup (should run every 60 seconds)
            await cleanup_service.start_scheduled_cleanup()
            
            # Verify scheduler was called with correct interval
            mock_scheduler.assert_called_once_with(interval_seconds=60, cleanup_service=cleanup_service)
    
    def test_background_cleanup_service_initialization(self):
        """
        RED TEST: BackgroundCleanupService should initialize properly
        """
        memory_manager = MemoryManager(capacity=100)
        
        # Default initialization
        cleanup_service = BackgroundCleanupService(memory_manager)
        assert cleanup_service.memory_manager is memory_manager
        assert cleanup_service.grace_period_minutes == 1  # Default grace period
        
        # Custom initialization
        cleanup_service_custom = BackgroundCleanupService(memory_manager, grace_period_minutes=5)
        assert cleanup_service_custom.grace_period_minutes == 5