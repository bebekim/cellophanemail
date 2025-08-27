"""Interface for webhook orchestrators supporting different processing strategies."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Protocol

from ...core.webhook_models import PostmarkWebhookPayload


class WebhookOrchestrator(Protocol):
    """Protocol for webhook orchestrators that process inbound emails."""
    
    async def process_webhook(self, webhook_payload: PostmarkWebhookPayload) -> Dict[str, Any]:
        """
        Process webhook payload and return response data.
        
        Args:
            webhook_payload: Inbound email webhook data
            
        Returns:
            Dict containing status, message_id, and processing info
        """
        ...


class BaseWebhookOrchestrator(ABC):
    """Abstract base class for webhook orchestrators with common functionality."""
    
    @abstractmethod
    async def process_webhook(self, webhook_payload: PostmarkWebhookPayload) -> Dict[str, Any]:
        """Process webhook through specific strategy (database, privacy, etc.)."""
        pass
    
    def _create_response(
        self, 
        status: str, 
        message_id: str, 
        processing_type: str,
        **additional_fields
    ) -> Dict[str, Any]:
        """Create standardized response format."""
        response = {
            "status": status,
            "message_id": message_id,
            "processing": processing_type
        }
        response.update(additional_fields)
        return response