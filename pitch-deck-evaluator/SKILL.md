---
name: pitch-deck-evaluator
description: Evaluate early-stage pitch decks across four investor credulity frames, stage-aware substantive rubric dimensions, optional named-POV reads, and markdown/JSON report rendering.
compatibility: Created for Zo Computer and standalone Python use
metadata:
  author: va.zo.computer
  version: 0.1.0
  entrypoint: scripts/evaluate.py
created: 2026-05-24
last_edited: 2026-05-24
version: 0.1
provenance: public-skill-export
---

# Pitch Deck Evaluator

## Purpose

`pitch-deck-evaluator` evaluates pre-seed, seed, and Series A pitch decks as fundraising artifacts. It reads the deck, applies `rubric/rubric_v1.md`, emits four frame-distinct substantive scorecards, preserves style/substance separation, and optionally adds source-inspired named-POV reads.

## Entry script

```bash
python3 Skills/pitch-deck-evaluator/scripts/evaluate.py <deck_path> [--config Skills/pitch-deck-evaluator/config/default_config.yaml] [--out evaluation.md]
```

## Inputs

- PDF deck with a text layer.
- Plain-text or markdown deck with one slide per delimited block (`---`, `Slide N:`, or `## Slide N`).
- Directory bundle containing `deck.pdf`, `slides.md`, `slides.txt`, or image files.
- Image-only decks are detected but not scored in v1; the skill exits with `image-only deck not supported in v1; OCR or text-layer required`.
- Optional YAML/JSON config that tunes the analytical lens, not the company-specific answer.

## Outputs

- Markdown evaluation report with:
  - header/config snapshot
  - executive read
  - score snapshot
  - F1-F4 frame scorecards
  - substantive composite
  - cross-frame synthesis
  - optional named-POV reads
  - per-slide annotations
  - prioritized action list
- Optional JSON companion via `--emit-json` or `--json-out`.

## Config schema

Default config lives at `config/default_config.yaml`:

```yaml
stage: pre_seed
enabled_frames: [F1, F2, F3, F4]
enabled_pov_palette: []
substantive_weight_overrides: {}
stylistic_weight_overrides: {}
register_override: auto
output_verbosity: standard
include_action_list: true
include_advisory_overall: true
model: claude-sonnet-4-6
scoring_backend: auto
emit_json: false
```

Key fields:

- `stage`: `pre_seed`, `seed`, or `series_a`; default `pre_seed`.
- `enabled_frames`: non-empty subset of `F1`, `F2`, `F3`, `F4`; default all.
- `enabled_pov_palette`: opt-in named lenses; default empty to avoid named-investor cosplay.
- `substantive_weight_overrides`: per-dimension multipliers from `0` to `3`.
- `output_verbosity`: `terse`, `standard`, or `deep`.

## Named-POV anti-cosplay rule

Every named-POV section is prefixed with this disclaimer:

> Based on public writing/interviews, this lens emphasizes certain questions and heuristics. It is not a claim to know how any named person or firm would evaluate, invest in, or pass on this company.

Named POVs are contrast lenses only. The evaluator must never claim that a real investor would invest or pass.

## Standalone mode

The skill has no N5 runtime dependency. To run outside N5:

```bash
git clone <vibe-thinker-skills-repo>
cd vibe-thinker-skills
python3 -m venv .venv
. .venv/bin/activate
pip install pdfplumber pyyaml
python3 Skills/pitch-deck-evaluator/scripts/evaluate.py /path/to/deck.pdf --out evaluation.md
```

For tests and fixture generation, install:

```bash
pip install pytest reportlab
```

## Examples

Default PDF evaluation:

```bash
python3 Skills/pitch-deck-evaluator/scripts/evaluate.py ~/Downloads/deck.pdf --out deck-evaluation.md
```

Text-deck evaluation with JSON companion:

```bash
python3 Skills/pitch-deck-evaluator/scripts/evaluate.py slides.md --out evaluation.md --emit-json
```

POV palette read:

```yaml
enabled_pov_palette: [hustle_fund_yin_bahn, naval_ravikant]
output_verbosity: deep
```

## Dependencies

Required runtime:

- Python 3.10+
- `pdfplumber`
- `pyyaml`

Test-only:

- `pytest`
- `reportlab`

The current v1 scorer defaults to a deterministic local heuristic backend, including when `scoring_backend` is `auto`. Use `scoring_backend: anthropic` explicitly to call the Anthropic Messages API with `ANTHROPIC_API_KEY`; CI and smoke tests never pay for model calls by default. The prompt boundaries and adapter protocols are present in `frame_scorer.py` and `named_pov_scorer.py`.

## Script map

- `scripts/evaluate.py`: CLI entry and pipeline wiring.
- `scripts/deck_reader.py`: PDF/text/directory ingestion.
- `scripts/rubric_loader.py`: markdown rubric parser and `rubric_v1.json` cache generator.
- `scripts/frame_scorer.py`: frame-wise substantive scoring and stage-discipline handling.
- `scripts/named_pov_scorer.py`: opt-in named-POV reads.
- `scripts/output_renderer.py`: markdown/JSON renderer.

## Failure modes

- Missing path: non-zero exit with usage/error.
- Unsupported type: non-zero exit listing supported inputs.
- Empty or image-only PDF: non-zero exit with OCR/text-layer requirement.
- Invalid config: field-level error.
- Unknown POV: error with valid IDs.
- Stylistic scorer missing: evaluation continues and marks style as not scored, because D4.2 owns that adapter.

## D4.2 interface contract

If present on `PYTHONPATH`, `scripts/evaluate.py` imports:

```python
from stylistic_scorer import score_stylistic
```

Expected signature:

```python
def score_stylistic(slides: list[dict], config: dict) -> dict:
    return {
        "stylistic_dimensions": [...],
        "stylistic_composite": 3.4,
        "style_substance_gap": {...},
    }
```

D4.1 does not implement stylistic scoring.
