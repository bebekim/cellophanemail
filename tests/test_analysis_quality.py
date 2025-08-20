#!/usr/bin/env python3
"""
Analysis Quality Test - Tests Four Horsemen detection on all samples.
This tests the AI/analysis quality, not code functionality.
No emails are sent - just analysis output evaluation.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

# Add src to path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

from tests.four_horsemen import (
    ALL_SAMPLES, ToxicityLevel, FourHorseman,
    get_samples_by_classification
)
from cellophanemail.core.content_analyzer import ContentAnalysisService


class AnalysisQualityTest:
    """Test analysis quality across all test samples."""
    
    def __init__(self, use_hybrid: bool = True):
        self.analyzer = ContentAnalysisService()
        self.use_hybrid = use_hybrid
        self.results = []
        self.stats = defaultdict(int)
        
    async def run_quality_test(self) -> Dict[str, Any]:
        """Run analysis on all samples and evaluate quality."""
        
        print("\n" + "="*70)
        print("ANALYSIS QUALITY TEST - Four Horsemen Detection")
        print("="*70)
        print(f"Mode: {'Hybrid (Local + AI)' if self.use_hybrid else 'AI Only'}")
        print(f"Samples: {len(ALL_SAMPLES)} total")
        print()
        
        # For testing, limit to first 3 samples to avoid hitting API limits
        test_samples = ALL_SAMPLES[:3] if os.getenv('QUICK_TEST') else ALL_SAMPLES
        
        # Analyze each sample
        for i, sample in enumerate(test_samples, 1):
            print(f"\nAnalyzing {i}/{len(test_samples)}: {sample.id}")
            print(f"Expected: {sample.expected_classification.value}")
            print(f"Content: {sample.content[:100]}{'...' if len(sample.content) > 100 else ''}")
            
            try:
                # Analyze content
                result = self.analyzer.analyze_content(
                    content=sample.content,
                    sender=sample.sender or "unknown@example.com",
                    use_hybrid=self.use_hybrid
                )
                
                # Store result
                test_result = {
                    'sample_id': sample.id,
                    'language': sample.language,
                    'category': sample.category,
                    'expected_classification': sample.expected_classification.value,
                    'expected_horsemen': [h.value for h in sample.expected_horsemen],
                    'actual_classification': result['classification'],
                    'actual_horsemen': result['horsemen_detected'],
                    'reasoning': result['reasoning'],
                    'correct_classification': result['classification'] == sample.expected_classification.value,
                    'cost_optimization': result.get('cost_optimization', 'unknown')
                }
                
                self.results.append(test_result)
                
                # Print result
                correct = "✅" if test_result['correct_classification'] else "❌"
                print(f"Result: {result['classification']} {correct}")
                if result['horsemen_detected']:
                    print(f"Horsemen: {', '.join(result['horsemen_detected'])}")
                if result.get('cost_optimization'):
                    print(f"Mode: {result['cost_optimization']}")
                
                # Update stats
                self.stats['total'] += 1
                if test_result['correct_classification']:
                    self.stats['correct'] += 1
                self.stats[f"expected_{sample.expected_classification.value}"] += 1
                self.stats[f"actual_{result['classification']}"] += 1
                
                # Brief pause to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error analyzing sample: {e}")
                self.stats['errors'] += 1
        
        # Generate summary
        return self._generate_summary()
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary and analysis."""
        
        print("\n" + "="*70)
        print("ANALYSIS QUALITY SUMMARY")
        print("="*70)
        
        # Overall accuracy
        accuracy = (self.stats['correct'] / self.stats['total']) * 100 if self.stats['total'] > 0 else 0
        print(f"\n📊 Overall Accuracy: {accuracy:.1f}% ({self.stats['correct']}/{self.stats['total']})")
        
        # Accuracy by classification
        print("\n📋 Accuracy by Expected Classification:")
        for classification in ToxicityLevel:
            expected_count = self.stats.get(f"expected_{classification.value}", 0)
            if expected_count > 0:
                correct_for_class = len([
                    r for r in self.results 
                    if r['expected_classification'] == classification.value 
                    and r['correct_classification']
                ])
                class_accuracy = (correct_for_class / expected_count) * 100
                print(f"  {classification.value}: {class_accuracy:.1f}% ({correct_for_class}/{expected_count})")
        
        # Confusion matrix
        print("\n🔄 Classification Results:")
        classification_matrix = defaultdict(int)
        for result in self.results:
            key = f"{result['expected_classification']} → {result['actual_classification']}"
            classification_matrix[key] += 1
        
        for key, count in sorted(classification_matrix.items()):
            print(f"  {key}: {count}")
        
        # Cost optimization breakdown
        print("\n💰 Cost Optimization:")
        cost_breakdown = defaultdict(int)
        for result in self.results:
            cost_breakdown[result['cost_optimization']] += 1
        
        for mode, count in cost_breakdown.items():
            percentage = (count / len(self.results)) * 100
            print(f"  {mode}: {count} ({percentage:.1f}%)")
        
        # Language breakdown
        print("\n🌍 Language Analysis:")
        language_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
        for result in self.results:
            lang = result['language']
            language_stats[lang]['total'] += 1
            if result['correct_classification']:
                language_stats[lang]['correct'] += 1
        
        for lang, stats in language_stats.items():
            lang_accuracy = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
            print(f"  {lang}: {lang_accuracy:.1f}% ({stats['correct']}/{stats['total']})")
        
        # Errors by horseman
        print("\n🐎 Four Horsemen Detection:")
        horseman_stats = defaultdict(lambda: {'expected': 0, 'detected': 0, 'missed': 0, 'false_positive': 0})
        
        for result in self.results:
            expected_set = set(result['expected_horsemen'])
            actual_set = set(result['actual_horsemen'])
            
            for horseman in expected_set:
                horseman_stats[horseman]['expected'] += 1
                if horseman in actual_set:
                    horseman_stats[horseman]['detected'] += 1
                else:
                    horseman_stats[horseman]['missed'] += 1
            
            for horseman in actual_set:
                if horseman not in expected_set:
                    horseman_stats[horseman]['false_positive'] += 1
        
        for horseman, stats in horseman_stats.items():
            precision = stats['detected'] / (stats['detected'] + stats['false_positive']) if (stats['detected'] + stats['false_positive']) > 0 else 0
            recall = stats['detected'] / stats['expected'] if stats['expected'] > 0 else 0
            print(f"  {horseman}: Precision {precision:.2f}, Recall {recall:.2f}")
        
        # Save detailed results
        self._save_results()
        
        summary = {
            'accuracy': accuracy,
            'total_samples': self.stats['total'],
            'correct_predictions': self.stats['correct'],
            'test_mode': 'hybrid' if self.use_hybrid else 'ai_only',
            'timestamp': datetime.now().isoformat(),
            'detailed_results': self.results
        }
        
        return summary
    
    def _save_results(self):
        """Save detailed results to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        mode = 'hybrid' if self.use_hybrid else 'ai_only'
        filename = f"analysis_quality_{mode}_{timestamp}.json"
        
        output = {
            'summary': {
                'accuracy': (self.stats['correct'] / self.stats['total']) * 100 if self.stats['total'] > 0 else 0,
                'total_samples': self.stats['total'],
                'correct_predictions': self.stats['correct'],
                'test_mode': mode,
                'timestamp': datetime.now().isoformat()
            },
            'detailed_results': self.results,
            'statistics': dict(self.stats)
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {filename}")


async def run_analysis_test(use_hybrid: bool = True, ai_only: bool = False):
    """Run the analysis quality test."""
    
    if ai_only:
        print("Running AI-only analysis test...")
        tester = AnalysisQualityTest(use_hybrid=False)
        await tester.run_quality_test()
    
    if use_hybrid:
        print("Running hybrid analysis test...")
        tester = AnalysisQualityTest(use_hybrid=True)
        await tester.run_quality_test()


def compare_modes():
    """Compare hybrid vs AI-only modes."""
    print("\n" + "="*70)
    print("COMPARISON MODE - Hybrid vs AI-Only")
    print("="*70)
    print("\nThis will run both modes and compare results...")
    print("Note: AI-only mode will use more API credits")
    
    response = input("\nProceed with comparison? (y/N): ").lower().strip()
    if response != 'y':
        print("Comparison cancelled.")
        return
    
    async def run_comparison():
        # Run hybrid first (cheaper)
        print("\n1️⃣ Running HYBRID mode...")
        await run_analysis_test(use_hybrid=True, ai_only=False)
        
        print("\n2️⃣ Running AI-ONLY mode...")
        await run_analysis_test(use_hybrid=False, ai_only=True)
        
        print("\n✅ Comparison complete! Check the saved JSON files for detailed comparison.")
    
    asyncio.run(run_comparison())


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Four Horsemen analysis quality")
    parser.add_argument('--ai-only', action='store_true', help='Test AI-only mode')
    parser.add_argument('--hybrid', action='store_true', help='Test hybrid mode (default)')
    parser.add_argument('--compare', action='store_true', help='Compare both modes')
    
    args = parser.parse_args()
    
    if args.compare:
        compare_modes()
    elif args.ai_only:
        asyncio.run(run_analysis_test(use_hybrid=False, ai_only=True))
    else:
        # Default to hybrid mode
        asyncio.run(run_analysis_test(use_hybrid=True, ai_only=False))