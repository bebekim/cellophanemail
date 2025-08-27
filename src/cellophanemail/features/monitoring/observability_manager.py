"""
Observability Management System for Privacy-Focused Email Processing

Unified observability with privacy-compliant logging, alerting, dashboard integration,
and comprehensive monitoring of the email protection pipeline.
"""

import time
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import logging

from .metrics_collector import MetricsCollector
from .health_monitor import HealthMonitor, HealthStatus

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LogLevel(Enum):
    """Logging levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LoggingConfig:
    """Configuration for privacy-compliant logging."""
    privacy_mode: bool = True
    content_redaction: bool = True
    metadata_only: bool = True
    max_log_entries: int = 1000
    log_level: LogLevel = LogLevel.INFO
    include_stack_traces: bool = False
    hash_sensitive_data: bool = True


@dataclass
class AlertingConfig:
    """Configuration for alerting system."""
    enabled: bool = True
    high_toxicity_threshold: float = 0.8
    performance_degradation_threshold_ms: float = 5000
    error_rate_threshold: float = 0.1
    memory_usage_threshold: float = 0.9
    cache_hit_rate_threshold: float = 0.5
    alert_cooldown_minutes: int = 15


@dataclass
class Alert:
    """Individual alert event."""
    id: str
    type: str
    severity: AlertSeverity
    message: str
    data: Dict[str, Any]
    timestamp: float
    resolved: bool = False
    resolved_timestamp: Optional[float] = None


@dataclass
class LogEntry:
    """Privacy-compliant log entry."""
    timestamp: float
    level: LogLevel
    component: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    duration_ms: Optional[float] = None


class ObservabilityManager:
    """
    Unified observability management system for privacy-focused email processing.
    
    Integrates metrics collection, health monitoring, alerting, and privacy-compliant
    logging to provide comprehensive system observability.
    """
    
    def __init__(self, memory_manager=None, max_logs: int = 1000, max_alerts: int = 500):
        """Initialize observability manager with configurable limits."""
        self.metrics_collector = MetricsCollector()
        self.health_monitor = HealthMonitor(memory_manager)
        
        # Configuration
        self.logging_config = LoggingConfig(max_log_entries=max_logs)
        self.alerting_config = AlertingConfig()
        
        # Storage with configurable limits
        self._log_entries: deque = deque(maxlen=max_logs)
        self._active_alerts: List[Alert] = []
        self._alert_history: deque = deque(maxlen=max_alerts)
        
        # Enhanced state tracking
        self._salt = str(time.time()).encode()
        self._last_alert_times: Dict[str, float] = {}
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes
        
        # Start time for uptime calculation
        self._start_time = time.time()
    
    def _periodic_cleanup(self) -> None:
        """Perform periodic cleanup of old data."""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            # Clean up old alert times
            self._last_alert_times = {
                k: v for k, v in self._last_alert_times.items()
                if current_time - v < self.alerting_config.alert_cooldown_minutes * 60 * 2
            }
            
            # Clean up resolved alerts older than 1 hour
            cutoff_time = current_time - 3600
            self._active_alerts = [
                alert for alert in self._active_alerts
                if not alert.resolved or (alert.resolved_timestamp and alert.resolved_timestamp > cutoff_time)
            ]
            
            self._last_cleanup = current_time
    
    def _hash_sensitive_data(self, data: str) -> str:
        """Create privacy-safe hash of sensitive data."""
        if not self.logging_config.hash_sensitive_data:
            return data
        return hashlib.sha256(self._salt + data.encode()).hexdigest()[:16]
    
    def configure_logging(self, config: LoggingConfig) -> None:
        """Configure logging behavior."""
        self.logging_config = config
        
        # Adjust log storage size
        if config.max_log_entries != self._log_entries.maxlen:
            old_entries = list(self._log_entries)
            self._log_entries = deque(old_entries, maxlen=config.max_log_entries)
    
    def configure_alerting(self, config: AlertingConfig) -> None:
        """Configure alerting behavior."""
        self.alerting_config = config
    
    def get_logging_config(self) -> LoggingConfig:
        """Get current logging configuration."""
        return self.logging_config
    
    def log_email_processed(self, message_id: str, processing_time_ms: float, 
                           toxicity_score: float, action: str, redact_sensitive_data: bool = True) -> None:
        """Log email processing event with privacy compliance."""
        # Perform periodic cleanup
        self._periodic_cleanup()
        
        # Create privacy-safe log entry
        metadata = {
            "processing_time_ms": processing_time_ms,
            "toxicity_score": toxicity_score,
            "action": action
        }
        
        if redact_sensitive_data and self.logging_config.privacy_mode:
            # Hash message ID for privacy
            correlation_id = self._hash_sensitive_data(message_id)
            message = f"Email processed with action {action}"
        else:
            correlation_id = message_id
            message = f"Email {message_id} processed with action {action}"
        
        self._add_log_entry(
            level=LogLevel.INFO,
            component="email_processor",
            message=message,
            metadata=metadata,
            correlation_id=correlation_id,
            duration_ms=processing_time_ms
        )
        
        # Update metrics - need to call the full sequence for proper metric tracking
        self.metrics_collector.record_email_received(message_id, "unknown@sender.com")
        self.metrics_collector.record_processing_start(message_id)
        self.metrics_collector.record_processing_complete(message_id, action, toxicity_score)
        
        # Check for alert conditions
        self._check_toxicity_alert(message_id, toxicity_score)
        self._check_performance_alert(processing_time_ms)
    
    def _add_log_entry(self, level: LogLevel, component: str, message: str,
                      metadata: Optional[Dict[str, Any]] = None,
                      correlation_id: Optional[str] = None,
                      duration_ms: Optional[float] = None) -> None:
        """Add log entry with level filtering."""
        # Check if log level meets threshold
        level_values = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }
        
        if level_values[level] < level_values[self.logging_config.log_level]:
            return  # Skip logs below threshold
        
        log_entry = LogEntry(
            timestamp=time.time(),
            level=level,
            component=component,
            message=message,
            metadata=metadata or {},
            correlation_id=correlation_id,
            duration_ms=duration_ms
        )
        
        self._log_entries.append(log_entry)
    
    def get_recent_logs(self, limit: int = 100, component: Optional[str] = None,
                       level: Optional[LogLevel] = None) -> List[Dict[str, Any]]:
        """Get recent log entries with optional filtering."""
        entries = list(self._log_entries)
        
        # Apply filters
        if component:
            entries = [e for e in entries if e.component == component]
        if level:
            entries = [e for e in entries if e.level == level]
        
        # Sort by timestamp (newest first) and limit
        entries.sort(key=lambda x: x.timestamp, reverse=True)
        entries = entries[:limit]
        
        # Convert to dictionary format
        return [
            {
                "timestamp": entry.timestamp,
                "level": entry.level.value,
                "component": entry.component,
                "message": entry.message,
                "metadata": entry.metadata,
                "correlation_id": entry.correlation_id,
                "duration_ms": entry.duration_ms
            }
            for entry in entries
        ]
    
    def record_high_toxicity_email(self, message_id: str, toxicity_score: float) -> None:
        """Record high toxicity email detection."""
        self.metrics_collector.record_toxic_email_detected(message_id, toxicity_score, [])
        
        self._add_log_entry(
            level=LogLevel.WARNING,
            component="toxicity_detector",
            message=f"High toxicity email detected (score: {toxicity_score:.3f})",
            metadata={"toxicity_score": toxicity_score, "threshold": self.alerting_config.high_toxicity_threshold},
            correlation_id=self._hash_sensitive_data(message_id)
        )
        
        # Also trigger alert check
        self._check_toxicity_alert(message_id, toxicity_score)
    
    def record_performance_degradation(self, processing_time_ms: float) -> None:
        """Record performance degradation event."""
        self._add_log_entry(
            level=LogLevel.WARNING,
            component="performance_monitor",
            message=f"Performance degradation detected ({processing_time_ms:.0f}ms)",
            metadata={"processing_time_ms": processing_time_ms, "threshold_ms": self.alerting_config.performance_degradation_threshold_ms},
            duration_ms=processing_time_ms
        )
        
        # Also trigger alert check
        self._check_performance_alert(processing_time_ms)
    
    def record_email_processing_complete(self, message_id: str, processing_time_ms: float, 
                                       toxicity_score: float, action: str) -> None:
        """Record email processing completion with full monitoring."""
        self.log_email_processed(message_id, processing_time_ms, toxicity_score, action, redact_sensitive_data=True)
    
    def _check_toxicity_alert(self, message_id: str, toxicity_score: float) -> None:
        """Check if toxicity score warrants an alert."""
        if not self.alerting_config.enabled:
            return
        
        if toxicity_score >= self.alerting_config.high_toxicity_threshold:
            alert_type = "high_toxicity"
            
            # Check cooldown
            last_alert = self._last_alert_times.get(alert_type, 0)
            if time.time() - last_alert < self.alerting_config.alert_cooldown_minutes * 60:
                return  # Still in cooldown
            
            # Create alert
            alert = Alert(
                id=f"{alert_type}_{int(time.time())}",
                type=alert_type,
                severity=AlertSeverity.HIGH if toxicity_score >= 0.9 else AlertSeverity.MEDIUM,
                message=f"High toxicity email detected with score {toxicity_score:.3f}",
                data={
                    "toxicity_score": toxicity_score,
                    "threshold": self.alerting_config.high_toxicity_threshold,
                    "message_id_hash": self._hash_sensitive_data(message_id)
                },
                timestamp=time.time()
            )
            
            self._add_alert(alert)
            self._last_alert_times[alert_type] = time.time()
    
    def _check_performance_alert(self, processing_time_ms: float) -> None:
        """Check if processing time warrants a performance alert."""
        if not self.alerting_config.enabled:
            return
        
        if processing_time_ms >= self.alerting_config.performance_degradation_threshold_ms:
            alert_type = "performance_degradation"
            
            # Check cooldown
            last_alert = self._last_alert_times.get(alert_type, 0)
            if time.time() - last_alert < self.alerting_config.alert_cooldown_minutes * 60:
                return
            
            # Create alert
            alert = Alert(
                id=f"{alert_type}_{int(time.time())}",
                type=alert_type,
                severity=AlertSeverity.MEDIUM,
                message=f"Performance degradation detected: {processing_time_ms:.0f}ms processing time",
                data={
                    "processing_time_ms": processing_time_ms,
                    "threshold_ms": self.alerting_config.performance_degradation_threshold_ms
                },
                timestamp=time.time()
            )
            
            self._add_alert(alert)
            self._last_alert_times[alert_type] = time.time()
    
    def _add_alert(self, alert: Alert) -> None:
        """Add alert to active alerts."""
        self._active_alerts.append(alert)
        self._alert_history.append(alert)
        
        # Log the alert
        self._add_log_entry(
            level=LogLevel.ERROR if alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL] else LogLevel.WARNING,
            component="alerting",
            message=f"Alert triggered: {alert.message}",
            metadata={"alert_id": alert.id, "severity": alert.severity.value, "type": alert.type}
        )
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active (unresolved) alerts."""
        return [
            {
                "id": alert.id,
                "type": alert.type,
                "severity": alert.severity.value,
                "message": alert.message,
                "data": alert.data,
                "timestamp": alert.timestamp,
                "age_minutes": (time.time() - alert.timestamp) / 60
            }
            for alert in self._active_alerts
            if not alert.resolved
        ]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert."""
        for alert in self._active_alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_timestamp = time.time()
                
                self._add_log_entry(
                    level=LogLevel.INFO,
                    component="alerting",
                    message=f"Alert resolved: {alert.message}",
                    metadata={"alert_id": alert_id, "resolution_time": alert.resolved_timestamp}
                )
                
                return True
        return False
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        health_status = self.health_monitor.get_overall_health()
        
        dashboard = {
            "timestamp": time.time(),
            "uptime_seconds": time.time() - self._start_time,
            "health": {
                "overall_status": health_status.overall_status.value,
                "is_healthy": health_status.is_healthy,
                "components": {
                    name: {
                        "status": component.status.value,
                        "message": component.message,
                        "response_time_ms": component.response_time_ms
                    }
                    for name, component in health_status.components.items()
                },
                "failed_components": health_status.failed_components
            },
            "metrics": {
                "email_processing": {
                    "total_processed": self.metrics_collector.email_metrics.total_emails_processed,
                    "safe_emails": self.metrics_collector.email_metrics.safe_emails,
                    "toxic_emails": self.metrics_collector.email_metrics.toxic_emails,
                    "average_processing_time_ms": self.metrics_collector.email_metrics.average_processing_time_ms
                },
                "performance": {
                    "memory_usage_mb": self.metrics_collector.performance_metrics.memory_usage_mb,
                    "cache_hit_rate": self.metrics_collector.performance_metrics.cache_hit_rate,
                    "avg_api_response_time_ms": self.metrics_collector.performance_metrics.avg_api_response_time_ms,
                    "api_success_rate": self.metrics_collector.performance_metrics.api_success_rate
                },
                "security": {
                    "toxic_emails_detected": self.metrics_collector.security_metrics.toxic_emails_detected,
                    "auth_failures": self.metrics_collector.security_metrics.auth_failures,
                    "rate_limit_violations": self.metrics_collector.security_metrics.rate_limit_violations,
                    "webhook_signature_success_rate": self.metrics_collector.security_metrics.webhook_signature_success_rate
                }
            },
            "alerts": {
                "active_count": len([a for a in self._active_alerts if not a.resolved]),
                "total_count": len(self._active_alerts),
                "recent_alerts": self.get_active_alerts()[:5]  # Last 5 alerts
            }
        }
        
        return dashboard
    
    def export_logs_json(self, limit: int = 100) -> str:
        """Export recent logs in JSON format."""
        logs = self.get_recent_logs(limit=limit)
        return json.dumps({
            "export_timestamp": time.time(),
            "total_logs": len(logs),
            "privacy_mode": self.logging_config.privacy_mode,
            "logs": logs
        }, indent=2)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        return {
            "uptime_seconds": time.time() - self._start_time,
            "log_entries_count": len(self._log_entries),
            "active_alerts_count": len([a for a in self._active_alerts if not a.resolved]),
            "total_alerts_count": len(self._alert_history),
            "memory_stats": {
                "usage_mb": self.metrics_collector.performance_metrics.memory_usage_mb,
                "available_mb": self.metrics_collector.performance_metrics.memory_available_mb
            },
            "processing_stats": {
                "total_emails": self.metrics_collector.email_metrics.total_emails_processed,
                "avg_processing_time_ms": self.metrics_collector.email_metrics.average_processing_time_ms,
                "success_rate": (
                    self.metrics_collector.email_metrics.safe_emails /
                    self.metrics_collector.email_metrics.total_emails_processed
                    if self.metrics_collector.email_metrics.total_emails_processed > 0 else 0
                )
            }
        }
    
    async def health_check_with_metrics(self) -> Dict[str, Any]:
        """Perform health check and return with metrics."""
        health_status = await self.health_monitor.check_all_components_async()
        
        return {
            "health": {
                "overall_healthy": health_status.is_healthy,
                "status": health_status.overall_status.value,
                "components": {
                    name: component.status.value
                    for name, component in health_status.components.items()
                }
            },
            "metrics": self.get_system_stats(),
            "alerts": len(self.get_active_alerts()),
            "timestamp": time.time()
        }