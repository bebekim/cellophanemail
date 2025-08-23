"""Test runner for comprehensive Four Horsemen analysis testing."""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from uuid import uuid4

from .test_samples import (
    ALL_SAMPLES, 
    EmailTestSample, 
    ToxicityLevel, 
    FourHorseman,
    get_samples_by_classification,
    get_samples_by_language,
    get_test_sample_summary
)
from .pipeline_tracer import (
    PipelineTracer, 
    ProcessingStage, 
    start_trace, 
    trace_stage, 
    complete_trace,
    get_pipeline_tracer
)
from .metrics_collector import MetricsCollector
from .analysis_comparator import AnalysisComparator


@dataclass
class FourHorsemenTestConfiguration:
    """Configuration for test runs."""
    run_id: str = field(default_factory=lambda: str(uuid4())[:8])
    test_name: str = "Four Horsemen Analysis Test"
    
    # Sample selection
    max_samples: Optional[int] = None
    filter_by_language: Optional[str] = None  # "en", "ko", "mixed"
    filter_by_classification: Optional[ToxicityLevel] = None
    
    # Test modes
    test_hybrid_mode: bool = True
    test_traditional_mode: bool = False
    test_local_only: bool = False
    
    # Comparison settings
    compare_methods: bool = True
    
    # Output settings
    verbose: bool = True
    generate_html_report: bool = False
    save_json_results: bool = True
    output_dir: str = "test_results"


class FourHorsemenTestRunner:
    """Main test runner for Four Horsemen analysis evaluation."""
    
    def __init__(self, config: FourHorsemenTestConfiguration):
        """Initialize test runner with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Components
        self.tracer = get_pipeline_tracer()
        self.metrics = MetricsCollector()
        self.comparator = AnalysisComparator()
        
        # Results storage
        self.test_results: List[Dict[str, Any]] = []
        
        # Import ContentAnalysisService dynamically to avoid import issues
        try:
            from cellophanemail.core.content_analyzer import ContentAnalysisService
            self.analyzer = ContentAnalysisService()
        except ImportError as e:
            self.logger.warning(f"Could not import ContentAnalysisService: {e}")
            self.analyzer = None
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive Four Horsemen analysis test."""
        start_time = time.time()
        
        self.logger.info(f"🧪 Starting {self.config.test_name} [{self.config.run_id}]")
        
        # Get samples to test
        samples = self._get_test_samples()
        self.logger.info(f"📋 Testing {len(samples)} samples")
        
        # Clear previous results
        self.tracer.clear_traces()
        self.metrics.clear_results()
        self.comparator.clear_comparisons()
        
        # Run tests
        if self.config.test_hybrid_mode:
            await self._test_analysis_mode("hybrid", samples)
        
        if self.config.test_traditional_mode:
            await self._test_analysis_mode("traditional", samples)
        
        if self.config.test_local_only:
            await self._test_analysis_mode("local_only", samples)
        
        # Calculate comprehensive metrics
        test_duration = time.time() - start_time
        
        report = {
            "test_info": {
                "run_id": self.config.run_id,
                "test_name": self.config.test_name,
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": test_duration,
                "samples_tested": len(samples),
                "modes_tested": self._get_tested_modes()
            },
            "sections": []
        }
        
        # Add metrics sections
        if len(self.metrics.test_results) > 0:
            report["sections"].extend([
                self._build_accuracy_section(),
                self._build_performance_section(),
                self._build_cost_analysis_section()
            ])
        
        if self.config.compare_methods and len(self.comparator.comparisons) > 0:
            report["sections"].append(self._build_comparison_section())
        
        # Add sample analysis section
        report["sections"].append(self._build_sample_analysis_section(samples))
        
        # Save results if configured
        if self.config.save_json_results:
            await self._save_json_results(report)
        
        if self.config.generate_html_report:
            await self._save_html_report(report)
        
        self.logger.info(f"✅ Test completed in {test_duration:.2f}s")
        
        return report
    
    async def _test_analysis_mode(self, mode: str, samples: List[EmailTestSample]):
        """Test a specific analysis mode."""
        self.logger.info(f"🔍 Testing {mode} mode")
        
        for sample in samples:
            try:
                # Start pipeline trace
                trace_id = start_trace(sample.id, sample.sender, sample.language)
                
                # Run analysis
                result = await self._analyze_sample(sample, mode, trace_id)
                
                # Record metrics
                self.metrics.add_test_result(
                    sample=sample,
                    actual_classification=result.get('classification', 'UNKNOWN'),
                    actual_horsemen=result.get('horsemen_detected', []),
                    processing_time_ms=result.get('processing_time_ms', 0.0),
                    analysis_mode=mode,
                    cost_optimization=result.get('cost_optimization', 'unknown')
                )
                
                # Complete trace
                trace = complete_trace(
                    trace_id,
                    final_classification=result.get('classification'),
                    horsemen_detected=result.get('horsemen_detected', []),
                    should_forward=result.get('should_forward', True),
                    analysis_mode=mode,
                    cost_optimization=result.get('cost_optimization', 'unknown')
                )
                
                if trace:
                    self.metrics.add_pipeline_trace(trace)
                
                # Store detailed result
                self.test_results.append({
                    "sample_id": sample.id,
                    "mode": mode,
                    "result": result,
                    "trace_id": trace_id
                })
                
                if self.config.verbose:
                    self.logger.info(
                        f"✅ {sample.id} ({mode}): {result.get('classification')} - "
                        f"{result.get('processing_time_ms', 0):.1f}ms"
                    )
                    
            except Exception as e:
                self.logger.error(f"❌ Error testing {sample.id} in {mode} mode: {e}")
                
                # Record failed test
                self.metrics.add_test_result(
                    sample=sample,
                    actual_classification="ERROR",
                    actual_horsemen=[],
                    processing_time_ms=0.0,
                    analysis_mode=mode,
                    error=str(e)
                )
    
    async def _analyze_sample(self, sample: EmailTestSample, mode: str, trace_id: str) -> Dict[str, Any]:
        """Analyze a single sample using specified mode."""
        if not self.analyzer:
            raise Exception("ContentAnalysisService not available")
        
        start_time = time.time()
        
        # Trace analysis stages
        trace_stage(trace_id, ProcessingStage.CONTENT_EXTRACTED, 
                   content_length=len(sample.content), language=sample.language)
        
        # Run analysis based on mode
        if mode == "hybrid":
            result = self.analyzer.analyze_content(sample.content, sample.sender, use_hybrid=True)
        elif mode == "traditional":
            result = self.analyzer.analyze_content(sample.content, sample.sender, use_hybrid=False)
        elif mode == "local_only":
            result = self.analyzer._fallback_analysis(sample.content)
        else:
            raise ValueError(f"Unknown analysis mode: {mode}")
        
        processing_time = (time.time() - start_time) * 1000
        
        trace_stage(trace_id, ProcessingStage.CLASSIFICATION_DONE,
                   classification=result.get('classification'),
                   horsemen_count=len(result.get('horsemen_detected', [])))
        
        # Add processing metadata
        result['processing_time_ms'] = processing_time
        result['analysis_mode'] = mode
        
        # Determine forwarding decision (simple logic)
        classification = result.get('classification', 'SAFE')
        should_forward = classification in ['SAFE', 'WARNING']
        result['should_forward'] = should_forward
        
        trace_stage(trace_id, ProcessingStage.FORWARD_DECISION,
                   should_forward=should_forward)
        
        return result
    
    def _get_test_samples(self) -> List[EmailTestSample]:
        """Get samples for testing based on configuration."""
        samples = ALL_SAMPLES.copy()
        
        # Apply language filter
        if self.config.filter_by_language:
            samples = [s for s in samples if s.language == self.config.filter_by_language]
        
        # Apply classification filter
        if self.config.filter_by_classification:
            samples = [s for s in samples if s.expected_classification == self.config.filter_by_classification]
        
        # Apply max samples limit
        if self.config.max_samples and len(samples) > self.config.max_samples:
            samples = samples[:self.config.max_samples]
        
        return samples
    
    def _get_tested_modes(self) -> List[str]:
        """Get list of modes that were tested."""
        modes = []
        if self.config.test_hybrid_mode:
            modes.append("hybrid")
        if self.config.test_traditional_mode:
            modes.append("traditional")
        if self.config.test_local_only:
            modes.append("local_only")
        return modes
    
    def _build_accuracy_section(self) -> Dict[str, Any]:
        """Build accuracy analysis section."""
        classification_metrics = self.metrics.calculate_classification_metrics()
        horsemen_metrics = self.metrics.calculate_horsemen_metrics()
        language_metrics = self.metrics.calculate_language_metrics()
        
        return {
            "title": "📊 Accuracy Analysis",
            "type": "metrics",
            "data": {
                "overall_accuracy": classification_metrics.accuracy,
                "total_samples": classification_metrics.total_samples,
                "correct_classifications": classification_metrics.correct_classifications,
                "precision_by_class": classification_metrics.precision_by_class,
                "recall_by_class": classification_metrics.recall_by_class,
                "f1_by_class": classification_metrics.f1_by_class,
                "confusion_matrix": classification_metrics.confusion_matrix,
                "horsemen_precision": horsemen_metrics.horsemen_precision,
                "horsemen_recall": horsemen_metrics.horsemen_recall,
                "horsemen_f1": horsemen_metrics.horsemen_f1,
                "language_breakdown": language_metrics.languages
            }
        }
    
    def _build_performance_section(self) -> Dict[str, Any]:
        """Build performance analysis section."""
        performance_metrics = self.metrics.calculate_performance_metrics()
        tracer_summary = self.tracer.get_performance_summary()
        
        return {
            "title": "⚡ Performance Analysis",
            "type": "performance",
            "data": {
                "avg_processing_time_ms": performance_metrics.avg_processing_time_ms,
                "min_processing_time_ms": performance_metrics.min_processing_time_ms,
                "max_processing_time_ms": performance_metrics.max_processing_time_ms,
                "median_processing_time_ms": performance_metrics.median_processing_time_ms,
                "std_processing_time_ms": performance_metrics.std_processing_time_ms,
                "percentile_95_ms": performance_metrics.percentile_95_ms,
                "percentile_99_ms": performance_metrics.percentile_99_ms,
                "stage_performance": tracer_summary.get("stage_performance", {}),
                "analysis_mode_distribution": tracer_summary.get("analysis_mode_distribution", {})
            }
        }
    
    def _build_cost_analysis_section(self) -> Dict[str, Any]:
        """Build cost analysis section."""
        cost_metrics = self.metrics.calculate_cost_metrics()
        tracer_summary = self.tracer.get_performance_summary()
        
        return {
            "title": "💰 Cost Analysis",
            "type": "cost",
            "data": {
                "total_api_calls": cost_metrics.total_api_calls,
                "avg_api_calls_per_sample": cost_metrics.avg_api_calls_per_sample,
                "estimated_cost_usd": cost_metrics.estimated_cost_usd,
                "cost_savings_usd": cost_metrics.cost_savings_usd,
                "cache_hit_rate": cost_metrics.cache_hit_rate,
                "hybrid_usage_rate": cost_metrics.hybrid_usage_rate,
                "optimization_breakdown": cost_metrics.optimization_breakdown,
                "cache_performance": tracer_summary.get("cache_performance", {})
            }
        }
    
    def _build_comparison_section(self) -> Dict[str, Any]:
        """Build method comparison section."""
        comparison_metrics = self.comparator.calculate_comparison_metrics()
        effectiveness = self.comparator.calculate_method_effectiveness()
        disagreement_analysis = self.comparator.get_disagreement_analysis()
        recommendations = self.comparator.get_recommendation_analysis()
        
        return {
            "title": "⚖️ Method Comparison",
            "type": "comparison",
            "data": {
                "agreement_rates": {
                    "classification_agreement": comparison_metrics.classification_agreement_rate,
                    "horsemen_agreement": comparison_metrics.horsemen_agreement_rate,
                    "agreement_by_classification": comparison_metrics.agreement_by_classification,
                    "agreement_by_language": comparison_metrics.agreement_by_language
                },
                "effectiveness": {
                    "local_accuracy": effectiveness.local_accuracy,
                    "ai_accuracy": effectiveness.ai_accuracy,
                    "accuracy_difference": effectiveness.accuracy_difference,
                    "local_horsemen_f1": effectiveness.local_horsemen_f1,
                    "ai_horsemen_f1": effectiveness.ai_horsemen_f1
                },
                "performance_comparison": {
                    "local_avg_time_ms": comparison_metrics.local_avg_time_ms,
                    "ai_avg_time_ms": comparison_metrics.ai_avg_time_ms,
                    "speed_advantage": comparison_metrics.speed_advantage
                },
                "cost_comparison": {
                    "ai_total_cost": comparison_metrics.ai_total_cost,
                    "cost_savings": comparison_metrics.cost_savings
                },
                "disagreement_analysis": disagreement_analysis,
                "recommendations": recommendations
            }
        }
    
    def _build_sample_analysis_section(self, samples: List[EmailTestSample]) -> Dict[str, Any]:
        """Build sample analysis section."""
        sample_summary = get_test_sample_summary()
        
        # Add sample details
        sample_details = []
        for sample in samples[:10]:  # Show first 10 samples as examples
            sample_details.append({
                "id": sample.id,
                "language": sample.language,
                "classification": sample.expected_classification.value,
                "horsemen": [h.value for h in sample.expected_horsemen],
                "category": sample.category,
                "content_preview": sample.content[:100] + "..." if len(sample.content) > 100 else sample.content
            })
        
        return {
            "title": "📋 Sample Analysis",
            "type": "samples", 
            "data": {
                "summary": sample_summary,
                "sample_details": sample_details,
                "total_samples_tested": len(samples)
            }
        }
    
    async def _save_json_results(self, report: Dict[str, Any]):
        """Save results to JSON file."""
        import os
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        filename = f"{self.config.output_dir}/test_results_{self.config.run_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📄 Results saved to {filename}")
    
    async def _save_html_report(self, report: Dict[str, Any]):
        """Save results to HTML report."""
        # This would generate a comprehensive HTML report
        # Implementation omitted for brevity - would include charts, tables, etc.
        html_filename = f"{self.config.output_dir}/test_report_{self.config.run_id}.html"
        self.logger.info(f"📊 HTML report would be saved to {html_filename}")


# Convenience functions for quick testing
async def run_quick_test(max_samples: int = 5) -> Dict[str, Any]:
    """Run a quick test with limited samples."""
    config = TestConfiguration(
        test_name="Quick Four Horsemen Test",
        max_samples=max_samples,
        test_hybrid_mode=True,
        compare_methods=False,
        verbose=True,
        save_json_results=False
    )
    
    runner = FourHorsemenTestRunner(config)
    return await runner.run_comprehensive_test()


async def run_language_comparison_test(language: str = "en") -> Dict[str, Any]:
    """Run test focused on specific language."""
    config = TestConfiguration(
        test_name=f"Language Comparison Test ({language})",
        filter_by_language=language,
        test_hybrid_mode=True,
        test_traditional_mode=True,
        compare_methods=True,
        verbose=True
    )
    
    runner = FourHorsemenTestRunner(config)
    return await runner.run_comprehensive_test()


async def run_cost_optimization_test() -> Dict[str, Any]:
    """Run test focused on cost optimization."""
    config = TestConfiguration(
        test_name="Cost Optimization Analysis",
        test_hybrid_mode=True,
        test_traditional_mode=True,
        test_local_only=True,
        compare_methods=True,
        verbose=True,
        generate_html_report=True
    )
    
    runner = FourHorsemenTestRunner(config)
    return await runner.run_comprehensive_test()


# Export all for easy import
__all__ = [
    "TestConfiguration",
    "FourHorsemenTestRunner",
    "run_quick_test",
    "run_language_comparison_test", 
    "run_cost_optimization_test"
]
