"""
Production Configuration & Environment Management

Comprehensive configuration system for privacy-focused email processing with
support for multiple deployment environments, security validation, and 
integration with all privacy pipeline components.
"""

import os
import yaml
import json
import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


class EnvironmentProfile(Enum):
    """Supported environment profiles with different security and performance settings."""
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"


class DeploymentMode(Enum):
    """Supported deployment modes with different infrastructure configurations."""
    STANDALONE = "standalone"
    CONTAINER = "container"
    CLOUD = "cloud"


@dataclass
class SecurityConfig:
    """Security configuration for production deployment."""
    require_https: bool = True
    webhook_signature_validation: bool = True
    max_request_size_mb: int = 10
    rate_limiting: bool = True
    rate_limit_per_minute: int = 60
    cors_enabled: bool = False
    cors_origins: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate security configuration."""
        if self.max_request_size_mb <= 0 or self.max_request_size_mb > 100:
            raise ValueError("max_request_size_mb must be between 1 and 100")
        if self.rate_limit_per_minute <= 0:
            raise ValueError("rate_limit_per_minute must be positive")


@dataclass 
class APIConfig:
    """API server configuration."""
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1
    timeout_seconds: int = 30
    health_check_endpoint: str = "/health"
    metrics_endpoint: str = "/metrics"
    
    def __post_init__(self):
        """Validate API configuration."""
        if not (1 <= self.port <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        if self.workers <= 0:
            raise ValueError("Workers must be positive")


@dataclass
class LoggingConfig:
    """Logging configuration for monitoring and debugging."""
    level: str = "INFO"
    format: str = "text"  # text, json
    file_path: Optional[str] = None
    max_file_size_mb: int = 100
    backup_count: int = 3
    enable_console: bool = True
    
    def __post_init__(self):
        """Validate logging configuration."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        if self.format not in ["text", "json"]:
            raise ValueError("Log format must be 'text' or 'json'")


@dataclass
class ResourceLimits:
    """Resource limits and performance tuning."""
    max_concurrent_emails: int = 100
    max_memory_usage_mb: int = 512
    request_timeout_seconds: int = 60
    cleanup_interval_seconds: int = 300
    cache_ttl_seconds: int = 300
    
    def __post_init__(self):
        """Validate resource limits."""
        if self.max_concurrent_emails <= 0:
            raise ValueError("max_concurrent_emails must be positive")
        if self.max_memory_usage_mb <= 0:
            raise ValueError("max_memory_usage_mb must be positive") 
        if self.request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be positive")


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass  
class SecurityValidationResult:
    """Result of security validation."""
    is_secure: bool
    security_warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class ProductionConfig:
    """
    Comprehensive production configuration for privacy-focused email processing.
    
    Supports multiple environment profiles, security validation, file-based
    configuration, and integration with all privacy pipeline components.
    """
    
    def __init__(
        self,
        profile: EnvironmentProfile = EnvironmentProfile.DEVELOPMENT,
        deployment_mode: DeploymentMode = DeploymentMode.STANDALONE
    ):
        """Initialize production configuration."""
        self.profile = profile
        self.deployment_mode = deployment_mode
        
        # Core application settings
        self.database_url: Optional[str] = None
        self.webhook_secret: Optional[str] = None
        self.llm_analyzer_mode: str = "privacy"
        
        # Component configurations  
        self.security = SecurityConfig()
        self.api = APIConfig()
        self.logging = LoggingConfig()
        self.resources = ResourceLimits()
        
        # Apply profile-specific defaults
        self._apply_profile_defaults()
        self._apply_deployment_mode_defaults()
    
    def _apply_profile_defaults(self):
        """Apply environment profile-specific default configurations."""
        if self.profile == EnvironmentProfile.DEVELOPMENT:
            self.debug_enabled = True
            self.logging.level = "DEBUG"
            self.logging.format = "text"
            self.security.require_https = False
            self.security.webhook_signature_validation = False
            self.resources.max_concurrent_emails = 10
            
        elif self.profile == EnvironmentProfile.STAGING:
            self.debug_enabled = False
            self.logging.level = "INFO"
            self.logging.format = "json"
            self.security.require_https = True
            self.security.webhook_signature_validation = True
            self.resources.max_concurrent_emails = 50
            
        elif self.profile == EnvironmentProfile.PRODUCTION:
            self.debug_enabled = False
            self.logging.level = "WARNING"
            self.logging.format = "json"
            self.security.require_https = True
            self.security.webhook_signature_validation = True
            self.security.rate_limiting = True
            self.resources.max_concurrent_emails = 100
    
    def _apply_deployment_mode_defaults(self):
        """Apply deployment mode-specific configurations."""
        if self.deployment_mode == DeploymentMode.STANDALONE:
            self.api.host = "127.0.0.1"
            self.api.workers = 1
            self.metrics_enabled = False
            
        elif self.deployment_mode == DeploymentMode.CONTAINER:
            self.api.host = "0.0.0.0"
            self.api.workers = 4
            self.metrics_enabled = True
            self.api.health_check_endpoint = "/health"
            
        elif self.deployment_mode == DeploymentMode.CLOUD:
            self.api.host = "0.0.0.0"
            self.api.workers = 8
            self.metrics_enabled = True
            self.security.require_https = True
            self.security.cors_enabled = True
    
    @classmethod
    def from_profile(cls, profile: EnvironmentProfile) -> 'ProductionConfig':
        """Create configuration from environment profile."""
        return cls(profile=profile)
    
    @classmethod 
    def from_environment(cls) -> 'ProductionConfig':
        """Create configuration from environment variables."""
        # Determine profile from environment
        env_name = os.getenv('ENVIRONMENT', 'development').lower()
        try:
            profile = EnvironmentProfile(env_name)
        except ValueError:
            logger.warning(f"Unknown environment '{env_name}', using development")
            profile = EnvironmentProfile.DEVELOPMENT
        
        # Create base configuration
        config = cls(profile=profile)
        
        # Load from environment variables
        config.database_url = os.getenv('DATABASE_URL')
        config.webhook_secret = os.getenv('WEBHOOK_SECRET')
        config.llm_analyzer_mode = os.getenv('LLM_ANALYZER_MODE', 'privacy')
        
        # API configuration
        if os.getenv('API_HOST'):
            config.api.host = os.getenv('API_HOST')
        if os.getenv('API_PORT'):
            config.api.port = int(os.getenv('API_PORT'))
        
        # Resource limits
        if os.getenv('MAX_CONCURRENT_EMAILS'):
            config.resources.max_concurrent_emails = int(os.getenv('MAX_CONCURRENT_EMAILS'))
        
        # Logging configuration
        if os.getenv('LOG_LEVEL'):
            config.logging.level = os.getenv('LOG_LEVEL').upper()
        if os.getenv('LOG_FILE'):
            config.logging.file_path = os.getenv('LOG_FILE')
        
        return config
    
    @classmethod
    def from_file(cls, file_path: str) -> 'ProductionConfig':
        """Create configuration from YAML or JSON file."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        # Load configuration data
        with open(path, 'r') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif path.suffix.lower() == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {path.suffix}")
        
        # Create configuration from data
        profile_name = data.get('environment', 'development')
        profile = EnvironmentProfile(profile_name)
        config = cls(profile=profile)
        
        # Apply configuration from file
        config.database_url = data.get('database_url')
        config.webhook_secret = data.get('webhook_secret')
        config.llm_analyzer_mode = data.get('llm_analyzer', {}).get('mode', 'privacy')
        
        # API configuration
        if 'api' in data:
            api_data = data['api']
            config.api.host = api_data.get('host', config.api.host)
            config.api.port = api_data.get('port', config.api.port)
        
        # Security configuration
        if 'security' in data:
            sec_data = data['security']
            config.security.require_https = sec_data.get('require_https', config.security.require_https)
            config.security.max_request_size_mb = sec_data.get('max_request_size_mb', config.security.max_request_size_mb)
        
        # Logging configuration
        if 'logging' in data:
            log_data = data['logging']
            config.logging.level = log_data.get('level', config.logging.level).upper()
            config.logging.format = log_data.get('format', config.logging.format)
        
        return config
    
    @classmethod
    def for_deployment_mode(cls, mode: str) -> 'ProductionConfig':
        """Create configuration for specific deployment mode."""
        try:
            deployment_mode = DeploymentMode(mode)
        except ValueError:
            raise ValueError(f"Unknown deployment mode: {mode}")
        
        return cls(deployment_mode=deployment_mode)
    
    def merge_with_dict(self, config_dict: Dict[str, Any]) -> 'ProductionConfig':
        """Merge current configuration with dictionary, returning new instance."""
        # Create a copy of current configuration
        new_config = ProductionConfig(self.profile, self.deployment_mode)
        
        # Copy current state
        new_config.database_url = self.database_url
        new_config.webhook_secret = self.webhook_secret
        new_config.llm_analyzer_mode = self.llm_analyzer_mode
        new_config.debug_enabled = getattr(self, 'debug_enabled', False)
        new_config.metrics_enabled = getattr(self, 'metrics_enabled', False)
        
        # Apply overrides from dictionary
        if 'database_url' in config_dict:
            new_config.database_url = config_dict['database_url']
        if 'webhook_secret' in config_dict:
            new_config.webhook_secret = config_dict['webhook_secret']
        if 'llm_analyzer_mode' in config_dict:
            new_config.llm_analyzer_mode = config_dict['llm_analyzer_mode']
        
        # Merge API configuration
        if 'api' in config_dict:
            api_config = config_dict['api']
            if 'host' in api_config:
                new_config.api.host = api_config['host']
            if 'port' in api_config:
                new_config.api.port = api_config['port']
        
        # Merge security configuration
        if 'security' in config_dict:
            sec_config = config_dict['security']
            if 'require_https' in sec_config:
                new_config.security.require_https = sec_config['require_https']
            if 'max_request_size_mb' in sec_config:
                new_config.security.max_request_size_mb = sec_config['max_request_size_mb']
        
        # Merge resource limits
        if 'resources' in config_dict:
            res_config = config_dict['resources']
            if 'max_concurrent_emails' in res_config:
                new_config.resources.max_concurrent_emails = res_config['max_concurrent_emails']
        
        return new_config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return {
            'profile': self.profile.value,
            'deployment_mode': self.deployment_mode.value,
            'database_url': self.database_url,
            'webhook_secret': '***REDACTED***' if self.webhook_secret else None,
            'llm_analyzer_mode': self.llm_analyzer_mode,
            'debug_enabled': getattr(self, 'debug_enabled', False),
            'metrics_enabled': getattr(self, 'metrics_enabled', False),
            'api': {
                'host': self.api.host,
                'port': self.api.port,
                'workers': self.api.workers,
                'timeout_seconds': self.api.timeout_seconds,
                'health_check_endpoint': self.api.health_check_endpoint
            },
            'security': {
                'require_https': self.security.require_https,
                'webhook_signature_validation': self.security.webhook_signature_validation,
                'max_request_size_mb': self.security.max_request_size_mb,
                'rate_limiting': self.security.rate_limiting
            },
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'file_path': self.logging.file_path
            },
            'resources': {
                'max_concurrent_emails': self.resources.max_concurrent_emails,
                'max_memory_usage_mb': self.resources.max_memory_usage_mb,
                'request_timeout_seconds': self.resources.request_timeout_seconds,
                'cleanup_interval_seconds': self.resources.cleanup_interval_seconds
            }
        }
    
    def validate(self) -> ValidationResult:
        """Validate current configuration."""
        validator = ConfigurationValidator()
        return validator.validate_config(self.to_dict())
    
    def export_for_deployment(self, format: str = 'yaml') -> str:
        """Export configuration in deployment-ready format."""
        config_dict = self.to_dict()
        
        if format.lower() == 'yaml':
            return yaml.dump(config_dict, default_flow_style=False, indent=2)
        elif format.lower() == 'json':
            return json.dumps(config_dict, indent=2)
        elif format.lower() == 'env':
            # Generate environment variable format
            env_vars = []
            env_vars.append(f"ENVIRONMENT={self.profile.value}")
            env_vars.append(f"DATABASE_URL={self.database_url or ''}")
            env_vars.append(f"WEBHOOK_SECRET={self.webhook_secret or ''}")
            env_vars.append(f"API_HOST={self.api.host}")
            env_vars.append(f"API_PORT={self.api.port}")
            env_vars.append(f"LLM_ANALYZER_MODE={self.llm_analyzer_mode}")
            env_vars.append(f"LOG_LEVEL={self.logging.level}")
            return '\n'.join(env_vars)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def __repr__(self) -> str:
        """String representation of configuration."""
        return f"ProductionConfig(profile={self.profile.value}, mode={self.deployment_mode.value})"
    
    @property
    def log_level(self) -> str:
        """Get configured log level."""
        return self.logging.level
    
    @property  
    def log_format(self) -> str:
        """Get configured log format."""
        return self.logging.format
    
    @property
    def log_file_path(self) -> Optional[str]:
        """Get configured log file path."""
        return self.logging.file_path
    
    @property
    def api_host(self) -> str:
        """Get configured API host."""
        return self.api.host
    
    @property
    def api_port(self) -> int:
        """Get configured API port."""
        return self.api.port
    
    @property
    def health_check_endpoint(self) -> str:
        """Get health check endpoint."""
        return self.api.health_check_endpoint
    
    @property
    def max_concurrent_emails(self) -> int:
        """Get maximum concurrent emails limit."""
        return self.resources.max_concurrent_emails
    
    @property
    def max_memory_usage_mb(self) -> int:
        """Get maximum memory usage limit."""
        return self.resources.max_memory_usage_mb
    
    @property  
    def request_timeout_seconds(self) -> int:
        """Get request timeout in seconds."""
        return self.resources.request_timeout_seconds
    
    @property
    def cleanup_interval_seconds(self) -> int:
        """Get cleanup interval in seconds."""
        return self.resources.cleanup_interval_seconds
    
    def get_memory_manager_config(self) -> Dict[str, Any]:
        """Get configuration for memory manager component."""
        return {
            'ttl_seconds': self.resources.cache_ttl_seconds,
            'max_concurrent': self.resources.max_concurrent_emails,
            'cleanup_interval': self.resources.cleanup_interval_seconds
        }
    
    def get_processor_config(self) -> Dict[str, Any]:
        """Get configuration for email processor component."""
        return {
            'use_llm': True,  # Always enabled in production
            'processing_timeout': self.resources.request_timeout_seconds,
            'analyzer_mode': self.llm_analyzer_mode
        }
    
    def get_delivery_config(self) -> Dict[str, Any]:
        """Get configuration for delivery manager component."""
        return {
            'retry_attempts': 3,
            'retry_delay_seconds': 5,
            'timeout_seconds': self.resources.request_timeout_seconds
        }


class ConfigurationValidator:
    """Enhanced validator for production configuration settings."""
    
    REQUIRED_FIELDS = [
        'database_url',
        'webhook_secret',
        'api_host',
        'api_port', 
        'llm_analyzer_mode',
        'max_concurrent_emails'
    ]
    
    VALID_LLM_MODES = ['privacy', 'anthropic', 'openai']
    VALID_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    def validate_config(self, config_dict: Dict[str, Any]) -> ValidationResult:
        """Validate complete configuration dictionary with enhanced checks."""
        errors = []
        warnings = []
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in config_dict or config_dict[field] is None:
                errors.append(f"Required field missing: {field}")
        
        # Validate specific fields with enhanced logic
        errors.extend(self._validate_webhook_secret(config_dict))
        errors.extend(self._validate_api_configuration(config_dict))
        errors.extend(self._validate_resource_limits(config_dict))
        errors.extend(self._validate_llm_configuration(config_dict))
        
        # Generate warnings for suboptimal settings
        warnings.extend(self._generate_configuration_warnings(config_dict))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_webhook_secret(self, config_dict: Dict[str, Any]) -> List[str]:
        """Validate webhook secret with enhanced security checks."""
        errors = []
        if 'webhook_secret' in config_dict:
            secret = config_dict['webhook_secret']
            if not isinstance(secret, str):
                errors.append("webhook_secret must be a string")
            elif len(secret) < 32:
                errors.append("webhook_secret must be at least 32 characters long")
            elif secret.lower() in ['secret', 'password', 'key', 'webhook']:
                errors.append("webhook_secret cannot be a common word")
            elif len(set(secret)) < 8:
                errors.append("webhook_secret should contain more character variety")
        return errors
    
    def _validate_api_configuration(self, config_dict: Dict[str, Any]) -> List[str]:
        """Validate API configuration parameters."""
        errors = []
        
        if 'api_port' in config_dict:
            port = config_dict['api_port']
            if not isinstance(port, int) or not (1 <= port <= 65535):
                errors.append("api_port must be an integer between 1 and 65535")
            elif port < 1024 and port != 80 and port != 443:
                errors.append("api_port below 1024 requires root privileges")
        
        if 'api_host' in config_dict:
            host = config_dict['api_host']
            if not isinstance(host, str):
                errors.append("api_host must be a string")
            elif host not in ['0.0.0.0', '127.0.0.1', 'localhost'] and not host.replace('.', '').isdigit():
                # Basic validation - in production, use proper IP validation
                pass  # Allow custom hostnames
        
        return errors
    
    def _validate_resource_limits(self, config_dict: Dict[str, Any]) -> List[str]:
        """Validate resource limit parameters."""
        errors = []
        
        if 'max_concurrent_emails' in config_dict:
            max_emails = config_dict['max_concurrent_emails']
            if not isinstance(max_emails, int) or max_emails <= 0:
                errors.append("max_concurrent_emails must be a positive integer")
            elif max_emails > 10000:
                errors.append("max_concurrent_emails exceeds reasonable limit (10000)")
        
        return errors
    
    def _validate_llm_configuration(self, config_dict: Dict[str, Any]) -> List[str]:
        """Validate LLM analyzer configuration."""
        errors = []
        
        if 'llm_analyzer_mode' in config_dict:
            mode = config_dict['llm_analyzer_mode']
            if not isinstance(mode, str):
                errors.append("llm_analyzer_mode must be a string")
            elif mode.lower() not in self.VALID_LLM_MODES:
                errors.append(f"llm_analyzer_mode must be one of: {self.VALID_LLM_MODES}")
        
        return errors
    
    def _generate_configuration_warnings(self, config_dict: Dict[str, Any]) -> List[str]:
        """Generate warnings for suboptimal but valid configurations."""
        warnings = []
        
        # Check for development-like settings in production
        if config_dict.get('environment') == 'production':
            if config_dict.get('api_host') == '127.0.0.1':
                warnings.append("Production deployment should use '0.0.0.0' to accept external connections")
            
            if config_dict.get('max_concurrent_emails', 0) < 50:
                warnings.append("Production deployment should handle at least 50 concurrent emails")
        
        return warnings
    
    def validate_security(self, config_dict: Dict[str, Any]) -> SecurityValidationResult:
        """Validate security configuration."""
        warnings = []
        recommendations = []
        
        # Check webhook secret strength
        if 'webhook_secret' in config_dict:
            secret = config_dict['webhook_secret']
            if isinstance(secret, str) and len(secret) < 64:
                warnings.append("webhook_secret should be at least 64 characters for maximum security")
        
        # Check HTTPS requirement
        security_config = config_dict.get('security', {})
        if not security_config.get('require_https', False):
            warnings.append("require_https should be enabled for production deployments")
            recommendations.append("Enable HTTPS with valid SSL certificates")
        
        # Check webhook signature validation
        if not security_config.get('webhook_signature_validation', False):
            warnings.append("webhook_signature_validation should be enabled")
            recommendations.append("Enable webhook signature validation to prevent unauthorized requests")
        
        # Check database URL security
        if 'database_url' in config_dict:
            db_url = config_dict['database_url']
            if isinstance(db_url, str) and db_url.startswith('http://'):
                warnings.append("database_url uses insecure HTTP protocol")
                recommendations.append("Use SSL-enabled database connections")
        
        return SecurityValidationResult(
            is_secure=len(warnings) == 0,
            security_warnings=warnings,
            recommendations=recommendations
        )