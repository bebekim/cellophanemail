"""
Unified Security Management System for Privacy-Focused Email Processing

Integrates all security components (rate limiting, webhook validation, request validation)
with threat detection, audit logging, and comprehensive security management.
"""

import time
import threading
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

from .rate_limiter import RateLimiter, RateLimitStrategy, RateLimitResult
from .webhook_validator import WebhookValidator, ValidationResult
from .request_validator import RequestValidator, SecurityPolicy, IPWhitelist, ContentValidator

logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """Unified security configuration."""
    rate_limiting_enabled: bool = True
    webhook_signature_validation: bool = True
    ip_whitelisting_enabled: bool = False
    content_validation_enabled: bool = True
    https_required: bool = True
    
    # Rate limiting configuration
    rate_limit_strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    default_rate_limit: int = 60  # requests per minute
    
    # Webhook configuration
    webhook_tolerance_seconds: int = 300
    
    # Request validation
    max_content_length_mb: int = 10
    allowed_content_types: List[str] = field(default_factory=lambda: [
        "application/json", "application/x-www-form-urlencoded"
    ])
    
    # Threat detection
    enable_threat_detection: bool = True
    suspicious_ip_threshold: int = 10
    threat_detection_window_minutes: int = 5


@dataclass
class ThreatDetection:
    """Threat analysis result."""
    client_ip: str
    threat_level: str  # low, medium, high, critical
    should_block: bool
    detected_patterns: List[str]
    failed_attempts: int
    time_window_start: float
    confidence_score: float
    
    def __post_init__(self):
        """Calculate derived properties."""
        if self.confidence_score > 0.8:
            self.threat_level = "critical"
            self.should_block = True
        elif self.confidence_score > 0.6:
            self.threat_level = "high"
            self.should_block = True
        elif self.confidence_score > 0.4:
            self.threat_level = "medium"
            self.should_block = False
        else:
            self.threat_level = "low"
            self.should_block = False


@dataclass
class SecurityValidationResult:
    """Result of comprehensive security validation."""
    allowed: bool
    violations: List[str]
    rate_limit_info: Optional[RateLimitResult] = None
    webhook_validation: Optional[ValidationResult] = None
    request_validation: Optional[ValidationResult] = None
    threat_detection: Optional[ThreatDetection] = None
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Calculate overall allowed status."""
        if not self.violations:
            self.violations = []
        
        # Collect violations from sub-validations
        if self.rate_limit_info and not self.rate_limit_info.allowed:
            self.violations.append("rate_limit_exceeded")
        
        if self.webhook_validation and not self.webhook_validation.is_valid:
            self.violations.append("webhook_validation_failed")
        
        if self.request_validation and not self.request_validation.is_valid:
            self.violations.append("request_validation_failed")
        
        if self.threat_detection and self.threat_detection.should_block:
            self.violations.append("threat_detected")
        
        # Update allowed status
        self.allowed = len(self.violations) == 0


class SecurityManager:
    """
    Unified security management system integrating all security components.
    
    Features:
    - Centralized security configuration and management
    - Rate limiting with multiple strategies
    - Webhook signature validation
    - Request validation and IP whitelisting
    - Content validation and sanitization
    - Threat detection and pattern analysis
    - Comprehensive audit logging
    - Security metrics collection
    """
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        """Initialize security manager with configuration."""
        self.config = config or SecurityConfig()
        self._lock = threading.RLock()
        
        # Initialize security components
        self._init_security_components()
        
        # Threat detection tracking
        self._failed_requests: Dict[str, List[Dict[str, Any]]] = {}  # IP -> failed attempts
        self._threat_detection_enabled = False
        
        # Audit logging
        self._audit_logs: List[Dict[str, Any]] = []
        self._audit_logging_config = {
            'log_successful_requests': False,
            'log_failed_requests': True,
            'log_rate_limit_violations': True,
            'log_suspicious_activity': True,
            'max_log_entries': 10000
        }
        
        # Metrics collection
        self.metrics_collector = None  # Will be injected if monitoring is available
        
        logger.info("SecurityManager initialized with comprehensive security controls")
    
    def _init_security_components(self):
        """Initialize individual security components."""
        # Rate limiter
        if self.config.rate_limiting_enabled:
            self.rate_limiter = RateLimiter(strategy=self.config.rate_limit_strategy)
        else:
            self.rate_limiter = None
        
        # Webhook validator (will be configured per webhook secret)
        self.webhook_validator = None
        
        # Request validator
        security_policy = SecurityPolicy(
            require_https=self.config.https_required,
            max_content_length_mb=self.config.max_content_length_mb,
            allowed_content_types=self.config.allowed_content_types
        )
        self.request_validator = RequestValidator(security_policy)
        
        # Content validator
        self.content_validator = ContentValidator()
    
    def configure_webhook_secret(self, webhook_secret: str):
        """Configure webhook validation with secret."""
        self.webhook_validator = WebhookValidator(
            webhook_secret=webhook_secret,
            tolerance_seconds=self.config.webhook_tolerance_seconds
        )
    
    def configure_ip_whitelist(self, ip_whitelist: IPWhitelist):
        """Configure IP whitelisting."""
        if self.config.ip_whitelisting_enabled:
            self.request_validator.configure_ip_whitelist(ip_whitelist)
    
    def enable_threat_detection(self, track_failed_attempts: bool = True,
                              suspicious_ip_threshold: int = 10,
                              time_window_minutes: int = 5):
        """Enable threat detection with configuration."""
        self._threat_detection_enabled = True
        self.config.suspicious_ip_threshold = suspicious_ip_threshold
        self.config.threat_detection_window_minutes = time_window_minutes
        
        logger.info(f"Threat detection enabled: threshold={suspicious_ip_threshold}, window={time_window_minutes}min")
    
    def enable_audit_logging(self, log_successful_requests: bool = False,
                           log_failed_requests: bool = True,
                           log_rate_limit_violations: bool = True,
                           log_suspicious_activity: bool = True):
        """Configure audit logging settings."""
        self._audit_logging_config.update({
            'log_successful_requests': log_successful_requests,
            'log_failed_requests': log_failed_requests,
            'log_rate_limit_violations': log_rate_limit_violations,
            'log_suspicious_activity': log_suspicious_activity
        })
        
        logger.info("Audit logging configured")
    
    def validate_request(self, request_data: Dict[str, Any]) -> SecurityValidationResult:
        """
        Perform comprehensive security validation of incoming request.
        
        Args:
            request_data: Dictionary containing:
                - client_ip: Client IP address
                - endpoint: API endpoint name
                - headers: HTTP headers dict
                - payload: Request payload (bytes or dict)
                - url: Full request URL
                
        Returns:
            SecurityValidationResult with detailed validation information
        """
        result = SecurityValidationResult(allowed=True, violations=[])
        
        client_ip = request_data.get('client_ip')
        endpoint = request_data.get('endpoint')
        headers = request_data.get('headers', {})
        payload = request_data.get('payload')
        url = request_data.get('url', '')
        
        try:
            # 1. Rate limiting check
            if self.rate_limiter and client_ip and endpoint:
                rate_result = self.rate_limiter.check_limit(client_ip, endpoint)
                result.rate_limit_info = rate_result
                
                if not rate_result.allowed:
                    self._log_audit_event('rate_limit_violation', {
                        'client_ip': client_ip,
                        'endpoint': endpoint,
                        'retry_after': rate_result.retry_after_seconds
                    })
            
            # 2. IP whitelisting check
            if client_ip and not self.request_validator.is_ip_allowed(client_ip):
                result.violations.append('ip_not_whitelisted')
                self._log_audit_event('ip_blocked', {
                    'client_ip': client_ip,
                    'reason': 'not_whitelisted'
                })
            
            # 3. Request validation
            if headers and url:
                request_result = self.request_validator.validate_request_headers(headers, url)
                result.request_validation = request_result
            
            # 4. Webhook signature validation
            if (self.webhook_validator and payload and 
                headers.get('x-postmark-signature') or headers.get('x-webhook-signature')):
                signature_header = (headers.get('x-postmark-signature') or 
                                  headers.get('x-webhook-signature'))
                
                if isinstance(payload, bytes):
                    webhook_result = self.webhook_validator.validate_signature(payload, signature_header)
                else:
                    webhook_result = self.webhook_validator.validate_json_webhook(str(payload), signature_header)
                
                result.webhook_validation = webhook_result
                
                if not webhook_result.is_valid:
                    self._log_audit_event('webhook_validation_failed', {
                        'client_ip': client_ip,
                        'error': webhook_result.error_message
                    })
            
            # 5. Threat detection
            if self._threat_detection_enabled and client_ip:
                threat_result = self.analyze_threat_level(client_ip)
                result.threat_detection = threat_result
            
            # 6. Log successful validation if configured
            if result.allowed and self._audit_logging_config.get('log_successful_requests'):
                self._log_audit_event('request_validated', {
                    'client_ip': client_ip,
                    'endpoint': endpoint
                })
            
            # 7. Record failed request for threat detection
            if not result.allowed and client_ip:
                violation_types = ', '.join(result.violations)
                self.record_failed_request(client_ip, violation_types)
            
            return result
            
        except Exception as e:
            logger.error(f"Security validation error: {e}")
            return SecurityValidationResult(
                allowed=False,
                violations=['validation_error'],
                timestamp=time.time()
            )
    
    def record_failed_request(self, client_ip: str, reason: str):
        """Record failed request for threat analysis."""
        with self._lock:
            current_time = time.time()
            
            if client_ip not in self._failed_requests:
                self._failed_requests[client_ip] = []
            
            self._failed_requests[client_ip].append({
                'timestamp': current_time,
                'reason': reason
            })
            
            # Clean old entries
            cutoff_time = current_time - (self.config.threat_detection_window_minutes * 60)
            self._failed_requests[client_ip] = [
                req for req in self._failed_requests[client_ip]
                if req['timestamp'] > cutoff_time
            ]
    
    def analyze_threat_level(self, client_ip: str) -> ThreatDetection:
        """Analyze threat level for specific IP address."""
        with self._lock:
            current_time = time.time()
            window_start = current_time - (self.config.threat_detection_window_minutes * 60)
            
            # Get failed attempts in window
            failed_attempts = self._failed_requests.get(client_ip, [])
            recent_failures = [req for req in failed_attempts if req['timestamp'] > window_start]
            
            # Analyze patterns
            detected_patterns = []
            failure_count = len(recent_failures)
            
            if failure_count >= self.config.suspicious_ip_threshold:
                detected_patterns.append("excessive_failed_requests")
            
            # Check for rapid-fire requests
            if len(recent_failures) >= 5:
                timestamps = [req['timestamp'] for req in recent_failures[-5:]]
                if timestamps[-1] - timestamps[0] < 60:  # 5 failures in 1 minute
                    detected_patterns.append("rapid_fire_requests")
            
            # Check for diverse failure types
            failure_reasons = set(req['reason'] for req in recent_failures)
            if len(failure_reasons) >= 3:
                detected_patterns.append("diverse_attack_vectors")
            
            # Calculate confidence score
            confidence_score = min(1.0, failure_count / self.config.suspicious_ip_threshold)
            if detected_patterns:
                confidence_score += len(detected_patterns) * 0.1
                confidence_score = min(1.0, confidence_score)
            
            return ThreatDetection(
                client_ip=client_ip,
                threat_level="low",  # Will be calculated in __post_init__
                should_block=False,  # Will be calculated
                detected_patterns=detected_patterns,
                failed_attempts=failure_count,
                time_window_start=window_start,
                confidence_score=confidence_score
            )
    
    def record_rate_limit_violation(self, client_ip: str, endpoint: str):
        """Record rate limit violation for audit."""
        self._log_audit_event('rate_limit_violation', {
            'client_ip': client_ip,
            'endpoint': endpoint,
            'timestamp': time.time()
        })
    
    def record_invalid_signature(self, client_ip: str, error_details: str):
        """Record invalid webhook signature for audit."""
        self._log_audit_event('invalid_signature', {
            'client_ip': client_ip,
            'error_details': error_details,
            'timestamp': time.time()
        })
    
    def record_ip_blocked(self, client_ip: str, reason: str):
        """Record IP blocking event for audit."""
        self._log_audit_event('ip_blocked', {
            'client_ip': client_ip,
            'reason': reason,
            'timestamp': time.time()
        })
    
    def _log_audit_event(self, event_type: str, details: Dict[str, Any]):
        """Log security event for audit trail."""
        if not self._audit_logging_config.get(f'log_{event_type}', True):
            return
        
        with self._lock:
            audit_entry = {
                'timestamp': time.time(),
                'event_type': event_type,
                'client_ip': details.get('client_ip', 'unknown'),
                'details': details
            }
            
            self._audit_logs.append(audit_entry)
            
            # Maintain log size limit
            max_entries = self._audit_logging_config.get('max_log_entries', 10000)
            if len(self._audit_logs) > max_entries:
                self._audit_logs = self._audit_logs[-max_entries:]
    
    def get_audit_logs(self, limit: int = 100, since_timestamp: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get recent audit log entries."""
        with self._lock:
            logs = self._audit_logs.copy()
            
            if since_timestamp:
                logs = [log for log in logs if log['timestamp'] >= since_timestamp]
            
            # Return most recent entries
            return logs[-limit:] if limit else logs
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get comprehensive security metrics."""
        with self._lock:
            current_time = time.time()
            hour_ago = current_time - 3600
            
            # Count recent events
            recent_logs = [log for log in self._audit_logs if log['timestamp'] > hour_ago]
            
            metrics = {
                'requests_validated': len(recent_logs),
                'violations_detected': len([log for log in recent_logs 
                                          if log['event_type'] in ['rate_limit_violation', 'ip_blocked', 'invalid_signature']]),
                'threat_ips_detected': len([ip for ip, failures in self._failed_requests.items() 
                                          if len(failures) >= self.config.suspicious_ip_threshold]),
                'total_audit_entries': len(self._audit_logs),
                'components_enabled': {
                    'rate_limiting': self.rate_limiter is not None,
                    'webhook_validation': self.webhook_validator is not None,
                    'ip_whitelisting': self.config.ip_whitelisting_enabled,
                    'content_validation': self.config.content_validation_enabled,
                    'threat_detection': self._threat_detection_enabled
                }
            }
            
            # Add component-specific metrics
            if self.rate_limiter:
                metrics['rate_limiter'] = self.rate_limiter.get_stats()
            
            if self.webhook_validator:
                metrics['webhook_validator'] = self.webhook_validator.get_stats()
            
            metrics['request_validator'] = self.request_validator.get_stats()
            
            return metrics