"""Singleton MemoryManager for shared use across the application."""

from .memory_manager import MemoryManager

# Global singleton instance
_memory_manager_instance = None


def get_memory_manager() -> MemoryManager:
    """
    Get the shared MemoryManager singleton instance.
    
    This ensures all components use the same memory manager for
    consistent email storage and cleanup.
    
    Returns:
        MemoryManager: Shared memory manager instance
    """
    global _memory_manager_instance
    
    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager(capacity=100)
    
    return _memory_manager_instance


def reset_memory_manager() -> None:
    """
    Reset the memory manager singleton (used for testing).
    """
    global _memory_manager_instance
    _memory_manager_instance = None