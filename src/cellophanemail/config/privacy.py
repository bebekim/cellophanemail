"""Privacy configuration and utilities for CellophoneMail."""

import os
import hashlib
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class PrivacyConfig:
    """Configuration for privacy-safe logging and data handling."""
    
    # Logging privacy settings
    enable_content_logging: bool = False  # Never log email content
    enable_address_logging: bool = False  # Never log email addresses  
    enable_subject_logging: bool = False  # Never log email subjects
    hash_identifiers: bool = True         # Always hash identifiers
    
    # Hash configuration
    hash_salt: str = "cellophanemail-privacy"
    hash_length: int = 12
    
    @classmethod
    def from_environment(cls) -> 'PrivacyConfig':
        """Create privacy config from environment variables."""
        # Privacy is enabled by default - only disabled explicitly
        privacy_enabled = os.getenv('PRIVACY_SAFE_LOGGING', 'true').lower() == 'true'
        
        if privacy_enabled:
            # Full privacy mode - no content logging
            return cls(
                enable_content_logging=False,
                enable_address_logging=False,
                enable_subject_logging=False,
                hash_identifiers=True
            )
        else:
            # Legacy mode - for backward compatibility only
            return cls(
                enable_content_logging=True,  # DEPRECATED
                enable_address_logging=True,  # DEPRECATED
                enable_subject_logging=True,  # DEPRECATED
                hash_identifiers=False
            )
    
    def hash_identifier(self, value: str) -> str:
        """Create a privacy-safe hash of an identifier."""
        if not self.hash_identifiers:
            return value
        
        salted_value = f"{self.hash_salt}:{value}"
        return hashlib.sha256(salted_value.encode()).hexdigest()[:self.hash_length]
    
    def sanitize_log_entry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize a log entry according to privacy settings."""
        sanitized = data.copy()
        
        # Remove content fields if privacy enabled
        if not self.enable_subject_logging:
            sanitized.pop('subject', None)
        
        if not self.enable_address_logging:
            sanitized.pop('from', None)
            sanitized.pop('to', None)
            sanitized.pop('from_address', None)
            sanitized.pop('to_addresses', None)
        
        # Hash identifiers if enabled
        if self.hash_identifiers and 'message_id' in sanitized:
            sanitized['message_id'] = self.hash_identifier(sanitized['message_id'])
        
        return sanitized


# Global privacy configuration instance
PRIVACY_CONFIG = PrivacyConfig.from_environment()