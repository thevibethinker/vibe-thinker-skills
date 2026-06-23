# Rubric Generator Worker

Generates a scoring rubric from a job description (and optional founder notes). No external APIs. Deterministic heuristics.

## Inputs
- jobs/<job>/job-description.md (required)
- Founder notes (optional): free text; lines may include tier hints like `Must: X`, `Should: Y`, `Nice: Z`

## Outputs
- jobs/<job>/rubric.json — machine-readable rubric
- jobs/<job>/rubric.md — human-readable summary
- jobs/<job>/deal_breakers.json — extracted hard requirements

## CLI
```
python workers/rubric/main.py \
  --jd jobs/<job>/job-description.md \
  --out jobs/<job>/rubric.json \
  [--founder-notes path/to/notes.md] \
  [--interactive | --non-interactive] \
  [--dry-run]
```

## Heuristics
- Sections recognized: Requirements (Must), Responsibilities (Should), Other (Nice)
- Keyword upgrades/downgrades (e.g., "required", "preferred", "nice to have")
- Weights distributed by bucket: 60% Must, 30% Should, 10% Nice (renormalized to sum to 100)
- Deal breakers detected via hard-requirement language (e.g., authorization, clearance, on-site)

## Bands
- Must: Meets vs Below
- Should: Meets vs Below
- Nice: Meets vs Below (no penalty when below)

## Quality
- Logging, `--dry-run`, error handling, and verification (weights sum to 100)

## Notes
- This is an MVP to unblock the end-to-end pipeline; refine heuristics in later iterations.
