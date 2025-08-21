"""Metrics collector for Four Horsemen analysis quality evaluation."""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import statistics
from collections import defaultdict

from .test_samples import EmailTestSample, ToxicityLevel, FourHorseman
from .pipeline_tracer import PipelineTrace


@dataclass
class ClassificationMetrics:
    """Classification accuracy metrics."""
    total_samples: int = 0
    correct_classifications: int = 0
    accuracy: float = 0.0
    precision_by_class: Dict[str, float] = field(default_factory=dict)
    recall_by_class: Dict[str, float] = field(default_factory=dict)
    f1_by_class: Dict[str, float] = field(default_factory=dict)
    confusion_matrix: Dict[str, Dict[str, int]] = field(default_factory=dict)


@dataclass
class HorsemenMetrics:
    """Four Horsemen detection metrics."""
    total_samples: int = 0
    horsemen_precision: Dict[str, float] = field(default_factory=dict)
    horsemen_recall: Dict[str, float] = field(default_factory=dict)
    horsemen_f1: Dict[str, float] = field(default_factory=dict)
    false_positives: Dict[str, int] = field(default_factory=dict)
    false_negatives: Dict[str, int] = field(default_factory=dict)
    true_positives: Dict[str, int] = field(default_factory=dict)
    true_negatives: Dict[str, int] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance timing metrics."""
    total_samples: int = 0
    avg_processing_time_ms: float = 0.0
    min_processing_time_ms: float = 0.0
    max_processing_time_ms: float = 0.0
    median_processing_time_ms: float = 0.0
    std_processing_time_ms: float = 0.0
    stage_averages: Dict[str, float] = field(default_factory=dict)
    percentile_95_ms: float = 0.0
    percentile_99_ms: float = 0.0


@dataclass
class CostMetrics:
    """Cost and optimization metrics."""
    total_samples: int = 0
    total_api_calls: int = 0
    avg_api_calls_per_sample: float = 0.0
    cache_hit_rate: float = 0.0
    hybrid_usage_rate: float = 0.0
    estimated_cost_usd: float = 0.0
    cost_savings_usd: float = 0.0
    optimization_breakdown: Dict[str, int] = field(default_factory=dict)


@dataclass
class LanguageMetrics:
    """Language-specific performance metrics."""
    languages: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass 
class TestResult:
    """Individual test result."""
    sample_id: str
    expected_classification: str
    actual_classification: str
    expected_horsemen: List[str]
    actual_horsemen: List[str]
    processing_time_ms: float
    analysis_mode: str
    cost_optimization: str
    success: bool
    error: Optional[str] = None


@dataclass
class TestRunMetrics:
    """Comprehensive metrics for a complete test run."""
    classification_metrics: ClassificationMetrics
    horsemen_metrics: HorsemenMetrics  
    performance_metrics: PerformanceMetrics
    cost_metrics: CostMetrics
    language_metrics: LanguageMetrics
    test_results: List[TestResult]
    total_samples: int
    successful_tests: int
    failed_tests: int
    test_duration_seconds: float


class MetricsCollector:
    """Collector for Four Horsemen analysis quality metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.test_results: List[TestResult] = []
        self.pipeline_traces: List[PipelineTrace] = []
        
    def add_test_result(
        self,
        sample: EmailTestSample,
        actual_classification: str,
        actual_horsemen: List[str],
        processing_time_ms: float,
        analysis_mode: str = "unknown",
        cost_optimization: str = "unknown",
        error: Optional[str] = None
    ):
        """Add a test result."""
        result = TestResult(
            sample_id=sample.id,
            expected_classification=sample.expected_classification.value,
            actual_classification=actual_classification,
            expected_horsemen=[h.value for h in sample.expected_horsemen],
            actual_horsemen=actual_horsemen,
            processing_time_ms=processing_time_ms,
            analysis_mode=analysis_mode,
            cost_optimization=cost_optimization,
            success=error is None,
            error=error
        )
        self.test_results.append(result)
    
    def add_pipeline_trace(self, trace: PipelineTrace):
        """Add a pipeline trace for detailed analysis."""
        self.pipeline_traces.append(trace)
    
    def calculate_classification_metrics(self) -> ClassificationMetrics:
        """Calculate classification accuracy metrics."""
        if not self.test_results:
            return ClassificationMetrics()
        
        successful_results = [r for r in self.test_results if r.success]
        total_samples = len(successful_results)
        
        if total_samples == 0:
            return ClassificationMetrics()
        
        # Basic accuracy
        correct = sum(1 for r in successful_results if r.expected_classification == r.actual_classification)
        accuracy = correct / total_samples
        
        # Confusion matrix
        confusion_matrix = defaultdict(lambda: defaultdict(int))
        for result in successful_results:
            confusion_matrix[result.expected_classification][result.actual_classification] += 1
        
        # Per-class metrics
        classes = list(set(r.expected_classification for r in successful_results))
        precision_by_class = {}
        recall_by_class = {}
        f1_by_class = {}
        
        for cls in classes:
            # True positives: correctly predicted as this class
            tp = confusion_matrix[cls][cls]
            
            # False positives: incorrectly predicted as this class
            fp = sum(confusion_matrix[other_cls][cls] for other_cls in classes if other_cls != cls)
            
            # False negatives: this class incorrectly predicted as other
            fn = sum(confusion_matrix[cls][other_cls] for other_cls in classes if other_cls != cls)
            
            # Calculate precision, recall, F1
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            precision_by_class[cls] = precision
            recall_by_class[cls] = recall
            f1_by_class[cls] = f1
        
        return ClassificationMetrics(
            total_samples=total_samples,
            correct_classifications=correct,
            accuracy=accuracy,
            precision_by_class=precision_by_class,
            recall_by_class=recall_by_class,
            f1_by_class=f1_by_class,
            confusion_matrix=dict(confusion_matrix)
        )
    
    def calculate_horsemen_metrics(self) -> HorsemenMetrics:
        """Calculate Four Horsemen detection metrics."""
        if not self.test_results:
            return HorsemenMetrics()
        
        successful_results = [r for r in self.test_results if r.success]
        total_samples = len(successful_results)
        
        if total_samples == 0:
            return HorsemenMetrics()
        
        horsemen = ["criticism", "contempt", "defensiveness", "stonewalling"]
        metrics = HorsemenMetrics(total_samples=total_samples)
        
        for horseman in horsemen:
            tp = 0  # True positive: correctly detected
            fp = 0  # False positive: incorrectly detected
            tn = 0  # True negative: correctly not detected
            fn = 0  # False negative: missed detection
            
            for result in successful_results:
                expected_has = horseman in result.expected_horsemen
                actual_has = horseman in result.actual_horsemen
                
                if expected_has and actual_has:
                    tp += 1
                elif not expected_has and actual_has:
                    fp += 1
                elif not expected_has and not actual_has:
                    tn += 1
                elif expected_has and not actual_has:
                    fn += 1
            
            # Calculate metrics
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            metrics.horsemen_precision[horseman] = precision
            metrics.horsemen_recall[horseman] = recall
            metrics.horsemen_f1[horseman] = f1
            metrics.false_positives[horseman] = fp
            metrics.false_negatives[horseman] = fn
            metrics.true_positives[horseman] = tp
            metrics.true_negatives[horseman] = tn
        
        return metrics
    
    def calculate_performance_metrics(self) -> PerformanceMetrics:
        """Calculate performance timing metrics."""
        if not self.test_results:
            return PerformanceMetrics()
        
        successful_results = [r for r in self.test_results if r.success and r.processing_time_ms > 0]
        
        if not successful_results:
            return PerformanceMetrics()
        
        processing_times = [r.processing_time_ms for r in successful_results]
        
        metrics = PerformanceMetrics(
            total_samples=len(successful_results),
            avg_processing_time_ms=statistics.mean(processing_times),
            min_processing_time_ms=min(processing_times),
            max_processing_time_ms=max(processing_times),
            median_processing_time_ms=statistics.median(processing_times),
            std_processing_time_ms=statistics.stdev(processing_times) if len(processing_times) > 1 else 0.0
        )
        
        # Percentiles
        if len(processing_times) >= 5:
            sorted_times = sorted(processing_times)
            metrics.percentile_95_ms = sorted_times[int(len(sorted_times) * 0.95)]
            metrics.percentile_99_ms = sorted_times[int(len(sorted_times) * 0.99)]
        
        # Stage averages from pipeline traces
        if self.pipeline_traces:
            stage_times = defaultdict(list)
            for trace in self.pipeline_traces:
                for stage_trace in trace.stages:
                    if stage_trace.duration_ms is not None:
                        stage_times[stage_trace.stage.value].append(stage_trace.duration_ms)
            
            for stage, times in stage_times.items():
                if times:
                    metrics.stage_averages[stage] = statistics.mean(times)
        
        return metrics
    
    def calculate_cost_metrics(self, cost_per_api_call: float = 0.002) -> CostMetrics:
        """Calculate cost and optimization metrics."""
        if not self.pipeline_traces:
            return CostMetrics()
        
        total_samples = len(self.pipeline_traces)
        total_api_calls = sum(trace.ai_api_calls for trace in self.pipeline_traces)
        total_cache_hits = sum(trace.cache_hits for trace in self.pipeline_traces)
        total_cache_misses = sum(trace.cache_misses for trace in self.pipeline_traces)
        
        # Optimization breakdown
        optimization_breakdown = defaultdict(int)
        for trace in self.pipeline_traces:
            optimization_breakdown[trace.cost_optimization] += 1
        
        # Calculate metrics
        cache_hit_rate = total_cache_hits / (total_cache_hits + total_cache_misses) if (total_cache_hits + total_cache_misses) > 0 else 0.0
        hybrid_usage = optimization_breakdown.get("hybrid_local_only", 0) + optimization_breakdown.get("hybrid_ai_used", 0)
        hybrid_usage_rate = hybrid_usage / total_samples if total_samples > 0 else 0.0
        
        estimated_cost = total_api_calls * cost_per_api_call
        
        # Estimate cost savings (assume non-hybrid would use AI for all)
        non_hybrid_api_calls = total_samples  # Would call AI for every email
        potential_cost = non_hybrid_api_calls * cost_per_api_call
        cost_savings = max(0, potential_cost - estimated_cost)
        
        return CostMetrics(
            total_samples=total_samples,
            total_api_calls=total_api_calls,
            avg_api_calls_per_sample=total_api_calls / total_samples if total_samples > 0 else 0.0,
            cache_hit_rate=cache_hit_rate,
            hybrid_usage_rate=hybrid_usage_rate,
            estimated_cost_usd=estimated_cost,
            cost_savings_usd=cost_savings,
            optimization_breakdown=dict(optimization_breakdown)
        )
    
    def calculate_language_metrics(self) -> LanguageMetrics:
        """Calculate language-specific metrics."""
        language_stats = defaultdict(lambda: {
            "total_samples": 0,
            "accuracy": 0.0,
            "avg_processing_time": 0.0,
            "api_calls": 0,
            "classifications": defaultdict(int)
        })
        
        # Process test results
        for result in self.test_results:
            if not result.success:
                continue
                
            # Determine language from sample ID
            if result.sample_id.startswith("en_"):
                lang = "english"
            elif result.sample_id.startswith("ko_"):
                lang = "korean" 
            elif result.sample_id.startswith("mixed_"):
                lang = "mixed"
            else:
                lang = "unknown"
            
            stats = language_stats[lang]
            stats["total_samples"] += 1
            stats["classifications"][result.actual_classification] += 1
            
            if result.expected_classification == result.actual_classification:
                stats["accuracy"] += 1.0
        
        # Process pipeline traces for timing and API info
        for trace in self.pipeline_traces:
            lang = trace.language
            if lang in language_stats:
                stats = language_stats[lang]
                if trace.total_duration_ms:
                    stats["avg_processing_time"] += trace.total_duration_ms
                stats["api_calls"] += trace.ai_api_calls
        
        # Finalize calculations
        for lang, stats in language_stats.items():
            if stats["total_samples"] > 0:
                stats["accuracy"] /= stats["total_samples"]
                if stats["avg_processing_time"] > 0:
                    stats["avg_processing_time"] /= stats["total_samples"]
                stats["classifications"] = dict(stats["classifications"])
        
        return LanguageMetrics(languages=dict(language_stats))
    
    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get all metrics in one comprehensive report."""
        return {
            "classification_metrics": self.calculate_classification_metrics(),
            "horsemen_metrics": self.calculate_horsemen_metrics(),
            "performance_metrics": self.calculate_performance_metrics(),
            "cost_metrics": self.calculate_cost_metrics(),
            "language_metrics": self.calculate_language_metrics()
        }
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get high-level summary statistics."""
        if not self.test_results:
            return {"error": "No test results available"}
        
        classification_metrics = self.calculate_classification_metrics()
        performance_metrics = self.calculate_performance_metrics()
        cost_metrics = self.calculate_cost_metrics()
        
        return {
            "total_tests": len(self.test_results),
            "successful_tests": len([r for r in self.test_results if r.success]),
            "overall_accuracy": classification_metrics.accuracy,
            "avg_processing_time_ms": performance_metrics.avg_processing_time_ms,
            "total_api_calls": cost_metrics.total_api_calls,
            "estimated_cost_usd": cost_metrics.estimated_cost_usd,
            "cache_hit_rate": cost_metrics.cache_hit_rate,
            "cost_savings_usd": cost_metrics.cost_savings_usd
        }
    
    def clear_results(self):
        """Clear all collected results."""
        self.test_results.clear()
        self.pipeline_traces.clear()


# Export all for easy import
__all__ = [
    "ClassificationMetrics",
    "HorsemenMetrics", 
    "PerformanceMetrics",
    "CostMetrics",
    "LanguageMetrics",
    "TestResult",
    "MetricsCollector"
]
