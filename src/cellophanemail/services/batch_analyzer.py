"""Batch analyzer service for processing multiple messages."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID

from cellophanemail.models import (
    MessageAnalysis,
    MessageChannel,
    MessageDirection,
    SenderSummary,
)
from cellophanemail.features.email_protection.analyzer_factory import AnalyzerFactory
from cellophanemail.services.aggregation_service import AggregationService

logger = logging.getLogger(__name__)


class BatchAnalyzerService:
    """Service for batch message analysis with Four Horsemen detection."""

    # Sync batch size limit
    SYNC_BATCH_LIMIT = 100

    # Async job batch size limit
    ASYNC_BATCH_LIMIT = 1000

    def __init__(self, user_id: UUID):
        """
        Initialize batch analyzer for a specific user.

        Args:
            user_id: UUID of the authenticated user
        """
        self.user_id = user_id
        self.analyzer = AnalyzerFactory.create_analyzer()
        self.aggregation_service = AggregationService(user_id)

    async def process_batch(
        self,
        messages: List[Dict[str, Any]],
        privacy_settings: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of messages synchronously.

        Args:
            messages: List of message dicts with content and metadata
            privacy_settings: Optional privacy configuration

        Returns:
            List of analysis results

        Raises:
            ValueError: If batch exceeds sync limit
        """
        if len(messages) > self.SYNC_BATCH_LIMIT:
            raise ValueError(
                f"Batch size {len(messages)} exceeds sync limit of {self.SYNC_BATCH_LIMIT}. "
                "Use async job endpoint for larger batches."
            )

        privacy = privacy_settings or {"store_body": False, "body_ttl_hours": 24}
        results: List[Dict[str, Any]] = []

        for message in messages:
            try:
                analysis = await self.analyze_single(message, privacy)
                results.append(self._format_result(analysis, message))
            except Exception as e:
                logger.error(f"Failed to analyze message {message.get('client_message_id')}: {e}")
                results.append({
                    "client_message_id": message.get("client_message_id"),
                    "success": False,
                    "error": str(e),
                })

        return results

    async def analyze_single(
        self,
        message: Dict[str, Any],
        privacy_settings: Dict[str, Any],
    ) -> MessageAnalysis:
        """
        Analyze a single message for Four Horsemen patterns.

        Args:
            message: Message dict with content and metadata
            privacy_settings: Privacy configuration for body storage

        Returns:
            MessageAnalysis record (saved to DB)
        """
        client_message_id = message.get("client_message_id", "")
        content = message.get("content", "")
        sender = message.get("sender", "")
        channel = message.get("channel", "sms")
        direction = message.get("direction", "inbound")
        timestamp = message.get("timestamp")

        # Check for existing analysis (idempotency)
        existing = await (
            MessageAnalysis.select()
            .where(MessageAnalysis.user == self.user_id)
            .where(MessageAnalysis.client_message_id == client_message_id)
            .first()
            .run()
        )

        if existing:
            logger.debug(f"Returning existing analysis for {client_message_id}")
            return existing

        # Call LLM analyzer
        analysis_result = self.analyzer.analyze_email_toxicity(
            email_content=content,
            sender_email=sender,
        )

        # Extract horsemen data
        horsemen_detected = [
            {
                "type": h.horseman,
                "confidence": h.confidence,
                "severity": h.severity,
                "indicators": h.indicators,
            }
            for h in analysis_result.horsemen_detected
        ]

        horsemen_types = {h.horseman for h in analysis_result.horsemen_detected}

        # Determine body storage based on privacy settings
        message_body = None
        body_expires_at = None

        if privacy_settings.get("store_body", False):
            message_body = content
            ttl_hours = privacy_settings.get("body_ttl_hours", 24)
            body_expires_at = datetime.now() + timedelta(hours=ttl_hours)

        # Create analysis record
        analysis = MessageAnalysis(
            user=self.user_id,
            client_message_id=client_message_id,
            channel=self._parse_channel(channel),
            sender_identifier=sender,
            direction=self._parse_direction(direction),
            message_timestamp=timestamp,
            horsemen_detected=horsemen_detected,
            has_horsemen=len(horsemen_detected) > 0,
            has_criticism="criticism" in horsemen_types,
            has_contempt="contempt" in horsemen_types,
            has_defensiveness="defensiveness" in horsemen_types,
            has_stonewalling="stonewalling" in horsemen_types,
            # toxicity_score is deprecated - threat_level derived from horsemen
            threat_level=analysis_result.threat_level.value,
            reasoning=analysis_result.reasoning,
            message_body=message_body,
            body_expires_at=body_expires_at,
            processing_time_ms=analysis_result.processing_time_ms,
            model_used=getattr(self.analyzer, "model_name", "unknown"),
            analyzed_at=datetime.now(),
        )

        await analysis.save().run()

        # Update sender aggregates
        await self.aggregation_service.update_for_analysis(
            analysis=analysis,
            channel=channel,
        )

        return analysis

    def _format_result(
        self,
        analysis: MessageAnalysis,
        original_message: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Format analysis result for API response."""
        horsemen_types = []
        if analysis.has_criticism:
            horsemen_types.append("criticism")
        if analysis.has_contempt:
            horsemen_types.append("contempt")
        if analysis.has_defensiveness:
            horsemen_types.append("defensiveness")
        if analysis.has_stonewalling:
            horsemen_types.append("stonewalling")

        return {
            "client_message_id": analysis.client_message_id,
            "horsemen": analysis.horsemen_detected,
            "horsemen_types": horsemen_types,
            "has_horsemen": analysis.has_horsemen,
            "threat_level": analysis.threat_level,
            "reasoning": analysis.reasoning,
            "processing_time_ms": analysis.processing_time_ms,
            "success": True,
        }

    def _parse_channel(self, channel: str) -> str:
        """Parse channel string to enum value."""
        channel_lower = channel.lower()
        if channel_lower in ("sms", "email", "chat", "other"):
            return channel_lower
        return MessageChannel.OTHER.value

    def _parse_direction(self, direction: str) -> str:
        """Parse direction string to enum value."""
        direction_lower = direction.lower()
        if direction_lower in ("inbound", "outbound"):
            return direction_lower
        return MessageDirection.INBOUND.value
