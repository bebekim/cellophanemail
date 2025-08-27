"""Background cleanup service for expired ephemeral emails."""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Optional

from .memory_manager import MemoryManager
from .ephemeral_email import EphemeralEmail

logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_CLEANUP_INTERVAL_SECONDS = 60  # Run cleanup every minute
DEFAULT_GRACE_PERIOD_MINUTES = 1      # Allow 1 minute grace period
MAX_CLEANUP_BATCH_SIZE = 100          # Process at most 100 emails per cleanup


class BackgroundCleanupService:
    """
    Service for cleaning up expired ephemeral emails from memory.
    Prevents memory exhaustion by automatically removing emails past their TTL.
    """
    
    def __init__(
        self, 
        memory_manager: MemoryManager, 
        grace_period_minutes: int = DEFAULT_GRACE_PERIOD_MINUTES
    ):
        self.memory_manager = memory_manager
        self.grace_period_minutes = grace_period_minutes
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def cleanup_expired_emails(self) -> int:
        """
        Remove emails that have exceeded their TTL + grace period.
        Uses batch processing for efficiency with large email counts.
        Returns the number of emails cleaned up.
        """
        try:
            all_emails = await self.memory_manager.get_all_emails()
            
            if not all_emails:
                return 0
            
            current_time = time.time()
            grace_period_seconds = self.grace_period_minutes * 60
            expired_ids = []
            
            # Identify expired emails (batch collect)
            for email in all_emails[:MAX_CLEANUP_BATCH_SIZE]:  # Limit batch size
                total_ttl_seconds = email.ttl_seconds + grace_period_seconds
                
                if (current_time - email._created_at) > total_ttl_seconds:
                    expired_ids.append(email.message_id)
            
            # Remove expired emails in batch
            expired_count = 0
            for message_id in expired_ids:
                if await self.memory_manager.remove_email(message_id):
                    expired_count += 1
            
            if expired_count > 0:
                logger.info(f"Background cleanup completed: removed {expired_count} expired emails from memory")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Background cleanup failed: {e}")
            return 0
    
    async def start_scheduled_cleanup(self, interval_seconds: int = DEFAULT_CLEANUP_INTERVAL_SECONDS) -> None:
        """Start scheduled cleanup with configurable interval."""
        await schedule_cleanup_task(interval_seconds=interval_seconds, cleanup_service=self)
    
    def get_stats(self) -> dict:
        """Get cleanup service statistics."""
        return {
            "grace_period_minutes": self.grace_period_minutes,
            "is_running": self._cleanup_task is not None and not self._cleanup_task.done(),
            "max_batch_size": MAX_CLEANUP_BATCH_SIZE
        }
    
    async def stop_scheduled_cleanup(self) -> None:
        """Stop the scheduled cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


async def schedule_cleanup_task(interval_seconds: int, cleanup_service: BackgroundCleanupService) -> None:
    """
    Schedule cleanup to run at regular intervals.
    This integrates with Litestar's background task system.
    """
    cleanup_service._cleanup_task = asyncio.create_task(_cleanup_loop(interval_seconds, cleanup_service))


async def _cleanup_loop(interval_seconds: int, cleanup_service: BackgroundCleanupService) -> None:
    """Internal cleanup loop with proper error handling."""
    logger.info(f"Starting background cleanup loop (interval: {interval_seconds}s)")
    
    while True:
        try:
            await cleanup_service.cleanup_expired_emails()
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("Background cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Background cleanup task error: {e}")
            await asyncio.sleep(interval_seconds)  # Continue despite errors