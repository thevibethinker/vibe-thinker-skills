# ZoATS Worker Assignments — Pending Deployment

**Orchestrator:** con_R3Mk2LoKx4AEGtYy  
**Created:** 2025-10-22 23:55 ET  
**Status:** Ready for worker thread creation

---

## Assignment 1: Scoring Engine Expansion

**Priority:** High  
**Estimated Time:** 1-2 hours  
**Dependencies:** Rubric Generator (complete), Resume Parser (complete)

### Task Description
Expand the Scoring Engine stub to implement full criterion-by-criterion scoring.

### Context Files
- file 'ZoATS/workers/scoring/main.py' (3KB stub — starting point)
- file 'ZoATS/workers/rubric/main.py' (15KB — reference for rubric schema)
- file 'ZoATS/jobs/test-fixture/rubric.json' (example rubric with tier/weight/bands)
- file 'ZoATS/workers/scoring_engine.md' (original spec)
- file 'ZoATS/WORKERS_STATUS_ACTUAL.md' (discovered architecture)

### Requirements

**Inputs:**
- `jobs/<job>/rubric.json` — criteria with tiers, weights, evaluation_guidance bands, keywords
- `jobs/<job>/candidates/<id>/parsed/text.md` — candidate resume text
- `jobs/<job>/candidates/<id>/parsed/fields.json` — extracted fields

**Outputs:**
- `jobs/<job>/candidates/<id>/outputs/scores.json`

**scores.json Schema:**
```json
{
  "candidate_id": "string",
  "job_id": "string",
  "timestamp": "ISO8601",
  "criteria_scores": [
    {
      "criterion_id": "string",
      "criterion_name": "string",
      "tier": "must|should|nice",
      "weight": float,
      "score": float,  // 0-10
      "weighted_score": float,
      "evidence": ["string"],  // text snippets that support the score
      "band": "string"  // which evaluation_guidance band (e.g., "7-8")
    }
  ],
  "total_score": float,  // weighted sum
  "tier_breakdown": {
    "must": {"score": float, "max": float},
    "should": {"score": float, "max": float},
    "nice": {"score": float, "max": float}
  }
}
```

**Implementation Approach:**
1. Load rubric.json and parsed resume
2. For each criterion:
   - Extract evidence: keyword matching + context windows
   - Score heuristically based on evidence strength (0-10)
   - Map to evaluation_guidance band
   - Calculate weighted_score = score * weight
3. Compute total_score and tier_breakdown
4. Write scores.json

**Quality Requirements:**
- Support `--dry-run`
- Logging with timestamps
- Error handling
- Verify outputs exist and valid JSON
- Target: 200-300 lines

**Interface:**
```bash
python workers/scoring/main.py \
  --job <job-id> \
  --candidate <candidate-id> \
  [--dry-run]
```

---

## Assignment 2: Dossier Generator Expansion

**Priority:** High  
**Estimated Time:** 1 hour  
**Dependencies:** Scoring Engine, Quick Test (both must complete first)

### Task Description
Expand the Dossier Generator stub to create comprehensive candidate summaries for decisioning.

### Context Files
- file 'ZoATS/workers/dossier/main.py' (2.6KB stub — starting point)
- file 'ZoATS/workers/dossier.md' (original spec)
- file 'ZoATS/WORKERS_STATUS_ACTUAL.md' (discovered architecture)

### Requirements

**Inputs:**
- `jobs/<job>/candidates/<id>/parsed/text.md` — resume text
- `jobs/<job>/candidates/<id>/parsed/fields.json` — extracted fields
- `jobs/<job>/candidates/<id>/outputs/quick_test.json` — pre-screening result
- `jobs/<job>/candidates/<id>/outputs/scores.json` — criterion scores
- `jobs/<job>/candidates/<id>/outputs/interactions.md` — timeline (read/append)
- `jobs/<job>/rubric.json` — for criterion names/descriptions

**Outputs:**
- `jobs/<job>/candidates/<id>/outputs/dossier.md` (human-readable summary)
- `jobs/<job>/candidates/<id>/outputs/dossier.json` (machine-readable)

**dossier.md Format:**
```markdown
# Candidate Dossier: [Name]

**Job:** [job_id]  
**Date:** [timestamp]  
**Quick Test:** [pass/flag/fail] | Score: [X/5]  
**Overall Score:** [weighted total]/100  

## Summary
[2-3 sentence executive summary]

## Strengths
- [Top scoring criteria with evidence]
- [Key achievements]

## Weaknesses / Gaps
- [Low scoring criteria]
- [Missing requirements]

## Red Flags
[From quick_test.json if any]

## Recommendation
[Strong Yes / Yes / Maybe / No / Strong No]  
[Rationale paragraph]

## Suggested Interview Questions
1. [Question targeting gap/strength]
2. [Question probing achievement]
3. [Question about red flag if applicable]

## Next Steps
[Suggested action: schedule, request info, park, reject]
```

**dossier.json Schema:**
```json
{
  "candidate_id": "string",
  "job_id": "string",
  "timestamp": "ISO8601",
  "summary": "string",
  "strengths": ["string"],
  "weaknesses": ["string"],
  "red_flags": ["string"],
  "recommendation": "strong_yes|yes|maybe|no|strong_no",
  "rationale": "string",
  "interview_questions": ["string"],
  "next_steps": "string"
}
```

**Implementation Approach:**
1. Load all input files
2. Generate summary from scores + quick_test
3. Extract strengths (high scores + evidence)
4. Extract weaknesses (low scores, especially Must criteria)
5. Consolidate red_flags from quick_test
6. Compute recommendation based on tier_breakdown and quick_test
7. Generate interview questions targeting gaps/strengths
8. Suggest next_steps
9. Write both MD and JSON outputs

**Quality Requirements:**
- Support `--dry-run`
- Logging with timestamps
- Error handling
- Verify outputs
- Target: 200-250 lines

**Interface:**
```bash
python workers/dossier/main.py \
  --job <job-id> \
  --candidate <candidate-id> \
  [--dry-run]
```

---

## Assignment 3: Test Harness (Smoke Test)

**Priority:** High  
**Estimated Time:** 30-45 minutes  
**Dependencies:** All workers above (wait for completion)

### Task Description
Create end-to-end smoke test that validates the full ZoATS pipeline.

### Context Files
- file 'ZoATS/workers/test_harness.md' (original spec)
- file 'ZoATS/pipeline/run.py' (5.2KB — orchestrator to test)
- file 'ZoATS/WORKERS_STATUS_ACTUAL.md'

### Requirements

**Create:**
- `tests/smoke_test.py` — main test script
- `fixtures/demo-job/` — test data
  - `job-description.md` (short JD)
  - `candidates/` (2-3 test resumes: 1 strong, 1 weak, 1 borderline)

**Test Flow:**
1. Setup: Create demo-job with rubric
2. Seed inbox_drop with test resumes
3. Run pipeline: `python pipeline/run.py --job demo-job`
4. Assertions:
   - All expected output files exist
   - Files are non-empty
   - JSON files are valid
   - scores.json has correct structure
   - dossier.md exists for each candidate
5. Cleanup (optional)
6. Report: Summary of pass/fail

**Output:**
```
=== ZoATS Smoke Test ===
✓ Setup: demo-job created
✓ Rubric generated
✓ Candidate 1: all outputs present
✓ Candidate 2: all outputs present
✓ Candidate 3: all outputs present
✓ All JSON valid
✓ Dossiers readable

Tests: 8/8 passed
✓✓✓ SMOKE TEST PASSED
```

**Quality Requirements:**
- Clear test output
- Exit code 0 on success, 1 on failure
- Logging
- Target: 150-200 lines

**Interface:**
```bash
python tests/smoke_test.py
```

---

## Deployment Instructions

### For Each Assignment:
1. Create new conversation for the worker
2. Load context files listed above
3. Copy task description and requirements
4. Implement + test
5. Report completion status to orchestrator workspace:
   - `/home/.z/workspaces/con_R3Mk2LoKx4AEGtYy/worker_updates/[worker-name]-STATUS.md`

### Completion Criteria:
- All 3 workers implemented
- Smoke test passes
- Ready for production use

### Estimated Total Time: 2.5-3.5 hours

---

**Orchestrator Check-in:** Next review at 00:30 ET or on completion notification
