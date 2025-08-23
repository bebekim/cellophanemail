"""Four Horsemen testing framework for CellophoneMail."""

from .test_samples import (
    EmailTestSample,
    ToxicityLevel, 
    FourHorseman,
    ALL_SAMPLES,
    ENGLISH_SAMPLES,
    KOREAN_SAMPLES,
    get_samples_by_classification,
    get_samples_by_language,
    get_samples_by_horseman,
    get_test_sample_summary
)

from .pipeline_tracer import (
    PipelineTracer,
    ProcessingStage,
    PipelineTrace,
    StageTrace,
    pipeline_tracer,
    get_pipeline_tracer,
    start_trace,
    trace_stage,
    complete_trace
)

from .metrics_collector import (
    MetricsCollector,
    ClassificationMetrics,
    HorsemenMetrics,
    PerformanceMetrics,
    CostMetrics,
    LanguageMetrics,
    TestResult
)

from .analysis_comparator import (
    AnalysisComparator,
    AnalysisComparison,
    ComparisonMetrics,
    MethodEffectiveness
)

from .test_runner import (
    FourHorsemenTestRunner,
    FourHorsemenTestConfiguration,
    run_quick_test,
    run_language_comparison_test,
    run_cost_optimization_test
)

__all__ = [
    # Test samples
    "EmailTestSample", "ToxicityLevel", "FourHorseman",
    "ALL_SAMPLES", "ENGLISH_SAMPLES", "KOREAN_SAMPLES",
    "get_samples_by_classification", "get_samples_by_language", "get_samples_by_horseman",
    "get_test_sample_summary",
    
    # Pipeline tracing
    "PipelineTracer", "ProcessingStage", "PipelineTrace", "StageTrace",
    "pipeline_tracer", "get_pipeline_tracer", "start_trace", "trace_stage", "complete_trace",
    
    # Metrics collection
    "MetricsCollector", "ClassificationMetrics", "HorsemenMetrics", 
    "PerformanceMetrics", "CostMetrics", "LanguageMetrics", "TestResult",
    
    # Analysis comparison
    "AnalysisComparator", "AnalysisComparison", "ComparisonMetrics", "MethodEffectiveness",
    
    # Test runner
    "FourHorsemenTestRunner", "FourHorsemenTestConfiguration",
    "run_quick_test", "run_language_comparison_test", "run_cost_optimization_test"
]
