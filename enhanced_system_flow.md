# Enhanced Four Horsemen System - Data Flow Diagram

## ASCII State Diagram: Email Processing with Summary + Context Flagging

```
ACTORS:
- [S] Sender (external email source)  
- [R] Recipient (CellophoneMail user)
- [SYS] CellophoneMail System
- [AI] Anthropic Claude API
- [CACHE] Redis Cache Layer

TRIGGERS:
- →→ Email received
- ⚡ Analysis needed
- 🔍 Cache lookup
- 🤖 AI analysis
- 📝 Summary generation
- ✉️ Email delivery

═══════════════════════════════════════════════════════════════════════

                    ┌─────┐
                    │ [S] │ ──→→ Email sent
                    └─────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                    EMAIL INGESTION                               │
    │  TRIGGER: →→ Webhook received from email provider               │
    └──────────────────────────────────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                  CONTENT EXTRACTION                              │
    │  ACTOR: [SYS] extracts sender, subject, body                    │
    │  DATA: raw_email → {sender, subject, content, metadata}         │
    └──────────────────────────────────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                  CONTEXT DETECTION                               │
    │  TRIGGER: ⚡ Analyze sender domain and role patterns             │
    │  OUTPUT: communication_context = {                               │
    │           type: "management|peer|external|customer",             │
    │           relationship: "supervisor_to_subordinate|peer_to_peer", │
    │           domain_authority: "internal|external"                  │
    │          }                                                       │
    └──────────────────────────────────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                    CACHE LOOKUP                                  │
    │  TRIGGER: 🔍 Check for existing analysis                        │
    │  ACTOR: [CACHE] Redis lookup with content+sender hash           │
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
    │   CACHED RESULT │  │              LOCAL ANALYSIS                  │
    │                 │  │  ACTOR: [SYS] Four Horsemen pattern matching│
    │ Skip analysis   │  │  TRIGGER: ⚡ Keyword pattern detection       │
    │ Use stored data │  │  OUTPUT: {                                   │
    │                 │  │    classification: SAFE|WARNING|HARMFUL|    │
    │                 │  │                   ABUSIVE,                   │
    │                 │  │    horsemen: [criticism|contempt|defensive  │
    │                 │  │              |stonewalling],                 │
    │                 │  │    examples: [...],                          │
    │                 │  │    reasoning: "..."                          │
    │                 │  │  }                                           │
    └─────────────────┘  └──────────────────────────────────────────────┘
              │                               │
              │                               ▼
              │                    ┌─────────────────┐
              │                    │ HYBRID DECISION │
              │                    │                 │
              │                    │ IF suspicious   │
              │                    │ (NOT SAFE OR    │
              │                    │ horsemen > 0)   │
              │                    └─────────────────┘
              │                               │
              │                        ┌─────┴─────┐
              │                        │SUSPICIOUS?│
              │                        └─────┬─────┘
              │                         YES  │  NO
              │                    ┌─────────┴──────────┐
              │                    ▼                    ▼
              │      ┌──────────────────────────┐  ┌──────────────────┐
              │      │       AI ANALYSIS        │  │  SKIP AI ANALYSIS│
              │      │  TRIGGER: 🤖 API call   │  │  (Cost savings)  │
              │      │  ACTOR: [AI] Claude API  │  │                  │
              │      │  INPUT: content + prompt │  │  Use local result│
              │      │  OUTPUT: detailed analysis│  └──────────────────┘
              │      └──────────────────────────┘             │
              │                    │                          │
              └────────────────────┼──────────────────────────┘
                                   ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                 RESULT CONSOLIDATION                             │
    │  Merge local + AI results (if AI was used)                      │
    │  final_result = {                                                │
    │    classification: SAFE|WARNING|HARMFUL|ABUSIVE,                 │
    │    horsemen_detected: [...],                                     │
    │    confidence: high|medium|low,                                  │
    │    analysis_method: "local"|"ai"|"cached"                        │
    │  }                                                               │
    └──────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │               COMMUNICATION TYPE ANALYSIS                        │
    │  TRIGGER: 📝 Context-aware content categorization               │
    │  LOGIC:                                                          │
    │    IF (context = management + content = policy/demands) THEN     │
    │      content_type = "institutional_directive"                    │
    │    ELSE IF (context = peer + toxicity > 0) THEN                 │
    │      content_type = "interpersonal_conflict"                     │
    │    ELSE                                                          │
    │      content_type = "standard_communication"                     │
    └──────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                    DELIVERY DECISION                             │
    │                                                                  │
    │  RULE ENGINE:                                                    │
    │  ┌────────────────────────────────────────────────────────────┐  │
    │  │ IF toxicity = ABUSIVE → QUARANTINE                        │  │
    │  │ ELSE IF toxicity = HARMFUL → QUARANTINE                   │  │
    │  │ ELSE IF toxicity = WARNING + context = peer → DELIVER     │  │
    │  │      with warning                                          │  │
    │  │ ELSE → DELIVER (may include summary)                      │  │
    │  └────────────────────────────────────────────────────────────┘  │
    └──────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │        DELIVER?             │
                    └──────────────┬──────────────┘
                              YES  │  NO
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
    ┌─────────────────────────────┐  ┌─────────────────────────────┐
    │     ENHANCED DELIVERY       │  │        QUARANTINE           │
    │                             │  │                             │
    │ TRIGGER: ✉️ Email delivery  │  │ ACTOR: [SYS] Block delivery │
    │ ACTOR: [SYS] → [R]          │  │ ACTION: Store in quarantine │
    │                             │  │         queue                │
    │ CONTENT ENHANCEMENT:        │  │                             │
    │ ┌─────────────────────────┐ │  │ NOTIFICATION:               │
    │ │ IF content_type =       │ │  │ - Alert recipient           │
    │ │   "institutional_       │ │  │ - Log for admin review      │
    │ │    directive"           │ │  │ - Generate incident report  │
    │ │ THEN add:               │ │  └─────────────────────────────┘
    │ │                         │ │                 │
    │ │ 📋 SUMMARY:             │ │                 ▼
    │ │ 1) Requirement A        │ │      ┌─────────────────────┐
    │ │ 2) Requirement B        │ │      │   ADMIN DASHBOARD   │
    │ │ 3) Deadline: X          │ │      │                     │
    │ │                         │ │      │ - Review quarantine │
    │ │ ⚠️ CONTEXT: Management  │ │      │ - Manual release    │
    │ │   directive             │ │      │ - Pattern analysis  │
    │ │ 💼 SOURCE: Supervisor   │ │      └─────────────────────┘
    │ └─────────────────────────┘ │
    └─────────────────────────────┘
                    │
                    ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                   RECIPIENT DELIVERY                             │
    │  ACTOR: [R] receives email with enhancements                    │
    │                                                                  │
    │  STANDARD EMAIL:                                                 │
    │  ┌────────────────────────────────────────────────────────────┐  │
    │  │ From: sender@domain.com                                    │  │
    │  │ Subject: Original subject                                  │  │
    │  │ Body: [Original content]                                   │  │
    │  │                                                            │  │
    │  │ ═══ CELLOPHANEMAIL ANALYSIS ═══                           │  │
    │  │ 📋 COMMUNICATION SUMMARY: (if institutional)              │  │
    │  │ The following has been requested:                          │  │
    │  │ 1) Work requirement A                                      │  │
    │  │ 2) Policy change B                                         │  │
    │  │ 3) Deadline: Date                                          │  │
    │  │                                                            │  │
    │  │ ⚠️ CONTEXT: Management directive                           │  │
    │  │ 💼 COMMUNICATION TYPE: Supervisor to team                  │  │
    │  │ 🛡️ TOXICITY STATUS: Safe for delivery                     │  │
    │  └────────────────────────────────────────────────────────────┘  │
    └──────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                      ANALYTICS & CACHING                        │
    │                                                                  │
    │  ACTOR: [CACHE] Store analysis result                           │
    │  ACTOR: [SYS] Log metrics                                       │
    │                                                                  │
    │  STORED DATA:                                                    │
    │  - Analysis result (30min TTL)                                  │
    │  - Processing metrics                                            │
    │  - Communication patterns                                        │
    │  - Cost optimization data                                        │
    └──────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════

DECISION MATRIX:

Context Type    | Toxicity Level | Action           | Enhancement
─────────────────────────────────────────────────────────────────────
Management      | SAFE          | Deliver          | + Summary
Management      | WARNING       | Deliver          | + Summary + Warning
Management      | HARMFUL       | Quarantine       | Admin review
Management      | ABUSIVE       | Quarantine       | Admin review
Peer            | SAFE          | Deliver          | None
Peer            | WARNING       | Deliver          | + Context note
Peer            | HARMFUL       | Quarantine       | Block delivery
Peer            | ABUSIVE       | Quarantine       | Block delivery
External        | Any level     | Deliver/Block    | + Sender verification

═══════════════════════════════════════════════════════════════════════

KEY IMPROVEMENTS:
1. Context-aware processing (management vs peer)
2. Content summarization for institutional directives
3. Enhanced delivery with structured information
4. Preserved factual communication delivery
5. No censorship of legitimate management communication
```