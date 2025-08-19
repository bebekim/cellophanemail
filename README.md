# CellophoneMail

AI-powered email protection using the Four Horsemen framework to filter toxic communication patterns.

## Overview

CellophoneMail is an email filtering system that uses Gottman's Four Horsemen of the Apocalypse framework to detect and block toxic communication patterns:

1. **Criticism** - Attacks on character/personality rather than specific behavior
2. **Contempt** - Expressions of superiority, disrespect, mockery (most destructive)
3. **Defensiveness** - Playing victim, counter-attacking, making excuses
4. **Stonewalling** - Emotional withdrawal, shutting down communication

The system uses a hybrid AI approach combining local keyword analysis with Anthropic Claude for cost-effective, accurate toxicity detection.

## Architecture

- **WebhookController** - Receives emails from Postmark/SMTP
- **EmailProcessor** - Main orchestration pipeline
- **ContentProcessor** - Analysis workflow management
- **ContentAnalysisService** - Hybrid AI + local analysis engine

### Analysis Pipeline

```
Inbound Email ’ Webhook ’ Email Processor ’ Content Processor ’ Content Analyzer
     “              “              “               “               “
Cache Check ’ Local Analysis ’ AI Analysis (if suspicious) ’ Classification ’ Forward/Block
```

## Four Horsemen Testing Framework

Comprehensive testing framework for evaluating analysis quality across multiple languages.

### Features

- **=Ë Multilingual Test Samples**: 16+ samples in English, Korean, and mixed languages
- **= Pipeline Tracer**: 13-stage monitoring from email receipt to forwarding
- **=Ê Metrics Collector**: Classification accuracy, Four Horsemen detection, performance metrics
- **– Analysis Comparator**: Local vs AI comparison with cost-benefit analysis
- **=€ Test Runner**: Comprehensive evaluation with detailed reporting

### Quick Usage

```python
# Quick test (5 samples)
from tests.four_horsemen.test_runner import run_quick_test
result = await run_quick_test()
print(f"Accuracy: {result['sections'][0]['data']['overall_accuracy']:.1%}")

# Language-specific test
from tests.four_horsemen.test_runner import run_language_comparison_test
ko_results = await run_language_comparison_test("ko")  # Korean
en_results = await run_language_comparison_test("en")  # English

# Comprehensive analysis
from tests.four_horsemen.test_runner import run_cost_optimization_test
full_results = await run_cost_optimization_test()
```

### Custom Configuration

```python
from tests.four_horsemen import FourHorsemenTestRunner, TestConfiguration

config = TestConfiguration(
    test_name="My Custom Test",
    max_samples=10,
    filter_by_language="ko",  # Korean only
    test_hybrid_mode=True,
    test_traditional_mode=True,
    compare_methods=True,
    generate_html_report=True
)

runner = FourHorsemenTestRunner(config)
report = await runner.run_comprehensive_test()
```

### Test Components

#### 1. Test Samples (`tests/four_horsemen/test_samples.py`)
- Realistic email scenarios with ground truth labels
- Multiple toxicity levels: SAFE, WARNING, HARMFUL, ABUSIVE
- All Four Horsemen patterns represented
- Cross-linguistic validation

#### 2. Pipeline Tracer (`tests/four_horsemen/pipeline_tracer.py`)
- Stage-by-stage performance monitoring
- Cache hit/miss tracking
- Language-specific performance breakdown
- Error capture and debugging support

#### 3. Metrics Collector (`tests/four_horsemen/metrics_collector.py`)
- Classification accuracy with precision/recall/F1
- Per-horseman detection metrics
- Performance timing analysis
- Cost optimization tracking

#### 4. Analysis Comparator (`tests/four_horsemen/analysis_comparator.py`)
- Local vs AI method comparison
- Agreement rate analysis
- Cost-effectiveness evaluation
- Automated optimization recommendations

#### 5. Test Runner (`tests/four_horsemen/test_runner.py`)
- Configurable test execution
- Multiple analysis modes (hybrid, traditional, local-only)
- Comprehensive reporting (JSON, HTML)
- Sample filtering and selection

### Reports Generated

- **=Ê Accuracy Analysis**: Overall and per-class metrics, confusion matrix
- **¡ Performance Analysis**: Processing times, stage breakdowns, bottlenecks
- **=° Cost Analysis**: API usage, cache efficiency, optimization savings
- **– Method Comparison**: Local vs AI effectiveness and recommendations
- **=Ë Sample Analysis**: Test sample distribution and characteristics

### Key Advantages

1. **Cost-effective**: Hybrid approach reduces AI API costs by 60-80%
2. **Multilingual**: Supports English, Korean, and code-switching patterns
3. **Reliable**: Local fallback ensures service continuity
4. **Accurate**: Research-backed Four Horsemen framework
5. **Scalable**: Caching and local analysis handle high volume
6. **Transparent**: Detailed logging and reasoning provided

## Getting Started

1. Clone the repository
2. Set up environment variables (ANTHROPIC_API_KEY)
3. Run tests: `python -m tests.four_horsemen.test_runner`
4. Configure email webhook endpoints
5. Deploy and monitor with the testing framework

## Testing & Quality Assurance

The Four Horsemen testing framework provides systematic quality evaluation:

- Test 10+ multilingual email samples regularly
- Monitor LLM + hybrid analysis performance
- Compare local vs AI effectiveness
- Track cost optimization over time
- Validate accuracy across languages and toxicity levels

Use the framework to maintain high-quality email filtering while optimizing costs and performance.