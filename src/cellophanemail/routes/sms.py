# ABOUTME: Android SMS batch analysis API endpoints (STATELESS MODE)
# ABOUTME: Sync batch (≤100), async jobs (≤1000) - returns all data in response
# ABOUTME: Client stores everything locally, no round-trips for aggregates

import logging
from collections import defaultdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from litestar import Controller, get, post, Request
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_202_ACCEPTED
from litestar.exceptions import NotFoundException, HTTPException
from pydantic import BaseModel, Field

from cellophanemail.middleware.jwt_auth import jwt_auth_required, JWTUser
from cellophanemail.models import (
    MessageAnalysis,
    SenderSummary,
    AnalysisJob,
    JobStatus,
)
from cellophanemail.services.batch_analyzer import BatchAnalyzerService
from cellophanemail.services.aggregation_service import AggregationService

logger = logging.getLogger(__name__)

# Engine version for client compatibility tracking
ENGINE_VERSION = "v1"


# ============================================================================
# Request DTOs
# ============================================================================


class MessageInput(BaseModel):
    """Single message for batch analysis."""

    client_message_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique message ID from client (e.g., 'sms:123456')",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Message content to analyze",
    )
    sender: str = Field(
        ...,
        max_length=500,
        description="Sender identifier (phone number, email, etc.)",
    )
    channel: str = Field(
        default="sms",
        description="Message channel: sms, email, chat, other",
    )
    direction: str = Field(
        default="inbound",
        description="Message direction: inbound, outbound",
    )
    timestamp: Optional[int] = Field(
        None,
        description="Message timestamp (Unix epoch ms)",
    )


class PrivacySettings(BaseModel):
    """Privacy configuration for message body storage."""

    store_body: bool = Field(
        default=False,
        description="Whether to store message body for LLM evaluation",
    )
    body_ttl_hours: int = Field(
        default=24,
        ge=1,
        le=168,  # Max 1 week
        description="TTL in hours for stored message bodies",
    )


class BatchAnalyzeRequest(BaseModel):
    """Request for synchronous batch analysis (≤100 messages)."""

    messages: List[MessageInput] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Messages to analyze (max 100)",
    )
    privacy: Optional[PrivacySettings] = Field(
        default=None,
        description="Optional privacy settings for body storage",
    )


class CreateJobRequest(BaseModel):
    """Request for async job creation (≤1000 messages)."""

    messages: List[MessageInput] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Messages to analyze (max 1000)",
    )
    privacy: Optional[PrivacySettings] = Field(
        default=None,
        description="Optional privacy settings for body storage",
    )


class MessageQueryParams(BaseModel):
    """Query parameters for message listing."""

    sender: Optional[str] = Field(None, description="Filter by sender identifier")
    channel: Optional[str] = Field(None, description="Filter by channel")
    has_horsemen: Optional[bool] = Field(None, description="Filter by horsemen presence")
    horseman_type: Optional[str] = Field(None, description="Filter by specific horseman type")
    limit: int = Field(50, ge=1, le=100, description="Max results")
    offset: int = Field(0, ge=0, description="Pagination offset")


# ============================================================================
# Response DTOs
# ============================================================================


class HorsemanDetail(BaseModel):
    """Detailed horseman detection."""

    type: str
    confidence: float
    severity: str
    indicators: List[str]


class MessageAnalysisResponse(BaseModel):
    """Single message analysis result."""

    client_message_id: str
    horsemen: List[HorsemanDetail]
    horsemen_types: List[str]
    has_horsemen: bool
    toxicity_score: float
    threat_level: str
    reasoning: str
    processing_time_ms: Optional[int]
    success: bool
    error: Optional[str] = None


# ============================================================================
# Stateless Response DTOs (computed from batch, not stored)
# Must be defined before BatchAnalyzeResponse which references them
# ============================================================================


class HorsemenCounts(BaseModel):
    """Counts of each horseman type detected."""

    CRITICISM: int = 0
    CONTEMPT: int = 0
    DEFENSIVENESS: int = 0
    STONEWALLING: int = 0


class BatchSenderSummary(BaseModel):
    """
    Per-sender aggregates computed from batch results.

    Client should upsert this into local sender cache.
    """

    senderId: str = Field(..., description="Normalized sender identifier")
    filteredCount: int = Field(0, description="Messages with any horsemen detected")
    cleanCount: int = Field(0, description="Messages without horsemen (safe)")
    totalInBatch: int = Field(0, description="Total messages from this sender in batch")
    lastFilteredTimestampMs: Optional[int] = Field(None, description="Most recent filtered message timestamp")
    horsemenCounts: HorsemenCounts = Field(default_factory=HorsemenCounts)


class DashboardRollup(BaseModel):
    """
    Quick stats for dashboard update.

    Computed from the batch results so client can update UI immediately.
    """

    totalAnalyzed: int = Field(0, description="Total messages in this batch")
    filteredMessages: int = Field(0, description="Messages with horsemen detected")
    cleanMessages: int = Field(0, description="Messages without horsemen")
    uniqueSenders: int = Field(0, description="Unique senders in this batch")
    sendersWithFiltered: int = Field(0, description="Senders that have filtered messages")


class BatchAnalyzeResponse(BaseModel):
    """
    Response for batch analysis (STATELESS MODE).

    Contains everything the client needs to update local state:
    - results: Per-message analysis
    - senderSummaries: Per-sender aggregates for this batch
    - dashboardRollup: Quick stats for dashboard update
    """

    engineVersion: str = Field(ENGINE_VERSION, description="Analysis engine version")
    results: List[MessageAnalysisResponse]
    total: int
    successful: int
    failed: int
    senderSummaries: List[BatchSenderSummary] = Field(
        default_factory=list,
        description="Per-sender aggregates computed from this batch"
    )
    dashboardRollup: DashboardRollup = Field(
        default_factory=DashboardRollup,
        description="Aggregated stats for quick dashboard update"
    )


class JobStatusResponse(BaseModel):
    """Job status and progress."""

    job_id: str
    status: str
    total_messages: int
    processed_messages: int
    failed_messages: int
    progress_percent: float
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]


class SenderSummaryResponse(BaseModel):
    """Sender aggregate statistics (for deprecated GET endpoint)."""

    sender_identifier: str
    channel: str
    total_messages: int
    messages_with_horsemen: int
    clean_messages: int
    horsemen_counts: dict
    first_message_at: Optional[str]
    last_message_at: Optional[str]
    last_horseman_at: Optional[str]


# ============================================================================
# Controllers
# ============================================================================


class SMSAnalysisController(Controller):
    """SMS batch analysis endpoints."""

    path = "/api/v1/sms"
    tags = ["SMS Analysis"]
    guards = [jwt_auth_required]

    @post("/analyze:batch", status_code=HTTP_200_OK)
    async def batch_analyze(
        self,
        request: Request,
        data: BatchAnalyzeRequest,
    ) -> BatchAnalyzeResponse:
        """
        Analyze a batch of messages synchronously (STATELESS MODE).

        Returns complete results including per-sender summaries and dashboard
        rollup so client can update local state without additional API calls.

        Max 100 messages. For larger batches, use the job endpoint.
        """
        user: JWTUser = request.user
        user_id = UUID(user.id)

        logger.info(f"Batch analyze: {len(data.messages)} messages for user {user_id}")

        # Build sender lookup from input
        sender_by_message: Dict[str, str] = {
            msg.client_message_id: msg.sender for msg in data.messages
        }
        timestamp_by_message: Dict[str, Optional[int]] = {
            msg.client_message_id: msg.timestamp for msg in data.messages
        }

        # Convert messages to dicts
        messages = [msg.model_dump() for msg in data.messages]
        privacy = (data.privacy.model_dump() if data.privacy else {"store_body": False, "body_ttl_hours": 24})

        # Process batch
        service = BatchAnalyzerService(user_id=user_id)
        results = await service.process_batch(messages=messages, privacy_settings=privacy)

        # Format response and compute aggregates
        response_results: List[MessageAnalysisResponse] = []
        successful = 0
        failed = 0

        # Aggregation structures
        sender_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "filteredCount": 0,
            "cleanCount": 0,
            "totalInBatch": 0,
            "lastFilteredTimestampMs": None,
            "horsemenCounts": {"CRITICISM": 0, "CONTEMPT": 0, "DEFENSIVENESS": 0, "STONEWALLING": 0},
        })
        total_filtered = 0
        total_clean = 0

        for r in results:
            client_msg_id = r.get("client_message_id", "unknown")
            sender_id = sender_by_message.get(client_msg_id, "unknown")
            timestamp_ms = timestamp_by_message.get(client_msg_id)

            if r.get("success", False):
                successful += 1
                has_horsemen = r.get("has_horsemen", False)
                horsemen_types = r.get("horsemen_types", [])

                response_results.append(MessageAnalysisResponse(
                    client_message_id=client_msg_id,
                    horsemen=[
                        HorsemanDetail(**h) for h in r.get("horsemen", [])
                    ],
                    horsemen_types=horsemen_types,
                    has_horsemen=has_horsemen,
                    toxicity_score=r.get("toxicity_score", 0.0),
                    threat_level=r.get("threat_level", "safe"),
                    reasoning=r.get("reasoning", ""),
                    processing_time_ms=r.get("processing_time_ms"),
                    success=True,
                ))

                # Update sender aggregates
                sender_stats[sender_id]["totalInBatch"] += 1

                if has_horsemen:
                    sender_stats[sender_id]["filteredCount"] += 1
                    total_filtered += 1

                    # Track last filtered timestamp
                    if timestamp_ms:
                        current_last = sender_stats[sender_id]["lastFilteredTimestampMs"]
                        if current_last is None or timestamp_ms > current_last:
                            sender_stats[sender_id]["lastFilteredTimestampMs"] = timestamp_ms

                    # Count individual horsemen
                    for ht in horsemen_types:
                        ht_upper = ht.upper()
                        if ht_upper in sender_stats[sender_id]["horsemenCounts"]:
                            sender_stats[sender_id]["horsemenCounts"][ht_upper] += 1
                else:
                    sender_stats[sender_id]["cleanCount"] += 1
                    total_clean += 1
            else:
                failed += 1
                response_results.append(MessageAnalysisResponse(
                    client_message_id=client_msg_id,
                    horsemen=[],
                    horsemen_types=[],
                    has_horsemen=False,
                    toxicity_score=0.0,
                    threat_level="unknown",
                    reasoning="",
                    processing_time_ms=None,
                    success=False,
                    error=r.get("error", "Unknown error"),
                ))

        # Build sender summaries
        sender_summaries = [
            BatchSenderSummary(
                senderId=sender_id,
                filteredCount=stats["filteredCount"],
                cleanCount=stats["cleanCount"],
                totalInBatch=stats["totalInBatch"],
                lastFilteredTimestampMs=stats["lastFilteredTimestampMs"],
                horsemenCounts=HorsemenCounts(**stats["horsemenCounts"]),
            )
            for sender_id, stats in sender_stats.items()
        ]

        # Build dashboard rollup
        senders_with_filtered = sum(1 for s in sender_stats.values() if s["filteredCount"] > 0)
        dashboard_rollup = DashboardRollup(
            totalAnalyzed=successful,
            filteredMessages=total_filtered,
            cleanMessages=total_clean,
            uniqueSenders=len(sender_stats),
            sendersWithFiltered=senders_with_filtered,
        )

        return BatchAnalyzeResponse(
            engineVersion=ENGINE_VERSION,
            results=response_results,
            total=len(results),
            successful=successful,
            failed=failed,
            senderSummaries=sender_summaries,
            dashboardRollup=dashboard_rollup,
        )

    @post("/analyze:job", status_code=HTTP_202_ACCEPTED)
    async def create_job(
        self,
        request: Request,
        data: CreateJobRequest,
    ) -> JobStatusResponse:
        """
        Create an async analysis job for larger batches.

        Max 1000 messages. Returns job ID for status polling.
        """
        user: JWTUser = request.user
        user_id = UUID(user.id)

        logger.info(f"Create job: {len(data.messages)} messages for user {user_id}")

        # Create job record
        privacy = (data.privacy.model_dump() if data.privacy else {"store_body": False, "body_ttl_hours": 24})
        message_ids = [msg.client_message_id for msg in data.messages]

        job = AnalysisJob(
            user=user_id,
            status=JobStatus.PENDING.value,
            total_messages=len(data.messages),
            processed_messages=0,
            failed_messages=0,
            message_ids=message_ids,
            privacy_settings=privacy,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await job.save().run()

        # Enqueue async task (if Redis available)
        try:
            from arq import create_pool
            from cellophanemail.jobs.settings import get_redis_settings

            redis = await create_pool(get_redis_settings())
            messages_data = [msg.model_dump() for msg in data.messages]

            arq_job = await redis.enqueue_job(
                "analyze_batch_task",
                str(job.id),
                str(user_id),
                messages_data,
                privacy,
            )

            # Update job with arq reference
            job.arq_job_id = arq_job.job_id
            await job.save().run()

            logger.info(f"Enqueued job {job.id} as arq job {arq_job.job_id}")
        except Exception as e:
            logger.warning(f"Failed to enqueue job, Redis may not be available: {e}")
            # Job stays in PENDING state - could be picked up by a worker later
            # or processed via polling

        return JobStatusResponse(
            job_id=str(job.id),
            status=job.status,
            total_messages=job.total_messages,
            processed_messages=job.processed_messages,
            failed_messages=job.failed_messages,
            progress_percent=0.0,
            created_at=job.created_at.isoformat() if job.created_at else "",
            started_at=None,
            completed_at=None,
            error_message=None,
        )


class AnalysisController(Controller):
    """Analysis results and job management endpoints."""

    path = "/api/v1/analysis"
    tags = ["Analysis"]
    guards = [jwt_auth_required]

    @get("/jobs/{job_id:str}", status_code=HTTP_200_OK)
    async def get_job_status(
        self,
        request: Request,
        job_id: str,
    ) -> JobStatusResponse:
        """Get status and progress of an analysis job."""
        user: JWTUser = request.user
        user_id = UUID(user.id)

        try:
            job_uuid = UUID(job_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid job ID format")

        job = await (
            AnalysisJob.select()
            .where(AnalysisJob.id == job_uuid)
            .where(AnalysisJob.user == user_id)
            .first()
            .run()
        )

        if not job:
            raise NotFoundException(f"Job {job_id} not found")

        progress = 0.0
        if job.total_messages > 0:
            progress = (job.processed_messages / job.total_messages) * 100

        return JobStatusResponse(
            job_id=str(job.id),
            status=job.status,
            total_messages=job.total_messages,
            processed_messages=job.processed_messages,
            failed_messages=job.failed_messages,
            progress_percent=progress,
            created_at=job.created_at.isoformat() if job.created_at else "",
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            error_message=job.error_message,
        )

    @get("/jobs/{job_id:str}/results", status_code=HTTP_200_OK)
    async def get_job_results(
        self,
        request: Request,
        job_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> BatchAnalyzeResponse:
        """
        Get paginated results for a completed job (STATELESS MODE).

        Returns results with senderSummaries and dashboardRollup computed
        from the paginated results for incremental client updates.
        """
        user: JWTUser = request.user
        user_id = UUID(user.id)

        try:
            job_uuid = UUID(job_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid job ID format")

        # Verify job belongs to user
        job = await (
            AnalysisJob.select()
            .where(AnalysisJob.id == job_uuid)
            .where(AnalysisJob.user == user_id)
            .first()
            .run()
        )

        if not job:
            raise NotFoundException(f"Job {job_id} not found")

        # Get message IDs from job
        message_ids = job.message_ids or []
        if offset >= len(message_ids):
            return BatchAnalyzeResponse(
                engineVersion=ENGINE_VERSION,
                results=[],
                total=0,
                successful=0,
                failed=0,
                senderSummaries=[],
                dashboardRollup=DashboardRollup(),
            )

        # Slice for pagination
        paginated_ids = message_ids[offset:offset + limit]

        # Query analyses for these message IDs
        analyses = await (
            MessageAnalysis.select()
            .where(MessageAnalysis.user == user_id)
            .where(MessageAnalysis.client_message_id.is_in(paginated_ids))
            .run()
        )

        # Build response with aggregates
        results: List[MessageAnalysisResponse] = []
        sender_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "filteredCount": 0,
            "cleanCount": 0,
            "totalInBatch": 0,
            "lastFilteredTimestampMs": None,
            "horsemenCounts": {"CRITICISM": 0, "CONTEMPT": 0, "DEFENSIVENESS": 0, "STONEWALLING": 0},
        })
        total_filtered = 0
        total_clean = 0

        for analysis in analyses:
            horsemen = analysis.horsemen_detected or []
            horsemen_types = []
            if analysis.has_criticism:
                horsemen_types.append("criticism")
            if analysis.has_contempt:
                horsemen_types.append("contempt")
            if analysis.has_defensiveness:
                horsemen_types.append("defensiveness")
            if analysis.has_stonewalling:
                horsemen_types.append("stonewalling")

            results.append(MessageAnalysisResponse(
                client_message_id=analysis.client_message_id,
                horsemen=[HorsemanDetail(**h) for h in horsemen],
                horsemen_types=horsemen_types,
                has_horsemen=analysis.has_horsemen,
                toxicity_score=(analysis.toxicity_score or 0) / 1000.0,
                threat_level=analysis.threat_level or "unknown",
                reasoning=analysis.reasoning or "",
                processing_time_ms=analysis.processing_time_ms,
                success=True,
            ))

            # Compute sender aggregates
            sender_id = analysis.sender_identifier or "unknown"
            sender_stats[sender_id]["totalInBatch"] += 1

            if analysis.has_horsemen:
                sender_stats[sender_id]["filteredCount"] += 1
                total_filtered += 1

                if analysis.message_timestamp:
                    current_last = sender_stats[sender_id]["lastFilteredTimestampMs"]
                    if current_last is None or analysis.message_timestamp > current_last:
                        sender_stats[sender_id]["lastFilteredTimestampMs"] = analysis.message_timestamp

                for ht in horsemen_types:
                    ht_upper = ht.upper()
                    if ht_upper in sender_stats[sender_id]["horsemenCounts"]:
                        sender_stats[sender_id]["horsemenCounts"][ht_upper] += 1
            else:
                sender_stats[sender_id]["cleanCount"] += 1
                total_clean += 1

        # Build sender summaries
        sender_summaries = [
            BatchSenderSummary(
                senderId=sender_id,
                filteredCount=stats["filteredCount"],
                cleanCount=stats["cleanCount"],
                totalInBatch=stats["totalInBatch"],
                lastFilteredTimestampMs=stats["lastFilteredTimestampMs"],
                horsemenCounts=HorsemenCounts(**stats["horsemenCounts"]),
            )
            for sender_id, stats in sender_stats.items()
        ]

        # Build dashboard rollup
        senders_with_filtered = sum(1 for s in sender_stats.values() if s["filteredCount"] > 0)
        dashboard_rollup = DashboardRollup(
            totalAnalyzed=len(results),
            filteredMessages=total_filtered,
            cleanMessages=total_clean,
            uniqueSenders=len(sender_stats),
            sendersWithFiltered=senders_with_filtered,
        )

        return BatchAnalyzeResponse(
            engineVersion=ENGINE_VERSION,
            results=results,
            total=len(message_ids),
            successful=len(results),
            failed=job.failed_messages,
            senderSummaries=sender_summaries,
            dashboardRollup=dashboard_rollup,
        )

    @get("/senders/{sender_id:str}/summary", status_code=HTTP_200_OK)
    async def get_sender_summary(
        self,
        request: Request,
        sender_id: str,
        channel: Optional[str] = None,
    ) -> SenderSummaryResponse:
        """
        Get aggregated statistics for a specific sender.

        DEPRECATED: In stateless mode, client should compute sender summaries
        locally from batch results. This endpoint remains for backwards
        compatibility but may be removed in a future version.
        """
        user: JWTUser = request.user
        user_id = UUID(user.id)

        service = AggregationService(user_id=user_id)
        summary = await service.get_sender_summary(
            sender_identifier=sender_id,
            channel=channel,
        )

        if not summary:
            raise NotFoundException(f"Sender {sender_id} not found")

        return SenderSummaryResponse(
            sender_identifier=summary.sender_identifier,
            channel=summary.channel,
            total_messages=summary.total_messages or 0,
            messages_with_horsemen=summary.messages_with_horsemen or 0,
            clean_messages=summary.clean_messages or 0,
            horsemen_counts=summary.horsemen_counts or {},
            first_message_at=summary.first_message_at.isoformat() if summary.first_message_at else None,
            last_message_at=summary.last_message_at.isoformat() if summary.last_message_at else None,
            last_horseman_at=summary.last_horseman_at.isoformat() if summary.last_horseman_at else None,
        )

    @get("/messages", status_code=HTTP_200_OK)
    async def list_messages(
        self,
        request: Request,
        sender: Optional[str] = None,
        channel: Optional[str] = None,
        has_horsemen: Optional[bool] = None,
        horseman_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[MessageAnalysisResponse]:
        """
        Query analyzed messages with filters.

        DEPRECATED: In stateless mode, client should store and query messages
        locally. This endpoint remains for backwards compatibility but may be
        removed in a future version.
        """
        user: JWTUser = request.user
        user_id = UUID(user.id)

        # Build query
        query = MessageAnalysis.select().where(MessageAnalysis.user == user_id)

        if sender:
            query = query.where(MessageAnalysis.sender_identifier == sender)

        if channel:
            query = query.where(MessageAnalysis.channel == channel.lower())

        if has_horsemen is True:
            query = query.where(MessageAnalysis.has_horsemen == True)
        elif has_horsemen is False:
            query = query.where(MessageAnalysis.has_horsemen == False)

        if horseman_type:
            ht = horseman_type.lower()
            if ht == "criticism":
                query = query.where(MessageAnalysis.has_criticism == True)
            elif ht == "contempt":
                query = query.where(MessageAnalysis.has_contempt == True)
            elif ht == "defensiveness":
                query = query.where(MessageAnalysis.has_defensiveness == True)
            elif ht == "stonewalling":
                query = query.where(MessageAnalysis.has_stonewalling == True)

        query = query.order_by(MessageAnalysis.analyzed_at, ascending=False)
        query = query.limit(limit).offset(offset)

        analyses = await query.run()

        results = []
        for analysis in analyses:
            horsemen = analysis.horsemen_detected or []
            horsemen_types = []
            if analysis.has_criticism:
                horsemen_types.append("criticism")
            if analysis.has_contempt:
                horsemen_types.append("contempt")
            if analysis.has_defensiveness:
                horsemen_types.append("defensiveness")
            if analysis.has_stonewalling:
                horsemen_types.append("stonewalling")

            results.append(MessageAnalysisResponse(
                client_message_id=analysis.client_message_id,
                horsemen=[HorsemanDetail(**h) for h in horsemen],
                horsemen_types=horsemen_types,
                has_horsemen=analysis.has_horsemen,
                toxicity_score=(analysis.toxicity_score or 0) / 1000.0,
                threat_level=analysis.threat_level or "unknown",
                reasoning=analysis.reasoning or "",
                processing_time_ms=analysis.processing_time_ms,
                success=True,
            ))

        return results
