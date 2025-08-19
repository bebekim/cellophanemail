# Hybrid Pipeline Architecture - Data Flow Diagram

## ASCII Data Flow: Sequential Pipeline with Smart Routing

```
ACTORS:
- [S] Sender                    - [R] Recipient           - [SYS] Pipeline System
- [ROUTER] Content Router       - [FACT] Fact Extractor   - [CTX] Context Analyzer  
- [TOX] Toxicity Analyzer      - [QUAL] Quality Scorer   - [ENH] Enhancement Generator
- [AI] Anthropic Claude        - [CACHE] Redis Cache     - [CFG] Configuration Engine

TRIGGERS:
- →→ Email received            - 🎯 Route decision       - 📊 Analysis trigger
- 🔍 Cache lookup             - ⚡ Conditional execution - 🔄 Iteration trigger
- ✉️ Enhanced delivery        - 📝 Result aggregation   - 🚨 Error fallback

═══════════════════════════════════════════════════════════════════════════════

                        ┌─────┐
                        │ [S] │ ──→→ Email sent
                        └─────┘
                           │
                           ▼
        ┌────────────────────────────────────────────────────────────────┐
        │                    EMAIL INGESTION                             │
        │  TRIGGER: →→ Webhook from email provider                       │
        │  ACTOR: [SYS] Raw email processing                             │
        │  OUTPUT: email_envelope = {                                    │
        │    raw_content, sender, subject, timestamp, size, attachments  │
        │  }                                                             │
        └────────────────────────────────────────────────────────────────┘
                           │
                           ▼
        ┌────────────────────────────────────────────────────────────────┐
        │                   CONTENT ROUTER                               │
        │  TRIGGER: 🎯 Intelligent routing decision                      │
        │  ACTOR: [ROUTER] Smart pipeline orchestrator                   │
        │                                                                │
        │  ROUTING LOGIC:                                                │
        │  ┌──────────────────────────────────────────────────────────┐  │
        │  │ 1. Quick content scan (keywords, patterns, length)      │  │
        │  │ 2. Sender analysis (domain, authority, history)         │  │
        │  │ 3. Content type detection (automated, personal, formal) │  │
        │  │ 4. Pipeline selection based on characteristics          │  │
        │  └──────────────────────────────────────────────────────────┘  │
        │                                                                │
        │  ROUTING OUTCOMES:                                             │
        │  • FAST_TRACK: Automated emails (minimal analysis)            │
        │  • STANDARD: Regular communication (full pipeline)            │
        │  • HIGH_RISK: Suspicious content (enhanced analysis)          │
        │  • AUTHORITY: Management communication (fact-focused)         │
        │                                                                │
        │  OUTPUT: pipeline_config = {                                  │
        │    route: "standard|fast_track|high_risk|authority",          │
        │    enabled_stages: ["fact", "context", "toxicity"],           │
        │    iteration_budget: 2,                                       │
        │    ai_budget_cents: 5                                         │
        │  }                                                             │
        └────────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  ▼                  │
        │    ┌─────────────────────────────────┴────┐
        │    │         SHARED CONTEXT               │
        │    │  ACTOR: [SYS] Context management     │
        │    │                                      │
        │    │  analysis_context = {                │
        │    │    email_envelope: {...},            │
        │    │    pipeline_config: {...},           │
        │    │    stage_results: {},                │
        │    │    iteration_count: 0,               │
        │    │    confidence_scores: {},            │
        │    │    cost_tracking: {                  │
        │    │      ai_calls: 0,                    │
        │    │      total_cost_cents: 0             │
        │    │    },                                │
        │    │    error_log: []                     │
        │    │  }                                   │
        │    └──────────────────────────────────────┘
        │                      │
        │                      ▼
        │    ┌─────────────────────────────────────────────────────────────┐
        │    │                  PIPELINE EXECUTOR                          │
        │    │  TRIGGER: 📊 Sequential stage execution                     │
        │    │  ACTOR: [SYS] Stage orchestration                           │
        │    │                                                             │
        │    │  EXECUTION FLOW:                                            │
        │    │  FOR each enabled_stage IN pipeline_config:                │
        │    │    1. Check stage conditions                               │
        │    │    2. Execute stage with shared context                    │
        │    │    3. Update context with results                          │
        │    │    4. Check iteration triggers                             │
        │    │    5. Apply circuit breakers                               │
        │    └─────────────────────────────────────────────────────────────┘
        │                      │
        │                      ▼
        │    ╔═══════════════ STAGE 1: FACT EXTRACTOR ═══════════════╗
        │    ║ TRIGGER: 📊 Always runs (core analysis)                ║
        │    ║ ACTOR: [FACT] Fact extraction engine                   ║
        │    ║ INPUT: email_content, shared_context                   ║
        │    ║                                                        ║
        │    ║ PROCESSING:                                            ║
        │    ║ ┌────────────────────────────────────────────────────┐ ║
        │    ║ │ 1. Parse email structure                           │ ║
        │    ║ │ 2. Extract actionable items                        │ ║
        │    ║ │ 3. Identify dates, numbers, requirements           │ ║
        │    ║ │ 4. Separate factual vs. opinion content            │ ║
        │    ║ │ 5. Calculate fact/fluff ratios                     │ ║
        │    ║ └────────────────────────────────────────────────────┘ ║
        │    ║                                                        ║
        │    ║ OUTPUT: fact_result = {                                ║
        │    ║   actionable_facts: [...],                             ║
        │    ║   contextual_facts: [...],                             ║
        │    ║   non_factual_content: [...],                          ║
        │    ║   fact_ratio: 0.75,                                   ║
        │    ║   information_density: "high",                         ║
        │    ║   confidence: 0.9                                     ║
        │    ║ }                                                      ║
        │    ║                                                        ║
        │    ║ TRIGGERS GENERATED:                                    ║
        │    ║ • IF fact_ratio < 0.3 → high_risk_flag = true         ║
        │    ║ • IF actionable_facts > 5 → management_flag = true    ║
        │    ╚════════════════════════════════════════════════════════╝
        │                      │
        │                      ▼
        │    ╔═══════════════ STAGE 2: CONTEXT ANALYZER ═════════════╗
        │    ║ TRIGGER: 📊 Always runs (needs fact context)           ║
        │    ║ ACTOR: [CTX] Context analysis engine                   ║
        │    ║ INPUT: fact_result, sender_info, shared_context        ║
        │    ║                                                        ║
        │    ║ PROCESSING:                                            ║
        │    ║ ┌────────────────────────────────────────────────────┐ ║
        │    ║ │ 1. Analyze sender authority (domain, role)         │ ║
        │    ║ │ 2. Determine communication type from facts         │ ║
        │    ║ │ 3. Assess urgency from deadlines/requirements      │ ║
        │    ║ │ 4. Identify relationship dynamics                  │ ║
        │    ║ └────────────────────────────────────────────────────┘ ║
        │    ║                                                        ║
        │    ║ OUTPUT: context_result = {                             ║
        │    ║   communication_type: "management_directive",          ║
        │    ║   sender_authority: "high",                            ║
        │    ║   relationship: "supervisor_to_subordinate",           ║
        │    ║   urgency: "medium",                                   ║
        │    ║   formality: "formal",                                 ║
        │    ║   confidence: 0.85                                    ║
        │    ║ }                                                      ║
        │    ║                                                        ║
        │    ║ TRIGGERS GENERATED:                                    ║
        │    ║ • IF communication_type = "peer_personal" →            ║
        │    ║   enable toxicity_analysis                             ║
        │    ║ • IF sender_authority = "low" AND fact_ratio < 0.4 →   ║
        │    ║   high_toxicity_risk = true                            ║
        │    ╚════════════════════════════════════════════════════════╝
        │                      │
        │                      ▼
        │    ╔══════════════ CONDITIONAL STAGE: TOXICITY ════════════╗
        │    ║ TRIGGER: ⚡ Conditional execution                       ║
        │    ║ CONDITIONS:                                            ║
        │    ║ • peer_communication = true OR                         ║
        │    ║ • fact_ratio < 0.5 OR                                  ║
        │    ║ • high_toxicity_risk = true                            ║
        │    ║                                                        ║
        │    ║ ACTOR: [TOX] Toxicity analyzer                         ║
        │    ║ INPUT: non_factual_content, context_result             ║
        │    ║                                                        ║
        │    ║ CACHE CHECK:                                           ║
        │    ║ ┌────────────────────────────────────────────────────┐ ║
        │    ║ │ TRIGGER: 🔍 Cache lookup                           │ ║
        │    ║ │ KEY: hash(non_factual_content + context)          │ ║
        │    ║ │ IF cache_hit → use cached toxicity result          │ ║
        │    ║ │ ELSE → proceed with analysis                       │ ║
        │    ║ └────────────────────────────────────────────────────┘ ║
        │    ║                                                        ║
        │    ║ HYBRID ANALYSIS:                                       ║
        │    ║ ┌────────────────────────────────────────────────────┐ ║
        │    ║ │ 1. Local Four Horsemen pattern matching            │ ║
        │    ║ │ 2. IF suspicious → AI analysis                     │ ║
        │    ║ │ 3. ELSE → local result only                        │ ║
        │    ║ └────────────────────────────────────────────────────┘ ║
        │    ║                                                        ║
        │    ║ OUTPUT: toxicity_result = {                            ║
        │    ║   classification: "SAFE|WARNING|HARMFUL|ABUSIVE",      ║
        │    ║   horsemen_detected: [...],                            ║
        │    ║   toxic_content_ratio: 0.15,                          ║
        │    ║   analysis_method: "local|ai",                         ║
        │    ║   confidence: 0.92                                    ║
        │    ║ }                                                      ║
        │    ╚════════════════════════════════════════════════════════╝
        │                      │
        │      ┌───────────────┴───────────────┐
        │      │        STAGE SKIPPED?          │
        │      │   (conditions not met)         │
        │      └───────────────┬───────────────┘
        │                 YES  │  NO
        │    ┌────────────────┴─────────────────┐
        │    ▼                                  ▼
        │ ┌─────────────────────┐  ╔═══════════════ STAGE 3: QUALITY SCORER ═══════════════╗
        │ │  DEFAULT RESULT:    │  ║ TRIGGER: 📊 Always runs                                ║
        │ │  toxicity_result =  │  ║ ACTOR: [QUAL] Quality assessment engine                ║
        │ │  {                  │  ║ INPUT: fact_result, context_result, toxicity_result   ║
        │ │   classification:   │  ║                                                        ║
        │ │   "SAFE",          │  ║ PROCESSING:                                            ║
        │ │   horsemen: [],     │  ║ ┌────────────────────────────────────────────────────┐ ║
        │ │   confidence: 1.0   │  ║ │ 1. Calculate communication effectiveness           │ ║
        │ │  }                  │  ║ │ 2. Assess information density                      │ ║
        │ │                     │  ║ │ 3. Evaluate actionability of content              │ ║
        │ └─────────────────────┘  ║ │ 4. Score clarity and structure                     │ ║
        │           │              ║ │ 5. Weight by toxicity findings                     │ ║
        │           └──────────────╫─┤ └────────────────────────────────────────────────────┘ ║
        │                          ║                                                        ║
        │                          ║ OUTPUT: quality_result = {                             ║
        │                          ║   overall_score: 0.85,                                ║
        │                          ║   information_density: "high",                         ║
        │                          ║   actionability: 0.90,                                ║
        │                          ║   clarity: 0.80,                                      ║
        │                          ║   communication_effectiveness: "excellent",            ║
        │                          ║   delivery_recommendation: "enhance"                   ║
        │                          ║ }                                                      ║
        │                          ║                                                        ║
        │                          ║ TRIGGERS GENERATED:                                    ║
        │                          ║ • IF overall_score > 0.8 → enable_enhancement         ║
        │                          ║ • IF actionability > 0.7 → create_summary             ║
        │                          ╚════════════════════════════════════════════════════════╝
        │                                         │
        │                                         ▼
        │         ╔══════════════ CONDITIONAL STAGE: ENHANCEMENT ═══════════════╗
        │         ║ TRIGGER: ⚡ Conditional execution                             ║
        │         ║ CONDITIONS:                                                  ║
        │         ║ • quality_score > 0.6 OR                                     ║
        │         ║ • management_directive = true OR                             ║
        │         ║ • actionable_facts > 2                                       ║
        │         ║                                                              ║
        │         ║ ACTOR: [ENH] Enhancement generator                           ║
        │         ║ INPUT: All previous stage results                            ║
        │         ║                                                              ║
        │         ║ PROCESSING:                                                  ║
        │         ║ ┌──────────────────────────────────────────────────────────┐ ║
        │         ║ │ 1. Generate fact summary                                 │ ║
        │         ║ │ 2. Create context explanations                           │ ║
        │         ║ │ 3. Add quality indicators                                │ ║
        │         ║ │ 4. Format delivery enhancements                          │ ║
        │         ║ └──────────────────────────────────────────────────────────┘ ║
        │         ║                                                              ║
        │         ║ OUTPUT: enhancement_result = {                               ║
        │         ║   summary: "Key facts: 1) 50hr/week 2) Jan 31 deadline",    ║
        │         ║   context_note: "Management directive from supervisor",      ║
        │         ║   quality_indicators: {...},                                ║
        │         ║   delivery_enhancements: {...}                              ║
        │         ║ }                                                            ║
        │         ╚══════════════════════════════════════════════════════════════╝
        │                                    │
        └────────────────────────────────────┘
                                             │
                                             ▼
        ┌────────────────────────────────────────────────────────────────┐
        │                    RESULT AGGREGATION                          │
        │  TRIGGER: 📝 Combine all stage results                         │
        │  ACTOR: [SYS] Result consolidation                             │
        │                                                                │
        │  AGGREGATION LOGIC:                                            │
        │  ┌──────────────────────────────────────────────────────────┐  │
        │  │ 1. Merge all stage_results into final_analysis           │  │
        │  │ 2. Calculate confidence scores                            │  │
        │  │ 3. Determine delivery action                             │  │
        │  │ 4. Prepare enhancement content                           │  │
        │  │ 5. Log performance metrics                               │  │
        │  └──────────────────────────────────────────────────────────┘  │
        │                                                                │
        │  OUTPUT: final_analysis = {                                    │
        │    fact_analysis: {...},                                      │
        │    context_analysis: {...},                                   │
        │    toxicity_analysis: {...},                                  │
        │    quality_analysis: {...},                                   │
        │    enhancement_data: {...},                                   │
        │    delivery_decision: "deliver_enhanced",                     │
        │    confidence: 0.88,                                          │
        │    processing_metrics: {                                      │
        │      total_time_ms: 1250,                                     │
        │      stages_executed: 4,                                      │
        │      ai_calls: 1,                                             │
        │      cost_cents: 2.3                                          │
        │    }                                                           │
        │  }                                                             │
        └────────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
        ┌────────────────────────────────────────────────────────────────┐
        │                    ITERATION CONTROL                           │
        │  TRIGGER: 🔄 Check if additional passes needed                 │
        │  ACTOR: [SYS] Iteration decision engine                        │
        │                                                                │
        │  ITERATION CONDITIONS:                                         │
        │  ┌──────────────────────────────────────────────────────────┐  │
        │  │ CONTINUE IF:                                             │  │
        │  │ • confidence < 0.7 AND iterations < max_iterations       │  │
        │  │ • new_information_discovered = true                      │  │
        │  │ • cost_budget_remaining > 0                              │  │
        │  │                                                          │  │
        │  │ STOP IF:                                                 │  │
        │  │ • confidence >= 0.8                                      │  │
        │  │ • iterations >= max_iterations                           │  │
        │  │ • cost_budget_exceeded = true                            │  │
        │  │ • no_significant_changes_detected = true                 │  │
        │  └──────────────────────────────────────────────────────────┘  │
        └────────────────────────────────────────────────────────────────┘
                                             │
                    ┌────────────────────────┴────────────────────────┐
                    │              CONTINUE?                          │
                    └────────────────────────┬────────────────────────┘
                                        YES  │  NO
                        ┌───────────────────┴────────────────────┐
                        ▼                                        ▼
        ┌─────────────────────────────────┐  ┌────────────────────────────────────────────────┐
        │       NEXT ITERATION            │  │               FINAL DELIVERY                   │
        │                                 │  │                                                │
        │ • Update shared_context         │  │  TRIGGER: ✉️ Enhanced email delivery           │
        │ • Reset stage execution         │  │  ACTOR: [SYS] → [R] Recipient                  │
        │ • Increment iteration_count     │  │                                                │
        │ • Return to PIPELINE EXECUTOR   │  │  DELIVERY DECISION MATRIX:                     │
        │                                 │  │  ┌──────────────────────────────────────────┐  │
        └─────────────────────────────────┘  │  │ IF toxicity = ABUSIVE → QUARANTINE      │  │
                        │                    │  │ ELSE IF toxicity = HARMFUL →             │  │
                        └────────────────────┼──┤   QUARANTINE + admin review              │  │
                                             │  │ ELSE IF quality > 0.7 →                  │  │
                                             │  │   DELIVER + enhancements                 │  │
                                             │  │ ELSE → DELIVER standard                  │  │
                                             │  │                                          │  │
                                             │  │ ENHANCED DELIVERY INCLUDES:              │  │
                                             │  │ • Original email content                 │  │
                                             │  │ • Fact summary (if available)            │  │
                                             │  │ • Context indicators                     │  │
                                             │  │ • Quality metrics                        │  │
                                             │  │ • Communication type labels              │  │
                                             │  └──────────────────────────────────────────┘  │
                                             │                                                │
                                             │  FINAL OUTPUT TO RECIPIENT:                    │
                                             │  Original email + CellophoneMail analysis bar │
                                             └────────────────────────────────────────────────┘
                                                                    │
                                                                    ▼
        ┌────────────────────────────────────────────────────────────────────────────────┐
        │                        ANALYTICS & CACHING                                    │
        │                                                                                │
        │  ACTOR: [CACHE] Store results for future use                                  │
        │  ACTOR: [SYS] Log performance and cost metrics                                │
        │                                                                                │
        │  CACHED DATA:                                                                  │
        │  • Stage results (30min TTL)                                                  │
        │  • Fact extractions (1hr TTL)                                                 │
        │  • Context analysis (24hr TTL for same sender)                                │
        │  • Toxicity results (1hr TTL)                                                 │
        │                                                                                │
        │  METRICS LOGGED:                                                               │
        │  • Pipeline route taken                                                        │
        │  • Stages executed                                                             │
        │  • Processing time per stage                                                   │
        │  • AI API costs                                                                │
        │  • Cache hit/miss rates                                                        │
        │  • Confidence scores                                                           │
        │  • User feedback (if available)                                                │
        └────────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════════

ROUTING EXAMPLES:

EMAIL TYPE          | ROUTE        | ENABLED STAGES           | BUDGET  | ITERATIONS
──────────────────────────────────────────────────────────────────────────────────────
System notification | FAST_TRACK   | fact, context           | $0.01   | 1
Personal peer msg   | STANDARD     | fact, context, toxicity | $0.05   | 2  
Management memo     | AUTHORITY    | fact, context, quality, | $0.03   | 1
                   |              | enhance                  |         |
Suspicious content  | HIGH_RISK    | All stages + validation  | $0.10   | 3
Customer complaint  | STANDARD     | fact, context, toxicity, | $0.07   | 2
                   |              | quality, enhance         |         |

ERROR HANDLING FLOWS:

STAGE FAILURE → Circuit breaker → Fallback to previous stage results → Continue pipeline
AI TIMEOUT → Use local analysis → Log degraded service → Continue
CACHE ERROR → Skip cache → Direct computation → Continue  
BUDGET EXCEEDED → Stop iterations → Use best results so far → Deliver

KEY ADVANTAGES:
1. Intelligent routing avoids unnecessary computation
2. Each stage is independently testable and cacheable  
3. Controlled iteration prevents runaway costs
4. Graceful degradation on component failures
5. Clear observability at each decision point
6. Configuration-driven pipeline behavior
7. Predictable performance and cost characteristics
```