"""Test reporting system for Four Horsemen analysis results visualization."""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import statistics

from .metrics_collector import MetricsCollector, RunMetrics
from .analysis_comparator import AnalysisComparator
from .pipeline_tracer import PipelineTrace
from .test_samples import EmailTestSample, ToxicityLevel


@dataclass
class ReportSection:
    """A section of the test report."""
    title: str
    content: str
    data: Optional[Dict[str, Any]] = None
    charts: Optional[List[Dict[str, Any]]] = None


class FourHorsemenReporter:
    """Generates comprehensive reports for Four Horsemen analysis testing."""
    
    def __init__(self):
        """Initialize the test reporter."""
        pass
    
    def generate_comprehensive_report(self, 
                                    metrics: RunMetrics,
                                    comparator: AnalysisComparator,
                                    traces: List[PipelineTrace],
                                    samples: List[EmailTestSample]) -> Dict[str, Any]:
        """Generate a comprehensive test report."""
        
        report = {
            'metadata': self._generate_metadata(metrics),
            'executive_summary': self._generate_executive_summary(metrics, comparator),
            'sections': [
                self._generate_overview_section(metrics),
                self._generate_accuracy_section(metrics, samples),
                self._generate_performance_section(metrics, traces),
                self._generate_cost_analysis_section(metrics),
                self._generate_comparison_section(comparator),
                self._generate_detailed_results_section(metrics, traces),
                self._generate_recommendations_section(metrics, comparator)
            ]
        }
        
        return report
    
    def _generate_metadata(self, metrics: RunMetrics) -> Dict[str, Any]:
        """Generate report metadata."""
        return {
            'generated_at': datetime.now().isoformat(),
            'run_id': metrics.run_id,
            'test_duration_minutes': (metrics.completed_at - metrics.started_at).total_seconds() / 60 if metrics.completed_at else None,
            'framework_version': '1.0.0',
            'report_type': 'Four Horsemen Analysis Test Report'
        }
    
    def _generate_executive_summary(self, metrics: RunMetrics, comparator: AnalysisComparator) -> str:
        """Generate executive summary."""
        
        accuracy = metrics.accuracy_metrics.classification_accuracy
        avg_time = metrics.performance_metrics.average_processing_time_ms
        total_cost = metrics.cost_metrics.total_estimated_cost
        hybrid_savings = metrics.cost_metrics.cost_savings_from_hybrid
        
        # Get comparison insights
        local_vs_ai_summary = None
        if ComparisonType.LOCAL_VS_AI in comparator.summaries:
            local_vs_ai_summary = comparator.summaries[ComparisonType.LOCAL_VS_AI]
        
        summary = f"""
## Executive Summary

This comprehensive test evaluated the Four Horsemen email analysis system across {metrics.total_samples} diverse email samples.

### Key Findings:

**Accuracy Performance:**
- Overall classification accuracy: {accuracy:.1%}
- Precision: {metrics.accuracy_metrics.precision:.1%}
- Recall: {metrics.accuracy_metrics.recall:.1%}
- F1-Score: {metrics.accuracy_metrics.f1_score:.3f}

**Performance Metrics:**
- Average processing time: {avg_time:.1f}ms per email
- Median processing time: {metrics.performance_metrics.median_processing_time_ms:.1f}ms
- Processing range: {metrics.performance_metrics.min_processing_time_ms:.1f}ms - {metrics.performance_metrics.max_processing_time_ms:.1f}ms

**Cost Optimization:**
- Total estimated API cost: ${total_cost:.4f}
- Average cost per email: ${metrics.cost_metrics.average_cost_per_email:.4f}
- Hybrid approach savings: ${hybrid_savings:.4f}
- Cache hit rate: {metrics.cost_metrics.cache_hit_count / max(metrics.cost_metrics.cache_hit_count + metrics.cost_metrics.cache_miss_count, 1):.1%}
"""
        
        if local_vs_ai_summary:
            summary += f"""
**Local vs AI Analysis:**
- Classification agreement rate: {local_vs_ai_summary.classification_agreement_rate:.1%}
- Four Horsemen detection agreement: {local_vs_ai_summary.horsemen_agreement_rate:.1%}
- Average speed advantage of local analysis: {-local_vs_ai_summary.average_speed_difference_ms:.1f}ms
- AI accuracy advantage: {local_vs_ai_summary.accuracy_difference:.1%}
"""
        
        # Add key recommendations
        if accuracy < 0.8:
            summary += "\n**⚠️ Key Concern:** Classification accuracy below 80% threshold - review model parameters."
        
        if hybrid_savings > total_cost * 0.3:
            summary += "\n**✅ Success:** Hybrid approach achieving significant cost savings (>30%)."
        
        return summary
    
    def _generate_overview_section(self, metrics: RunMetrics) -> ReportSection:
        """Generate test overview section."""
        
        content = f"""
### Test Overview

**Test Configuration:**
- Run ID: {metrics.run_id}
- Total samples processed: {metrics.total_samples}
- Successful analyses: {metrics.successful_samples}
- Failed analyses: {metrics.failed_samples}
- Success rate: {metrics.successful_samples / metrics.total_samples:.1%}

**Test Duration:** {(metrics.completed_at - metrics.started_at).total_seconds() / 60:.1f} minutes

**Error Summary:**
"""
        
        if metrics.error_summary:
            for error_type, count in metrics.error_summary.items():
                content += f"- {error_type}: {count} occurrences\n"
        else:
            content += "- No errors encountered\n"
        
        return ReportSection(
            title="Test Overview",
            content=content,
            data={
                'total_samples': metrics.total_samples,
                'successful_samples': metrics.successful_samples,
                'failed_samples': metrics.failed_samples,
                'error_summary': metrics.error_summary
            }
        )
    
    def _generate_accuracy_section(self, metrics: RunMetrics, samples: List[EmailTestSample]) -> ReportSection:
        """Generate accuracy analysis section."""
        
        acc = metrics.accuracy_metrics
        
        content = f"""
### Accuracy Analysis

**Overall Classification Performance:**
- Classification Accuracy: {acc.classification_accuracy:.3f} ({acc.correct_classifications}/{acc.total_samples})
- Precision: {acc.precision:.3f}
- Recall: {acc.recall:.3f}
- F1-Score: {acc.f1_score:.3f}

**Error Analysis:**
- False Positives: {acc.false_positives} (over-blocking safe content)
- False Negatives: {acc.false_negatives} (missing toxic content)

**Four Horsemen Detection Performance:**
"""
        
        for horseman in ['criticism', 'contempt', 'defensiveness', 'stonewalling']:
            precision = acc.horsemen_precision.get(horseman, 0)
            recall = acc.horsemen_recall.get(horseman, 0)
            content += f"- **{horseman.title()}**: Precision={precision:.3f}, Recall={recall:.3f}\n"
        
        # Performance by toxicity level
        content += "\n**Performance by Toxicity Level:**\n"
        
        # Group samples by expected classification
        by_level = {}
        for sample in samples:
            level = sample.expected_classification.value
            by_level[level] = by_level.get(level, 0) + 1
        
        for level, count in by_level.items():
            content += f"- {level}: {count} samples\n"
        
        return ReportSection(
            title="Accuracy Analysis",
            content=content,
            data={
                'classification_accuracy': acc.classification_accuracy,
                'precision': acc.precision,
                'recall': acc.recall,
                'f1_score': acc.f1_score,
                'false_positives': acc.false_positives,
                'false_negatives': acc.false_negatives,
                'horsemen_performance': {
                    horseman: {
                        'precision': acc.horsemen_precision.get(horseman, 0),
                        'recall': acc.horsemen_recall.get(horseman, 0)
                    }
                    for horseman in ['criticism', 'contempt', 'defensiveness', 'stonewalling']
                }
            },
            charts=[
                {
                    'type': 'bar',
                    'title': 'Four Horsemen Detection Performance',
                    'data': {
                        'horsemen': ['criticism', 'contempt', 'defensiveness', 'stonewalling'],
                        'precision': [acc.horsemen_precision.get(h, 0) for h in ['criticism', 'contempt', 'defensiveness', 'stonewalling']],
                        'recall': [acc.horsemen_recall.get(h, 0) for h in ['criticism', 'contempt', 'defensiveness', 'stonewalling']]
                    }
                }
            ]
        )
    
    def _generate_performance_section(self, metrics: RunMetrics, traces: List[PipelineTrace]) -> ReportSection:
        """Generate performance analysis section."""
        
        perf = metrics.performance_metrics
        
        content = f"""
### Performance Analysis

**Processing Speed:**
- Average: {perf.average_processing_time_ms:.1f}ms per email
- Median: {perf.median_processing_time_ms:.1f}ms per email
- Range: {perf.min_processing_time_ms:.1f}ms - {perf.max_processing_time_ms:.1f}ms
- Total time: {perf.total_processing_time_ms:.1f}ms

**Stage Performance:**
"""
        
        for stage, avg_time in perf.stage_averages.items():
            content += f"- {stage.replace('_', ' ').title()}: {avg_time:.1f}ms average\n"
        
        if perf.local_analysis_time_ms:
            local_avg = statistics.mean(perf.local_analysis_time_ms)
            content += f"\n**Local Analysis:** {local_avg:.1f}ms average\n"
        
        if perf.ai_analysis_time_ms:
            ai_avg = statistics.mean(perf.ai_analysis_time_ms)
            content += f"**AI Analysis:** {ai_avg:.1f}ms average\n"
            
            if perf.local_analysis_time_ms:
                speedup = ai_avg / local_avg
                content += f"**Speed Ratio:** AI is {speedup:.1f}x slower than local analysis\n"
        
        # Performance distribution
        all_times = [perf.total_processing_time_ms / metrics.successful_samples] * metrics.successful_samples
        if traces:
            all_times = [t.total_duration_ms for t in traces if t.total_duration_ms]
        
        content += f"""
**Performance Distribution:**
- 50th percentile: {statistics.median(all_times) if all_times else 0:.1f}ms
- 95th percentile: {statistics.quantiles(all_times, n=20)[18] if len(all_times) > 20 else max(all_times) if all_times else 0:.1f}ms
- 99th percentile: {statistics.quantiles(all_times, n=100)[98] if len(all_times) > 100 else max(all_times) if all_times else 0:.1f}ms
"""
        
        return ReportSection(
            title="Performance Analysis",
            content=content,
            data={
                'average_time_ms': perf.average_processing_time_ms,
                'median_time_ms': perf.median_processing_time_ms,
                'min_time_ms': perf.min_processing_time_ms,
                'max_time_ms': perf.max_processing_time_ms,
                'stage_averages': perf.stage_averages,
                'local_analysis_avg': statistics.mean(perf.local_analysis_time_ms) if perf.local_analysis_time_ms else None,
                'ai_analysis_avg': statistics.mean(perf.ai_analysis_time_ms) if perf.ai_analysis_time_ms else None
            },
            charts=[
                {
                    'type': 'histogram',
                    'title': 'Processing Time Distribution',
                    'data': {
                        'times': all_times,
                        'bins': 20
                    }
                }
            ]
        )
    
    def _generate_cost_analysis_section(self, metrics: RunMetrics) -> ReportSection:
        """Generate cost analysis section."""
        
        cost = metrics.cost_metrics
        
        content = f"""
### Cost Analysis

**API Usage:**
- Total API calls: {cost.total_api_calls}
- Total tokens used: {cost.total_tokens_used:,}
- Total estimated cost: ${cost.total_estimated_cost:.4f}
- Average cost per email: ${cost.average_cost_per_email:.4f}

**Hybrid Optimization Results:**
- Local-only processing: {cost.hybrid_local_only_count} emails ({cost.hybrid_local_only_count/metrics.total_samples:.1%})
- AI processing used: {cost.hybrid_ai_used_count} emails ({cost.hybrid_ai_used_count/metrics.total_samples:.1%})
- Traditional AI (no hybrid): {cost.traditional_ai_count} emails

**Cost Savings:**
- Estimated savings from hybrid approach: ${cost.cost_savings_from_hybrid:.4f}
- Savings rate: {cost.cost_savings_from_hybrid / max(cost.total_estimated_cost + cost.cost_savings_from_hybrid, 0.0001):.1%}

**Cache Performance:**
- Cache hits: {cost.cache_hit_count}
- Cache misses: {cost.cache_miss_count}
- Cache hit rate: {cost.cache_hit_count / max(cost.cache_hit_count + cost.cache_miss_count, 1):.1%}
"""
        
        return ReportSection(
            title="Cost Analysis",
            content=content,
            data={
                'total_api_calls': cost.total_api_calls,
                'total_cost': cost.total_estimated_cost,
                'average_cost_per_email': cost.average_cost_per_email,
                'hybrid_local_only': cost.hybrid_local_only_count,
                'hybrid_ai_used': cost.hybrid_ai_used_count,
                'cost_savings': cost.cost_savings_from_hybrid,
                'cache_hit_rate': cost.cache_hit_count / max(cost.cache_hit_count + cost.cache_miss_count, 1)
            },
            charts=[
                {
                    'type': 'pie',
                    'title': 'Processing Mode Distribution',
                    'data': {
                        'labels': ['Local Only', 'AI Used', 'Traditional AI'],
                        'values': [cost.hybrid_local_only_count, cost.hybrid_ai_used_count, cost.traditional_ai_count]
                    }
                }
            ]
        )
    
    def _generate_comparison_section(self, comparator: AnalysisComparator) -> ReportSection:
        """Generate analysis comparison section."""
        
        content = "### Analysis Method Comparison\n\n"
        
        for comparison_type, summary in comparator.summaries.items():
            content += f"**{comparison_type.value.replace('_', ' ').title()}:**\n"
            content += f"- Total comparisons: {summary.total_comparisons}\n"
            content += f"- Classification agreement: {summary.classification_agreement_rate:.1%}\n"
            content += f"- Four Horsemen agreement: {summary.horsemen_agreement_rate:.1%}\n"
            content += f"- Average speed difference: {summary.average_speed_difference_ms:.1f}ms\n"
            content += f"- Average cost difference: ${summary.average_cost_difference:.4f}\n"
            
            if summary.accuracy_difference != 0:
                content += f"- Accuracy difference: {summary.accuracy_difference:.1%}\n"
            
            if summary.when_a_better:
                content += f"- Method A advantages: {', '.join(summary.when_a_better)}\n"
            
            if summary.when_b_better:
                content += f"- Method B advantages: {', '.join(summary.when_b_better)}\n"
            
            content += "\n"
        
        return ReportSection(
            title="Analysis Method Comparison",
            content=content,
            data={
                comparison_type.value: {
                    'total_comparisons': summary.total_comparisons,
                    'classification_agreement_rate': summary.classification_agreement_rate,
                    'horsemen_agreement_rate': summary.horsemen_agreement_rate,
                    'average_speed_difference_ms': summary.average_speed_difference_ms,
                    'accuracy_difference': summary.accuracy_difference,
                    'when_a_better': summary.when_a_better,
                    'when_b_better': summary.when_b_better
                }
                for comparison_type, summary in comparator.summaries.items()
            }
        )
    
    def _generate_detailed_results_section(self, metrics: RunMetrics, traces: List[PipelineTrace]) -> ReportSection:
        """Generate detailed results section."""
        
        content = f"""
### Detailed Test Results

**Sample Results Summary:**
- Total samples analyzed: {len(metrics.sample_results)}
- Classification distribution:
"""
        
        # Count classifications
        classifications = {}
        for result in metrics.sample_results:
            actual_class = result['actual'].get('classification', 'UNKNOWN')
            classifications[actual_class] = classifications.get(actual_class, 0) + 1
        
        for classification, count in sorted(classifications.items()):
            content += f"  - {classification}: {count} ({count/len(metrics.sample_results):.1%})\n"
        
        content += "\n**Four Horsemen Detection Summary:**\n"
        
        # Count horsemen detections
        all_horsemen = []
        for result in metrics.sample_results:
            all_horsemen.extend(result['actual'].get('horsemen_detected', []))
        
        from collections import Counter
        horsemen_counts = Counter(all_horsemen)
        
        for horseman, count in horsemen_counts.most_common():
            content += f"  - {horseman}: detected in {count} samples\n"
        
        if not horsemen_counts:
            content += "  - No Four Horsemen patterns detected in any samples\n"
        
        return ReportSection(
            title="Detailed Test Results",
            content=content,
            data={
                'classification_distribution': classifications,
                'horsemen_detections': dict(horsemen_counts),
                'sample_count': len(metrics.sample_results)
            }
        )
    
    def _generate_recommendations_section(self, metrics: RunMetrics, comparator: AnalysisComparator) -> ReportSection:
        """Generate recommendations based on test results."""
        
        recommendations = []
        
        # Accuracy recommendations
        if metrics.accuracy_metrics.classification_accuracy < 0.8:
            recommendations.append("🔴 **Critical**: Classification accuracy is below 80%. Review model parameters and training data.")
        
        if metrics.accuracy_metrics.false_negatives > metrics.accuracy_metrics.false_positives * 2:
            recommendations.append("⚠️ **Important**: High false negative rate - system may be under-detecting toxic content.")
        
        if metrics.accuracy_metrics.false_positives > metrics.accuracy_metrics.false_negatives * 2:
            recommendations.append("⚠️ **Important**: High false positive rate - system may be over-blocking safe content.")
        
        # Performance recommendations
        if metrics.performance_metrics.average_processing_time_ms > 1000:
            recommendations.append("⚠️ **Performance**: Average processing time exceeds 1 second. Consider optimization.")
        
        # Cost recommendations
        savings_rate = metrics.cost_metrics.cost_savings_from_hybrid / max(metrics.cost_metrics.total_estimated_cost + metrics.cost_metrics.cost_savings_from_hybrid, 0.0001)
        if savings_rate < 0.2:
            recommendations.append("💡 **Optimization**: Hybrid approach savings are low. Review local analysis effectiveness.")
        
        cache_hit_rate = metrics.cost_metrics.cache_hit_count / max(metrics.cost_metrics.cache_hit_count + metrics.cost_metrics.cache_miss_count, 1)
        if cache_hit_rate < 0.1:
            recommendations.append("💡 **Optimization**: Low cache hit rate. Consider adjusting cache strategy.")
        
        # Comparison recommendations
        for comparison_type, summary in comparator.summaries.items():
            if summary.classification_agreement_rate < 0.7:
                recommendations.append(f"🔍 **Investigation**: Low agreement rate ({summary.classification_agreement_rate:.1%}) between {comparison_type.value.replace('_', ' ')} methods.")
        
        if not recommendations:
            recommendations.append("✅ **Excellent**: All metrics are within acceptable ranges. System performing well.")
        
        content = "### Recommendations\n\n"
        for i, rec in enumerate(recommendations, 1):
            content += f"{i}. {rec}\n\n"
        
        return ReportSection(
            title="Recommendations",
            content=content,
            data={'recommendations': recommendations}
        )
    
    def export_html_report(self, report: Dict[str, Any], output_path: str):
        """Export report as HTML file."""
        
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Four Horsemen Analysis Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1, h2, h3 { color: #333; }
        .summary { background: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .metric { display: inline-block; margin: 10px 20px 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 3px; }
        .section { margin: 30px 0; }
        .recommendation { margin: 10px 0; padding: 10px; border-left: 4px solid #007bff; background: #f8f9fa; }
        .critical { border-left-color: #dc3545; }
        .warning { border-left-color: #ffc107; }
        .success { border-left-color: #28a745; }
        pre { background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Four Horsemen Analysis Test Report</h1>
    
    <div class="summary">
        <h2>Report Metadata</h2>
        <div class="metric">
            <strong>Generated:</strong> {generated_at}
        </div>
        <div class="metric">
            <strong>Run ID:</strong> {run_id}
        </div>
        <div class="metric">
            <strong>Duration:</strong> {test_duration:.1f} minutes
        </div>
    </div>
    
    <div class="summary">
        {executive_summary}
    </div>
    
    {sections_html}
</body>
</html>
"""
        
        # Generate sections HTML
        sections_html = ""
        for section in report['sections']:
            sections_html += f'<div class="section"><h2>{section.title}</h2>\n'
            
            # Convert markdown-style content to HTML
            content_html = section.content.replace('\n', '<br>\n')
            content_html = content_html.replace('**', '<strong>').replace('**', '</strong>')
            content_html = content_html.replace('###', '<h3>').replace('\n', '</h3>\n', 1)
            
            sections_html += f'<div>{content_html}</div>\n'
            
            # Add data tables if available
            if section.data:
                sections_html += '<h4>Data Summary</h4>\n<pre>'
                sections_html += json.dumps(section.data, indent=2)
                sections_html += '</pre>\n'
            
            sections_html += '</div>\n'
        
        # Fill template
        html_content = html_template.format(
            generated_at=report['metadata']['generated_at'],
            run_id=report['metadata']['run_id'],
            test_duration=report['metadata']['test_duration_minutes'] or 0,
            executive_summary=report['executive_summary'].replace('\n', '<br>\n'),
            sections_html=sections_html
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def export_json_report(self, report: Dict[str, Any], output_path: str):
        """Export report as JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
