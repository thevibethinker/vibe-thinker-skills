---
created: 2026-05-24
last_edited: 2026-05-24
version: 1.0
provenance: public-skill-export
drop_id: D3.1
title: Output Format
---

# Output Format — Evaluation Report

## Rendering principles
The report is a founder decision tool. Preserve frame distinction, substance/style distinction, stage distinction, and evidence/confidence distinction.

## Layout
```markdown
# Pitch Deck Evaluation — <Deck Name>
## Header
## Executive Read
## Score Snapshot
## Frame Scorecards
## Cross-Frame Synthesis
## Substantive vs. Stylistic Split
## Named-POV Reads (if enabled)
## Per-Slide Annotations
## Prioritized Action List
## Appendix: Config Snapshot and Scoring Notes
```

## Header block
| Field | Value |
|---|---|
| Evaluation date | ISO date |
| Stage | pre_seed/seed/series_a |
| Deck source | path or filename |
| Frames enabled | F1, F2, F3, F4 |
| Named POVs enabled | none or IDs |
| Register | auto → detected mode |
| Output verbosity | terse/standard/deep |
| Extraction confidence | high/medium/low |

## Executive read
Include bottom line, strongest investor-positive signal, most dangerous pass reason, and likely read pattern across warm/cold/hostile readers. Cite slide refs.

## Score snapshot
| Frame | Substantive | Stylistic | Advisory overall | Primary interpretation |
|---|---:|---:|---:|---|
| F1 Warm Believer | 74 | 63 | 71 | Belief possible if founder spike is trusted. |
| F2 Curious Skeptic | 62 | 63 | 62 | Needs sharper proof ladder and milestone map. |
| F3 Cold Partner Read | 48 | 57 | 50 | Opening is too slow for cold scan. |
| F4 Hostile Diligence | 39 | 55 | 43 | Market and evidence claims do not survive pressure. |

## Frame scorecard section
Each frame includes: frame interpretation, hard gates/escalations, substantive dimension table, stylistic dimension table.

| Dimension | Score | Weight | Evidence | Rationale | Top fix |
|---|---:|---:|---|---|---|
| Founder-market fit + team capacity | 3.5/5 | 15.6 | S5: domain background | Relevant founder access appears, but technical ownership is unclear. | Add who owns the core build and what has shipped. |
| Non-obvious insight + thesis clarity | 2.5/5 | 12.0 | S2-S3: trend claim | Legible but not yet non-obvious. | Replace trend statement with customer truth. |

## Cross-frame synthesis
Render where frames agree, where they diverge, and frame switches. Divergence is the signal: e.g. F1 grants founder story while F3 misses it means move why-this-founder earlier.

## Substantive vs stylistic split
Report separate composites and required gap label if triggered. Example: `Strong style, weak substance` means polish may mask missing proof; repair substance rather than visual polish.

## Named POV reads
Only render if enabled. Start with: “These are source-inspired lenses, not predictions of named investors.” For each POV include emphasis, read, and top POV-specific fix.

## Per-slide annotations
| Slide | Likely role | Strength | Weakness | Suggested repair |
|---|---|---|---|---|
| S1 | Opening claim | Category ambition is clear. | Product/customer/action unclear. | Use: “We help <ICP> do <action> so <outcome>.” |

## Prioritized action list
Rank top 5 changes by impact-per-effort.
| Rank | Action | Impact | Effort | Frames helped | Why this is first |
|---:|---|---|---|---|---|
| 1 | Rewrite slides 1-3 to name product, ICP, and thesis. | High | Medium | F2,F3,F4 | Cold readers exit before proof. |

## Concrete illustrative mini-report
# Pitch Deck Evaluation — Atlas Claims AI Deck

| Field | Value |
|---|---|
| Evaluation date | 2026-05-24 |
| Stage | pre_seed |
| Deck source | atlas-claims-ai.pdf |
| Frames enabled | F1, F2, F3, F4 |
| Named POVs enabled | none |
| Register | auto → concrete_operator |
| Extraction confidence | medium |

**Bottom line:** The illustrative deck has plausible founder-market fit and a concrete B2B workflow, but asks investors to infer too much about demand proof and market expansion. Warm believers may take the meeting; cold and hostile readers will push on bottom-up market logic and validation.

| Frame | Substantive | Stylistic | Advisory overall | Read |
|---|---:|---:|---:|---|
| F1 | 72 | 66 | 70 | Worth meeting if founder spike is trusted. |
| F2 | 59 | 66 | 61 | Needs validation and milestones. |
| F3 | 46 | 58 | 49 | Opening too slow. |
| F4 | 38 | 54 | 42 | Forecast/market claims trigger pressure. |

**Cross-frame divergence:** F2 grants no revenue, but F4 penalizes an unsupported precise forecast. Replace forecast with pricing hypothesis, pilots, and milestone math.

**Top actions:** rewrite opening to name ICP/product/outcome; add demand evidence; replace forecast with milestone math; map use of funds to risk reduction; label hypotheses vs facts.

This example is illustrative and does not reference V's deck.

## 14. Report length by verbosity

| Verbosity | Expected report shape |
|---|---|
| `terse` | 2-4 pages: executive read, score snapshot, cross-frame divergence, top actions. |
| `standard` | 6-12 pages: all frame scorecards, style/substance split, per-slide annotations, top actions. |
| `deep` | 12+ pages when deck length warrants it: evidence-rich rationale, POV reads, expanded appendices. |

## 15. Required language patterns

Use stage-precise language:

- Say: “Revenue scale is granted at pre-seed; the weakness is no alternate demand evidence.”
- Do not say: “Traction is weak” when the only issue is no revenue.
- Say: “This precise forecast creates false-precision risk.”
- Do not say: “You need a five-year model” for a true pre-seed deck.
- Say: “A cold reader may exit before seeing the founder signal.”
- Do not say: “Investors will pass” as a universal prediction.

## 16. Required appendix metadata

Every report should end with:

```yaml
rubric_version: rubric_v1
config_source: defaults|path|cli_overrides
effective_config: object
deck_extraction:
  source_type: pdf|markdown|image_bundle|directory
  slide_count: integer
  extraction_confidence: high|medium|low
evaluator_notes:
  limitations: [string]
```

## 17. Machine-readable companion file

If the user requests JSON/YAML output, it should mirror the markdown report but preserve raw scores, effective weights, evidence arrays, hard-gate objects, frame switches, and action rankings. The renderer should be able to regenerate the markdown from this object without re-scoring.
