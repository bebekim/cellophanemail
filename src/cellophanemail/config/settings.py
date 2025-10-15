"""CellophoneMail configuration settings."""

from functools import lru_cache
from typing import List
import os

from pydantic import Field, field_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """CellophoneMail application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # App settings
    debug: bool = Field(default=False, description="Debug mode")
    testing: bool = Field(default=False, description="Testing mode")
    host: str = Field(default="127.0.0.1", description="Host to bind to")
    port: int = Field(default=8000, description="Port to bind to")
    secret_key: str = Field(
        description="Secret key for JWT and sessions (min 32 chars, no defaults)"
    )
    encryption_key: str = Field(
        default="",
        description="Encryption key for sensitive data"
    )
    
    # Database settings
    database_url: str = Field(
        description="Database URL for Piccolo ORM (no default password allowed)"
    )
    database_echo: bool = Field(default=False, description="Echo SQL queries")
    
    # Redis settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching and rate limiting"
    )
    
    # CORS settings
    cors_allowed_origins: str = Field(
        default="http://localhost:3000,https://cellophanemail.com",
        description="Allowed CORS origins (comma-separated)"
    )

    @property
    def cors_allowed_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if isinstance(self.cors_allowed_origins, str):
            return [origin.strip() for origin in self.cors_allowed_origins.split(',')]
        return self.cors_allowed_origins
    
    # AI Service settings (preserve from protectedtex)
    anthropic_api_key: str = Field(description="Anthropic API key")
    upstage_api_key: str = Field(default="", description="Upstage API key")
    ai_provider: str = Field(default="anthropic", description="AI provider (anthropic, upstage)")
    ai_model: str = Field(
        default="claude-3-5-sonnet-20241022", 
        description="AI model for content analysis"
    )
    ai_max_tokens: int = Field(default=1000, description="Max tokens for AI")
    
    # Email settings (preserve from protectedtex)
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP host")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")
    email_username: str = Field(description="Email username")
    email_password: str = Field(description="Email password")
    smtp_domain: str = Field(default="cellophanemail.com", description="Service domain for email")
    
    # Outbound email delivery settings
    email_delivery_method: str = Field(
        default="smtp", 
        description="Email delivery method: 'smtp' or 'postmark'"
    )
    outbound_smtp_host: str = Field(default="smtp.gmail.com", description="Outbound SMTP host")
    outbound_smtp_port: int = Field(default=587, description="Outbound SMTP port")
    outbound_smtp_use_tls: bool = Field(default=True, description="Use TLS for outbound SMTP")
    
    # Postmark settings
    postmark_api_token: str = Field(default="", description="Postmark API token")
    postmark_server_id: str = Field(default="", description="Postmark Server ID")
    postmark_account_api_token: str = Field(default="", description="Postmark Account API token")
    postmark_from_email: str = Field(default="", description="Default from email for Postmark")
    postmark_from_address: str = Field(default="", description="Default from address for Postmark (alias for from_email)")
    postmark_dry_run: bool = Field(default=False, description="Enable Postmark dry-run mode")
    
    # Plugin settings
    enabled_plugins: str = Field(
        default="smtp,postmark",
        description="Enabled email input plugins (comma-separated)"
    )

    @property
    def enabled_plugins_list(self) -> List[str]:
        """Parse enabled plugins from comma-separated string."""
        if isinstance(self.enabled_plugins, str):
            return [plugin.strip() for plugin in self.enabled_plugins.split(',') if plugin.strip()]
        return self.enabled_plugins
    
    # SaaS settings
    stripe_api_key: str = Field(default="", description="Stripe API key")
    stripe_webhook_secret: str = Field(default="", description="Stripe webhook secret")

    # Feature flags
    privacy_safe_logging: bool = Field(default=True, description="Enable privacy-safe logging mode")
    llm_analyzer_mode: str = Field(default="privacy", description="LLM analyzer mode (privacy/standard)")

    # Validation methods
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key strength."""
        if not v or len(v.strip()) == 0:
            raise ValueError("SECRET_KEY is required and cannot be empty")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        if v == "dev-secret-key-change-in-production":
            raise ValueError("Default SECRET_KEY is not allowed in any environment")
        if v.lower() in ['secret', 'password', 'changeme', 'default']:
            raise ValueError("SECRET_KEY is too weak - detected common weak value")
        # Check for sufficient entropy (basic check)
        if len(set(v)) < 8:
            raise ValueError("SECRET_KEY should contain more character variety for security")
        return v

    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL doesn't contain default password."""
        if not v or len(v.strip()) == 0:
            raise ValueError("DATABASE_URL is required and cannot be empty")
        if 'password@' in v.lower():
            raise ValueError("DATABASE_URL cannot contain default 'password' - use a secure password")
        if 'postgres:password' in v.lower():
            raise ValueError("DATABASE_URL contains default postgres credentials - change password")
        return v

    @field_validator('anthropic_api_key')
    @classmethod
    def validate_anthropic_api_key(cls, v: str) -> str:
        """Validate Anthropic API key format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("ANTHROPIC_API_KEY is required for AI features")
        if not v.startswith('sk-ant-api03-'):
            raise ValueError("ANTHROPIC_API_KEY must be a valid Anthropic API key format")
        if len(v) < 50:
            raise ValueError("ANTHROPIC_API_KEY appears to be invalid (too short)")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug and not self.testing

    @property
    def piccolo_config(self):
        """Piccolo ORM configuration."""
        return {
            "database_url": self.database_url,
            "app_name": "cellophanemail",
        }
    
    @property
    def email_delivery_config(self):
        """Email delivery configuration for EmailSenderFactory."""
        return {
            'EMAIL_DELIVERY_METHOD': self.email_delivery_method,
            'SMTP_DOMAIN': self.smtp_domain,
            'EMAIL_USERNAME': self.email_username,
            'EMAIL_PASSWORD': self.email_password,
            'OUTBOUND_SMTP_HOST': self.outbound_smtp_host,
            'OUTBOUND_SMTP_PORT': self.outbound_smtp_port,
            'OUTBOUND_SMTP_USE_TLS': self.outbound_smtp_use_tls,
            'POSTMARK_API_TOKEN': self.postmark_api_token,
            'POSTMARK_FROM_EMAIL': self.postmark_from_email or f'noreply@{self.smtp_domain}',
            'SERVICE_CONSTANTS': {}
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()