"""Storage optimization service for cost reduction."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
from ..models.email_log import EmailLog
from ..models.user import User

logger = logging.getLogger(__name__)


class StorageOptimizationService:
    """Service to optimize storage costs through data lifecycle management."""
    
    def __init__(self):
        # Retention policies for different plan tiers
        self.retention_policies = {
            'starter': {
                'full_retention_days': 7,      # Full content for 7 days
                'metadata_retention_days': 30,  # Metadata only for 30 days
                'total_retention_days': 30      # Complete deletion after 30 days
            },
            'plus': {
                'full_retention_days': 14,     # Full content for 14 days
                'metadata_retention_days': 60,  # Metadata only for 60 days
                'total_retention_days': 60      # Complete deletion after 60 days
            },
            'professional': {
                'full_retention_days': 30,     # Full content for 30 days
                'metadata_retention_days': 90,  # Metadata only for 90 days
                'total_retention_days': 90      # Complete deletion after 90 days
            }
        }
    
    async def archive_old_content(self, plan_type: str = 'starter') -> Dict:
        """Archive email content to reduce storage costs."""
        policy = self.retention_policies.get(plan_type, self.retention_policies['starter'])
        cutoff_date = datetime.now() - timedelta(days=policy['full_retention_days'])
        
        # Find emails older than full retention period but still within metadata retention
        emails_to_archive = await EmailLog.select().where(
            (EmailLog.created_at < cutoff_date) &
            (EmailLog.content_archived == False) &
            (EmailLog.original_content.is_not_null() | EmailLog.filtered_content.is_not_null())
        )
        
        archived_count = 0
        for email in emails_to_archive:
            # In production, would compress and move to cheaper storage (S3 Glacier, etc.)
            # For now, just clear the content to save database space
            await email.update(
                original_content=None,
                filtered_content=None,
                content_archived=True
            )
            archived_count += 1
        
        logger.info(f"Archived content for {archived_count} emails (plan: {plan_type})")
        return {
            'archived_count': archived_count,
            'plan_type': plan_type,
            'retention_days': policy['full_retention_days']
        }
    
    async def cleanup_old_metadata(self, plan_type: str = 'starter') -> Dict:
        """Remove old email metadata to reduce storage costs."""
        policy = self.retention_policies.get(plan_type, self.retention_policies['starter'])
        cutoff_date = datetime.now() - timedelta(days=policy['total_retention_days'])
        
        # Find emails older than total retention period
        old_emails = await EmailLog.select().where(
            EmailLog.created_at < cutoff_date
        )
        
        deleted_count = 0
        for email in old_emails:
            await email.remove()
            deleted_count += 1
        
        logger.info(f"Deleted {deleted_count} old email records (plan: {plan_type})")
        return {
            'deleted_count': deleted_count,
            'plan_type': plan_type,
            'retention_days': policy['total_retention_days']
        }
    
    async def optimize_user_storage(self, user_id: str) -> Dict:
        """Optimize storage for a specific user based on their plan."""
        # Get user's plan type
        user = await User.select().where(User.id == user_id).first()
        if not user:
            return {'error': 'User not found'}
        
        # Determine plan type from subscription status
        plan_type = 'starter'  # Default
        if hasattr(user, 'subscription_status'):
            if 'professional' in str(user.subscription_status).lower():
                plan_type = 'professional'
            elif 'plus' in str(user.subscription_status).lower():
                plan_type = 'plus'
        
        # Archive content and cleanup old data
        archive_result = await self.archive_old_content(plan_type)
        cleanup_result = await self.cleanup_old_metadata(plan_type)
        
        return {
            'user_id': user_id,
            'plan_type': plan_type,
            'archived': archive_result,
            'cleaned': cleanup_result
        }
    
    async def get_storage_stats(self) -> Dict:
        """Get storage usage statistics for cost monitoring."""
        # Count emails by content status
        total_emails = await EmailLog.count()
        archived_emails = await EmailLog.count().where(EmailLog.content_archived == True)
        with_content = await EmailLog.count().where(
            (EmailLog.original_content.is_not_null()) |
            (EmailLog.filtered_content.is_not_null())
        )
        
        # Estimate storage costs (rough calculation)
        # Assume: 1KB per email metadata, 5KB per email with content
        metadata_only_count = archived_emails
        full_content_count = with_content
        
        estimated_storage_kb = (metadata_only_count * 1) + (full_content_count * 5)
        estimated_monthly_cost = estimated_storage_kb * 0.000023  # $0.023 per GB/month for PostgreSQL
        
        return {
            'total_emails': total_emails,
            'emails_with_content': full_content_count,
            'archived_emails': archived_emails,
            'estimated_storage_kb': estimated_storage_kb,
            'estimated_monthly_cost_usd': round(estimated_monthly_cost, 4)
        }


# Convenience function for background tasks
async def run_daily_storage_optimization():
    """Run daily storage optimization for all plan types."""
    service = StorageOptimizationService()
    
    results = {}
    for plan_type in ['starter', 'plus', 'professional']:
        archive_result = await service.archive_old_content(plan_type)
        cleanup_result = await service.cleanup_old_metadata(plan_type)
        results[plan_type] = {
            'archived': archive_result,
            'cleaned': cleanup_result
        }
    
    stats = await service.get_storage_stats()
    results['storage_stats'] = stats
    
    logger.info(f"Daily storage optimization completed: {results}")
    return results