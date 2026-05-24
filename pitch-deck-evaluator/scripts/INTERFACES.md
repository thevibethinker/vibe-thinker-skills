---
created: 2026-05-24
last_edited: 2026-05-24
version: 1.0
provenance: public-skill-export
---

# Pitch Deck Evaluator — D4.1/D4.2 Interfaces

## Shared orchestration contract

D4.2 defines the conservative style interface for `evaluate.py`:

```python
score_stylistic(slides, config) -> dict
```

- `slides`: list of slide objects or strings. Preferred object shape: `{ "slide_num": int, "text": str, "notes": optional str }`.
- `config`: dict matching D3.1 `CONFIG_SCHEMA.md`; D4.2 reads `register_override` and `stylistic_weight_overrides` only.
- Return: serializable stylistic scorecard dict.
- Guardrail: `score_stylistic` does not accept or inspect substantive scores.

## Stylistic scorecard shape

```yaml
detected_voice_mode: sharp_declarative|concrete_operator|earnest_founder|visionary_narrative|consultative_analytical|mixed
voice_confidence: high|medium|low
style_score: number # 0-100
dimensions:
  - dimension_id: punch_density|specificity_quantification|voice_register_fit|claim_hygiene|hierarchy_scannability|anti_buzzword_discipline|narrative_cohesion
    label: string
    score: number # 0-5
    weight_default: number
    weight_effective: number
    weighted_points: number
    reasoning: string
    evidence:
      - slide_ref: string
        excerpt: string
        evidence_type: string
    register_applied: boolean
    top_fix: string
    confidence: high|medium|low
strengths: [string]
weaknesses: [string]
gap_flag: null|string
notes: [string]
```

## Voice detector contract

```python
detect_voice_mode(slides, config=None) -> VoiceModeResult
```

The result is dataclass-backed and serializable with `dataclasses.asdict`. Mode names use snake_case internally and can be rendered to D2.5 labels by callers.

## Action list contract

```python
build_action_list(substantive_scorecard, stylistic_scorecard, frame_matrix_outputs=None, top_n=5) -> dict
```

- `substantive_scorecard`: D4.1 scorecard; accepts either top-level `dimensions[]`, `substantive_dimensions[]`, or frame-scoped `frames.{F}.dimensions[]`.
- `stylistic_scorecard`: output from `score_stylistic`.
- `frame_matrix_outputs`: optional D4.1 frame outputs, used to identify frames helped.
- `top_n`: strict maximum count. The builder never emits more than this.

Action item shape:

```yaml
rank: integer
dimension_id: string
dimension_label: string
surface: substantive|style
action: string
impact: High|Medium|Low
impact_score: number
effort: slide rewrite|medium|additional evidence required|founder positioning shift
impact_per_effort: number
frames_helped: [F1|F2|F3|F4]
why_this_is_first: string
evidence: [object]
```

## Synthesis renderer contract

```python
render_cross_frame_synthesis(frame_matrix_outputs, substantive_scorecard=None, stylistic_scorecard=None, divergence_threshold=1.5) -> str
```

Renderer is deterministic once scorecards exist. It does not re-score.

## Coordination note for D4.1

D4.2 landed before a `D4.1.json` deposit was present, so this file defines the initial interface. If D4.1 needs an additional argument, propose it in the D4.1 deposit rather than silently creating a second incompatible signature.
