---
created: 2026-05-24
last_edited: 2026-05-24
version: 0.1
provenance: public-skill-export
---

# Pitch Deck Evaluator

`pitch-deck-evaluator` evaluates early-stage pitch decks through four investor credulity frames, a stage-aware substantive rubric, optional source-inspired named-POV lenses, and a separate style surface.

It is designed as a founder decision tool, not a fundraising oracle. Advice is contextual; the report should expose how different investors may read the same evidence rather than collapse everything into one universal answer.

## What it does

- Reads PDF decks with a text layer, markdown/text decks, or directory bundles.
- Applies the rubric in `references/rubric_v1.md` across four frames:
  - F1 warm believer
  - F2 curious skeptic
  - F3 cold partner read
  - F4 hostile diligence
- Keeps substantive quality and stylistic/message quality separate.
- Optionally renders named-POV reads from public-source-inspired lenses.
- Produces markdown and optional JSON output.

## What it does not do

- It does not predict whether any named investor will invest.
- It does not guarantee fundraising outcomes.
- It does not score image-only decks in v1; use a PDF/text export with a text layer.
- It does not replace founder judgment or investor-specific context.

## Install

From the repository root:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r Skills/pitch-deck-evaluator/requirements.txt
```

For tests:

```bash
pip install -r Skills/pitch-deck-evaluator/tests/requirements-test.txt
```

## Run

```bash
python3 Skills/pitch-deck-evaluator/scripts/evaluate.py /path/to/deck.pdf --out evaluation.md
```

Use the packaged default config:

```bash
python3 Skills/pitch-deck-evaluator/scripts/evaluate.py /path/to/deck.pdf \
  --config Skills/pitch-deck-evaluator/assets/default_config.yaml \
  --out evaluation.md \
  --emit-json
```

Run a dry validation pass:

```bash
python3 Skills/pitch-deck-evaluator/scripts/evaluate.py /path/to/deck.pdf --dry-run
```

## Config

Default config lives in both:

- `assets/default_config.yaml` for public/package layout
- `config/default_config.yaml` for local script compatibility

See `references/CONFIG_SCHEMA.md` for allowed values.

## Named-POV lenses

Named POVs are opt-in. They are contrast lenses based on public writing/interviews, not predictions of what any real investor would do.

Example config snippet:

```yaml
enabled_pov_palette:
  - hustle_fund_yin_bahn
  - naval_ravikant
```

Every named-POV output must include the anti-cosplay disclaimer documented in `SKILL.md`.

## Outputs

The markdown report follows `references/OUTPUT_FORMAT.md` and includes:

- Header / config snapshot
- Executive read
- Score snapshot
- Frame scorecards
- Cross-frame synthesis
- Substantive vs. stylistic split
- Optional named-POV reads
- Per-slide annotations
- Prioritized action list

## Privacy and security

This skill evaluates local files supplied by the user. Do not run private decks through third-party model APIs unless you understand and accept the chosen provider's data policy. The current v1 implementation uses deterministic local heuristics by default and does not require an external model call for tests/smoke runs.

## Development checks

```bash
pytest Skills/pitch-deck-evaluator/tests
python3 Skills/pitch-deck-evaluator/scripts/evaluate.py \
  Skills/pitch-deck-evaluator/tests/fixtures/sample_seed_deck.pdf \
  --config Skills/pitch-deck-evaluator/assets/default_config.yaml \
  --out /tmp/sample_eval.md \
  --emit-json
```

## Version

- Skill version: 0.1.0
- Rubric version: v1
