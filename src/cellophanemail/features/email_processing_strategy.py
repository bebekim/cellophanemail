"""
Email Processing Strategy Manager - Routes emails through privacy or normal pipelines.

This module implements the Strategy pattern to cleanly separate privacy-focused 
in-memory processing from traditional database-logging processing, based on 
environment configuration.
"""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Protocol, Union

from ..core.email_message import EmailMessage
from ..core.webhook_models import PostmarkWebhookPayload
from .privacy_integration.privacy_webhook_orchestrator import PrivacyWebhookOrchestrator
from .email_protection import EmailProtectionProcessor
from .shield_addresses import ShieldAddressManager

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """Email processing mode configuration."""
    NORMAL = "normal"      # Database logging, 200 OK responses
    PRIVACY = "privacy"    # In-memory only, 202 Accepted responses


@dataclass
class ProcessingConfig:
    """Configuration for email processing behavior."""
    mode: ProcessingMode
    privacy_enabled: bool
    
    @classmethod
    def from_environment(cls) -> 'ProcessingConfig':
        """Create configuration from environment variables."""
        privacy_mode = os.getenv('PRIVACY_MODE', 'false').lower() == 'true'
        return cls(
            mode=ProcessingMode.PRIVACY if privacy_mode else ProcessingMode.NORMAL,
            privacy_enabled=privacy_mode
        )


@dataclass  
class ProcessingResult:
    """Unified result from either processing strategy."""
    status_code: int
    response_data: Dict[str, Any]
    processing_mode: ProcessingMode


class EmailProcessingStrategy(ABC):
    """Abstract strategy for email processing."""
    
    @abstractmethod
    async def process(
        self, 
        webhook_payload: PostmarkWebhookPayload,
        user_context: Dict[str, Any]
    ) -> ProcessingResult:
        """Process email through specific strategy."""
        pass


class PrivacyProcessingStrategy(EmailProcessingStrategy):
    """Privacy-focused in-memory processing strategy."""
    
    def __init__(self):
        self.orchestrator = PrivacyWebhookOrchestrator()
    
    async def process(
        self, 
        webhook_payload: PostmarkWebhookPayload,
        user_context: Dict[str, Any]
    ) -> ProcessingResult:
        """Process email through privacy pipeline."""
        logger.info(f"Processing email {webhook_payload.MessageID} through privacy pipeline")
        
        response_data = await self.orchestrator.process_webhook(webhook_payload)
        
        # Privacy pipeline returns 202 Accepted for async processing
        return ProcessingResult(
            status_code=202,
            response_data=response_data,
            processing_mode=ProcessingMode.PRIVACY
        )


class NormalProcessingStrategy(EmailProcessingStrategy):
    """Traditional database-logging processing strategy."""
    
    def __init__(self):
        self.protection_processor = EmailProtectionProcessor()
        self.shield_manager = ShieldAddressManager()
    
    async def process(
        self, 
        webhook_payload: PostmarkWebhookPayload,
        user_context: Dict[str, Any]
    ) -> ProcessingResult:
        """Process email through normal pipeline with database logging."""
        logger.info(f"Processing email {webhook_payload.MessageID} through normal pipeline")
        
        # Create EmailMessage from webhook
        email_message = EmailMessage.from_postmark_webhook(webhook_payload.model_dump())
        
        # Set user context
        email_message.user_id = str(user_context["id"])
        email_message.organization_id = str(user_context["organization"]) if user_context.get("organization") else None
        email_message.to_addresses = [user_context["email"]]
        email_message.shield_address = webhook_payload.To.lower().strip()
        
        # Look up shield info for processing
        shield_info = await self.shield_manager.lookup_user_by_shield_address(
            email_message.shield_address
        )
        if not shield_info:
            return ProcessingResult(
                status_code=404,
                response_data={"error": "Shield address not found", "message_id": webhook_payload.MessageID},
                processing_mode=ProcessingMode.NORMAL
            )
        
        # Process through protection feature
        protection_result = await self.protection_processor.process_email(
            email_message,
            user_email=shield_info.user_email,
            organization_id=shield_info.organization_id
        )
        
        # Build response data
        response_data = {
            "status": "accepted",
            "message_id": webhook_payload.MessageID,
            "user_id": str(user_context["id"]),
            "toxicity_score": protection_result.analysis.toxicity_score if protection_result.analysis else 0.0,
            "processing_time_ms": protection_result.analysis.processing_time_ms if protection_result.analysis else 0
        }
        
        if protection_result.should_forward:
            response_data["processing"] = "forwarded"
        else:
            response_data.update({
                "processing": "blocked",
                "block_reason": protection_result.block_reason,
                "horsemen_detected": [h.horseman for h in (protection_result.analysis.horsemen_detected if protection_result.analysis else [])]
            })
        
        return ProcessingResult(
            status_code=200,
            response_data=response_data,
            processing_mode=ProcessingMode.NORMAL
        )


class ProcessingStrategyManager:
    """Manages switching between privacy and normal email processing strategies."""
    
    def __init__(self, config: ProcessingConfig = None):
        """Initialize with processing configuration."""
        self.config = config or ProcessingConfig.from_environment()
        
        # Initialize strategies
        if self.config.privacy_enabled:
            self.strategy = PrivacyProcessingStrategy()
            logger.info("Email processing configured for PRIVACY mode")
        else:
            self.strategy = NormalProcessingStrategy()
            logger.info("Email processing configured for NORMAL mode")
    
    async def process_email(
        self, 
        webhook_payload: PostmarkWebhookPayload,
        user_context: Dict[str, Any]
    ) -> ProcessingResult:
        """
        Route email through appropriate processing pipeline.
        
        Args:
            webhook_payload: Inbound email data from webhook
            user_context: User and organization information
            
        Returns:
            ProcessingResult with status code and response data
        """
        try:
            return await self.strategy.process(webhook_payload, user_context)
        except Exception as e:
            logger.error(f"Error in {self.config.mode.value} processing: {e}", exc_info=True)
            
            # Return appropriate error response based on mode
            if self.config.privacy_enabled:
                return ProcessingResult(
                    status_code=503,
                    response_data={
                        "error": "Privacy processing unavailable",
                        "message_id": webhook_payload.MessageID
                    },
                    processing_mode=ProcessingMode.PRIVACY
                )
            else:
                return ProcessingResult(
                    status_code=500,
                    response_data={
                        "error": "Internal processing error", 
                        "message_id": webhook_payload.MessageID
                    },
                    processing_mode=ProcessingMode.NORMAL
                )