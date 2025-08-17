"""Webhook provider abstractions and implementations."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List

from litestar import Request
from pydantic import BaseModel, ValidationError

from ..core.email_message import EmailMessage

logger = logging.getLogger(__name__)


@dataclass
class WebhookPayload:
    """Base class for all webhook payloads."""
    message_id: str
    provider: str
    raw_data: Dict[str, Any]
    received_at: datetime = None
    
    def __post_init__(self):
        if self.received_at is None:
            self.received_at = datetime.now()


class PostmarkWebhookPayload(BaseModel):
    """Postmark inbound webhook payload structure."""
    
    From: str
    FromName: Optional[str] = None
    To: str
    ToFull: Optional[List[Dict[str, str]]] = None
    Subject: str
    MessageID: str
    Date: str
    TextBody: Optional[str] = None
    HtmlBody: Optional[str] = None
    Tag: Optional[str] = None
    Headers: Optional[List[Dict[str, str]]] = None
    Attachments: Optional[List[Dict[str, Any]]] = None


class WebhookProvider(ABC):
    """Abstract base class for webhook providers."""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name identifier."""
        pass
    
    @abstractmethod
    async def validate_payload(self, request: Request, data: Dict[str, Any]) -> bool:
        """Validate provider-specific webhook payload.
        
        Args:
            request: HTTP request object
            data: Raw webhook payload data
            
        Returns:
            True if payload is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def parse_payload(self, data: Dict[str, Any]) -> WebhookPayload:
        """Parse provider payload into standardized format.
        
        Args:
            data: Raw webhook payload data
            
        Returns:
            Standardized WebhookPayload instance
            
        Raises:
            ValueError: If payload cannot be parsed
        """
        pass
    
    @abstractmethod
    def create_email_message(self, payload: WebhookPayload) -> EmailMessage:
        """Create EmailMessage from provider payload.
        
        Args:
            payload: Standardized webhook payload
            
        Returns:
            EmailMessage instance ready for processing
        """
        pass


class PostmarkWebhookProvider(WebhookProvider):
    """Postmark webhook provider implementation."""
    
    @property
    def provider_name(self) -> str:
        return "postmark"
    
    async def validate_payload(self, request: Request, data: Dict[str, Any]) -> bool:
        """Validate Postmark webhook payload structure.
        
        # TDD_IMPLEMENT: Postmark signature validation
        # TDD_IMPLEMENT: Required field validation
        # TDD_IMPLEMENT: Message ID format validation
        """
        try:
            # Validate payload structure using Pydantic
            PostmarkWebhookPayload(**data)
            
            # TODO: TDD_IMPLEMENT: Postmark webhook signature validation
            # if request.headers.get("X-Postmark-Signature"):
            #     return self._verify_postmark_signature(request, data)
            
            return True
            
        except ValidationError as e:
            logger.warning(f"Invalid Postmark payload structure: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating Postmark payload: {e}")
            return False
    
    def parse_payload(self, data: Dict[str, Any]) -> WebhookPayload:
        """Parse Postmark payload into standardized format.
        
        # TDD_IMPLEMENT: Extract message ID from Postmark format
        # TDD_IMPLEMENT: Handle malformed Postmark data gracefully
        """
        try:
            # Validate and parse using Pydantic model
            postmark_payload = PostmarkWebhookPayload(**data)
            
            return WebhookPayload(
                message_id=postmark_payload.MessageID,
                provider=self.provider_name,
                raw_data=data
            )
            
        except ValidationError as e:
            raise ValueError(f"Invalid Postmark payload: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing Postmark payload: {e}")
    
    def create_email_message(self, payload: WebhookPayload) -> EmailMessage:
        """Create EmailMessage from Postmark webhook payload.
        
        # TDD_IMPLEMENT: Postmark to EmailMessage conversion
        # TDD_IMPLEMENT: Handle missing optional fields gracefully
        # TDD_IMPLEMENT: Set proper source plugin identifier
        """
        try:
            # Use existing Postmark parsing logic
            email_message = EmailMessage.from_postmark_webhook(payload.raw_data)
            
            # Ensure source plugin is set correctly
            email_message.source_plugin = self.provider_name
            
            return email_message
            
        except Exception as e:
            raise ValueError(f"Error creating EmailMessage from Postmark payload: {e}")


class GmailWebhookProvider(WebhookProvider):
    """Gmail webhook provider implementation (placeholder for future)."""
    
    @property
    def provider_name(self) -> str:
        return "gmail"
    
    async def validate_payload(self, request: Request, data: Dict[str, Any]) -> bool:
        """Validate Gmail webhook payload.
        
        # TDD_IMPLEMENT: Gmail push notification validation
        # TDD_IMPLEMENT: Google Cloud Pub/Sub message verification
        """
        # TODO: TDD_IMPLEMENT: Gmail webhook validation logic
        logger.warning("Gmail webhook validation not yet implemented")
        return False
    
    def parse_payload(self, data: Dict[str, Any]) -> WebhookPayload:
        """Parse Gmail payload into standardized format.
        
        # TDD_IMPLEMENT: Gmail push notification parsing
        # TDD_IMPLEMENT: Extract historyId and messageId from Gmail format
        """
        # TODO: TDD_IMPLEMENT: Gmail payload parsing
        raise NotImplementedError("Gmail webhook parsing not yet implemented")
    
    def create_email_message(self, payload: WebhookPayload) -> EmailMessage:
        """Create EmailMessage from Gmail webhook payload.
        
        # TDD_IMPLEMENT: Gmail API message fetching
        # TDD_IMPLEMENT: Gmail message to EmailMessage conversion
        """
        # TODO: TDD_IMPLEMENT: Gmail message creation
        raise NotImplementedError("Gmail message creation not yet implemented")


class TestWebhookProvider(WebhookProvider):
    """Test webhook provider for development."""
    
    @property
    def provider_name(self) -> str:
        return "test"
    
    async def validate_payload(self, request: Request, data: Dict[str, Any]) -> bool:
        """Always validates test payloads.
        
        # TDD_IMPLEMENT: Basic test payload validation
        """
        return isinstance(data, dict) and "test" in data
    
    def parse_payload(self, data: Dict[str, Any]) -> WebhookPayload:
        """Parse test payload.
        
        # TDD_IMPLEMENT: Test payload parsing with mock data
        """
        return WebhookPayload(
            message_id=data.get("message_id", "test-message"),
            provider=self.provider_name,
            raw_data=data
        )
    
    def create_email_message(self, payload: WebhookPayload) -> EmailMessage:
        """Create test EmailMessage.
        
        # TDD_IMPLEMENT: Test message creation with safe defaults
        """
        return EmailMessage(
            from_address="test@example.com",
            to_addresses=["test@cellophanemail.com"],
            subject="Test Message",
            message_id=payload.message_id,
            text_content="Test email content",
            source_plugin=self.provider_name
        )


class WebhookProviderRegistry:
    """Registry for managing webhook providers."""
    
    def __init__(self):
        """Initialize registry with default providers.
        
        # TDD_IMPLEMENT: Provider registration system
        # TDD_IMPLEMENT: Provider lookup by name
        """
        self._providers: Dict[str, WebhookProvider] = {}
        
        # Register default providers
        self.register_provider(PostmarkWebhookProvider())
        self.register_provider(GmailWebhookProvider())
        self.register_provider(TestWebhookProvider())
    
    def register_provider(self, provider: WebhookProvider) -> None:
        """Register a webhook provider.
        
        # TDD_IMPLEMENT: Provider registration with validation
        # TDD_IMPLEMENT: Prevent duplicate provider names
        """
        if not isinstance(provider, WebhookProvider):
            raise ValueError("Provider must implement WebhookProvider interface")
        
        self._providers[provider.provider_name] = provider
        logger.info(f"Registered webhook provider: {provider.provider_name}")
    
    def get_provider(self, provider_name: str) -> Optional[WebhookProvider]:
        """Get provider by name.
        
        # TDD_IMPLEMENT: Provider lookup with error handling
        """
        return self._providers.get(provider_name)
    
    def list_providers(self) -> List[str]:
        """List all registered provider names.
        
        # TDD_IMPLEMENT: Provider enumeration
        """
        return list(self._providers.keys())


# Global provider registry instance
provider_registry = WebhookProviderRegistry()