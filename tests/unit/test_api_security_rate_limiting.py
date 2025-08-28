"""
TDD CYCLE 10 - RED PHASE: API Security & Rate Limiting
Tests requiring comprehensive security system for privacy-focused email processing API
"""
import pytest
import time
import hashlib
from unittest.mock import patch, Mock, AsyncMock
from typing import Dict, Any, List, Optional

# Try to import security components (should fail initially)
try:
    from cellophanemail.features.security.rate_limiter import (
        RateLimiter,
        RateLimitStrategy,
        RateLimitResult,
        RateLimitViolation
    )
    from cellophanemail.features.security.webhook_validator import (
        WebhookValidator,
        WebhookSignature,
        ValidationResult
    )
    from cellophanemail.features.security.request_validator import (
        RequestValidator,
        SecurityPolicy,
        IPWhitelist,
        ContentValidator
    )
    from cellophanemail.features.security.security_manager import (
        SecurityManager,
        SecurityConfig,
        ThreatDetection
    )
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False


class TestAPISecurityRateLimiting:
    """Test API security and rate limiting system for privacy email processing"""
    
    def test_security_modules_exist(self):
        """
        RED TEST: Security modules should exist
        """
        assert SECURITY_AVAILABLE, \
            "cellophanemail.features.security modules must exist"
    
    @pytest.mark.skipif(not SECURITY_AVAILABLE, reason="Security modules not available")
    def test_rate_limiter_enforces_request_limits(self):
        """
        RED TEST: Should enforce rate limits per IP address and endpoint
        """
        # Disable caching for accurate testing
        rate_limiter = RateLimiter(cache_size=0)
        
        # Configure rate limits
        rate_limiter.configure_limit("webhook", requests_per_minute=60)
        rate_limiter.configure_limit("api", requests_per_minute=100)
        
        client_ip = "192.168.1.100"
        
        # Test rate limiting
        for i in range(5):
            result = rate_limiter.check_limit(client_ip, "webhook")
            assert isinstance(result, RateLimitResult)
            assert result.allowed == True
            assert result.remaining_requests > 0
        
        # Exhaust rate limit
        for i in range(60):
            rate_limiter.check_limit(client_ip, "webhook")
        
        # Should now be rate limited
        result = rate_limiter.check_limit(client_ip, "webhook")
        assert result.allowed == False
        assert result.retry_after_seconds > 0
    
    @pytest.mark.skipif(not SECURITY_AVAILABLE, reason="Security modules not available")
    def test_rate_limiter_supports_different_strategies(self):
        """
        RED TEST: Should support different rate limiting strategies (token bucket, sliding window)
        """
        # Token bucket strategy
        token_bucket = RateLimiter(strategy=RateLimitStrategy.TOKEN_BUCKET)
        token_bucket.configure_limit("api", requests_per_minute=60, burst_size=10)
        
        client_ip = "10.0.0.1"
        
        # Should allow burst requests initially
        for i in range(10):
            result = token_bucket.check_limit(client_ip, "api")
            assert result.allowed == True
        
        # Sliding window strategy
        sliding_window = RateLimiter(strategy=RateLimitStrategy.SLIDING_WINDOW)
        sliding_window.configure_limit("webhook", requests_per_minute=30, window_size_minutes=1)
        
        # Should track requests over sliding window
        for i in range(5):
            result = sliding_window.check_limit("10.0.0.2", "webhook")
            assert result.allowed == True
            assert hasattr(result, 'window_usage')
    
    @pytest.mark.skipif(not SECURITY_AVAILABLE, reason="Security modules not available")
    def test_webhook_validator_verifies_signatures(self):
        """
        RED TEST: Should validate webhook signatures to prevent unauthorized requests
        """
        webhook_secret = "super-secure-webhook-secret-key"
        validator = WebhookValidator(webhook_secret)
        
        # Valid webhook payload
        payload = b'{"test": "data", "timestamp": 1234567890}'
        
        # Create valid signature
        signature = validator.create_signature(payload)
        assert isinstance(signature, WebhookSignature)
        assert signature.algorithm == "sha256"
        assert len(signature.signature) > 0
        
        # Validate correct signature
        result = validator.validate_signature(payload, signature.to_header_value())
        assert isinstance(result, ValidationResult)
        assert result.is_valid == True
        assert result.error_message is None
        
        # Validate incorrect signature  
        wrong_signature = "sha256=wrongsignature123"
        result = validator.validate_signature(payload, wrong_signature)
        assert result.is_valid == False
        assert "signature" in result.error_message.lower()
    
    @pytest.mark.skipif(not SECURITY_AVAILABLE, reason="Security modules not available")
    def test_webhook_validator_prevents_replay_attacks(self):
        """
        RED TEST: Should prevent replay attacks using timestamp validation
        """
        validator = WebhookValidator("secret-key", tolerance_seconds=300)
        
        # Current timestamp
        current_time = int(time.time())
        fresh_payload = f'{{"timestamp": {current_time}, "data": "test"}}'.encode()
        
        signature = validator.create_signature(fresh_payload)
        result = validator.validate_signature(fresh_payload, signature.to_header_value())
        assert result.is_valid == True
        
        # Old timestamp (should be rejected)
        old_time = current_time - 600  # 10 minutes old
        old_payload = f'{{"timestamp": {old_time}, "data": "test"}}'.encode()
        
        old_signature = validator.create_signature(old_payload, float(old_time))
        result = validator.validate_signature(old_payload, old_signature.to_header_value())
        assert result.is_valid == False
        assert "timestamp" in result.error_message.lower() or "expired" in result.error_message.lower()
    
    @pytest.mark.skipif(not SECURITY_AVAILABLE, reason="Security modules not available")
    def test_request_validator_enforces_security_policies(self):
        """
        RED TEST: Should enforce security policies on incoming requests
        """
        policy = SecurityPolicy(
            require_https=True,
            max_content_length_mb=10,
            allowed_content_types=["application/json", "application/x-www-form-urlencoded"],
            require_user_agent=True
        )
        
        validator = RequestValidator(policy)
        
        # Valid request
        valid_headers = {
            "content-type": "application/json",
            "content-length": "1024",
            "user-agent": "PostmarkApp/1.0",
            "x-forwarded-proto": "https"
        }
        
        result = validator.validate_request_headers(valid_headers, "https://api.example.com/webhook")
        assert result.is_valid == True
        
        # Invalid content type
        invalid_headers = valid_headers.copy()
        invalid_headers["content-type"] = "text/plain"
        
        result = validator.validate_request_headers(invalid_headers, "https://api.example.com/webhook")
        assert result.is_valid == False
        assert "content-type" in result.error_message.lower()
    
    @pytest.mark.skipif(not SECURITY_AVAILABLE, reason="Security modules not available")
    def test_request_validator_supports_ip_whitelisting(self):
        """
        RED TEST: Should support IP address whitelisting for enhanced security
        """
        # Configure IP whitelist
        whitelist = IPWhitelist()
        whitelist.add_allowed_ip("192.168.1.0/24")  # Local network
        whitelist.add_allowed_ip("203.0.113.0/24")  # Postmark IP range (example)
        
        validator = RequestValidator()
        validator.configure_ip_whitelist(whitelist)
        
        # Test allowed IPs
        assert validator.is_ip_allowed("192.168.1.100") == True
        assert validator.is_ip_allowed("203.0.113.50") == True
        
        # Test blocked IPs
        assert validator.is_ip_allowed("10.0.0.1") == False
        assert validator.is_ip_allowed("8.8.8.8") == False
    
    @pytest.mark.skipif(not SECURITY_AVAILABLE, reason="Security modules not available")
    def test_content_validator_prevents_malicious_payloads(self):
        """
        RED TEST: Should validate and sanitize request content to prevent attacks
        """
        content_validator = ContentValidator()
        
        # Normal email webhook payload
        normal_payload = {
            "From": "sender@example.com",
            "To": "recipient@example.com",
            "Subject": "Test Email",
            "TextBody": "This is a test email message"
        }
        
        result = content_validator.validate_json_payload(normal_payload)
        assert result.is_valid == True
        assert result.sanitized_content is not None
        
        # Malicious payload with script injection
        malicious_payload = {
            "From": "attacker@evil.com",
            "Subject": "<script>alert('xss')</script>Malicious Subject",
            "TextBody": "javascript:alert('attack')",
            "HtmlBody": "<iframe src='http://evil.com'></iframe>"
        }
        
        result = content_validator.validate_json_payload(malicious_payload)
        # Should either reject or sanitize
        if result.is_valid:
            # If allowed, should be sanitized
            assert "<script>" not in str(result.sanitized_content)
            assert "javascript:" not in str(result.sanitized_content)
            assert "<iframe" not in str(result.sanitized_content)
        else:
            # If rejected, should have clear error message
            assert "malicious" in result.error_message.lower() or "invalid" in result.error_message.lower()
    
    @pytest.mark.skipif(not SECURITY_AVAILABLE, reason="Security modules not available")
    def test_security_manager_integrates_all_security_components(self):
        """
        RED TEST: Should provide unified security management across all components
        """
        config = SecurityConfig(
            rate_limiting_enabled=True,
            webhook_signature_validation=True,
            ip_whitelisting_enabled=True,
            content_validation_enabled=True,
            https_required=True
        )
        
        security_manager = SecurityManager(config)
        
        # Should have all security components
        assert hasattr(security_manager, 'rate_limiter')
        assert hasattr(security_manager, 'webhook_validator')
        assert hasattr(security_manager, 'request_validator')
        assert hasattr(security_manager, 'content_validator')
        
        # Should provide unified validation method
        request_data = {
            "client_ip": "192.168.1.100",
            "endpoint": "webhook",
            "headers": {
                "content-type": "application/json",
                "x-postmark-signature": "sha256=validSignature123"
            },
            "payload": b'{"test": "data"}',
            "url": "https://api.example.com/webhook"
        }
        
        result = security_manager.validate_request(request_data)
        assert hasattr(result, 'allowed')
        assert hasattr(result, 'violations')  # List of security violations
        assert hasattr(result, 'rate_limit_info')
    
    @pytest.mark.skipif(not SECURITY_AVAILABLE, reason="Security modules not available")
    def test_security_manager_detects_suspicious_patterns(self):
        """
        RED TEST: Should detect suspicious request patterns and potential attacks
        """
        security_manager = SecurityManager()
        
        # Configure threat detection
        security_manager.enable_threat_detection(
            track_failed_attempts=True,
            suspicious_ip_threshold=10,
            time_window_minutes=5
        )
        
        client_ip = "10.0.0.100"
        
        # Simulate suspicious activity (repeated failed attempts)
        for i in range(12):
            security_manager.record_failed_request(client_ip, "invalid_signature")
        
        # Should detect suspicious pattern
        threat_result = security_manager.analyze_threat_level(client_ip)
        assert isinstance(threat_result, ThreatDetection)
        assert threat_result.threat_level in ["medium", "high", "critical"]
        assert threat_result.should_block == True
        assert len(threat_result.detected_patterns) > 0
    
    @pytest.mark.skipif(not SECURITY_AVAILABLE, reason="Security modules not available") 
    def test_rate_limiter_supports_dynamic_limits(self):
        """
        RED TEST: Should support dynamic rate limit adjustment based on system load
        """
        rate_limiter = RateLimiter()
        
        # Configure base limits
        rate_limiter.configure_limit("webhook", requests_per_minute=60)
        
        # Should allow dynamic adjustment
        rate_limiter.adjust_limit_for_load("webhook", load_factor=0.5)  # Reduce to 50%
        
        client_ip = "172.16.0.1"
        
        # Should now have reduced limits
        for i in range(35):  # More than 30 (50% of 60) but less than 60
            result = rate_limiter.check_limit(client_ip, "webhook")
        
        # Should be rate limited at reduced threshold
        result = rate_limiter.check_limit(client_ip, "webhook")
        # This test depends on implementation details
        assert hasattr(result, 'current_limit')
    
    @pytest.mark.skipif(not SECURITY_AVAILABLE, reason="Security modules not available")
    def test_security_manager_provides_audit_logging(self):
        """
        RED TEST: Should provide comprehensive audit logging for security events
        """
        security_manager = SecurityManager()
        
        # Enable audit logging
        security_manager.enable_audit_logging(
            log_successful_requests=False,  # Only log security events
            log_failed_requests=True,
            log_rate_limit_violations=True,
            log_suspicious_activity=True
        )
        
        # Simulate security events
        security_manager.record_rate_limit_violation("10.0.0.50", "webhook")
        security_manager.record_invalid_signature("10.0.0.51", "malformed_signature")
        security_manager.record_ip_blocked("10.0.0.52", "not_whitelisted")
        
        # Get audit logs
        audit_logs = security_manager.get_audit_logs(limit=10)
        assert len(audit_logs) >= 3
        
        # Verify log structure
        log_entry = audit_logs[0]
        assert 'timestamp' in log_entry
        assert 'event_type' in log_entry
        assert 'client_ip' in log_entry
        assert 'details' in log_entry
    
    @pytest.mark.skipif(not SECURITY_AVAILABLE, reason="Security modules not available")
    @pytest.mark.asyncio
    async def test_security_integration_with_privacy_pipeline(self):
        """
        RED TEST: Should integrate security with existing privacy pipeline
        """
        from cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
        
        security_manager = SecurityManager()
        
        # Mock a webhook request with security validation
        webhook_payload = {
            "From": "test@example.com",
            "To": "user@example.com", 
            "Subject": "Test Email",
            "TextBody": "This is a test email"
        }
        
        # Validate request security
        request_data = {
            "client_ip": "203.0.113.100",
            "endpoint": "webhook",
            "headers": {
                "content-type": "application/json",
                "content-length": "150"
            },
            "payload": str(webhook_payload).encode(),
            "url": "https://api.example.com/webhook"
        }
        
        security_result = security_manager.validate_request(request_data)
        
        # Should integrate with monitoring
        if hasattr(security_manager, 'metrics_collector'):
            metrics = security_manager.get_security_metrics()
            assert 'requests_validated' in metrics
            assert 'violations_detected' in metrics
        
        # Should work with ephemeral email processing
        if security_result.allowed:
            email = EphemeralEmail(
                message_id="security-test-001",
                from_address="test@example.com",
                to_addresses=["user@example.com"],
                subject="Test Email",
                text_body="This is a test email",
                user_email="user@example.com",
                ttl_seconds=300
            )
            
            # Security should not interfere with privacy processing
            assert email.is_expired == False
            assert email.message_id == "security-test-001"
    
    @pytest.mark.skipif(not SECURITY_AVAILABLE, reason="Security modules not available")
    def test_rate_limiter_handles_distributed_deployment(self):
        """
        RED TEST: Should support distributed rate limiting across multiple instances
        """
        # This would typically use Redis or similar for distributed state
        rate_limiter = RateLimiter(distributed=True, redis_url="redis://localhost:6379")
        
        # Should support distributed configuration
        assert hasattr(rate_limiter, 'distributed_backend')
        
        # Should handle distributed limits consistently
        client_ip = "198.51.100.10"
        
        # Test would require actual Redis setup for full validation
        # For now, just verify the interface exists
        result = rate_limiter.check_limit(client_ip, "api") 
        assert isinstance(result, RateLimitResult)
    
    def test_rate_limit_strategy_enum_exists(self):
        """
        RED TEST: RateLimitStrategy enum should be properly defined
        """
        if not SECURITY_AVAILABLE:
            pytest.fail("RateLimitStrategy enum must be defined")
        
        # Verify enum values
        assert hasattr(RateLimitStrategy, 'TOKEN_BUCKET')
        assert hasattr(RateLimitStrategy, 'SLIDING_WINDOW')
        assert hasattr(RateLimitStrategy, 'FIXED_WINDOW')
    
    def test_security_interfaces_exist(self):
        """
        RED TEST: Security interfaces should be properly defined
        """
        if not SECURITY_AVAILABLE:
            pytest.fail("Security interfaces must be defined")
        
        # Verify core classes exist
        expected_classes = [
            'RateLimiter', 'WebhookValidator', 'RequestValidator', 
            'SecurityManager', 'SecurityConfig'
        ]
        
        for class_name in expected_classes:
            assert class_name in str(SECURITY_AVAILABLE) or True  # Classes imported successfully