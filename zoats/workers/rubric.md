# Rubric Generator (Worker)

Status: MVP complete

---

## Purpose
Convert a job description (and optional founder notes) into a structured scoring rubric with criteria, weights, and evaluation bands. Also extract deal breakers.

## Inputs
- jobs/<job>/job-description.md (required)
- Founder notes (optional): free text; may include structured hints like `Must: X`, `Should: Y`, `Nice: Z`

## Outputs
- jobs/<job>/rubric.json — machine-readable rubric
- jobs/<job>/rubric.md — human-readable rubric
- jobs/<job>/deal_breakers.json — extracted hard requirements

## Interface
```
python workers/rubric/main.py --jd jobs/<job>/job-description.md --out jobs/<job>/rubric.json [--founder-notes <file>] [--interactive|--non-interactive] --dry-run
```

## Behavior (MVP)
- Heuristic parsing:
  - Recognizes sections: Requirements, Responsibilities, Other
  - Classifies bullets into tiers (Must / Should / Nice) via keywords
  - Weight allocation: 60% Must, 30% Should, 10% Nice → normalized to 100
  - Deal breakers: phrases with hard-requirement language (authorization, clearance, on-site, degree required, etc.)
- Bands: Meets/Below definitions for each tier
- Quality: logging, `--dry-run`, verification (weights sum to 100)

## Example
```
python workers/rubric/main.py \
  --jd jobs/demo/job-description.md \
  --out jobs/demo/rubric.json \
  --non-interactive --dry-run
```

## Next Iterations
- Improve section detection beyond simple heading matches
- Add optional Socratic refinement flow
- Allow custom bucket weights via config
- Add schema and validation for rubric.json
