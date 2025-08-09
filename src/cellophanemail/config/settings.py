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
    
    # Plugin settings
    enabled_plugins: List[str] = Field(
        default=["smtp", "postmark"], 
        description="Enabled email input plugins"
    )
    
    # SaaS settings
    stripe_api_key: str = Field(default="", description="Stripe API key")
    stripe_webhook_secret: str = Field(default="", description="Stripe webhook secret")
    
    @property
    def piccolo_config(self):
        """Piccolo ORM configuration."""
        return {
            "database_url": self.database_url,
            "app_name": "cellophanemail",
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()