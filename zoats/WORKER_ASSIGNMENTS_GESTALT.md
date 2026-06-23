# ZoATS Worker Assignments — Gestalt System

**Orchestrator:** con_R3Mk2LoKx4AEGtYy  
**Created:** 2025-10-23 01:15 ET  
**Architecture:** Gestalt evaluation (bundle-based pattern recognition)  
**Status:** Ready for deployment

---

## System Architecture (Current State)

### ✅ Complete
1. **Resume Parser** — PDF/DOCX/MD → text.md + fields.json
2. **Rubric Generator** — JD → rubric.json (legacy, informational only)
3. **Candidate Intake** — inbox_drop/ → candidates/*/raw + interactions.md
4. **Quick Test** — Deal-breaker pre-screening → quick_test.json
5. **Gestalt Scorer** — Pattern recognition → gestalt_evaluation.json
   - Decision: STRONG_INTERVIEW | INTERVIEW | MAYBE | PASS
   - Key strengths, concerns, interview focus
   - Elite signals, business impact, AI detection
6. **AI Detection** — Bullshit filter embedded in gestalt evaluation

### ⏳ Need Implementation
7. **Dossier Generator** — Consume gestalt → human-readable dossier
8. **Maybe Email Composer** — For MAYBE decisions → clarification questions
9. **Pipeline Orchestrator** — Update to use gestalt scorer
10. **Test Harness** — End-to-end smoke test

---

## Assignment 1: Dossier Generator (Gestalt-Aware)

**Priority:** High  
**Estimated Time:** 45-60 minutes  
**Complexity:** Medium

### Context
- Gestalt system produces: file 'ZoATS/jobs/test-fixture/candidates/vrijen/outputs/gestalt_evaluation.json'
- Schema includes: decision, confidence, key_strengths, concerns, overall_narrative, interview_focus, clarification_questions, elite_signals, business_impact, ai_detection
- Current stub: file 'ZoATS/workers/dossier/main.py' (2.6KB)

### Task
Expand dossier generator to consume gestalt_evaluation.json and produce:

**Outputs:**
1. **dossier.md** (human-readable)
   ```markdown
   # Candidate Dossier: [Name]
   
   **Decision:** [STRONG_INTERVIEW/INTERVIEW/MAYBE/PASS]  
   **Confidence:** [high/medium/low]  
   **Date:** [timestamp]
   
   ## Executive Summary
   [overall_narrative from gestalt]
   
   ## Key Strengths
   [table: category | evidence | relevance]
   
   ## Concerns
   [list with detail]
   
   ## Elite Signals
   [Cornell (0.95 confidence, 1.15x boost), McKinsey (0.9, 1.4x), etc.]
   
   ## Business Impact
   [$4M revenue opportunity, $650K B2C revenue, etc.]
   
   ## AI Detection
   **Likelihood:** [low/medium/high]  
   **Flags:** [list]
   
   ## Interview Focus
   [areas to probe based on gestalt]
   
   ## Clarification Questions
   [if MAYBE decision, show questions to ask]
   
   ## Next Steps
   [decision-specific recommendations]
   ```

2. **dossier.json** (machine-readable rollup)
   ```json
   {
     "candidate_id": "...",
     "decision": "INTERVIEW",
     "confidence": "medium",
     "quick_test_status": "pass",
     "gestalt_summary": "...",
     "top_3_strengths": [...],
     "top_3_concerns": [...],
     "recommended_action": "...",
     "timestamp": "..."
   }
   ```

### Interface
```bash
python workers/dossier/main.py \
  --job <job-id> \
  --candidate <candidate-id> \
  [--dry-run]
```

### Files to Study
- file 'ZoATS/workers/scoring/gestalt_scorer.py' (output schema)
- file 'ZoATS/jobs/test-fixture/candidates/vrijen/outputs/gestalt_evaluation.json' (example)
- file '/home/.z/workspaces/con_wE3aD3nGfQik9tTP/GESTALT_SYSTEM_COMPLETE.md' (design doc)

### Requirements
- Logging, --dry-run, error handling
- Verify inputs exist (gestalt_evaluation.json, quick_test.json)
- Format elite signals with confidence + boost factor
- Business impact with dollar amounts and context
- Decision-specific next steps (STRONG_INTERVIEW → priority scheduling, MAYBE → send clarification)
- Target: 200-250 lines

### Success Criteria
- dossier.md exists and is human-readable
- dossier.json valid and complete
- Handles all decision types (STRONG_INTERVIEW, INTERVIEW, MAYBE, PASS)
- Dry-run mode functional

---

## Assignment 2: Maybe Email Composer

**Priority:** Medium  
**Estimated Time:** 30-45 minutes  
**Complexity:** Low

### Context
- Gestalt evaluation includes clarification_questions for MAYBE decisions
- Need automated email composer to send to candidates
- Employer approval workflow (future: ask founder before sending)

### Task
Create email composer that:
1. Reads gestalt_evaluation.json
2. If decision == "MAYBE", compose clarification email
3. Output email template for review/sending

**Output:** clarification_email.md
```markdown
To: [candidate email from parsed/fields.json]
Subject: Additional information needed for [job title]

Dear [candidate name],

Thank you for applying to [job title] at [company]. We're interested in learning more about your background.

Before scheduling an interview, could you help us understand:

1. [Question 1 from gestalt]
2. [Question 2 from gestalt]
3. [Question 3 from gestalt]

Please respond by [date]. We appreciate your time and interest.

Best regards,
[Hiring manager name]
```

### Interface
```bash
python workers/maybe_email/main.py \
  --job <job-id> \
  --candidate <candidate-id> \
  [--dry-run]
```

### Files to Study
- file 'ZoATS/jobs/test-fixture/candidates/sample1/outputs/gestalt_evaluation.json' (MAYBE example)
- file '/home/.z/workspaces/con_wE3aD3nGfQik9tTP/GESTALT_SYSTEM_COMPLETE.md' (design)

### Requirements
- Only trigger for MAYBE decisions
- Polite, professional tone
- Include deadline (7 days from generation)
- Support --dry-run
- Log email preview
- Target: 100-150 lines

### Success Criteria
- clarification_email.md generated for MAYBE cases
- Skips non-MAYBE decisions
- Email is professional and clear
- Questions pulled verbatim from gestalt

---

## Assignment 3: Pipeline Orchestrator Update

**Priority:** High  
**Estimated Time:** 30-45 minutes  
**Complexity:** Low

### Context
- Current pipeline: file 'ZoATS/pipeline/run.py' (5.2KB)
- Needs to call gestalt scorer instead of (or in addition to) old scoring

### Task
Update pipeline to:
1. Call quick_test (deal-breaker gate)
2. Call gestalt scorer (main evaluation)
3. Call dossier generator
4. Optionally call maybe_email composer if MAYBE
5. Skip downstream if quick_test fails or gestalt = PASS

**Flow:**
```
Parser → Quick Test → (if pass) → Gestalt Scorer → Dossier → (if MAYBE) → Email Composer
```

### Interface
```bash
python pipeline/run.py \
  --job <job-id> \
  [--candidate <candidate-id>] \  # specific candidate
  [--all]                          # all candidates
  [--dry-run]
```

### Files to Study
- file 'ZoATS/pipeline/run.py' (current implementation)
- file 'ZoATS/workers/scoring/main_gestalt.py' (CLI interface)

### Requirements
- Maintain existing parser integration
- Add gestalt scorer step
- Skip scoring if quick_test = fail
- Generate summary report (how many STRONG_INTERVIEW, INTERVIEW, MAYBE, PASS)
- Dry-run support
- Target: 250-300 lines

### Success Criteria
- Pipeline runs end-to-end
- Generates gestalt_evaluation.json + dossier.md for each candidate
- Summary report shows decision distribution
- Idempotent (can re-run safely)

---

## Assignment 4: Test Harness (Gestalt System)

**Priority:** High  
**Estimated Time:** 30-45 minutes  
**Complexity:** Low

### Task
Create smoke test that:
1. Uses existing test job: test-fixture
2. Runs full pipeline on all 4 candidates
3. Verifies outputs exist and are valid
4. Checks decision distribution makes sense

**Test Structure:**
```python
def test_end_to_end():
    # Run pipeline
    result = subprocess.run([
        "python", "pipeline/run.py",
        "--job", "test-fixture",
        "--all"
    ])
    
    # Verify outputs for each candidate
    for candidate in ["vrijen", "whitney", "sample1", "marla"]:
        assert_exists(f"jobs/.../candidates/{candidate}/outputs/gestalt_evaluation.json")
        assert_exists(f"jobs/.../candidates/{candidate}/outputs/dossier.md")
        assert_valid_json(gestalt_evaluation.json)
        assert_valid_decision(gestalt_evaluation.json)
    
    # Check decision distribution
    decisions = collect_decisions()
    assert len([d for d in decisions if d == "STRONG_INTERVIEW"]) >= 1
    assert len([d for d in decisions if d == "PASS"]) == 0  # all should pass quick test
```

### Interface
```bash
python tests/smoke.py
```

### Requirements
- Tests all workers in sequence
- Clear pass/fail per candidate
- Summary report
- Exit code 0 if all pass, 1 if any fail
- Target: 150-200 lines

### Success Criteria
- All 4 candidates process successfully
- Outputs validated (exist, valid JSON, correct schema)
- Decision distribution reasonable
- Clean error messages on failure

---

## Deployment Order

1. **Dossier Generator** (Assignment 1) — blocks pipeline testing
2. **Pipeline Update** (Assignment 3) — integrates all workers
3. **Test Harness** (Assignment 4) — validates end-to-end
4. **Maybe Email Composer** (Assignment 2) — nice-to-have for Night 1

---

## Success Metrics (Night 1 Complete)

✅ All 4 candidates in test-fixture processed  
✅ Each has: parsed/, quick_test.json, gestalt_evaluation.json, dossier.md  
✅ Smoke test passes  
✅ Pipeline idempotent (can re-run)  
✅ Decision distribution: 1 STRONG_INTERVIEW, 2-3 INTERVIEW, 0-1 MAYBE, 0 PASS

---

**Total Estimated Time:** 2.5-3 hours  
**Architecture:** Gestalt evaluation (complete)  
**Next Phase:** Clarification response handling, employer approval workflow

---

*Generated: 2025-10-23 01:15 ET*
