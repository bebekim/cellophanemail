"""
Webhook Signature Validation System for Privacy-Focused Email Processing

Provides secure webhook validation with HMAC signatures, replay attack prevention,
and comprehensive validation reporting for email service integrations.
"""

import hmac
import hashlib
import time
import json
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from contextlib import contextmanager
import logging
import threading

logger = logging.getLogger(__name__)


@dataclass
class WebhookSignature:
    """Webhook signature data."""
    algorithm: str
    signature: str
    timestamp: Optional[float] = None
    
    def to_header_value(self) -> str:
        """Convert to HTTP header format."""
        if self.timestamp:
            return f"{self.algorithm}={self.signature},t={int(self.timestamp)}"
        return f"{self.algorithm}={self.signature}"
    
    @classmethod
    def from_header_value(cls, header_value: str) -> 'WebhookSignature':
        """Parse from HTTP header format."""
        parts = header_value.split(',')
        algorithm = None
        signature = None
        timestamp = None
        
        for part in parts:
            key, value = part.split('=', 1)
            if key == 'sha256':
                algorithm = 'sha256'
                signature = value
            elif key == 't':
                timestamp = float(value)
        
        return cls(algorithm=algorithm or 'sha256', signature=signature, timestamp=timestamp)


@dataclass
class ValidationResult:
    """Result of webhook validation."""
    is_valid: bool
    error_message: Optional[str] = None
    signature_verified: bool = False
    timestamp_valid: bool = True
    computed_signature: Optional[str] = None
    
    def __post_init__(self):
        """Ensure consistent state."""
        if self.is_valid:
            self.signature_verified = True
            self.error_message = None


class WebhookValidator:
    """
    Secure webhook signature validation with replay attack prevention.
    
    Features:
    - HMAC-SHA256 signature verification
    - Timestamp-based replay attack prevention
    - Configurable tolerance windows
    - Detailed validation reporting
    - Support for multiple webhook secrets
    """
    
    def __init__(self, webhook_secret: str, tolerance_seconds: int = 300, 
                 algorithm: str = "sha256", max_payload_size: int = 10485760,
                 enable_performance_logging: bool = False):
        """
        Initialize webhook validator with enhanced security and performance features.
        
        Args:
            webhook_secret: Secret key for HMAC signing
            tolerance_seconds: Time tolerance for timestamp validation (default 5 minutes)
            algorithm: Hash algorithm (default sha256)
            max_payload_size: Maximum payload size in bytes (default 10MB)
            enable_performance_logging: Enable detailed performance logging
        """
        self.webhook_secret = webhook_secret.encode('utf-8')
        self.tolerance_seconds = tolerance_seconds
        self.algorithm = algorithm
        self.max_payload_size = max_payload_size
        self.enable_performance_logging = enable_performance_logging
        
        # Signature replay prevention
        self._processed_signatures: Dict[str, float] = {}  # Signature -> timestamp
        self._max_cached_signatures = 1000
        self._lock = threading.RLock()
        
        # Performance tracking
        self._stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'replay_attempts': 0,
            'expired_timestamps': 0,
            'signature_errors': 0,
            'payload_too_large': 0
        }
        
        # Key rotation support
        self._key_rotation_log: List[Dict[str, Any]] = []
        
        logger.info(f"WebhookValidator initialized: algorithm={algorithm}, tolerance={tolerance_seconds}s, "
                   f"max_payload={max_payload_size/1048576:.1f}MB")
    
    def create_signature(self, payload: bytes, timestamp: Optional[float] = None) -> WebhookSignature:
        """
        Create HMAC signature for webhook payload.
        
        Args:
            payload: Raw webhook payload bytes
            timestamp: Optional timestamp (uses current time if not provided)
            
        Returns:
            WebhookSignature object with algorithm, signature, and timestamp
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Create signature payload: timestamp + payload
        signature_payload = f"{int(timestamp)}.".encode('utf-8') + payload
        
        # Generate HMAC signature
        signature_hash = hmac.new(
            self.webhook_secret,
            signature_payload,
            hashlib.sha256
        ).hexdigest()
        
        return WebhookSignature(
            algorithm=self.algorithm,
            signature=signature_hash,
            timestamp=timestamp
        )
    
    def validate_signature(self, payload: bytes, signature_header: str) -> ValidationResult:
        """
        Validate webhook signature with enhanced security and performance tracking.
        
        Args:
            payload: Raw webhook payload bytes
            signature_header: HTTP header value containing signature
            
        Returns:
            ValidationResult with detailed validation information
        """
        validation_start = time.time()
        
        try:
            with self._lock:
                self._stats['total_validations'] += 1
                
                # Check payload size
                if len(payload) > self.max_payload_size:
                    self._stats['payload_too_large'] += 1
                    self._stats['failed_validations'] += 1
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"Payload too large: {len(payload)} > {self.max_payload_size} bytes",
                        signature_verified=False
                    )
                
                # Parse signature header
                try:
                    webhook_sig = WebhookSignature.from_header_value(signature_header)
                except Exception as e:
                    self._stats['signature_errors'] += 1
                    self._stats['failed_validations'] += 1
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"Invalid signature header format: {str(e)}",
                        signature_verified=False
                    )
                
                # Validate timestamp if present
                current_time = time.time()
                if webhook_sig.timestamp:
                    time_diff = abs(current_time - webhook_sig.timestamp)
                    if time_diff > self.tolerance_seconds:
                        self._stats['expired_timestamps'] += 1
                        self._stats['failed_validations'] += 1
                        return ValidationResult(
                            is_valid=False,
                            error_message=f"Timestamp expired: {time_diff}s > {self.tolerance_seconds}s tolerance",
                            signature_verified=False,
                            timestamp_valid=False
                        )
                    
                    # Check for replay attacks
                    signature_key = f"{webhook_sig.signature}:{int(webhook_sig.timestamp)}"
                    if signature_key in self._processed_signatures:
                        self._stats['replay_attempts'] += 1
                        self._stats['failed_validations'] += 1
                        return ValidationResult(
                            is_valid=False,
                            error_message="Signature replay detected",
                            signature_verified=False,
                            timestamp_valid=False
                        )
                
                # Compute expected signature - use the original timestamp from header
                expected_signature = self.create_signature(payload, webhook_sig.timestamp or current_time)
                
                # Verify signature using constant-time comparison
                signature_valid = hmac.compare_digest(
                    webhook_sig.signature,
                    expected_signature.signature
                )
                
                if signature_valid:
                    # Record signature to prevent replay
                    if webhook_sig.timestamp:
                        signature_key = f"{webhook_sig.signature}:{int(webhook_sig.timestamp)}"
                        self._processed_signatures[signature_key] = current_time
                        self._cleanup_old_signatures()
                    
                    self._stats['successful_validations'] += 1
                    
                    result = ValidationResult(
                        is_valid=True,
                        signature_verified=True,
                        computed_signature=expected_signature.signature
                    )
                else:
                    self._stats['signature_errors'] += 1
                    self._stats['failed_validations'] += 1
                    
                    result = ValidationResult(
                        is_valid=False,
                        error_message="Signature verification failed",
                        signature_verified=False,
                        computed_signature=expected_signature.signature
                    )
                
                # Performance logging
                validation_time = (time.time() - validation_start) * 1000
                if self.enable_performance_logging:
                    logger.debug(f"Webhook validation completed in {validation_time:.2f}ms, "
                               f"result={'PASS' if result.is_valid else 'FAIL'}")
                
                return result
        
        except Exception as e:
            self._stats['failed_validations'] += 1
            logger.error(f"Webhook validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}",
                signature_verified=False
            )
    
    def _cleanup_old_signatures(self):
        """Remove old processed signatures to prevent memory leaks."""
        if len(self._processed_signatures) <= self._max_cached_signatures:
            return
        
        current_time = time.time()
        cutoff_time = current_time - (self.tolerance_seconds * 2)  # Keep extra buffer
        
        # Remove old signatures
        old_keys = [
            key for key, timestamp in self._processed_signatures.items()
            if timestamp < cutoff_time
        ]
        
        for key in old_keys:
            del self._processed_signatures[key]
        
        # If still too many, keep only the most recent
        if len(self._processed_signatures) > self._max_cached_signatures:
            sorted_sigs = sorted(
                self._processed_signatures.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            self._processed_signatures = dict(sorted_sigs[:self._max_cached_signatures])
    
    def validate_json_webhook(self, json_payload: str, signature_header: str) -> ValidationResult:
        """
        Validate JSON webhook with additional JSON-specific checks.
        
        Args:
            json_payload: JSON string payload
            signature_header: HTTP header value containing signature
            
        Returns:
            ValidationResult with JSON validation included
        """
        # First validate JSON format
        try:
            json.loads(json_payload)
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Invalid JSON payload: {str(e)}",
                signature_verified=False
            )
        
        # Then validate signature
        return self.validate_signature(json_payload.encode('utf-8'), signature_header)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive webhook validator statistics."""
        with self._lock:
            current_time = time.time()
            recent_validations = sum(
                1 for timestamp in self._processed_signatures.values()
                if current_time - timestamp < 3600  # Last hour
            )
            
            # Calculate success rate
            total_validations = self._stats['total_validations']
            success_rate = (self._stats['successful_validations'] / total_validations * 100) if total_validations > 0 else 0
            
            return {
                'configuration': {
                    'algorithm': self.algorithm,
                    'tolerance_seconds': self.tolerance_seconds,
                    'max_payload_size_mb': round(self.max_payload_size / 1048576, 2),
                    'max_cached_signatures': self._max_cached_signatures,
                    'performance_logging_enabled': self.enable_performance_logging
                },
                'performance': {
                    'total_validations': total_validations,
                    'successful_validations': self._stats['successful_validations'],
                    'failed_validations': self._stats['failed_validations'],
                    'success_rate_percent': round(success_rate, 2),
                    'recent_validations_1h': recent_validations
                },
                'security': {
                    'replay_attempts_blocked': self._stats['replay_attempts'],
                    'expired_timestamp_rejections': self._stats['expired_timestamps'],
                    'signature_errors': self._stats['signature_errors'],
                    'payload_size_rejections': self._stats['payload_too_large'],
                    'active_signature_cache_size': len(self._processed_signatures)
                },
                'key_rotation': {
                    'rotations_performed': len(self._key_rotation_log),
                    'last_rotation': self._key_rotation_log[-1] if self._key_rotation_log else None
                }
            }
    
    async def get_stats_async(self) -> Dict[str, Any]:
        """Get statistics asynchronously."""
        return await asyncio.get_event_loop().run_in_executor(None, self.get_stats)
    
    def update_secret(self, new_secret: str, rotation_reason: str = "manual"):
        """
        Update webhook secret with rotation logging and graceful transition.
        
        Args:
            new_secret: New webhook secret
            rotation_reason: Reason for rotation (e.g., "scheduled", "compromise", "manual")
        """
        with self._lock:
            old_secret_hash = hashlib.sha256(self.webhook_secret).hexdigest()[:8]
            
            # Record rotation event
            rotation_event = {
                'timestamp': time.time(),
                'old_secret_hash': old_secret_hash,
                'new_secret_hash': hashlib.sha256(new_secret.encode('utf-8')).hexdigest()[:8],
                'reason': rotation_reason,
                'signatures_cleared': len(self._processed_signatures)
            }
            self._key_rotation_log.append(rotation_event)
            
            # Keep only last 10 rotation events
            if len(self._key_rotation_log) > 10:
                self._key_rotation_log = self._key_rotation_log[-10:]
            
            # Update secret
            self.webhook_secret = new_secret.encode('utf-8')
            
            # Clear processed signatures since they're tied to the old secret
            self._processed_signatures.clear()
            
            logger.info(f"Webhook secret rotated successfully: reason={rotation_reason}, "
                       f"old_hash={old_secret_hash}, new_hash={rotation_event['new_secret_hash']}")
    
    def configure_tolerance(self, tolerance_seconds: int):
        """Update timestamp tolerance configuration."""
        self.tolerance_seconds = tolerance_seconds
        logger.info(f"Webhook timestamp tolerance updated to {tolerance_seconds}s")