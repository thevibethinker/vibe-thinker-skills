# Scoring Engine Archive

**Archived:** 2025-10-23 21:10 ET  
**Reason:** Paradigm shift from arithmetic to gestalt evaluation

---

## Archived Versions

### main.py (27KB - 2025-10-23)
**Built in:** con_h6FHxtZmK1d8uQ9u  
**Approach:** Criterion-by-criterion arithmetic scoring  
**Status:** Well-executed implementation of wrong paradigm  
**Why Archived:** Gestalt bundle evaluation is superior

**What it did:**
- Scored each criterion 0-10
- Applied weights
- Computed weighted sum
- Output: scores.json with numeric totals

**Why it failed:**
- Pretends precision exists (6/10 vs 7/10 meaningless)
- Ignores emergent properties (elite signals)
- Gameable via keyword stuffing
- Misses context (McKinsey ≠ random consulting)

### main_v2.py (2.4KB - 2025-10-23)
**Approach:** Early improvement attempt  
**Status:** Incomplete

### main_v3_semantic.py (29KB - 2025-10-23)
**Approach:** Semantic scorer with corruption  
**Status:** Got corrupted during integration

### main_v3_clean.py (11KB - 2025-10-23)
**Approach:** Working fix for v3 with signal extraction  
**Status:** Functional but replaced by gestalt

---

## Current Production System

**main.py** (copied from main_gestalt.py)
- Bundle evaluation (not arithmetic)
- Signal extraction (business impact, elite markers, trajectory)
- Outputs: STRONG_INTERVIEW | INTERVIEW | MAYBE | PASS
- Integrates with clarification system
- 4/4 test accuracy

**Core files:**
- `main.py` - Entry point (2.4KB)
- `gestalt_scorer.py` - Bundle evaluation logic (12KB)
- `extractors.py` - Signal extraction (12KB)

---

## Lessons Learned

**The Paradigm Shift:**
- FROM: Arithmetic scoring (sum of parts)
- TO: Gestalt evaluation (pattern recognition)

**Key Insight:** Talent assessment isn't grading homework. Elite signals (0.02% acceptance at McKinsey) carry more information than 10 criteria combined.

**See:** `/home/.z/workspaces/con_h6FHxtZmK1d8uQ9u/GESTALT_VS_CRITERION_COMPARISON.md`

---

*Archived for learning purposes only - DO NOT deploy*
