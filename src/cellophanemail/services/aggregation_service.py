"""Aggregation service for sender-level Four Horsemen statistics."""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

from cellophanemail.models import (
    MessageAnalysis,
    SenderSummary,
    MessageChannel,
)

logger = logging.getLogger(__name__)


class AggregationService:
    """Service for managing sender-level aggregates."""

    def __init__(self, user_id: UUID):
        """
        Initialize aggregation service for a specific user.

        Args:
            user_id: UUID of the authenticated user
        """
        self.user_id = user_id

    async def update_for_analysis(
        self,
        analysis: MessageAnalysis,
        channel: str,
    ) -> SenderSummary:
        """
        Update sender aggregates after a new message analysis.

        Args:
            analysis: The MessageAnalysis record
            channel: Message channel (sms, email, etc.)

        Returns:
            Updated SenderSummary record
        """
        sender_id = analysis.sender_identifier
        channel_value = self._parse_channel(channel)

        # Get or create sender summary
        summary = await (
            SenderSummary.select()
            .where(SenderSummary.user == self.user_id)
            .where(SenderSummary.sender_identifier == sender_id)
            .where(SenderSummary.channel == channel_value)
            .first()
            .run()
        )

        now = datetime.now()

        if not summary:
            # Create new summary
            summary = SenderSummary(
                user=self.user_id,
                sender_identifier=sender_id,
                channel=channel_value,
                total_messages=0,
                messages_with_horsemen=0,
                clean_messages=0,
                criticism_count=0,
                contempt_count=0,
                defensiveness_count=0,
                stonewalling_count=0,
                horsemen_counts={
                    "criticism": 0,
                    "contempt": 0,
                    "defensiveness": 0,
                    "stonewalling": 0,
                },
                first_message_at=now,
                last_message_at=now,
                created_at=now,
                updated_at=now,
            )

        # Increment message count
        summary.total_messages = (summary.total_messages or 0) + 1
        summary.last_message_at = now
        summary.updated_at = now

        # Update horsemen counts
        if analysis.has_horsemen:
            summary.messages_with_horsemen = (summary.messages_with_horsemen or 0) + 1
            summary.last_horseman_at = now

            # Update individual horseman counts
            horsemen_counts = summary.horsemen_counts or {
                "criticism": 0,
                "contempt": 0,
                "defensiveness": 0,
                "stonewalling": 0,
            }

            if analysis.has_criticism:
                summary.criticism_count = (summary.criticism_count or 0) + 1
                horsemen_counts["criticism"] = (horsemen_counts.get("criticism", 0) or 0) + 1

            if analysis.has_contempt:
                summary.contempt_count = (summary.contempt_count or 0) + 1
                horsemen_counts["contempt"] = (horsemen_counts.get("contempt", 0) or 0) + 1

            if analysis.has_defensiveness:
                summary.defensiveness_count = (summary.defensiveness_count or 0) + 1
                horsemen_counts["defensiveness"] = (horsemen_counts.get("defensiveness", 0) or 0) + 1

            if analysis.has_stonewalling:
                summary.stonewalling_count = (summary.stonewalling_count or 0) + 1
                horsemen_counts["stonewalling"] = (horsemen_counts.get("stonewalling", 0) or 0) + 1

            summary.horsemen_counts = horsemen_counts
        else:
            summary.clean_messages = (summary.clean_messages or 0) + 1

        await summary.save().run()
        return summary

    async def get_sender_summary(
        self,
        sender_identifier: str,
        channel: Optional[str] = None,
    ) -> Optional[SenderSummary]:
        """
        Get aggregated statistics for a specific sender.

        Args:
            sender_identifier: The sender's phone/email/username
            channel: Optional channel filter

        Returns:
            SenderSummary or None if not found
        """
        query = (
            SenderSummary.select()
            .where(SenderSummary.user == self.user_id)
            .where(SenderSummary.sender_identifier == sender_identifier)
        )

        if channel:
            channel_value = self._parse_channel(channel)
            query = query.where(SenderSummary.channel == channel_value)

        return await query.first().run()

    async def list_sender_summaries(
        self,
        channel: Optional[str] = None,
        has_horsemen: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "last_message_at",
        order_desc: bool = True,
    ) -> List[SenderSummary]:
        """
        List sender summaries with optional filters.

        Args:
            channel: Optional channel filter
            has_horsemen: Filter for senders with/without horsemen
            limit: Max results to return
            offset: Pagination offset
            order_by: Field to order by
            order_desc: Whether to order descending

        Returns:
            List of SenderSummary records
        """
        query = SenderSummary.select().where(SenderSummary.user == self.user_id)

        if channel:
            channel_value = self._parse_channel(channel)
            query = query.where(SenderSummary.channel == channel_value)

        if has_horsemen is True:
            query = query.where(SenderSummary.messages_with_horsemen > 0)
        elif has_horsemen is False:
            query = query.where(SenderSummary.messages_with_horsemen == 0)

        # Apply ordering
        order_field = getattr(SenderSummary, order_by, SenderSummary.last_message_at)
        if order_desc:
            query = query.order_by(order_field, ascending=False)
        else:
            query = query.order_by(order_field, ascending=True)

        query = query.limit(limit).offset(offset)

        return await query.run()

    async def get_user_stats(self) -> Dict[str, Any]:
        """
        Get overall statistics for the user.

        Returns:
            Dict with aggregated user statistics
        """
        summaries = await (
            SenderSummary.select()
            .where(SenderSummary.user == self.user_id)
            .run()
        )

        total_messages = sum(s.total_messages or 0 for s in summaries)
        total_horsemen = sum(s.messages_with_horsemen or 0 for s in summaries)
        total_clean = sum(s.clean_messages or 0 for s in summaries)

        horsemen_totals = {
            "criticism": sum(s.criticism_count or 0 for s in summaries),
            "contempt": sum(s.contempt_count or 0 for s in summaries),
            "defensiveness": sum(s.defensiveness_count or 0 for s in summaries),
            "stonewalling": sum(s.stonewalling_count or 0 for s in summaries),
        }

        return {
            "total_senders": len(summaries),
            "total_messages": total_messages,
            "messages_with_horsemen": total_horsemen,
            "clean_messages": total_clean,
            "horsemen_rate": total_horsemen / total_messages if total_messages > 0 else 0,
            "horsemen_totals": horsemen_totals,
        }

    def _parse_channel(self, channel: str) -> str:
        """Parse channel string to enum value."""
        channel_lower = channel.lower()
        if channel_lower in ("sms", "email", "chat", "other"):
            return channel_lower
        return MessageChannel.OTHER.value
