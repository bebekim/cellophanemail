# CellophoneMail Testing Strategy

## Two Types of Testing

CellophoneMail has **two completely different testing needs** that require different approaches:

### 1. 🔧 Code Functionality Testing
**Purpose**: Verify the email pipeline works correctly  
**Scope**: Minimal emails (1-3 samples)  
**Goal**: Ensure code executes without errors  

### 2. 🧠 Analysis Quality Testing  
**Purpose**: Monitor Four Horsemen detection accuracy  
**Scope**: All test samples (15+ emails)  
**Goal**: Evaluate AI analysis performance  

---

## 1. Code Functionality Testing

### What it tests:
- ✅ Email providers can receive webhooks
- ✅ Email protection processor works
- ✅ Provider registry loads correctly
- ✅ Complete webhook → analysis → forward flow
- ✅ Dry-run mode prevents quota usage

### How to run:
```bash
# Quick test - verifies code works
python scripts/run_tests.py code

# Uses DRY-RUN mode automatically
# No emails sent, no quota used
# Takes ~5 seconds
```

### Sample output:
```
🔧 RUNNING CODE FUNCTIONALITY TESTS
Testing that the email pipeline works with minimal samples.
Uses dry-run mode - no quota consumed, no emails sent.

✅ Postmark pipeline works
✅ SMTP pipeline works  
✅ Protection processor works - Decision: forward=true
✅ Registry works - 2 providers available
✅ Complete flow works - Email forwarded

✅ Code functionality tests PASSED!
Your pipeline is working correctly.
```

### When to use:
- ✅ Before committing code changes
- ✅ After refactoring
- ✅ CI/CD pipeline checks
- ✅ Quick verification during development

---

## 2. Analysis Quality Testing

### What it tests:
- 🎯 Four Horsemen detection accuracy
- 🎯 Classification precision (SAFE/WARNING/HARMFUL/ABUSIVE)
- 🎯 Language-specific performance (EN/KO/mixed)
- 🎯 Cost optimization (hybrid vs AI-only)
- 🎯 Individual horsemen detection (criticism, contempt, etc.)

### How to run:
```bash
# Test analysis quality (hybrid mode)
python scripts/run_tests.py analysis

# Test AI-only mode (uses more credits)
python scripts/run_tests.py ai-only

# Compare both modes
python scripts/run_tests.py compare

# Quick test (3 samples only)
QUICK_TEST=true python scripts/run_tests.py analysis
```

### Sample output:
```
🧠 RUNNING ANALYSIS QUALITY TESTS (HYBRID)
Testing Four Horsemen detection on all test samples.
No emails sent - just analysis output evaluation.

Analyzing 1/15: en_safe_001
Expected: SAFE
Content: Hi team, I hope everyone is doing well...
Result: SAFE ✅
Mode: hybrid_local_only

Analyzing 2/15: en_harmful_contempt_001  
Expected: HARMFUL
Content: You're so pathetic and worthless...
Result: HARMFUL ✅
Horsemen: contempt
Mode: hybrid_ai_used

📊 Overall Accuracy: 86.7% (13/15)

📋 Accuracy by Expected Classification:
  SAFE: 100.0% (5/5)
  WARNING: 75.0% (3/4)  
  HARMFUL: 83.3% (5/6)

💰 Cost Optimization:
  hybrid_local_only: 8 (53.3%)
  hybrid_ai_used: 7 (46.7%)

🐎 Four Horsemen Detection:
  contempt: Precision 0.91, Recall 0.85
  criticism: Precision 0.88, Recall 0.78
```

### When to use:
- 🎯 After changing analysis algorithms
- 🎯 Testing new AI models or prompts
- 🎯 Monitoring analysis performance over time
- 🎯 Before deploying analysis changes
- 🎯 Comparing different analysis modes

---

## Key Differences

| Aspect | Code Testing | Analysis Testing |
|--------|-------------|------------------|
| **Purpose** | Code works | AI quality |
| **Samples** | 1-3 emails | All samples (15+) |
| **Speed** | ~5 seconds | ~2-5 minutes |
| **Cost** | Free (dry-run) | API credits used |
| **Output** | Pass/Fail | Detailed metrics |
| **When** | Every change | Analysis changes |

---

## Usage Examples

### Daily Development
```bash
# Quick check that code still works
python scripts/run_tests.py code
```

### Before Committing Analysis Changes
```bash
# Test both types
python scripts/run_tests.py all
```

### Monitoring Analysis Performance
```bash
# Full analysis test
python scripts/run_tests.py analysis

# Compare modes to optimize costs
python scripts/run_tests.py compare
```

### CI/CD Pipeline
```bash
# Always test code functionality
python scripts/run_tests.py code

# Only test analysis if AI-related files changed
if [[ $CHANGED_FILES == *"content_analyzer"* ]]; then
  QUICK_TEST=true python scripts/run_tests.py analysis
fi
```

---

## Test Output Files

### Code Tests
- Console output only
- Pass/fail results
- No files generated

### Analysis Tests  
- **Console**: Summary statistics
- **JSON file**: `analysis_quality_hybrid_YYYYMMDD_HHMMSS.json`
  - Detailed results for each sample
  - Accuracy breakdowns
  - Cost optimization metrics
  - Individual sample predictions

---

## Safety Features

### Quota Protection
- Code tests use **DRY-RUN mode** automatically
- No real emails sent during testing
- No Postmark quota consumed
- Clear visual indicators (`🚫 DRY-RUN`, `🔵 [DRY-RUN]`)

### Cost Control
- Analysis tests support **QUICK_TEST** mode (3 samples)
- Hybrid mode reduces AI API usage by 60-80%
- Local-only analysis when content appears safe
- Configurable sample limits

### Clear Separation
- Different scripts for different purposes  
- Visual indicators in output
- Separate result files
- No accidental quota usage

---

## Best Practices

1. **Always run code tests first** - if code is broken, don't test analysis
2. **Use QUICK_TEST for development** - test analysis changes with 3 samples first
3. **Monitor analysis results over time** - save and compare JSON output files
4. **Use hybrid mode by default** - balances accuracy and cost
5. **Test analysis after AI prompt changes** - these significantly impact results
6. **Check both accuracy and cost optimization** - aim for high accuracy with low AI usage