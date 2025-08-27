"""
Metrics Collection System for Privacy-Focused Email Processing

Comprehensive metrics collection with privacy-safe logging, Prometheus export,
and time series analysis for monitoring privacy pipeline performance.
"""

import time
import threading
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import hashlib
import statistics

import logging
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class EmailProcessingMetrics:
    """Email processing performance metrics."""
    total_emails_processed: int = 0
    safe_emails: int = 0
    toxic_emails: int = 0
    redirected_emails: int = 0
    average_processing_time_ms: float = 0.0
    min_processing_time_ms: float = float('inf')
    max_processing_time_ms: float = 0.0
    processed_message_ids: List[str] = field(default_factory=list)
    processing_times: List[float] = field(default_factory=list)
    
    def add_processing_time(self, time_ms: float):
        """Add processing time measurement."""
        self.processing_times.append(time_ms)
        if len(self.processing_times) > 1000:  # Keep last 1000 measurements
            self.processing_times = self.processing_times[-1000:]
        
        self.min_processing_time_ms = min(self.min_processing_time_ms, time_ms)
        self.max_processing_time_ms = max(self.max_processing_time_ms, time_ms)
        self.average_processing_time_ms = statistics.mean(self.processing_times)


@dataclass
class PerformanceMetrics:
    """System performance metrics."""
    memory_usage_mb: int = 0
    memory_available_mb: int = 0
    cpu_usage_percent: float = 0.0
    active_connections: int = 0
    cache_hit_rate: float = 0.0
    cache_miss_rate: float = 0.0
    avg_api_response_time_ms: float = 0.0
    api_success_rate: float = 0.0
    api_call_history: List[Dict[str, Any]] = field(default_factory=list)
    cache_stats: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(lambda: {'hits': 0, 'misses': 0}))
    
    def calculate_cache_hit_rate(self):
        """Calculate overall cache hit rate."""
        total_hits = sum(stats['hits'] for stats in self.cache_stats.values())
        total_misses = sum(stats['misses'] for stats in self.cache_stats.values())
        total_requests = total_hits + total_misses
        
        if total_requests > 0:
            self.cache_hit_rate = total_hits / total_requests
            self.cache_miss_rate = total_misses / total_requests
        else:
            self.cache_hit_rate = 0.0
            self.cache_miss_rate = 0.0


@dataclass
class SecurityMetrics:
    """Security-related metrics."""
    toxic_emails_detected: int = 0
    high_toxicity_emails: int = 0  # Above 0.8 threshold
    rate_limit_violations: int = 0
    auth_failures: int = 0
    webhook_signature_failures: int = 0
    webhook_signature_successes: int = 0
    suspicious_patterns_detected: int = 0
    blocked_ips: List[str] = field(default_factory=list)
    
    @property
    def webhook_signature_success_rate(self) -> float:
        """Calculate webhook signature validation success rate."""
        total = self.webhook_signature_successes + self.webhook_signature_failures
        return self.webhook_signature_successes / total if total > 0 else 0.0


@dataclass
class TimeSeriesPoint:
    """Single point in time series data."""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Comprehensive metrics collection system for privacy-focused email processing.
    
    Provides thread-safe metrics collection with privacy-compliant logging,
    Prometheus export format, and time series analysis capabilities.
    """
    
    def __init__(self, max_time_series_points: int = 1000, max_processing_states: int = 500):
        """Initialize metrics collector with configurable limits."""
        self._lock = threading.RLock()  # Use RLock for better performance
        
        # Core metrics
        self.email_metrics = EmailProcessingMetrics()
        self.performance_metrics = PerformanceMetrics()
        self.security_metrics = SecurityMetrics()
        
        # Time series data storage with configurable limits
        self._time_series: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_time_series_points)
        )
        
        # Processing state tracking with size limits
        self._processing_states: Dict[str, Dict[str, Any]] = {}
        self._max_processing_states = max_processing_states
        
        # Privacy-safe hashing with rotating salt
        self._salt = str(time.time()).encode()
        self._salt_rotation_interval = 3600  # Rotate salt every hour
        self._last_salt_rotation = time.time()
    
    def _hash_sensitive_data(self, data: str) -> str:
        """Create privacy-safe hash of sensitive data with salt rotation."""
        # Rotate salt periodically for enhanced privacy
        current_time = time.time()
        if current_time - self._last_salt_rotation > self._salt_rotation_interval:
            self._salt = str(current_time).encode()
            self._last_salt_rotation = current_time
        
        return hashlib.sha256(self._salt + data.encode()).hexdigest()[:16]
    
    def _cleanup_old_states(self) -> None:
        """Clean up old processing states to prevent memory growth."""
        if len(self._processing_states) > self._max_processing_states:
            # Remove oldest states based on received_at timestamp
            sorted_states = sorted(
                self._processing_states.items(),
                key=lambda x: x[1].get('received_at', 0)
            )
            # Keep only the newest states
            to_keep = dict(sorted_states[-self._max_processing_states//2:])
            self._processing_states.clear()
            self._processing_states.update(to_keep)
    
    def record_email_received(self, message_id: str, sender_email: str) -> None:
        """Record email reception with privacy-safe logging."""
        with self._lock:
            # Clean up old states periodically
            self._cleanup_old_states()
            
            hashed_id = self._hash_sensitive_data(message_id)
            self._processing_states[hashed_id] = {
                'received_at': time.time(),
                'sender_hash': self._hash_sensitive_data(sender_email),
                'status': 'received'
            }
    
    def record_processing_start(self, message_id: str) -> None:
        """Record processing start time."""
        with self._lock:
            hashed_id = self._hash_sensitive_data(message_id)
            if hashed_id in self._processing_states:
                self._processing_states[hashed_id]['processing_start'] = time.time()
                self._processing_states[hashed_id]['status'] = 'processing'
    
    def record_processing_complete(self, message_id: str, action: str, toxicity_score: float) -> None:
        """Record processing completion with results."""
        with self._lock:
            hashed_id = self._hash_sensitive_data(message_id)
            current_time = time.time()
            
            if hashed_id in self._processing_states:
                state = self._processing_states[hashed_id]
                state['completed_at'] = current_time
                state['action'] = action
                state['toxicity_score'] = toxicity_score
                state['status'] = 'completed'
                
                # Calculate processing time
                if 'processing_start' in state:
                    processing_time = (current_time - state['processing_start']) * 1000
                    self.email_metrics.add_processing_time(processing_time)
                
                # Update counters
                self.email_metrics.total_emails_processed += 1
                self.email_metrics.processed_message_ids.append(hashed_id)
                
                if action == "SAFE":
                    self.email_metrics.safe_emails += 1
                elif action in ["TOXIC", "REDIRECT"]:
                    self.email_metrics.toxic_emails += 1
                    if toxicity_score > 0.8:
                        self.security_metrics.high_toxicity_emails += 1
                        self.security_metrics.toxic_emails_detected += 1
                elif action == "REDIRECT":
                    self.email_metrics.redirected_emails += 1
                
                # Add to time series
                self._time_series['processing_time_ms'].append(
                    TimeSeriesPoint(current_time, processing_time if 'processing_start' in state else 0)
                )
                self._time_series['toxicity_score'].append(
                    TimeSeriesPoint(current_time, toxicity_score)
                )
                
                # Clean up old state
                del self._processing_states[hashed_id]
    
    def record_memory_usage(self, used_mb: int, available_mb: int) -> None:
        """Record current memory usage."""
        with self._lock:
            self.performance_metrics.memory_usage_mb = used_mb
            self.performance_metrics.memory_available_mb = available_mb
            
            current_time = time.time()
            self._time_series['memory_usage_mb'].append(
                TimeSeriesPoint(current_time, used_mb)
            )
    
    def record_api_call(self, provider: str, duration_ms: int, success: bool) -> None:
        """Record API call metrics."""
        with self._lock:
            call_data = {
                'provider': provider,
                'duration_ms': duration_ms,
                'success': success,
                'timestamp': time.time()
            }
            
            self.performance_metrics.api_call_history.append(call_data)
            if len(self.performance_metrics.api_call_history) > 1000:
                self.performance_metrics.api_call_history = self.performance_metrics.api_call_history[-1000:]
            
            # Calculate average response time
            recent_calls = [call for call in self.performance_metrics.api_call_history 
                           if call['timestamp'] > time.time() - 300]  # Last 5 minutes
            if recent_calls:
                self.performance_metrics.avg_api_response_time_ms = statistics.mean(
                    call['duration_ms'] for call in recent_calls
                )
                success_count = sum(1 for call in recent_calls if call['success'])
                self.performance_metrics.api_success_rate = success_count / len(recent_calls)
            
            # Add to time series
            current_time = time.time()
            self._time_series['api_response_time_ms'].append(
                TimeSeriesPoint(current_time, duration_ms, {'provider': provider})
            )
    
    def record_cache_hit(self, cache_type: str, key_hash: str) -> None:
        """Record cache hit."""
        with self._lock:
            self.performance_metrics.cache_stats[cache_type]['hits'] += 1
            self.performance_metrics.calculate_cache_hit_rate()
    
    def record_cache_miss(self, cache_type: str, key_hash: str) -> None:
        """Record cache miss."""
        with self._lock:
            self.performance_metrics.cache_stats[cache_type]['misses'] += 1
            self.performance_metrics.calculate_cache_hit_rate()
    
    def record_toxic_email_detected(self, message_id: str, toxicity_score: float, tactics: List[str]) -> None:
        """Record toxic email detection."""
        with self._lock:
            self.security_metrics.toxic_emails_detected += 1
            if toxicity_score > 0.8:
                self.security_metrics.high_toxicity_emails += 1
    
    def record_rate_limit_exceeded(self, ip_address: str, endpoint: str) -> None:
        """Record rate limit violation."""
        with self._lock:
            self.security_metrics.rate_limit_violations += 1
            ip_hash = self._hash_sensitive_data(ip_address)
            if ip_hash not in self.security_metrics.blocked_ips:
                self.security_metrics.blocked_ips.append(ip_hash)
    
    def record_authentication_failure(self, identifier: str, reason: str) -> None:
        """Record authentication failure."""
        with self._lock:
            self.security_metrics.auth_failures += 1
    
    def record_webhook_signature_validation(self, success: bool) -> None:
        """Record webhook signature validation result."""
        with self._lock:
            if success:
                self.security_metrics.webhook_signature_successes += 1
            else:
                self.security_metrics.webhook_signature_failures += 1
    
    def record_email_processing_complete(self, message_id: str, processing_time_ms: float, 
                                       toxicity_score: float, action: str) -> None:
        """Convenience method for complete processing recording."""
        self.record_processing_complete(message_id, action, toxicity_score)
    
    def record_email_processed_at_time(self, timestamp: float, toxicity_score: float, processing_time_ms: float) -> None:
        """Record historical email processing data for time series."""
        with self._lock:
            self._time_series['processing_time_ms'].append(
                TimeSeriesPoint(timestamp, processing_time_ms)
            )
            self._time_series['toxicity_score'].append(
                TimeSeriesPoint(timestamp, toxicity_score)
            )
    
    def get_email_processing_metrics(self) -> EmailProcessingMetrics:
        """Get current email processing metrics."""
        with self._lock:
            return EmailProcessingMetrics(
                total_emails_processed=self.email_metrics.total_emails_processed,
                safe_emails=self.email_metrics.safe_emails,
                toxic_emails=self.email_metrics.toxic_emails,
                redirected_emails=self.email_metrics.redirected_emails,
                average_processing_time_ms=self.email_metrics.average_processing_time_ms,
                min_processing_time_ms=self.email_metrics.min_processing_time_ms,
                max_processing_time_ms=self.email_metrics.max_processing_time_ms,
                processed_message_ids=self.email_metrics.processed_message_ids.copy(),
                processing_times=self.email_metrics.processing_times.copy()
            )
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        with self._lock:
            metrics = PerformanceMetrics(
                memory_usage_mb=self.performance_metrics.memory_usage_mb,
                memory_available_mb=self.performance_metrics.memory_available_mb,
                cpu_usage_percent=self.performance_metrics.cpu_usage_percent,
                cache_hit_rate=self.performance_metrics.cache_hit_rate,
                cache_miss_rate=self.performance_metrics.cache_miss_rate,
                avg_api_response_time_ms=self.performance_metrics.avg_api_response_time_ms,
                api_success_rate=self.performance_metrics.api_success_rate,
                api_call_history=self.performance_metrics.api_call_history.copy(),
                cache_stats=dict(self.performance_metrics.cache_stats)
            )
            return metrics
    
    def get_security_metrics(self) -> SecurityMetrics:
        """Get current security metrics."""
        with self._lock:
            return SecurityMetrics(
                toxic_emails_detected=self.security_metrics.toxic_emails_detected,
                high_toxicity_emails=self.security_metrics.high_toxicity_emails,
                rate_limit_violations=self.security_metrics.rate_limit_violations,
                auth_failures=self.security_metrics.auth_failures,
                webhook_signature_failures=self.security_metrics.webhook_signature_failures,
                webhook_signature_successes=self.security_metrics.webhook_signature_successes,
                suspicious_patterns_detected=self.security_metrics.suspicious_patterns_detected,
                blocked_ips=self.security_metrics.blocked_ips.copy()
            )
    
    def get_time_series_data(self, metric: str, start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """Get time series data for specified metric and time range."""
        with self._lock:
            if metric not in self._time_series:
                return []
            
            filtered_points = [
                {
                    'timestamp': point.timestamp,
                    'value': point.value,
                    'labels': point.labels
                }
                for point in self._time_series[metric]
                if start_time <= point.timestamp <= end_time
            ]
            
            return sorted(filtered_points, key=lambda x: x['timestamp'])
    
    def analyze_trend(self, time_series: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trend in time series data."""
        if len(time_series) < 2:
            return {'direction': 'insufficient_data', 'slope': 0, 'correlation': 0}
        
        values = [point['value'] for point in time_series]
        timestamps = [point['timestamp'] for point in time_series]
        
        # Simple linear regression for trend
        n = len(values)
        sum_x = sum(timestamps)
        sum_y = sum(values)
        sum_xy = sum(t * v for t, v in zip(timestamps, values))
        sum_x2 = sum(t * t for t in timestamps)
        
        # Calculate slope
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denominator
        
        # Determine direction
        if abs(slope) < 0.001:  # Threshold for "stable"
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        # Calculate correlation coefficient
        if len(values) > 1:
            try:
                correlation = statistics.correlation(timestamps, values)
            except statistics.StatisticsError:
                correlation = 0
        else:
            correlation = 0
        
        return {
            'direction': direction,
            'slope': slope,
            'correlation': correlation,
            'data_points': n
        }
    
    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format."""
        with self._lock:
            prometheus_lines = []
            
            # Email processing metrics
            prometheus_lines.extend([
                "# HELP cellophanemail_emails_processed_total Total number of emails processed",
                "# TYPE cellophanemail_emails_processed_total counter",
                f"cellophanemail_emails_processed_total {self.email_metrics.total_emails_processed}",
                "",
                "# HELP cellophanemail_safe_emails_total Number of emails classified as safe",
                "# TYPE cellophanemail_safe_emails_total counter", 
                f"cellophanemail_safe_emails_total {self.email_metrics.safe_emails}",
                "",
                "# HELP cellophanemail_toxic_emails_total Number of emails classified as toxic",
                "# TYPE cellophanemail_toxic_emails_total counter",
                f"cellophanemail_toxic_emails_total {self.email_metrics.toxic_emails}",
                "",
                "# HELP cellophanemail_processing_duration_seconds Average email processing time",
                "# TYPE cellophanemail_processing_duration_seconds gauge",
                f"cellophanemail_processing_duration_seconds {self.email_metrics.average_processing_time_ms / 1000}",
                ""
            ])
            
            # Performance metrics
            prometheus_lines.extend([
                "# HELP cellophanemail_memory_usage_bytes Current memory usage",
                "# TYPE cellophanemail_memory_usage_bytes gauge",
                f"cellophanemail_memory_usage_bytes {self.performance_metrics.memory_usage_mb * 1024 * 1024}",
                "",
                "# HELP cellophanemail_cache_hit_rate Cache hit rate",
                "# TYPE cellophanemail_cache_hit_rate gauge",
                f"cellophanemail_cache_hit_rate {self.performance_metrics.cache_hit_rate}",
                "",
                "# HELP cellophanemail_api_calls_total Total API calls made",
                "# TYPE cellophanemail_api_calls_total counter",
                f"cellophanemail_api_calls_total {len(self.performance_metrics.api_call_history)}",
                ""
            ])
            
            # Security metrics
            prometheus_lines.extend([
                "# HELP cellophanemail_auth_failures_total Total authentication failures",
                "# TYPE cellophanemail_auth_failures_total counter",
                f"cellophanemail_auth_failures_total {self.security_metrics.auth_failures}",
                "",
                "# HELP cellophanemail_rate_limit_violations_total Total rate limit violations",
                "# TYPE cellophanemail_rate_limit_violations_total counter",
                f"cellophanemail_rate_limit_violations_total {self.security_metrics.rate_limit_violations}",
                ""
            ])
            
            return '\n'.join(prometheus_lines)