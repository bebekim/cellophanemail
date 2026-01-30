"""Background task definitions for arq workers."""

import logging
from datetime import datetime
from typing import Dict, Any, List
from uuid import UUID

logger = logging.getLogger(__name__)


async def analyze_batch_task(
    ctx: dict,
    job_id: str,
    user_id: str,
    messages: List[Dict[str, Any]],
    privacy_settings: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Process a batch of messages asynchronously.

    Args:
        ctx: arq context (contains Redis connection)
        job_id: AnalysisJob UUID
        user_id: User UUID
        messages: List of message dicts to analyze
        privacy_settings: Privacy configuration for body storage

    Returns:
        Dict with processing results summary
    """
    from cellophanemail.models import AnalysisJob, JobStatus
    from cellophanemail.services.batch_analyzer import BatchAnalyzerService

    logger.info(f"Starting batch analysis job {job_id} with {len(messages)} messages")

    # Update job status to processing
    job_uuid = UUID(job_id)
    await (
        AnalysisJob.update({AnalysisJob.status: JobStatus.PROCESSING.value})
        .where(AnalysisJob.id == job_uuid)
        .run()
    )
    await (
        AnalysisJob.update({AnalysisJob.started_at: datetime.now()})
        .where(AnalysisJob.id == job_uuid)
        .run()
    )

    try:
        # Create batch analyzer service
        analyzer_service = BatchAnalyzerService(user_id=UUID(user_id))

        # Process messages in smaller chunks for progress updates
        chunk_size = 10
        processed = 0
        failed = 0
        failed_ids: List[str] = []
        results: List[Dict[str, Any]] = []

        for i in range(0, len(messages), chunk_size):
            chunk = messages[i:i + chunk_size]

            for message in chunk:
                try:
                    result = await analyzer_service.analyze_single(
                        message=message,
                        privacy_settings=privacy_settings,
                    )
                    results.append({
                        "client_message_id": message.get("client_message_id"),
                        "has_horsemen": result.has_horsemen,
                        "success": True,
                    })
                    processed += 1
                except Exception as e:
                    logger.error(f"Failed to analyze message {message.get('client_message_id')}: {e}")
                    failed += 1
                    failed_ids.append(message.get("client_message_id", "unknown"))
                    results.append({
                        "client_message_id": message.get("client_message_id"),
                        "success": False,
                        "error": str(e),
                    })

            # Update progress
            await (
                AnalysisJob.update({
                    AnalysisJob.processed_messages: processed,
                    AnalysisJob.failed_messages: failed,
                    AnalysisJob.updated_at: datetime.now(),
                })
                .where(AnalysisJob.id == job_uuid)
                .run()
            )

        # Mark job as completed
        final_status = JobStatus.COMPLETED.value if failed == 0 else JobStatus.COMPLETED.value
        await (
            AnalysisJob.update({
                AnalysisJob.status: final_status,
                AnalysisJob.completed_at: datetime.now(),
                AnalysisJob.failed_message_ids: failed_ids,
                AnalysisJob.updated_at: datetime.now(),
            })
            .where(AnalysisJob.id == job_uuid)
            .run()
        )

        logger.info(f"Completed batch analysis job {job_id}: {processed} processed, {failed} failed")

        return {
            "job_id": job_id,
            "processed": processed,
            "failed": failed,
            "status": final_status,
        }

    except Exception as e:
        logger.error(f"Batch analysis job {job_id} failed: {e}")

        # Mark job as failed
        await (
            AnalysisJob.update({
                AnalysisJob.status: JobStatus.FAILED.value,
                AnalysisJob.error_message: str(e),
                AnalysisJob.completed_at: datetime.now(),
                AnalysisJob.updated_at: datetime.now(),
            })
            .where(AnalysisJob.id == job_uuid)
            .run()
        )

        raise
