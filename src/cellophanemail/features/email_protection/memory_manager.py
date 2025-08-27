"""MemoryManager for in-memory email storage with capacity limits."""

import asyncio
from typing import Dict, Optional, List
from .ephemeral_email import EphemeralEmail


class MemoryManager:
    """
    Thread-safe manager for in-memory email storage with capacity limits.
    
    Provides temporary storage for EphemeralEmail objects with configurable
    capacity limits and automatic cleanup of expired emails. Designed for
    high-concurrency email processing without persistence.
    
    Features:
    - Configurable capacity limits to prevent memory exhaustion
    - Automatic TTL-based cleanup of expired emails  
    - Thread-safe operations using asyncio locks
    - Memory-efficient storage with minimal overhead
    """
    
    def __init__(self, max_concurrent: int = 100):
        """
        Initialize MemoryManager with capacity limit.
        
        Args:
            max_concurrent: Maximum number of emails to store concurrently (default: 100)
        """
        self.max_concurrent = max_concurrent
        self._emails: Dict[str, EphemeralEmail] = {}
        self._lock = None  # Will be created when needed for async operations
    
    def store_email(self, email: EphemeralEmail) -> bool:
        """
        Store an email in memory (synchronous for simplicity).
        
        Note: This method is synchronous for ease of use in webhook contexts.
        For thread safety in high-concurrency scenarios, use async methods.
        
        Args:
            email: EphemeralEmail instance to store
            
        Returns:
            True if stored successfully, False if at capacity
        """
        if len(self._emails) >= self.max_concurrent:
            return False
        
        self._emails[email.message_id] = email
        return True
    
    def get_email(self, message_id: str) -> Optional[EphemeralEmail]:
        """
        Retrieve an email by message ID (synchronous for simplicity).
        
        Args:
            message_id: Unique identifier of the email
            
        Returns:
            EphemeralEmail if found, None otherwise
        """
        return self._emails.get(message_id)
    
    def _get_lock(self) -> asyncio.Lock:
        """Get or create the async lock."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock
    
    async def store_email_async(self, email: EphemeralEmail) -> bool:
        """
        Thread-safe async version of store_email.
        
        Args:
            email: EphemeralEmail instance to store
            
        Returns:
            True if stored successfully, False if at capacity
        """
        async with self._get_lock():
            if len(self._emails) >= self.max_concurrent:
                return False
            
            self._emails[email.message_id] = email
            return True
    
    async def get_email_async(self, message_id: str) -> Optional[EphemeralEmail]:
        """
        Thread-safe async version of get_email.
        
        Args:
            message_id: Unique identifier of the email
            
        Returns:
            EphemeralEmail if found, None otherwise
        """
        async with self._get_lock():
            return self._emails.get(message_id)
    
    async def cleanup_expired(self) -> int:
        """
        Thread-safe removal of expired emails from memory.
        
        Returns:
            Number of emails cleaned up
        """
        async with self._get_lock():
            expired_ids = []
            
            # Find expired emails
            for message_id, email in self._emails.items():
                if email.is_expired:
                    expired_ids.append(message_id)
            
            # Remove expired emails
            for message_id in expired_ids:
                del self._emails[message_id]
            
            return len(expired_ids)
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get current memory usage statistics.
        
        Returns:
            Dictionary with current email count and capacity info
        """
        return {
            'current_emails': len(self._emails),
            'max_concurrent': self.max_concurrent,
            'available_slots': self.max_concurrent - len(self._emails)
        }