"""
TDD CYCLE 9 - RED PHASE: Monitoring & Observability
Tests requiring comprehensive monitoring system for privacy-focused email processing
"""
import pytest
import time
import json
from unittest.mock import patch, Mock, AsyncMock
from typing import Dict, Any, List, Optional

# Try to import monitoring components (should fail initially)
try:
    from cellophanemail.features.monitoring.metrics_collector import (
        MetricsCollector,
        EmailProcessingMetrics,
        PerformanceMetrics,
        SecurityMetrics
    )
    from cellophanemail.features.monitoring.health_monitor import (
        HealthMonitor,
        HealthStatus,
        ComponentHealth,
        HealthCheck
    )
    from cellophanemail.features.monitoring.observability_manager import (
        ObservabilityManager,
        LoggingConfig,
        AlertingConfig
    )
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False


class TestMonitoringObservability:
    """Test monitoring and observability system for privacy email processing"""
    
    def test_monitoring_modules_exist(self):
        """
        RED TEST: Monitoring modules should exist
        """
        assert MONITORING_AVAILABLE, \
            "cellophanemail.features.monitoring modules must exist"
    
    @pytest.mark.skipif(not MONITORING_AVAILABLE, reason="Monitoring modules not available")
    def test_metrics_collector_tracks_email_processing(self):
        """
        RED TEST: Should collect comprehensive metrics during email processing
        """
        collector = MetricsCollector()
        
        # Should track email processing metrics
        collector.record_email_received("test-message-id", "sender@example.com")
        collector.record_processing_start("test-message-id")
        time.sleep(0.1)  # Simulate processing time
        collector.record_processing_complete("test-message-id", "SAFE", 0.15)
        
        # Get processing metrics
        metrics = collector.get_email_processing_metrics()
        
        assert isinstance(metrics, EmailProcessingMetrics)
        assert metrics.total_emails_processed >= 1
        assert metrics.safe_emails >= 1
        assert metrics.average_processing_time_ms > 0
        # Message IDs are hashed for privacy, so check count instead
        assert len(metrics.processed_message_ids) >= 1
    
    @pytest.mark.skipif(not MONITORING_AVAILABLE, reason="Monitoring modules not available")
    def test_metrics_collector_tracks_performance_data(self):
        """
        RED TEST: Should collect performance metrics for system optimization
        """
        collector = MetricsCollector()
        
        # Record performance events
        collector.record_memory_usage(512, 1024)  # used_mb, available_mb
        collector.record_api_call("anthropic", 1500, success=True)  # duration_ms
        collector.record_cache_hit("llm_analysis", "content_hash_123")
        collector.record_cache_miss("llm_analysis", "content_hash_456")
        
        # Get performance metrics
        perf_metrics = collector.get_performance_metrics()
        
        assert isinstance(perf_metrics, PerformanceMetrics)
        assert perf_metrics.memory_usage_mb == 512
        assert perf_metrics.memory_available_mb == 1024
        assert perf_metrics.avg_api_response_time_ms >= 1500
        assert perf_metrics.cache_hit_rate > 0.0
    
    @pytest.mark.skipif(not MONITORING_AVAILABLE, reason="Monitoring modules not available")
    def test_metrics_collector_tracks_security_events(self):
        """
        RED TEST: Should collect security-related metrics and events
        """
        collector = MetricsCollector()
        
        # Record security events
        collector.record_toxic_email_detected("msg-001", 0.85, ["manipulation"])
        collector.record_rate_limit_exceeded("127.0.0.1", "webhook")
        collector.record_authentication_failure("user@example.com", "invalid_password")
        collector.record_webhook_signature_validation(True)
        
        # Get security metrics
        sec_metrics = collector.get_security_metrics()
        
        assert isinstance(sec_metrics, SecurityMetrics)
        assert sec_metrics.toxic_emails_detected >= 1
        assert sec_metrics.rate_limit_violations >= 1
        assert sec_metrics.auth_failures >= 1
        assert sec_metrics.webhook_signature_success_rate > 0.0
    
    @pytest.mark.skipif(not MONITORING_AVAILABLE, reason="Monitoring modules not available")
    def test_health_monitor_checks_component_status(self):
        """
        RED TEST: Should monitor health of all privacy pipeline components
        """
        health_monitor = HealthMonitor()
        
        # Should check all critical components
        health_status = health_monitor.get_overall_health()
        
        # health_status is a HealthCheckResult, not HealthStatus enum
        from cellophanemail.features.monitoring.health_monitor import HealthCheckResult
        assert isinstance(health_status, HealthCheckResult)
        assert hasattr(health_status, 'is_healthy')
        assert hasattr(health_status, 'components')
        assert hasattr(health_status, 'timestamp')
        
        # Check individual components
        components = health_status.components
        expected_components = [
            'database', 'memory_manager', 'llm_analyzer', 
            'email_delivery', 'background_tasks'
        ]
        
        for component_name in expected_components:
            assert component_name in components
            component_health = components[component_name]
            assert isinstance(component_health, ComponentHealth)
            assert hasattr(component_health, 'status')  # healthy/degraded/unhealthy
            assert hasattr(component_health, 'message')
            assert hasattr(component_health, 'response_time_ms')
    
    @pytest.mark.skipif(not MONITORING_AVAILABLE, reason="Monitoring modules not available")
    @pytest.mark.asyncio
    async def test_health_monitor_detects_component_failures(self):
        """
        RED TEST: Should detect and report component failures
        """
        health_monitor = HealthMonitor()
        
        # Simulate component failure by patching the database health check method
        with patch.object(health_monitor.health_checks[0], '_check_database_connection',
                         side_effect=Exception("Database connection failed")):
            
            health_status = await health_monitor.check_all_components_async()
            
            assert health_status.is_healthy == False
            assert 'database' in health_status.failed_components
            assert 'Database connection failed' in str(health_status.components['database'].message)
    
    @pytest.mark.skipif(not MONITORING_AVAILABLE, reason="Monitoring modules not available")
    def test_observability_manager_integrates_metrics_and_health(self):
        """
        RED TEST: Should provide unified observability dashboard
        """
        obs_manager = ObservabilityManager()
        
        # Should integrate metrics and health monitoring
        dashboard = obs_manager.get_dashboard_data()
        
        assert isinstance(dashboard, dict)
        assert 'metrics' in dashboard
        assert 'health' in dashboard
        assert 'alerts' in dashboard
        assert 'timestamp' in dashboard
        
        # Metrics should include all categories
        metrics = dashboard['metrics']
        assert 'email_processing' in metrics
        assert 'performance' in metrics
        assert 'security' in metrics
    
    @pytest.mark.skipif(not MONITORING_AVAILABLE, reason="Monitoring modules not available")
    def test_observability_manager_provides_privacy_compliant_logging(self):
        """
        RED TEST: Should provide logging that maintains privacy compliance
        """
        obs_manager = ObservabilityManager()
        
        # Configure privacy-safe logging
        logging_config = obs_manager.get_logging_config()
        
        assert isinstance(logging_config, LoggingConfig)
        assert logging_config.privacy_mode == True
        assert logging_config.content_redaction == True
        assert logging_config.metadata_only == True
        
        # Log privacy-safe events
        obs_manager.log_email_processed(
            message_id="msg-123",
            processing_time_ms=1500,
            toxicity_score=0.25,
            action="SAFE",
            redact_sensitive_data=True
        )
        
        # Verify logs contain no sensitive content
        log_entries = obs_manager.get_recent_logs(limit=1)
        assert len(log_entries) >= 1
        
        log_entry = log_entries[0]
        # Privacy-safe logging uses correlation_id instead of message_id
        assert 'correlation_id' in log_entry  # Metadata OK (hashed)
        assert 'duration_ms' in log_entry or 'processing_time_ms' in log_entry['metadata']  # Processing time logged
        assert 'email_content' not in log_entry  # Content NOT logged
        assert 'sender_email' not in log_entry  # Sensitive data NOT logged
    
    @pytest.mark.skipif(not MONITORING_AVAILABLE, reason="Monitoring modules not available")
    def test_observability_manager_handles_alerting(self):
        """
        RED TEST: Should handle alerting for critical events
        """
        obs_manager = ObservabilityManager()
        
        # Configure alerting
        alerting_config = AlertingConfig(
            high_toxicity_threshold=0.8,
            performance_degradation_threshold_ms=5000,
            error_rate_threshold=0.1
        )
        obs_manager.configure_alerting(alerting_config)
        
        # Trigger alert conditions
        obs_manager.record_high_toxicity_email("msg-456", 0.95)
        obs_manager.record_performance_degradation(6000)  # 6 seconds
        
        # Check for generated alerts
        active_alerts = obs_manager.get_active_alerts()
        assert len(active_alerts) >= 2
        
        # Verify alert content
        toxicity_alerts = [a for a in active_alerts if a['type'] == 'high_toxicity']
        perf_alerts = [a for a in active_alerts if a['type'] == 'performance_degradation']
        
        assert len(toxicity_alerts) >= 1
        assert len(perf_alerts) >= 1
        
        assert toxicity_alerts[0]['severity'] == 'high'
        assert 'toxicity_score' in toxicity_alerts[0]['data']
    
    @pytest.mark.skipif(not MONITORING_AVAILABLE, reason="Monitoring modules not available")
    def test_metrics_collector_provides_prometheus_format(self):
        """
        RED TEST: Should export metrics in Prometheus format for monitoring systems
        """
        collector = MetricsCollector()
        
        # Record some sample metrics
        collector.record_email_received("msg-1", "sender@test.com")
        collector.record_processing_complete("msg-1", "SAFE", 0.2)
        collector.record_api_call("anthropic", 1200, success=True)
        
        # Export in Prometheus format
        prometheus_metrics = collector.export_prometheus_format()
        
        assert isinstance(prometheus_metrics, str)
        assert '# HELP' in prometheus_metrics
        assert '# TYPE' in prometheus_metrics
        assert 'cellophanemail_emails_processed_total' in prometheus_metrics
        assert 'cellophanemail_processing_duration_seconds' in prometheus_metrics
        assert 'cellophanemail_api_calls_total' in prometheus_metrics
    
    @pytest.mark.skipif(not MONITORING_AVAILABLE, reason="Monitoring modules not available")
    def test_health_monitor_provides_kubernetes_probes(self):
        """
        RED TEST: Should provide endpoints for Kubernetes liveness/readiness probes
        """
        health_monitor = HealthMonitor()
        
        # Liveness probe (basic service availability)
        liveness = health_monitor.get_liveness_status()
        assert isinstance(liveness, dict)
        assert 'status' in liveness  # healthy/unhealthy
        assert 'timestamp' in liveness
        
        # Readiness probe (ready to accept traffic)
        readiness = health_monitor.get_readiness_status()
        assert isinstance(readiness, dict)
        assert 'status' in readiness
        assert 'dependencies' in readiness  # database, external APIs, etc.
        
        # Should check critical dependencies for readiness
        dependencies = readiness['dependencies']
        assert 'database' in dependencies
        assert 'llm_analyzer' in dependencies
    
    @pytest.mark.skipif(not MONITORING_AVAILABLE, reason="Monitoring modules not available")
    @pytest.mark.asyncio
    async def test_observability_integration_with_privacy_pipeline(self):
        """
        RED TEST: Should integrate monitoring with privacy pipeline components
        """
        from cellophanemail.features.email_protection.in_memory_processor import InMemoryProcessor
        from cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
        
        # Create processor with monitoring enabled
        processor = InMemoryProcessor(use_llm=False)
        obs_manager = ObservabilityManager()
        
        # Process email with monitoring
        email = EphemeralEmail(
            message_id="monitor-test-001",
            from_address="test@example.com",
            to_addresses=["user@example.com"],
            subject="Test Email",
            text_body="This is a test email",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        # Monitor the processing
        start_time = time.time()
        result = await processor.process_email(email)
        processing_time = (time.time() - start_time) * 1000
        
        # Record metrics
        obs_manager.record_email_processing_complete(
            message_id=email.message_id,
            processing_time_ms=processing_time,
            toxicity_score=result.toxicity_score,
            action=result.action
        )
        
        # Verify monitoring captured the processing
        dashboard = obs_manager.get_dashboard_data()
        email_metrics = dashboard['metrics']['email_processing']
        
        # The record_email_processing_complete call should have updated metrics
        assert email_metrics['total_processed'] >= 1
        assert email_metrics['average_processing_time_ms'] > 0
    
    @pytest.mark.skipif(not MONITORING_AVAILABLE, reason="Monitoring modules not available")
    def test_metrics_collector_handles_time_series_data(self):
        """
        RED TEST: Should handle time series data for trend analysis
        """
        collector = MetricsCollector()
        
        # Record metrics over time
        base_time = time.time()
        for i in range(5):
            collector.record_email_processed_at_time(
                timestamp=base_time + i * 60,  # Every minute
                toxicity_score=0.1 + i * 0.1,
                processing_time_ms=1000 + i * 100
            )
        
        # Get time series data
        time_series = collector.get_time_series_data(
            metric='processing_time_ms',
            start_time=base_time,
            end_time=base_time + 300  # 5 minutes
        )
        
        assert len(time_series) == 5
        assert all('timestamp' in point for point in time_series)
        assert all('value' in point for point in time_series)
        
        # Verify trend analysis
        trend = collector.analyze_trend(time_series)
        assert trend['direction'] in ['increasing', 'decreasing', 'stable']
        assert 'slope' in trend
        assert 'correlation' in trend
    
    def test_health_check_interface_exists(self):
        """
        RED TEST: HealthCheck interface should be properly defined
        """
        if not MONITORING_AVAILABLE:
            pytest.fail("HealthCheck interface must be defined")
        
        # Verify interface methods
        assert hasattr(HealthCheck, 'check_health')
        assert hasattr(HealthCheck, 'get_component_name')
        assert hasattr(HealthCheck, 'get_dependencies')