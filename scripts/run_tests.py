#!/usr/bin/env python3
"""
Convenient test runner for CellophoneMail.

Two types of testing:
1. Code Functionality - Tests that pipeline works (1 email, dry-run)
2. Analysis Quality - Tests Four Horsemen detection (all samples, no sending)
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def run_code_tests():
    """Run minimal integration tests to verify code works."""
    print("\n🔧 RUNNING CODE FUNCTIONALITY TESTS")
    print("=" * 60)
    print("Testing that the email pipeline works with minimal samples.")
    print("Uses dry-run mode - no quota consumed, no emails sent.")
    print()
    
    # Ensure dry-run mode
    os.environ['POSTMARK_DRY_RUN'] = 'true'
    os.environ['CELLOPHANEMAIL_TEST_MODE'] = 'true'
    
    test_file = project_root / "tests" / "test_integration_minimal.py"
    
    try:
        result = subprocess.run([
            sys.executable, str(test_file)
        ], cwd=project_root)
        
        if result.returncode == 0:
            print("\n✅ Code functionality tests PASSED!")
            print("Your pipeline is working correctly.")
        else:
            print("\n❌ Code functionality tests FAILED!")
            print("Check the output above for issues.")
            
        return result.returncode
        
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1


def run_analysis_tests(mode='hybrid'):
    """Run analysis quality tests on all Four Horsemen samples."""
    print(f"\n🧠 RUNNING ANALYSIS QUALITY TESTS ({mode.upper()})")
    print("=" * 60)
    print("Testing Four Horsemen detection on all test samples.")
    print("No emails sent - just analysis output evaluation.")
    print()
    
    test_file = project_root / "tests" / "test_analysis_quality.py"
    
    args = [sys.executable, str(test_file)]
    if mode == 'ai-only':
        args.append('--ai-only')
    elif mode == 'compare':
        args.append('--compare')
    # hybrid is default
    
    try:
        result = subprocess.run(args, cwd=project_root)
        return result.returncode
    except Exception as e:
        print(f"\n❌ Error running analysis tests: {e}")
        return 1


def run_all_tests():
    """Run both types of tests."""
    print("\n🚀 RUNNING ALL TESTS")
    print("=" * 60)
    print("1. Code functionality tests (minimal)")
    print("2. Analysis quality tests (all samples)")
    print()
    
    # Run code tests first
    code_result = run_code_tests()
    
    if code_result != 0:
        print("\n⚠️ Code tests failed - skipping analysis tests")
        print("Fix code issues first, then test analysis quality.")
        return code_result
    
    # If code works, test analysis
    analysis_result = run_analysis_tests('hybrid')
    
    if analysis_result == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("Both code functionality and analysis quality look good.")
    else:
        print("\n⚠️ Analysis tests had issues")
        print("Code works but analysis quality needs attention.")
    
    return analysis_result


def main():
    parser = argparse.ArgumentParser(
        description="Run CellophoneMail tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_tests.py code        # Test code works (fast)
  python scripts/run_tests.py analysis    # Test AI analysis quality  
  python scripts/run_tests.py ai-only     # Test with AI-only mode
  python scripts/run_tests.py compare     # Compare hybrid vs AI-only
  python scripts/run_tests.py all         # Run all tests
        """
    )
    
    parser.add_argument(
        'test_type',
        choices=['code', 'analysis', 'ai-only', 'compare', 'all'],
        help='Type of test to run'
    )
    
    args = parser.parse_args()
    
    print("CellophoneMail Test Runner")
    print("=" * 60)
    
    if args.test_type == 'code':
        return run_code_tests()
    elif args.test_type == 'analysis':
        return run_analysis_tests('hybrid')
    elif args.test_type == 'ai-only':
        return run_analysis_tests('ai-only')
    elif args.test_type == 'compare':
        return run_analysis_tests('compare')
    elif args.test_type == 'all':
        return run_all_tests()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)