"""Pipeline tracer for detailed Four Horsemen analysis monitoring."""

import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid


class ProcessingStage(Enum):
    """Email processing pipeline stages."""
    WEBHOOK_RECEIVED = "webhook_received"
    EMAIL_PARSED = "email_parsed"
    CONTEXT_IDENTIFIED = "context_identified"
    ORG_LIMITS_CHECKED = "org_limits_checked"
    CONTENT_EXTRACTED = "content_extracted"
    CACHE_CHECKED = "cache_checked"
    LOCAL_ANALYSIS = "local_analysis"
    AI_ANALYSIS = "ai_analysis"
    CLASSIFICATION_DONE = "classification_done"
    FORWARD_DECISION = "forward_decision"
    EMAIL_LOGGED = "email_logged"
    EMAIL_FORWARDED = "email_forwarded"
    PROCESSING_COMPLETE = "processing_complete"


@dataclass
class StageTrace:
    """Individual stage trace information."""
    stage: ProcessingStage
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self, success: bool = True, error: Optional[str] = None, **metadata):
        """Mark stage as completed."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.success = success
        self.error = error
        self.metadata.update(metadata)


@dataclass
class PipelineTrace:
    """Complete pipeline trace for an email."""
    trace_id: str
    email_id: str
    sender: str
    language: str
    start_time: float
    end_time: Optional[float] = None
    total_duration_ms: Optional[float] = None
    stages: List[StageTrace] = field(default_factory=list)
    analysis_mode: str = "unknown"  # hybrid, traditional, local_only
    cache_hits: int = 0
    cache_misses: int = 0
    ai_api_calls: int = 0
    cost_optimization: str = "unknown"
    final_classification: Optional[str] = None
    horsemen_detected: List[str] = field(default_factory=list)
    should_forward: Optional[bool] = None
    
    def add_stage(self, stage: ProcessingStage, **metadata) -> StageTrace:
        """Add a new stage to the trace."""
        stage_trace = StageTrace(
            stage=stage,
            start_time=time.time(),
            metadata=metadata
        )
        self.stages.append(stage_trace)
        return stage_trace
    
    def complete_trace(self, **metadata):
        """Complete the entire pipeline trace."""
        self.end_time = time.time()
        self.total_duration_ms = (self.end_time - self.start_time) * 1000
        
        # Update final metadata
        for key, value in metadata.items():
            setattr(self, key, value)
    
    def get_stage_duration(self, stage: ProcessingStage) -> Optional[float]:
        """Get duration of a specific stage."""
        for stage_trace in self.stages:
            if stage_trace.stage == stage:
                return stage_trace.duration_ms
        return None
    
    def get_stage_metadata(self, stage: ProcessingStage) -> Dict[str, Any]:
        """Get metadata for a specific stage."""
        for stage_trace in self.stages:
            if stage_trace.stage == stage:
                return stage_trace.metadata
        return {}
    
    def get_performance_breakdown(self) -> Dict[str, float]:
        """Get performance breakdown by stage."""
        breakdown = {}
        for stage_trace in self.stages:
            if stage_trace.duration_ms is not None:
                breakdown[stage_trace.stage.value] = stage_trace.duration_ms
        return breakdown
    
    def get_error_stages(self) -> List[ProcessingStage]:
        """Get list of stages that had errors."""
        return [stage.stage for stage in self.stages if not stage.success]


class PipelineTracer:
    """Tracer for monitoring email processing pipeline."""
    
    def __init__(self):
        """Initialize the pipeline tracer."""
        self.logger = logging.getLogger(__name__)
        self.active_traces: Dict[str, PipelineTrace] = {}
        self.completed_traces: List[PipelineTrace] = []
        
    def start_trace(self, email_id: str, sender: str, language: str = "unknown") -> str:
        """Start a new pipeline trace."""
        trace_id = str(uuid.uuid4())
        
        trace = PipelineTrace(
            trace_id=trace_id,
            email_id=email_id,
            sender=sender,
            language=language,
            start_time=time.time()
        )
        
        self.active_traces[trace_id] = trace
        self.logger.info(f"🔍 [PipelineTracer] Started trace {trace_id} for email {email_id}")
        
        return trace_id
    
    def trace_stage(
        self, 
        trace_id: str, 
        stage: ProcessingStage, 
        success: bool = True, 
        error: Optional[str] = None,
        **metadata
    ):
        """Trace a processing stage."""
        if trace_id not in self.active_traces:
            self.logger.warning(f"Trace {trace_id} not found")
            return
            
        trace = self.active_traces[trace_id]
        
        # Find and complete the current stage if it exists
        current_stage = None
        for stage_trace in reversed(trace.stages):
            if stage_trace.end_time is None:
                current_stage = stage_trace
                break
        
        if current_stage and current_stage.stage != stage:
            # Complete the previous stage
            current_stage.complete(success=True)
        
        # Add new stage
        stage_trace = trace.add_stage(stage, **metadata)
        stage_trace.complete(success=success, error=error, **metadata)
        
        self.logger.info(
            f"🔍 [PipelineTracer] {trace_id} - {stage.value}: "
            f"{stage_trace.duration_ms:.2f}ms {'✅' if success else '❌'}"
        )
    
    def update_trace_metadata(self, trace_id: str, **metadata):
        """Update trace-level metadata."""
        if trace_id not in self.active_traces:
            self.logger.warning(f"Trace {trace_id} not found")
            return
            
        trace = self.active_traces[trace_id]
        for key, value in metadata.items():
            if hasattr(trace, key):
                setattr(trace, key, value)
    
    def complete_trace(self, trace_id: str, **final_metadata) -> Optional[PipelineTrace]:
        """Complete a pipeline trace."""
        if trace_id not in self.active_traces:
            self.logger.warning(f"Trace {trace_id} not found")
            return None
            
        trace = self.active_traces.pop(trace_id)
        
        # Complete any incomplete stages
        for stage_trace in trace.stages:
            if stage_trace.end_time is None:
                stage_trace.complete(success=True)
        
        trace.complete_trace(**final_metadata)
        self.completed_traces.append(trace)
        
        self.logger.info(
            f"🔍 [PipelineTracer] Completed trace {trace_id} - "
            f"Total: {trace.total_duration_ms:.2f}ms, "
            f"Classification: {trace.final_classification}, "
            f"Forward: {trace.should_forward}"
        )
        
        return trace
    
    def get_trace(self, trace_id: str) -> Optional[PipelineTrace]:
        """Get a specific trace."""
        if trace_id in self.active_traces:
            return self.active_traces[trace_id]
        
        for trace in self.completed_traces:
            if trace.trace_id == trace_id:
                return trace
                
        return None
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all completed traces."""
        if not self.completed_traces:
            return {"message": "No completed traces"}
        
        # Calculate averages
        total_traces = len(self.completed_traces)
        avg_total_duration = sum(trace.total_duration_ms for trace in self.completed_traces if trace.total_duration_ms) / total_traces
        
        # Stage performance averages
        stage_averages = {}
        for stage in ProcessingStage:
            stage_durations = []
            for trace in self.completed_traces:
                duration = trace.get_stage_duration(stage)
                if duration is not None:
                    stage_durations.append(duration)
            
            if stage_durations:
                stage_averages[stage.value] = {
                    "avg_ms": sum(stage_durations) / len(stage_durations),
                    "min_ms": min(stage_durations),
                    "max_ms": max(stage_durations),
                    "count": len(stage_durations)
                }
        
        # Analysis mode distribution
        analysis_modes = {}
        for trace in self.completed_traces:
            mode = trace.analysis_mode
            analysis_modes[mode] = analysis_modes.get(mode, 0) + 1
        
        # Cache performance
        total_cache_hits = sum(trace.cache_hits for trace in self.completed_traces)
        total_cache_misses = sum(trace.cache_misses for trace in self.completed_traces)
        cache_hit_rate = total_cache_hits / (total_cache_hits + total_cache_misses) if (total_cache_hits + total_cache_misses) > 0 else 0
        
        # AI API usage
        total_api_calls = sum(trace.ai_api_calls for trace in self.completed_traces)
        avg_api_calls = total_api_calls / total_traces if total_traces > 0 else 0
        
        return {
            "total_traces": total_traces,
            "avg_total_duration_ms": avg_total_duration,
            "stage_performance": stage_averages,
            "analysis_mode_distribution": analysis_modes,
            "cache_performance": {
                "total_hits": total_cache_hits,
                "total_misses": total_cache_misses,
                "hit_rate": cache_hit_rate
            },
            "api_usage": {
                "total_calls": total_api_calls,
                "avg_calls_per_email": avg_api_calls
            }
        }
    
    def get_language_performance(self) -> Dict[str, Any]:
        """Get performance breakdown by language."""
        language_stats = {}
        
        for trace in self.completed_traces:
            lang = trace.language
            if lang not in language_stats:
                language_stats[lang] = {
                    "count": 0,
                    "total_duration": 0,
                    "classifications": {},
                    "api_calls": 0,
                    "cache_hits": 0
                }
            
            stats = language_stats[lang]
            stats["count"] += 1
            if trace.total_duration_ms:
                stats["total_duration"] += trace.total_duration_ms
            stats["api_calls"] += trace.ai_api_calls
            stats["cache_hits"] += trace.cache_hits
            
            # Classification distribution
            classification = trace.final_classification or "unknown"
            stats["classifications"][classification] = stats["classifications"].get(classification, 0) + 1
        
        # Calculate averages
        for lang, stats in language_stats.items():
            if stats["count"] > 0:
                stats["avg_duration_ms"] = stats["total_duration"] / stats["count"]
                stats["avg_api_calls"] = stats["api_calls"] / stats["count"]
                stats["avg_cache_hits"] = stats["cache_hits"] / stats["count"]
        
        return language_stats
    
    def clear_traces(self):
        """Clear all traces (for testing)."""
        self.active_traces.clear()
        self.completed_traces.clear()
        self.logger.info("🔍 [PipelineTracer] Cleared all traces")


# Global tracer instance
pipeline_tracer = PipelineTracer()


def get_pipeline_tracer() -> PipelineTracer:
    """Get the global pipeline tracer instance."""
    return pipeline_tracer


# Convenient functions for direct use
def start_trace(email_id: str, sender: str, language: str = "unknown") -> str:
    """Start a new pipeline trace."""
    return pipeline_tracer.start_trace(email_id, sender, language)


def trace_stage(trace_id: str, stage: ProcessingStage, success: bool = True, error: Optional[str] = None, **metadata):
    """Trace a processing stage."""
    pipeline_tracer.trace_stage(trace_id, stage, success, error, **metadata)


def update_trace_metadata(trace_id: str, **metadata):
    """Update trace-level metadata."""
    pipeline_tracer.update_trace_metadata(trace_id, **metadata)


def complete_trace(trace_id: str, **final_metadata) -> Optional[PipelineTrace]:
    """Complete a pipeline trace."""
    return pipeline_tracer.complete_trace(trace_id, **final_metadata)


# Export all for easy import
__all__ = [
    "ProcessingStage",
    "StageTrace", 
    "PipelineTrace",
    "PipelineTracer",
    "pipeline_tracer",
    "get_pipeline_tracer",
    "start_trace",
    "trace_stage", 
    "update_trace_metadata",
    "complete_trace"
]
