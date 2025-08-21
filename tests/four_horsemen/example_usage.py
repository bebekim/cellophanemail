"""Example usage of the Four Horsemen testing framework.

This file demonstrates how to use the comprehensive testing framework
to evaluate your Four Horsemen email analysis system.
"""

import asyncio
import os
from datetime import datetime

from .test_runner import (
    FourHorsemenTestRunner, 
    TestConfiguration,
    run_quick_test,
    run_accuracy_test,
    run_cost_optimization_test
)
from .test_samples import ToxicityLevel


async def example_quick_test():
    """Example: Run a quick test with a few samples."""
    print("🚀 Running Quick Test Example")
    print("=" * 50)
    
    try:
        result = await run_quick_test()
        
        # Extract key metrics
        accuracy = result['sections'][1]['data']['classification_accuracy']
        avg_time = result['sections'][2]['data']['average_time_ms']
        total_cost = result['sections'][3]['data']['total_cost']
        
        print(f"✅ Test completed successfully!")
        print(f"📊 Classification Accuracy: {accuracy:.1%}")
        print(f"⏱️ Average Processing Time: {avg_time:.1f}ms")
        print(f"💰 Total API Cost: ${total_cost:.4f}")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise


async def example_custom_test():
    """Example: Run a custom test with specific configuration."""
    print("🔧 Running Custom Test Example")
    print("=" * 50)
    
    # Create custom configuration
    config = TestConfiguration(
        run_id=f"custom_{int(datetime.now().timestamp())}",
        test_name="Custom Four Horsemen Test",
        
        # Test only harmful and abusive samples
        include_toxicity_levels=[ToxicityLevel.HARMFUL, ToxicityLevel.ABUSIVE],
        sample_limit=8,  # Limit for demo
        
        # Test configuration
        test_hybrid_mode=True,
        test_traditional_mode=True,
        test_local_only=True,
        compare_methods=True,
        
        # Output configuration
        generate_html_report=True,
        generate_json_report=True,
        output_directory="test_results",
        
        # Logging
        detailed_logging=True,
        log_level="INFO"
    )
    
    try:
        # Run the test
        runner = FourHorsemenTestRunner(config)
        result = await runner.run_comprehensive_test()
        
        print("✅ Custom test completed!")
        
        # Print summary information
        metadata = result['metadata']
        print(f"📋 Run ID: {metadata['run_id']}")
        print(f"⏱️ Duration: {metadata['test_duration_minutes']:.1f} minutes")
        
        # Print accuracy summary
        accuracy_data = result['sections'][1]['data']
        print(f"📊 Accuracy: {accuracy_data['classification_accuracy']:.1%}")
        print(f"📊 Precision: {accuracy_data['precision']:.1%}")
        print(f"📊 Recall: {accuracy_data['recall']:.1%}")
        
        # Print cost summary
        cost_data = result['sections'][3]['data']
        print(f"💰 Total Cost: ${cost_data['total_cost']:.4f}")
        print(f"💰 Hybrid Savings: ${cost_data['cost_savings']:.4f}")
        print(f"🎯 Cache Hit Rate: {cost_data['cache_hit_rate']:.1%}")
        
        return result
        
    except Exception as e:
        print(f"❌ Custom test failed: {str(e)}")
        raise


async def example_performance_focused_test():
    """Example: Run a test focused on performance evaluation."""
    print("⚡ Running Performance-Focused Test Example")
    print("=" * 50)
    
    config = TestConfiguration(
        run_id=f"perf_{int(datetime.now().timestamp())}",
        test_name="Performance Evaluation Test",
        
        # Focus on business communications (most common)
        include_categories=["business_communication", "workplace_communication"],
        sample_limit=15,
        
        # Test all modes for comparison
        test_hybrid_mode=True,
        test_traditional_mode=True,
        test_local_only=True,
        compare_methods=True,
        
        # Performance-focused settings
        enable_detailed_tracing=True,
        parallel_execution=False,  # Set to True for real performance testing
        
        # Minimal logging for performance
        log_level="WARNING",
        detailed_logging=False
    )
    
    try:
        runner = FourHorsemenTestRunner(config)
        result = await runner.run_comprehensive_test()
        
        print("✅ Performance test completed!")
        
        # Extract performance insights
        perf_data = result['sections'][2]['data']
        print(f"⚡ Average Time: {perf_data['average_time_ms']:.1f}ms")
        print(f"⚡ Median Time: {perf_data['median_time_ms']:.1f}ms")
        print(f"⚡ Range: {perf_data['min_time_ms']:.1f}ms - {perf_data['max_time_ms']:.1f}ms")
        
        if perf_data.get('local_analysis_avg') and perf_data.get('ai_analysis_avg'):
            speedup = perf_data['ai_analysis_avg'] / perf_data['local_analysis_avg']
            print(f"🔄 AI vs Local Speed Ratio: {speedup:.1f}x")
        
        # Extract comparison insights
        if len(result['sections']) > 4:  # Has comparison section
            comp_data = result['sections'][4]['data']
            for comp_type, data in comp_data.items():
                if 'local_vs_ai' in comp_type:
                    print(f"⚖️ Local vs AI Agreement: {data['classification_agreement_rate']:.1%}")
                    print(f"⚖️ Speed Difference: {data['average_speed_difference_ms']:.1f}ms")
        
        return result
        
    except Exception as e:
        print(f"❌ Performance test failed: {str(e)}")
        raise


async def example_accuracy_deep_dive():
    """Example: Run a deep dive test focused on accuracy for challenging cases."""
    print("🎯 Running Accuracy Deep Dive Example")
    print("=" * 50)
    
    try:
        result = await run_accuracy_test()
        
        print("✅ Accuracy test completed!")
        
        # Deep dive into accuracy metrics
        accuracy_data = result['sections'][1]['data']
        
        print(f"🎯 Overall Accuracy: {accuracy_data['classification_accuracy']:.1%}")
        print(f"🎯 Precision: {accuracy_data['precision']:.1%}")
        print(f"🎯 Recall: {accuracy_data['recall']:.1%}")
        print(f"🎯 F1-Score: {accuracy_data['f1_score']:.3f}")
        
        print("\n🐎 Four Horsemen Detection Performance:")
        horsemen_perf = accuracy_data['horsemen_performance']
        
        for horseman, metrics in horsemen_perf.items():
            precision = metrics['precision']
            recall = metrics['recall']
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            print(f"  {horseman.title():>12}: Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")
        
        # Error analysis
        print(f"\n⚠️ Error Analysis:")
        print(f"  False Positives: {accuracy_data['false_positives']} (over-blocking)")
        print(f"  False Negatives: {accuracy_data['false_negatives']} (under-detecting)")
        
        return result
        
    except Exception as e:
        print(f"❌ Accuracy test failed: {str(e)}")
        raise


async def example_cost_optimization_analysis():
    """Example: Run a test focused on cost optimization evaluation."""
    print("💰 Running Cost Optimization Analysis Example")
    print("=" * 50)
    
    try:
        result = await run_cost_optimization_test()
        
        print("✅ Cost optimization test completed!")
        
        # Extract cost insights
        cost_data = result['sections'][3]['data']
        
        print(f"💰 Total API Calls: {cost_data['total_api_calls']}")
        print(f"💰 Total Cost: ${cost_data['total_cost']:.4f}")
        print(f"💰 Average Cost per Email: ${cost_data['average_cost_per_email']:.4f}")
        
        # Hybrid optimization breakdown
        total_emails = cost_data['hybrid_local_only'] + cost_data['hybrid_ai_used']
        if total_emails > 0:
            local_rate = cost_data['hybrid_local_only'] / total_emails
            print(f"🔄 Local-only Processing: {cost_data['hybrid_local_only']} emails ({local_rate:.1%})")
            print(f"🔄 AI Processing Used: {cost_data['hybrid_ai_used']} emails ({1-local_rate:.1%})")
        
        print(f"💾 Cache Hit Rate: {cost_data['cache_hit_rate']:.1%}")
        print(f"💵 Estimated Savings: ${cost_data['cost_savings']:.4f}")
        
        savings_rate = cost_data['cost_savings'] / (cost_data['total_cost'] + cost_data['cost_savings']) if cost_data['total_cost'] + cost_data['cost_savings'] > 0 else 0
        print(f"📊 Savings Rate: {savings_rate:.1%}")
        
        return result
        
    except Exception as e:
        print(f"❌ Cost optimization test failed: {str(e)}")
        raise


async def example_comparison_analysis():
    """Example: Analyze differences between local and AI analysis."""
    print("⚖️ Running Comparison Analysis Example")
    print("=" * 50)
    
    # Run a test that includes comparisons
    config = TestConfiguration(
        run_id=f"comparison_{int(datetime.now().timestamp())}",
        test_name="Analysis Method Comparison",
        sample_limit=10,
        test_hybrid_mode=True,
        test_traditional_mode=True,
        test_local_only=True,
        compare_methods=True,  # Important!
        enable_detailed_tracing=True
    )
    
    try:
        runner = FourHorsemenTestRunner(config)
        result = await runner.run_comprehensive_test()
        
        print("✅ Comparison analysis completed!")
        
        # Extract comparison insights
        comp_data = result['sections'][4]['data']  # Comparison section
        
        for comp_type, data in comp_data.items():
            print(f"\n📊 {comp_type.replace('_', ' ').title()}:")
            print(f"  Classification Agreement: {data['classification_agreement_rate']:.1%}")
            print(f"  Four Horsemen Agreement: {data['horsemen_agreement_rate']:.1%}")
            print(f"  Speed Difference: {data['average_speed_difference_ms']:.1f}ms")
            
            if data['accuracy_difference'] != 0:
                advantage = "Method B" if data['accuracy_difference'] > 0 else "Method A"
                print(f"  Accuracy Advantage: {advantage} (+{abs(data['accuracy_difference']):.1%})")
            
            if data['when_a_better']:
                print(f"  Method A Better For: {', '.join(data['when_a_better'])}")
            
            if data['when_b_better']:
                print(f"  Method B Better For: {', '.join(data['when_b_better'])}")
        
        return result
        
    except Exception as e:
        print(f"❌ Comparison analysis failed: {str(e)}")
        raise


async def run_all_examples():
    """Run all example tests sequentially."""
    print("🧪 Running All Four Horsemen Testing Examples")
    print("=" * 60)
    
    examples = [
        ("Quick Test", example_quick_test),
        ("Custom Test", example_custom_test),
        ("Performance Test", example_performance_focused_test),
        ("Accuracy Deep Dive", example_accuracy_deep_dive),
        ("Cost Optimization", example_cost_optimization_analysis),
        ("Comparison Analysis", example_comparison_analysis)
    ]
    
    results = {}
    
    for name, example_func in examples:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            start_time = datetime.now()
            result = await example_func()
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            results[name] = {
                'success': True,
                'duration_seconds': duration,
                'result': result
            }
            
            print(f"✅ {name} completed in {duration:.1f} seconds")
            
        except Exception as e:
            results[name] = {
                'success': False,
                'error': str(e)
            }
            print(f"❌ {name} failed: {str(e)}")
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY OF ALL TESTS")
    print(f"{'='*60}")
    
    successful = sum(1 for r in results.values() if r['success'])
    total = len(results)
    
    print(f"✅ Successful: {successful}/{total}")
    print(f"❌ Failed: {total - successful}/{total}")
    
    total_time = sum(r.get('duration_seconds', 0) for r in results.values() if r['success'])
    print(f"⏱️ Total Time: {total_time:.1f} seconds")
    
    for name, result in results.items():
        status = "✅" if result['success'] else "❌"
        duration = f"({result.get('duration_seconds', 0):.1f}s)" if result['success'] else ""
        print(f"  {status} {name} {duration}")
    
    return results


if __name__ == "__main__":
    """
    Example usage:
    
    # Run individual examples
    python -m tests.four_horsemen.example_usage
    
    # Or import and use in your code
    from tests.four_horsemen.example_usage import example_quick_test
    result = await example_quick_test()
    """
    
    # Ensure output directory exists
    os.makedirs("test_results", exist_ok=True)
    
    # Run all examples
    asyncio.run(run_all_examples())
