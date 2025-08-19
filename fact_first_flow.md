# Enhanced System: Fact-First Analysis Flow

## ASCII State Diagram: Fact Extraction → Categorization → Delivery

```
ACTORS:
- [S] Sender          - [R] Recipient         - [SYS] System
- [AI] Claude API     - [CACHE] Redis         - [FACT] Fact Extractor

TRIGGERS:
- →→ Email received   - 📊 Fact extraction    - 🔍 Cache lookup
- ⚡ Analysis needed  - 🎯 Categorization     - ✉️ Enhanced delivery

═══════════════════════════════════════════════════════════════════════

                    ┌─────┐
                    │ [S] │ ──→→ Email sent
                    └─────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                    EMAIL INGESTION                               │
    │  TRIGGER: →→ Webhook received                                    │
    │  OUTPUT: raw_email = {sender, subject, content, timestamp}       │
    └──────────────────────────────────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                   FACT EXTRACTION                                │
    │  TRIGGER: 📊 Extract structured information FIRST                │
    │  ACTOR: [FACT] Fact extraction engine                           │
    │                                                                  │
    │  EXTRACTION CATEGORIES:                                          │
    │  ┌────────────────────────────────────────────────────────────┐  │
    │  │ ACTIONABLE FACTS:                                          │  │
    │  │ • Requirements ("must do X")                               │  │
    │  │ • Deadlines ("by date Y")                                  │  │
    │  │ • Policies ("rule Z applies")                              │  │
    │  │ • Consequences ("if X then Y")                             │  │
    │  │ • Metrics ("50 hours", "20 days")                          │  │
    │  │                                                            │  │
    │  │ CONTEXTUAL FACTS:                                          │  │
    │  │ • Roles/positions mentioned                                │  │
    │  │ • Past events referenced                                   │  │
    │  │ • Current status updates                                   │  │
    │  │ • Comparative statements (factual)                         │  │
    │  │                                                            │  │
    │  │ NON-FACTUAL CONTENT:                                       │  │
    │  │ • Emotional language                                       │  │
    │  │ • Personal attacks                                         │  │
    │  │ • Subjective opinions                                      │  │
    │  │ • Unnecessary elaboration                                  │  │
    │  │ • Filler text                                              │  │
    │  └────────────────────────────────────────────────────────────┘  │
    │                                                                  │
    │  OUTPUT: fact_analysis = {                                       │
    │    actionable_facts: [...],      // Core requirements/actions    │
    │    contextual_facts: [...],      // Supporting information       │
    │    non_factual_content: [...],   // Opinions, emotions, fluff    │
    │    fact_ratio: 0.75,            // % of content that is factual  │
    │    fluff_ratio: 0.25,           // % that is non-essential       │
    │    total_word_count: 500,                                        │
    │    factual_word_count: 375,                                      │
    │    content_density: "high"       // high|medium|low              │
    │  }                                                               │
    └──────────────────────────────────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                 FACT QUALITY ANALYSIS                            │
    │                                                                  │
    │  QUALITY INDICATORS:                                             │
    │  ┌────────────────────────────────────────────────────────────┐  │
    │  │ HIGH QUALITY COMMUNICATION:                                │  │
    │  │ • Fact ratio > 70%                                        │  │
    │  │ • Clear actionable items                                  │  │
    │  │ • Specific deadlines/metrics                              │  │
    │  │ • Minimal emotional language                              │  │
    │  │                                                            │  │
    │  │ MEDIUM QUALITY:                                            │  │
    │  │ • Fact ratio 40-70%                                       │  │
    │  │ • Some actionable items                                   │  │
    │  │ • Mixed factual/opinion content                           │  │
    │  │                                                            │  │
    │  │ LOW QUALITY:                                               │  │
    │  │ • Fact ratio < 40%                                        │  │
    │  │ • Mostly opinions/emotions                                │  │
    │  │ • Unclear actionable items                                │  │
    │  │ • High fluff content                                      │  │
    │  └────────────────────────────────────────────────────────────┘  │
    │                                                                  │
    │  OUTPUT: communication_quality = {                               │
    │    quality_score: "high|medium|low",                             │
    │    clarity_index: 0.85,          // How clear are the facts     │
    │    actionability: 0.90,          // How actionable is content   │
    │    information_density: 0.75      // Information per word       │
    │  }                                                               │
    └──────────────────────────────────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                  CONTEXT DETECTION                               │
    │  Use fact analysis to determine communication context            │
    │                                                                  │
    │  LOGIC:                                                          │
    │  IF (actionable_facts > 3 AND sender = authority) THEN           │
    │    context = "management_directive"                              │
    │  ELSE IF (fact_ratio < 0.3 AND emotional_content > 0.5) THEN     │
    │    context = "emotional_communication"                           │
    │  ELSE IF (fact_ratio > 0.8 AND actionable_facts < 2) THEN        │
    │    context = "informational_update"                              │
    │                                                                  │
    │  OUTPUT: communication_context = {                               │
    │    type: "management_directive|peer_discussion|info_update",     │
    │    intent: "directive|collaborative|informational",              │
    │    urgency: "high|medium|low",    // Based on deadline facts     │
    │    authority_level: "high|medium|low"  // Based on sender role   │
    │  }                                                               │
    └──────────────────────────────────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                    CACHE LOOKUP                                  │
    │  TRIGGER: 🔍 Check for existing analysis                        │
    │  KEY: hash(content + sender + fact_signature)                   │
    └──────────────────────────────────────────────────────────────────┘
                       │
                    ┌──┴──┐
                    │CACHE│
                    │HIT? │
                    └──┬──┘
                  YES  │  NO
              ┌────────┴────────┐
              ▼                 ▼
    ┌─────────────────┐  ┌──────────────────────────────────────────────┐
    │   CACHED RESULT │  │            TOXICITY ANALYSIS                 │
    │                 │  │  Now analyze NON-FACTUAL content for toxicity│
    │ Skip analysis   │  │                                              │
    │ Use stored data │  │  FOCUS: non_factual_content array            │
    │                 │  │  ACTOR: [SYS] Four Horsemen on fluff only   │
    │                 │  │                                              │
    │                 │  │  LOGIC:                                      │
    │                 │  │  IF (fact_ratio > 0.8) THEN                 │
    │                 │  │    // Mostly facts - low toxicity risk      │
    │                 │  │    quick_local_analysis(non_factual_content) │
    │                 │  │  ELSE IF (fact_ratio < 0.4) THEN             │
    │                 │  │    // Mostly fluff - high toxicity risk     │
    │                 │  │    detailed_analysis(non_factual_content)    │
    │                 │  │                                              │
    │                 │  │  OUTPUT: toxicity_analysis = {              │
    │                 │  │    classification: SAFE|WARNING|HARMFUL|    │
    │                 │  │                   ABUSIVE,                   │
    │                 │  │    horsemen_in_fluff: [...],                │
    │                 │  │    toxic_fluff_ratio: 0.15,                 │
    │                 │  │    clean_facts_preserved: true               │
    │                 │  │  }                                           │
    │                 │  └──────────────────────────────────────────────┘
    └─────────────────┘                          │
              │                                  ▼
              │                    ┌─────────────────────────────────┐
              │                    │      HYBRID DECISION            │
              │                    │                                 │
              │                    │ IF (toxic_fluff_ratio > 0.2 OR │
              │                    │     classification != SAFE)     │
              │                    │ THEN need_ai_analysis = true    │
              │                    │                                 │
              │                    │ // High fact ratio emails       │
              │                    │ // rarely need AI analysis     │
              │                    └─────────────────────────────────┘
              │                                  │
              │                           ┌─────┴─────┐
              │                           │NEED AI?   │
              │                           └─────┬─────┘
              │                            YES  │  NO
              │                      ┌─────────┴──────────┐
              │                      ▼                    ▼
              │        ┌──────────────────────────┐  ┌──────────────────┐
              │        │       AI ANALYSIS        │  │  USE LOCAL ONLY  │
              │        │  Focus on non-factual    │  │                  │
              │        │  content for toxicity    │  │  Facts + local   │
              │        │  ACTOR: [AI] Claude API  │  │  toxicity check  │
              │        │                          │  │                  │
              │        └──────────────────────────┘  └──────────────────┘
              │                      │                          │
              └──────────────────────┼──────────────────────────┘
                                     ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                INTELLIGENT CATEGORIZATION                        │
    │  Combine fact analysis + toxicity analysis for smart routing     │
    │                                                                  │
    │  CATEGORIZATION MATRIX:                                          │
    │  ┌────────────────────────────────────────────────────────────┐  │
    │  │                    │ High Facts │ Medium Facts │ Low Facts │  │
    │  │                    │  (>70%)    │   (40-70%)   │  (<40%)   │  │
    │  │ ──────────────────────────────────────────────────────────── │  │
    │  │ SAFE Toxicity      │ DELIVER+   │   DELIVER    │ DELIVER-  │  │
    │  │                    │ SUMMARIZE  │              │ FLAG LOW  │  │
    │  │ ──────────────────────────────────────────────────────────── │  │
    │  │ WARNING Toxicity   │ DELIVER+   │   DELIVER+   │ DELIVER+  │  │
    │  │                    │ SUMMARIZE  │   WARNING    │ WARNING   │  │
    │  │ ──────────────────────────────────────────────────────────── │  │
    │  │ HARMFUL Toxicity   │ DELIVER+   │ QUARANTINE+  │QUARANTINE │  │
    │  │                    │ CLEAN FLUFF│ REVIEW       │           │  │
    │  │ ──────────────────────────────────────────────────────────── │  │
    │  │ ABUSIVE Toxicity   │QUARANTINE+ │ QUARANTINE   │QUARANTINE │  │
    │  │                    │EXTRACT FACTS│             │           │  │
    │  └────────────────────────────────────────────────────────────┘  │
    └──────────────────────────────────────────────────────────────────┘
                                     │
                      ┌──────────────┴──────────────┐
                      │     DELIVERY DECISION       │
                      └──────────────┬──────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │            DELIVER?             │
                    └────────────────┬────────────────┘
                                YES  │  NO
                      ┌─────────────┴─────────────┐
                      ▼                           ▼
    ┌───────────────────────────────────┐  ┌─────────────────────────────┐
    │      ENHANCED DELIVERY            │  │        QUARANTINE           │
    │                                   │  │                             │
    │ FACT-BASED ENHANCEMENT:           │  │ SMART QUARANTINE:           │
    │ ┌───────────────────────────────┐ │  │ ┌─────────────────────────┐ │
    │ │ ORIGINAL EMAIL                │ │  │ │ IF high_fact_ratio THEN │ │
    │ │ [Original content]            │ │  │ │   Extract clean facts   │ │
    │ │                               │ │  │ │   Quarantine toxic fluff│ │
    │ │ ═══ CELLOPHANEMAIL ANALYSIS ══│ │  │ │   Offer "facts only"    │ │
    │ │                               │ │  │ │   delivery option       │ │
    │ │ 📊 CONTENT ANALYSIS:          │ │  │ │                         │ │
    │ │ • Fact ratio: 85%             │ │  │ │ ELSE                    │ │
    │ │ • Information density: High   │ │  │ │   Full quarantine       │ │
    │ │ • Communication quality: High │ │  │ │   Admin review required │ │
    │ │                               │ │  │ └─────────────────────────┘ │
    │ │ 📋 KEY FACTS EXTRACTED:       │ │  └─────────────────────────────┘
    │ │ 1) Requirement: 50hr/week     │ │                 │
    │ │ 2) Deadline: Jan 31, 2002     │ │                 ▼
    │ │ 3) Review date: June 2002     │ │      ┌─────────────────────┐
    │ │ 4) Vacation limit: 20 days    │ │      │   ADMIN OPTIONS     │
    │ │                               │ │      │                     │
    │ │ ⚠️ CONTEXT: Management        │ │      │ □ Deliver facts only│
    │ │   directive (high authority)  │ │      │ □ Full quarantine   │
    │ │                               │ │      │ □ Manual review     │
    │ │ 🛡️ TOXICITY: Minimal (12%)    │ │      │ □ Request rewrite   │
    │ │   (Present in non-factual     │ │      └─────────────────────┘
    │ │    elaboration only)          │ │
    │ └───────────────────────────────┘ │
    └───────────────────────────────────┘
                      │
                      ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                   RECIPIENT EXPERIENCE                           │
    │                                                                  │
    │  HIGH-FACT EMAILS: Get enhanced with structured summaries       │
    │  LOW-FACT EMAILS: Get quality warnings                          │
    │  TOXIC HIGH-FACT: Option to receive "facts only" version        │
    │  TOXIC LOW-FACT: Full protection via quarantine                 │
    │                                                                  │
    │  RECIPIENT BENEFITS:                                             │
    │  • Never miss important factual information                     │
    │  • Clear separation of facts vs. opinions/emotions              │
    │  • Quality indicators help prioritize communications            │
    │  • Protection from abuse while preserving legitimate content    │
    └──────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════

FACT EXTRACTION EXAMPLES:

LAB MEMO ANALYSIS:
┌─────────────────────────────────────────────────────────────────────┐
│ ACTIONABLE FACTS (extracted):                                      │
│ • Work requirement: minimum 50 hours/week                          │
│ • Work schedule: 8+ hours/day, 6 days/week                         │
│ • Bench work requirement: 6 hours concentrated work daily          │
│ • Reading requirement: 2+ hours research activity daily            │
│ • Absence reporting: must inform supervisor                        │
│ • Vacation limit: maximum 20 working days/year                     │
│ • Compliance deadline: January 31, 2002                            │
│ • Review deadline: June 2002                                       │
│ • Performance target: paper at J. Neuroscience level               │
│ • Consequence: leave lab by August if target not met               │
│                                                                     │
│ NON-FACTUAL CONTENT:                                               │
│ • "cease to be a productive, first-rate lab"                       │
│ • "luxury to play around"                                          │
│ • "You may be smarter or do not want to be as successful"          │
│ • Personal comparisons and subjective assessments                  │
│                                                                     │
│ ANALYSIS RESULT:                                                    │
│ • Fact ratio: 78% (high)                                          │
│ • Quality: High information density                                │
│ • Context: Management directive                                     │
│ • Toxicity: Low (contained in 22% non-factual content)            │
│ • Action: DELIVER with enhanced fact summary                       │
└─────────────────────────────────────────────────────────────────────┘

KEY ADVANTAGES OF FACT-FIRST APPROACH:
1. Separates legitimate information from toxic delivery
2. Enables "facts only" delivery for abusive but informative content
3. Quality scoring helps recipients prioritize communications
4. Preserves essential workplace information regardless of tone
5. More nuanced handling of authority communications
6. Clear metrics for communication effectiveness
```