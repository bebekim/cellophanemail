"""
Request Validation and Security Policy System for Privacy-Focused Email Processing

Comprehensive request validation including security policies, IP whitelisting,
content validation, and malicious payload detection.
"""

import re
import ipaddress
import html
from typing import Dict, Any, List, Optional, Union, Set
from dataclasses import dataclass
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


@dataclass
class SecurityPolicy:
    """Security policy configuration."""
    require_https: bool = True
    max_content_length_mb: int = 10
    allowed_content_types: List[str] = None
    require_user_agent: bool = True
    block_suspicious_user_agents: bool = True
    max_header_size_kb: int = 8
    
    def __post_init__(self):
        if self.allowed_content_types is None:
            self.allowed_content_types = [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data"
            ]


@dataclass 
class ValidationResult:
    """Result of request validation."""
    is_valid: bool
    error_message: Optional[str] = None
    security_violations: List[str] = None
    sanitized_content: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.security_violations is None:
            self.security_violations = []


class IPWhitelist:
    """IP address whitelisting system."""
    
    def __init__(self):
        """Initialize IP whitelist."""
        self._allowed_networks: Set[ipaddress.IPv4Network] = set()
        self._allowed_ips: Set[ipaddress.IPv4Address] = set()
        self._blocked_ips: Set[ipaddress.IPv4Address] = set()
        
        logger.info("IPWhitelist initialized")
    
    def add_allowed_ip(self, ip_or_network: str):
        """
        Add IP address or CIDR network to whitelist.
        
        Args:
            ip_or_network: IP address (e.g., "192.168.1.1") or CIDR (e.g., "192.168.1.0/24")
        """
        try:
            if '/' in ip_or_network:
                # CIDR network
                network = ipaddress.IPv4Network(ip_or_network, strict=False)
                self._allowed_networks.add(network)
                logger.info(f"Added network to whitelist: {network}")
            else:
                # Single IP
                ip = ipaddress.IPv4Address(ip_or_network)
                self._allowed_ips.add(ip)
                logger.info(f"Added IP to whitelist: {ip}")
        except ValueError as e:
            logger.error(f"Invalid IP/network format: {ip_or_network} - {e}")
            raise
    
    def add_blocked_ip(self, ip_address: str):
        """Add IP address to explicit block list."""
        try:
            ip = ipaddress.IPv4Address(ip_address)
            self._blocked_ips.add(ip)
            logger.info(f"Added IP to blocklist: {ip}")
        except ValueError as e:
            logger.error(f"Invalid IP format: {ip_address} - {e}")
            raise
    
    def is_allowed(self, ip_address: str) -> bool:
        """Check if IP address is allowed."""
        try:
            ip = ipaddress.IPv4Address(ip_address)
            
            # Check explicit block list first
            if ip in self._blocked_ips:
                return False
            
            # Check explicit allow list
            if ip in self._allowed_ips:
                return True
            
            # Check allowed networks
            for network in self._allowed_networks:
                if ip in network:
                    return True
            
            return False
            
        except ValueError as e:
            logger.warning(f"Invalid IP format for validation: {ip_address} - {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get IP whitelist statistics."""
        return {
            'allowed_ips_count': len(self._allowed_ips),
            'allowed_networks_count': len(self._allowed_networks),
            'blocked_ips_count': len(self._blocked_ips),
            'allowed_networks': [str(net) for net in self._allowed_networks],
            'blocked_ips': [str(ip) for ip in self._blocked_ips]
        }


class ContentValidator:
    """Content validation and sanitization system."""
    
    # Suspicious patterns that might indicate malicious content
    MALICIOUS_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'vbscript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),  # Event handlers like onclick=
        re.compile(r'<iframe[^>]*>', re.IGNORECASE),
        re.compile(r'<object[^>]*>', re.IGNORECASE),
        re.compile(r'<embed[^>]*>', re.IGNORECASE),
        re.compile(r'data:text/html', re.IGNORECASE),
        re.compile(r'expression\s*\(', re.IGNORECASE),  # CSS expression()
    ]
    
    # Suspicious SQL patterns
    SQL_INJECTION_PATTERNS = [
        re.compile(r'\b(union|select|insert|update|delete|drop|create|alter)\b', re.IGNORECASE),
        re.compile(r'[\'";].*(-{2}|\/\*)', re.IGNORECASE),  # SQL comments
        re.compile(r'\b(or|and)\s+[\'"]\d+[\'"]?\s*=\s*[\'"]\d+[\'"]?', re.IGNORECASE),
    ]
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize content validator.
        
        Args:
            strict_mode: If True, reject any suspicious content; if False, sanitize
        """
        self.strict_mode = strict_mode
        logger.info(f"ContentValidator initialized, strict_mode={strict_mode}")
    
    def validate_json_payload(self, payload: Dict[str, Any]) -> ValidationResult:
        """
        Validate and sanitize JSON webhook payload.
        
        Args:
            payload: Dictionary containing webhook payload data
            
        Returns:
            ValidationResult with validation status and sanitized content
        """
        violations = []
        sanitized_payload = {}
        
        try:
            for key, value in payload.items():
                # Validate key name
                if not self._is_safe_key(key):
                    violations.append(f"Suspicious key name: {key}")
                    if self.strict_mode:
                        return ValidationResult(
                            is_valid=False,
                            error_message="Malicious key name detected",
                            security_violations=violations
                        )
                    continue  # Skip this key in non-strict mode
                
                # Validate and sanitize value
                if isinstance(value, str):
                    sanitized_value, value_violations = self._validate_string_content(value)
                    violations.extend(value_violations)
                    
                    if violations and self.strict_mode:
                        return ValidationResult(
                            is_valid=False,
                            error_message="Malicious content detected",
                            security_violations=violations
                        )
                    
                    sanitized_payload[key] = sanitized_value
                elif isinstance(value, (int, float, bool, type(None))):
                    sanitized_payload[key] = value
                elif isinstance(value, (list, dict)):
                    # Recursively validate nested structures
                    sanitized_nested, nested_violations = self._validate_nested_content(value)
                    violations.extend(nested_violations)
                    
                    if nested_violations and self.strict_mode:
                        return ValidationResult(
                            is_valid=False,
                            error_message="Malicious nested content detected",
                            security_violations=violations
                        )
                    
                    sanitized_payload[key] = sanitized_nested
                else:
                    violations.append(f"Unsupported data type for key '{key}': {type(value)}")
                    if self.strict_mode:
                        return ValidationResult(
                            is_valid=False,
                            error_message="Unsupported data type",
                            security_violations=violations
                        )
            
            # Determine validity
            is_valid = not violations if self.strict_mode else True
            
            return ValidationResult(
                is_valid=is_valid,
                error_message=None if is_valid else "Content validation failed",
                security_violations=violations,
                sanitized_content=sanitized_payload
            )
            
        except Exception as e:
            logger.error(f"Content validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation processing error: {str(e)}",
                security_violations=["processing_error"]
            )
    
    def _is_safe_key(self, key: str) -> bool:
        """Check if a dictionary key is safe."""
        # Basic key validation - alphanumeric, underscore, hyphen only
        if not re.match(r'^[a-zA-Z0-9_-]+$', key):
            return False
        
        # Check for suspicious key names
        suspicious_keys = ['eval', 'exec', 'system', 'command', '__proto__', 'constructor']
        return key.lower() not in suspicious_keys
    
    def _validate_string_content(self, content: str) -> tuple[str, List[str]]:
        """Validate and sanitize string content."""
        violations = []
        sanitized = content
        
        # Check for malicious patterns
        for pattern in self.MALICIOUS_PATTERNS:
            matches = pattern.findall(content)
            if matches:
                violations.append(f"Malicious pattern detected: {pattern.pattern}")
                # Remove malicious content
                sanitized = pattern.sub('', sanitized)
        
        # Check for SQL injection
        for pattern in self.SQL_INJECTION_PATTERNS:
            if pattern.search(content):
                violations.append(f"Potential SQL injection: {pattern.pattern}")
                # In strict mode, this would be rejected
                # In non-strict mode, we sanitize by HTML escaping
                if not self.strict_mode:
                    sanitized = html.escape(sanitized)
        
        # Additional sanitization
        if violations and not self.strict_mode:
            # HTML escape any remaining suspicious characters
            sanitized = html.escape(sanitized)
            # Remove null bytes and control characters
            sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
        
        return sanitized, violations
    
    def _validate_nested_content(self, content: Union[List, Dict]) -> tuple[Union[List, Dict], List[str]]:
        """Validate nested list or dictionary content."""
        violations = []
        
        if isinstance(content, dict):
            sanitized = {}
            for key, value in content.items():
                if isinstance(value, str):
                    sanitized_value, value_violations = self._validate_string_content(value)
                    violations.extend(value_violations)
                    sanitized[key] = sanitized_value
                elif isinstance(value, (list, dict)):
                    nested_sanitized, nested_violations = self._validate_nested_content(value)
                    violations.extend(nested_violations)
                    sanitized[key] = nested_sanitized
                else:
                    sanitized[key] = value
        elif isinstance(content, list):
            sanitized = []
            for item in content:
                if isinstance(item, str):
                    sanitized_item, item_violations = self._validate_string_content(item)
                    violations.extend(item_violations)
                    sanitized.append(sanitized_item)
                elif isinstance(item, (list, dict)):
                    nested_sanitized, nested_violations = self._validate_nested_content(item)
                    violations.extend(nested_violations)
                    sanitized.append(nested_sanitized)
                else:
                    sanitized.append(item)
        else:
            sanitized = content
        
        return sanitized, violations


class RequestValidator:
    """
    Comprehensive request validation system.
    
    Validates HTTP requests against security policies, IP whitelists,
    and content validation rules.
    """
    
    def __init__(self, policy: Optional[SecurityPolicy] = None):
        """Initialize request validator with security policy."""
        self.policy = policy or SecurityPolicy()
        self.ip_whitelist: Optional[IPWhitelist] = None
        self.content_validator = ContentValidator()
        
        logger.info("RequestValidator initialized")
    
    def configure_ip_whitelist(self, ip_whitelist: IPWhitelist):
        """Configure IP whitelisting."""
        self.ip_whitelist = ip_whitelist
        logger.info("IP whitelisting configured")
    
    def is_ip_allowed(self, client_ip: str) -> bool:
        """Check if client IP is allowed."""
        if self.ip_whitelist is None:
            return True  # No IP filtering configured
        return self.ip_whitelist.is_allowed(client_ip)
    
    def validate_request_headers(self, headers: Dict[str, str], url: str) -> ValidationResult:
        """
        Validate HTTP request headers against security policy.
        
        Args:
            headers: Dictionary of HTTP headers
            url: Request URL
            
        Returns:
            ValidationResult with validation status and violations
        """
        violations = []
        
        try:
            # Check HTTPS requirement
            if self.policy.require_https:
                parsed_url = urlparse(url)
                if parsed_url.scheme != 'https' and not headers.get('x-forwarded-proto') == 'https':
                    violations.append("HTTPS required but request is not secure")
            
            # Check content type
            content_type = headers.get('content-type', '').lower()
            if content_type:
                content_type_main = content_type.split(';')[0].strip()
                if content_type_main not in [ct.lower() for ct in self.policy.allowed_content_types]:
                    violations.append(f"Content-Type '{content_type_main}' not allowed")
            
            # Check content length
            content_length = headers.get('content-length')
            if content_length:
                try:
                    length_mb = int(content_length) / (1024 * 1024)
                    if length_mb > self.policy.max_content_length_mb:
                        violations.append(f"Content too large: {length_mb:.1f}MB > {self.policy.max_content_length_mb}MB")
                except ValueError:
                    violations.append("Invalid Content-Length header")
            
            # Check User-Agent requirement
            if self.policy.require_user_agent:
                user_agent = headers.get('user-agent', '').strip()
                if not user_agent:
                    violations.append("User-Agent header required but missing")
                elif self.policy.block_suspicious_user_agents:
                    if self._is_suspicious_user_agent(user_agent):
                        violations.append(f"Suspicious User-Agent: {user_agent}")
            
            # Check header sizes
            for key, value in headers.items():
                header_size_kb = (len(key) + len(value)) / 1024
                if header_size_kb > self.policy.max_header_size_kb:
                    violations.append(f"Header '{key}' too large: {header_size_kb:.1f}KB")
            
            is_valid = len(violations) == 0
            error_message = None
            if not is_valid:
                error_message = "; ".join(violations) if violations else "Request validation failed"
            
            return ValidationResult(
                is_valid=is_valid,
                error_message=error_message,
                security_violations=violations
            )
            
        except Exception as e:
            logger.error(f"Request validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}",
                security_violations=["validation_error"]
            )
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if User-Agent appears suspicious."""
        suspicious_patterns = [
            r'bot',
            r'crawler',
            r'spider',
            r'scan',
            r'hack',
            r'test',
            r'curl',
            r'wget',
            r'python-requests',
            r'^$',  # Empty
        ]
        
        # Allow legitimate email service user agents
        legitimate_patterns = [
            r'postmark',
            r'sendgrid',
            r'mailgun',
            r'amazonses',
            r'sparkpost',
        ]
        
        user_agent_lower = user_agent.lower()
        
        # Check for legitimate patterns first
        for pattern in legitimate_patterns:
            if re.search(pattern, user_agent_lower):
                return False
        
        # Then check for suspicious patterns
        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent_lower):
                return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get request validator statistics."""
        stats = {
            'policy': {
                'require_https': self.policy.require_https,
                'max_content_length_mb': self.policy.max_content_length_mb,
                'allowed_content_types': self.policy.allowed_content_types,
                'require_user_agent': self.policy.require_user_agent,
            },
            'ip_whitelisting_enabled': self.ip_whitelist is not None,
        }
        
        if self.ip_whitelist:
            stats['ip_whitelist'] = self.ip_whitelist.get_stats()
        
        return stats