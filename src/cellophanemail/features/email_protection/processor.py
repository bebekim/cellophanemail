"""
Modern email protection processor using streamlined single-pass architecture.

This replaces the legacy 4-phase pipeline with a high-performance streamlined processor.
"""

from .streamlined_processor import (
    StreamlinedEmailProtectionProcessor,
    create_streamlined_processor,
    EMPIRICAL_THRESHOLDS
)

# Backward compatibility alias - users can still import EmailProtectionProcessor
EmailProtectionProcessor = StreamlinedEmailProtectionProcessor

# Export the streamlined components
__all__ = [
    'EmailProtectionProcessor',
    'StreamlinedEmailProtectionProcessor', 
    'create_streamlined_processor',
    'EMPIRICAL_THRESHOLDS'
]