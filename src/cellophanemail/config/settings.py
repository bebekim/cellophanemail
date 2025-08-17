"""CellophoneMail configuration settings."""

from functools import lru_cache
from typing import List
import os

from pydantic import Field
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
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT and sessions"
    )
    encryption_key: str = Field(
        default="",
        description="Encryption key for sensitive data"
    )
    
    # Database settings  
    database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/cellophanemail",
        description="Database URL for Piccolo ORM"
    )
    database_echo: bool = Field(default=False, description="Echo SQL queries")
    
    # Redis settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching and rate limiting"
    )
    
    # CORS settings
    cors_allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "https://cellophanemail.com"],
        description="Allowed CORS origins"
    )
    
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
    
    # Plugin settings
    enabled_plugins: List[str] = Field(
        default=["smtp", "postmark"], 
        description="Enabled email input plugins"
    )
    
    # SaaS settings
    stripe_api_key: str = Field(default="", description="Stripe API key")
    stripe_webhook_secret: str = Field(default="", description="Stripe webhook secret")
    
    # OAuth settings
    google_client_id: str = Field(default="", description="Google OAuth client ID")
    google_client_secret: str = Field(default="", description="Google OAuth client secret")
    google_redirect_uri: str = Field(default="", description="Google OAuth redirect URI")
    
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