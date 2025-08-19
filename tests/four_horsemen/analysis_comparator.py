"""Analysis comparator for local vs AI Four Horsemen analysis comparison."""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import statistics

from .test_samples import EmailTestSample, ToxicityLevel, FourHorseman


@dataclass
class AnalysisComparison:
    """Comparison between two analysis results."""
    sample_id: str
    content: str
    language: str
    
    # Local analysis results
    local_classification: str
    local_horsemen: List[str]
    local_reasoning: str
    local_examples: List[str]
    local_processing_time_ms: float
    
    # AI analysis results  
    ai_classification: str
    ai_horsemen: List[str]
    ai_reasoning: str
    ai_examples: List[str]
    ai_processing_time_ms: float
    ai_cost_estimate: float
    
    # Comparison metrics
    classifications_agree: bool
    horsemen_agreement_rate: float
    confidence_difference: float
    speed_ratio: float  # local_time / ai_time


@dataclass
class ComparisonMetrics:
    """Metrics for comparing analysis methods."""
    total_comparisons: int = 0
    
    # Agreement rates
    classification_agreement_rate: float = 0.0
    horsemen_agreement_rate: float = 0.0
    
    # Performance comparison
    local_avg_time_ms: float = 0.0
    ai_avg_time_ms: float = 0.0
    speed_advantage: float = 0.0  # How much faster local is
    
    # Cost comparison
    ai_total_cost: float = 0.0
    local_total_cost: float = 0.0  # Usually 0
    cost_savings: float = 0.0
    
    # Agreement by classification level
    agreement_by_classification: Dict[str, float] = field(default_factory=dict)
    
    # Agreement by language
    agreement_by_language: Dict[str, float] = field(default_factory=dict)
    
    # Disagreement patterns
    disagreement_patterns: Dict[str, int] = field(default_factory=dict)


@dataclass
class MethodEffectiveness:
    """Effectiveness comparison between local and AI methods."""
    
    # Accuracy vs ground truth
    local_accuracy: float = 0.0
    ai_accuracy: float = 0.0
    accuracy_difference: float = 0.0
    
    # Per-horseman effectiveness
    local_horsemen_f1: Dict[str, float] = field(default_factory=dict)
    ai_horsemen_f1: Dict[str, float] = field(default_factory=dict)
    
    # When each method performs better
    local_better_cases: List[str] = field(default_factory=list)
    ai_better_cases: List[str] = field(default_factory=list)
    
    # Cost-effectiveness ratio
    local_cost_effectiveness: float = 0.0  # accuracy / cost
    ai_cost_effectiveness: float = 0.0


class AnalysisComparator:
    """Comparator for analyzing differences between local and AI analysis."""
    
    def __init__(self):
        """Initialize analysis comparator."""
        self.comparisons: List[AnalysisComparison] = []
        self.ground_truth_samples: Dict[str, EmailTestSample] = {}
        
    def add_comparison(
        self,
        sample: EmailTestSample,
        local_result: Dict[str, Any],
        ai_result: Dict[str, Any],
        local_time_ms: float,
        ai_time_ms: float,
        ai_cost_estimate: float = 0.002
    ):
        """Add a comparison between local and AI analysis."""
        
        # Calculate agreement metrics
        classifications_agree = (
            local_result.get('classification', '') == 
            ai_result.get('classification', '')
        )
        
        local_horsemen = set(local_result.get('horsemen_detected', []))
        ai_horsemen = set(ai_result.get('horsemen_detected', []))
        
        if local_horsemen or ai_horsemen:
            intersection = len(local_horsemen & ai_horsemen)
            union = len(local_horsemen | ai_horsemen)
            horsemen_agreement = intersection / union if union > 0 else 1.0
        else:
            horsemen_agreement = 1.0  # Both found no horsemen
        
        comparison = AnalysisComparison(
            sample_id=sample.id,
            content=sample.content,
            language=sample.language,
            
            # Local results
            local_classification=local_result.get('classification', 'UNKNOWN'),
            local_horsemen=local_result.get('horsemen_detected', []),
            local_reasoning=local_result.get('reasoning', ''),
            local_examples=local_result.get('specific_examples', []),
            local_processing_time_ms=local_time_ms,
            
            # AI results
            ai_classification=ai_result.get('classification', 'UNKNOWN'),
            ai_horsemen=ai_result.get('horsemen_detected', []),
            ai_reasoning=ai_result.get('reasoning', ''),
            ai_examples=ai_result.get('specific_examples', []),
            ai_processing_time_ms=ai_time_ms,
            ai_cost_estimate=ai_cost_estimate,
            
            # Comparison metrics
            classifications_agree=classifications_agree,
            horsemen_agreement_rate=horsemen_agreement,
            confidence_difference=0.0,  # Could be calculated from reasoning length/specificity
            speed_ratio=local_time_ms / ai_time_ms if ai_time_ms > 0 else 0.0
        )
        
        self.comparisons.append(comparison)
        self.ground_truth_samples[sample.id] = sample
    
    def calculate_comparison_metrics(self) -> ComparisonMetrics:
        """Calculate comprehensive comparison metrics."""
        if not self.comparisons:
            return ComparisonMetrics()
        
        total_comparisons = len(self.comparisons)
        
        # Agreement rates
        classification_agreements = sum(1 for c in self.comparisons if c.classifications_agree)
        classification_agreement_rate = classification_agreements / total_comparisons
        
        avg_horsemen_agreement = statistics.mean([c.horsemen_agreement_rate for c in self.comparisons])
        
        # Performance comparison
        local_times = [c.local_processing_time_ms for c in self.comparisons if c.local_processing_time_ms > 0]
        ai_times = [c.ai_processing_time_ms for c in self.comparisons if c.ai_processing_time_ms > 0]
        
        local_avg_time = statistics.mean(local_times) if local_times else 0.0
        ai_avg_time = statistics.mean(ai_times) if ai_times else 0.0
        speed_advantage = ai_avg_time / local_avg_time if local_avg_time > 0 else 0.0
        
        # Cost comparison
        ai_total_cost = sum(c.ai_cost_estimate for c in self.comparisons)
        local_total_cost = 0.0  # Local analysis is essentially free
        cost_savings = ai_total_cost - local_total_cost
        
        # Agreement by classification level
        agreement_by_classification = {}
        classification_counts = defaultdict(int)
        classification_agreements_count = defaultdict(int)
        
        for comparison in self.comparisons:
            expected_classification = self.ground_truth_samples[comparison.sample_id].expected_classification.value
            classification_counts[expected_classification] += 1
            if comparison.classifications_agree:
                classification_agreements_count[expected_classification] += 1
        
        for classification, count in classification_counts.items():
            if count > 0:
                agreement_by_classification[classification] = classification_agreements_count[classification] / count
        
        # Agreement by language
        agreement_by_language = {}
        language_counts = defaultdict(int)
        language_agreements_count = defaultdict(int)
        
        for comparison in self.comparisons:
            language_counts[comparison.language] += 1
            if comparison.classifications_agree:
                language_agreements_count[comparison.language] += 1
        
        for language, count in language_counts.items():
            if count > 0:
                agreement_by_language[language] = language_agreements_count[language] / count
        
        # Disagreement patterns
        disagreement_patterns = defaultdict(int)
        for comparison in self.comparisons:
            if not comparison.classifications_agree:
                pattern = f"{comparison.local_classification} → {comparison.ai_classification}"
                disagreement_patterns[pattern] += 1
        
        return ComparisonMetrics(
            total_comparisons=total_comparisons,
            classification_agreement_rate=classification_agreement_rate,
            horsemen_agreement_rate=avg_horsemen_agreement,
            local_avg_time_ms=local_avg_time,
            ai_avg_time_ms=ai_avg_time,
            speed_advantage=speed_advantage,
            ai_total_cost=ai_total_cost,
            local_total_cost=local_total_cost,
            cost_savings=cost_savings,
            agreement_by_classification=agreement_by_classification,
            agreement_by_language=agreement_by_language,
            disagreement_patterns=dict(disagreement_patterns)
        )
    
    def calculate_method_effectiveness(self) -> MethodEffectiveness:
        """Calculate effectiveness of each method against ground truth."""
        if not self.comparisons or not self.ground_truth_samples:
            return MethodEffectiveness()
        
        # Calculate accuracy vs ground truth
        local_correct = 0
        ai_correct = 0
        
        local_horsemen_metrics = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0})
        ai_horsemen_metrics = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0})
        
        local_better_cases = []
        ai_better_cases = []
        
        for comparison in self.comparisons:
            sample = self.ground_truth_samples[comparison.sample_id]
            expected_classification = sample.expected_classification.value
            expected_horsemen = set(h.value for h in sample.expected_horsemen)
            
            local_classification = comparison.local_classification
            ai_classification = comparison.ai_classification
            
            # Classification accuracy
            if local_classification == expected_classification:
                local_correct += 1
            if ai_classification == expected_classification:
                ai_correct += 1
            
            # Determine which method performed better for this sample
            local_class_correct = local_classification == expected_classification
            ai_class_correct = ai_classification == expected_classification
            
            if local_class_correct and not ai_class_correct:
                local_better_cases.append(comparison.sample_id)
            elif ai_class_correct and not local_class_correct:
                ai_better_cases.append(comparison.sample_id)
            
            # Horsemen detection metrics
            local_horsemen = set(comparison.local_horsemen)
            ai_horsemen = set(comparison.ai_horsemen)
            
            all_horsemen = {'criticism', 'contempt', 'defensiveness', 'stonewalling'}
            
            for horseman in all_horsemen:
                expected_has = horseman in expected_horsemen
                local_has = horseman in local_horsemen
                ai_has = horseman in ai_horsemen
                
                # Local metrics
                if expected_has and local_has:
                    local_horsemen_metrics[horseman]['tp'] += 1
                elif not expected_has and local_has:
                    local_horsemen_metrics[horseman]['fp'] += 1
                elif expected_has and not local_has:
                    local_horsemen_metrics[horseman]['fn'] += 1
                else:  # not expected_has and not local_has
                    local_horsemen_metrics[horseman]['tn'] += 1
                
                # AI metrics
                if expected_has and ai_has:
                    ai_horsemen_metrics[horseman]['tp'] += 1
                elif not expected_has and ai_has:
                    ai_horsemen_metrics[horseman]['fp'] += 1
                elif expected_has and not ai_has:
                    ai_horsemen_metrics[horseman]['fn'] += 1
                else:  # not expected_has and not ai_has
                    ai_horsemen_metrics[horseman]['tn'] += 1
        
        total_samples = len(self.comparisons)
        local_accuracy = local_correct / total_samples if total_samples > 0 else 0.0
        ai_accuracy = ai_correct / total_samples if total_samples > 0 else 0.0
        
        # Calculate F1 scores for horsemen detection
        local_horsemen_f1 = {}
        ai_horsemen_f1 = {}
        
        for horseman in local_horsemen_metrics:
            # Local F1
            local_metrics = local_horsemen_metrics[horseman]
            local_precision = local_metrics['tp'] / (local_metrics['tp'] + local_metrics['fp']) if (local_metrics['tp'] + local_metrics['fp']) > 0 else 0.0
            local_recall = local_metrics['tp'] / (local_metrics['tp'] + local_metrics['fn']) if (local_metrics['tp'] + local_metrics['fn']) > 0 else 0.0
            local_f1 = 2 * (local_precision * local_recall) / (local_precision + local_recall) if (local_precision + local_recall) > 0 else 0.0
            local_horsemen_f1[horseman] = local_f1
            
            # AI F1
            ai_metrics = ai_horsemen_metrics[horseman]
            ai_precision = ai_metrics['tp'] / (ai_metrics['tp'] + ai_metrics['fp']) if (ai_metrics['tp'] + ai_metrics['fp']) > 0 else 0.0
            ai_recall = ai_metrics['tp'] / (ai_metrics['tp'] + ai_metrics['fn']) if (ai_metrics['tp'] + ai_metrics['fn']) > 0 else 0.0
            ai_f1 = 2 * (ai_precision * ai_recall) / (ai_precision + ai_recall) if (ai_precision + ai_recall) > 0 else 0.0
            ai_horsemen_f1[horseman] = ai_f1
        
        # Cost-effectiveness (accuracy per dollar)
        comparison_metrics = self.calculate_comparison_metrics()
        local_cost_effectiveness = local_accuracy / 0.0001 if local_accuracy > 0 else 0.0  # Local cost is virtually zero
        ai_cost_effectiveness = ai_accuracy / comparison_metrics.ai_total_cost if comparison_metrics.ai_total_cost > 0 else 0.0
        
        return MethodEffectiveness(
            local_accuracy=local_accuracy,
            ai_accuracy=ai_accuracy,
            accuracy_difference=ai_accuracy - local_accuracy,
            local_horsemen_f1=local_horsemen_f1,
            ai_horsemen_f1=ai_horsemen_f1,
            local_better_cases=local_better_cases,
            ai_better_cases=ai_better_cases,
            local_cost_effectiveness=local_cost_effectiveness,
            ai_cost_effectiveness=ai_cost_effectiveness
        )
    
    def get_disagreement_analysis(self) -> Dict[str, Any]:
        """Analyze patterns in disagreements between local and AI."""
        disagreements = [c for c in self.comparisons if not c.classifications_agree]
        
        if not disagreements:
            return {"message": "No disagreements found"}
        
        # Pattern analysis
        patterns = defaultdict(list)
        for disagreement in disagreements:
            pattern = f"{disagreement.local_classification} vs {disagreement.ai_classification}"
            patterns[pattern].append({
                "sample_id": disagreement.sample_id,
                "content_preview": disagreement.content[:100] + "..." if len(disagreement.content) > 100 else disagreement.content,
                "language": disagreement.language,
                "local_reasoning": disagreement.local_reasoning,
                "ai_reasoning": disagreement.ai_reasoning
            })
        
        # Language-specific disagreements
        language_disagreements = defaultdict(int)
        for disagreement in disagreements:
            language_disagreements[disagreement.language] += 1
        
        # Cost of disagreements (when we'd need to use AI)
        disagreement_cost = len(disagreements) * 0.002  # Estimated cost per AI call
        
        return {
            "total_disagreements": len(disagreements),
            "disagreement_rate": len(disagreements) / len(self.comparisons) if self.comparisons else 0.0,
            "patterns": dict(patterns),
            "language_breakdown": dict(language_disagreements),
            "estimated_cost_of_disagreements": disagreement_cost,
            "most_common_pattern": max(patterns.keys(), key=lambda k: len(patterns[k])) if patterns else None
        }
    
    def get_recommendation_analysis(self) -> Dict[str, Any]:
        """Generate recommendations based on analysis comparison."""
        if not self.comparisons:
            return {"error": "No comparison data available"}
        
        comparison_metrics = self.calculate_comparison_metrics()
        effectiveness = self.calculate_method_effectiveness()
        
        recommendations = []
        
        # Speed recommendation
        if comparison_metrics.speed_advantage > 10:  # Local is 10x faster
            recommendations.append({
                "category": "performance",
                "recommendation": f"Local analysis is {comparison_metrics.speed_advantage:.1f}x faster than AI",
                "confidence": "high"
            })
        
        # Accuracy recommendation
        if abs(effectiveness.accuracy_difference) < 0.05:  # Within 5%
            recommendations.append({
                "category": "accuracy",
                "recommendation": "Local and AI analysis have similar accuracy - consider using local for cost savings",
                "confidence": "medium"
            })
        elif effectiveness.accuracy_difference > 0.1:  # AI is >10% better
            recommendations.append({
                "category": "accuracy", 
                "recommendation": "AI analysis significantly more accurate - worth the cost for high-stakes content",
                "confidence": "high"
            })
        
        # Cost recommendation
        if comparison_metrics.cost_savings > 0.10:  # Save >10 cents
            recommendations.append({
                "category": "cost",
                "recommendation": f"Local analysis saves ${comparison_metrics.cost_savings:.3f} per batch",
                "confidence": "high"
            })
        
        # Hybrid recommendation
        agreement_rate = comparison_metrics.classification_agreement_rate
        if 0.7 <= agreement_rate <= 0.9:  # 70-90% agreement
            recommendations.append({
                "category": "hybrid",
                "recommendation": "Use hybrid approach: local first, AI for disagreements or uncertain cases",
                "confidence": "high"
            })
        
        return {
            "overall_recommendation": self._get_overall_recommendation(comparison_metrics, effectiveness),
            "detailed_recommendations": recommendations,
            "key_metrics": {
                "agreement_rate": comparison_metrics.classification_agreement_rate,
                "speed_advantage": comparison_metrics.speed_advantage,
                "accuracy_difference": effectiveness.accuracy_difference,
                "cost_savings": comparison_metrics.cost_savings
            }
        }
    
    def _get_overall_recommendation(self, comparison_metrics: ComparisonMetrics, effectiveness: MethodEffectiveness) -> str:
        """Generate overall recommendation based on metrics."""
        agreement_rate = comparison_metrics.classification_agreement_rate
        accuracy_diff = effectiveness.accuracy_difference
        cost_savings = comparison_metrics.cost_savings
        
        if agreement_rate > 0.9 and abs(accuracy_diff) < 0.05:
            return "Use local analysis only - high agreement and similar accuracy with significant cost savings"
        elif agreement_rate > 0.8 and cost_savings > 0.05:
            return "Use hybrid approach - good agreement with meaningful cost savings"
        elif accuracy_diff > 0.15:
            return "Use AI analysis - significantly better accuracy justifies the cost"
        elif agreement_rate < 0.6:
            return "High disagreement - investigate local analysis patterns or use AI for critical content"
        else:
            return "Balanced approach - consider use case priorities (cost vs accuracy vs speed)"
    
    def clear_comparisons(self):
        """Clear all comparison data."""
        self.comparisons.clear()
        self.ground_truth_samples.clear()


# Export all for easy import
__all__ = [
    "AnalysisComparison",
    "ComparisonMetrics", 
    "MethodEffectiveness",
    "AnalysisComparator"
]