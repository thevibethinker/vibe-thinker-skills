---
created: 2026-05-24
last_edited: 2026-05-24
version: 1.0
provenance: public-skill-export
drop_id: D3.1
title: Config Schema
---

# Config Schema — `pitch-deck-evaluator`

## Principle
The config tunes the analytical lens. It must not encode company-specific answers, investor flattery, or target conclusions.

## Default config
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
```

## Fields
| Field | Type | Default | Allowed | Effect | Example |
|---|---|---|---|---|---|
| `stage` | string | `pre_seed` | `pre_seed`, `seed`, `series_a` | selects stage grants/penalties | run seed deck with seed expectations |
| `enabled_frames` | list[string] | all | non-empty subset of F1-F4 | controls scorecards | F3/F4 cold stress test |
| `enabled_pov_palette` | list[string] | `[]` | valid POV IDs | separate source-inspired reads | Pear market rigor read |
| `substantive_weight_overrides` | map[string,number] | `{}` | dimension IDs, 0-3 | multiplies substantive weights | emphasize market logic |
| `stylistic_weight_overrides` | map[string,number] | `{}` | style IDs, 0-3 | multiplies style weights | emphasize claim hygiene |
| `register_override` | string | `auto` | `auto`, `sharp_declarative`, `concrete_operator`, `earnest_founder`, `visionary_narrative`, `consultative_analytical` | overrides voice detection | force analytical B2B mode |
| `output_verbosity` | string | `standard` | `terse`, `standard`, `deep` | controls report depth | deep rewrite prep |
| `include_action_list` | boolean | `true` | true/false | shows ranked fixes | benchmark-only run |
| `include_advisory_overall` | boolean | `true` | true/false | shows advisory aggregate | hide single number |

## Valid IDs
Substantive: `founder_market_fit_team_capacity`, `non_obvious_insight_thesis_clarity`, `problem_urgency_icp_wedge`, `market_logic_venture_scale_path`, `why_now_timing_pressure`, `evidence_demand_learning_velocity`, `solution_product_clarity_proof`, `defensibility_compounding_advantage`, `competitive_landscape_differentiation`, `gtm_plausibility_first_distribution`, `business_model_economic_logic`, `ask_milestones_next_round`, `risk_honesty_derisking_plan`.

Stylistic: `punch_density`, `specificity_quantification`, `voice_register_fit`, `claim_hygiene`, `hierarchy_scannability`, `anti_buzzword_discipline`, `narrative_cohesion`.

Named POVs: `hustle_fund_yin_bahn`, `pear_nozad_hershenson`, `nfx_currier_levy_weiss`, `floodgate_maples_miura_ko`, `bloomberg_beta_bahat`, `precursor_hudson`, `boost_draper`, `designer_fund_blumenrose_allen`, `2048_iskold`, `k9_manu_kumar`, `naval_ravikant`, `jason_calacanis`, `sahil_lavingia`, `elad_gil`, `fabrice_grinda_fj_labs`.

## JSON-schema contract
Objects reject unknown top-level fields. `enabled_frames` must be non-empty and unique. Weight override values must be numbers from 0 to 3. Unknown dimension or POV IDs error. Missing config loads defaults and records `config_source: defaults`. CLI overrides are allowed and must be reflected in report config snapshot.

## Examples
### Default
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
```
### Cold-send stress
```yaml
stage: pre_seed
enabled_frames: [F3, F4]
enabled_pov_palette: []
substantive_weight_overrides:
  evidence_demand_learning_velocity: 1.2
  market_logic_venture_scale_path: 1.2
stylistic_weight_overrides:
  punch_density: 1.25
  hierarchy_scannability: 1.25
register_override: auto
output_verbosity: deep
include_action_list: true
include_advisory_overall: false
```
### Named market-rigor pass
```yaml
stage: pre_seed
enabled_frames: [F2, F4]
enabled_pov_palette: [pear_nozad_hershenson, k9_manu_kumar, fabrice_grinda_fj_labs]
substantive_weight_overrides:
  market_logic_venture_scale_path: 1.3
  business_model_economic_logic: 1.25
register_override: consultative_analytical
output_verbosity: deep
```

## 9. Full YAML schema equivalent

```yaml
type: object
additionalProperties: false
properties:
  stage:
    type: string
    default: pre_seed
    allowed: [pre_seed, seed, series_a]
    effect: Selects the stage-discipline table and determines which absences are granted.
  enabled_frames:
    type: list[string]
    default: [F1, F2, F3, F4]
    min_items: 1
    unique_items: true
    allowed_items: [F1, F2, F3, F4]
    effect: Controls which frame-distinct scorecards are emitted.
  enabled_pov_palette:
    type: list[string]
    default: []
    unique_items: true
    allowed_items:
      - hustle_fund_yin_bahn
      - pear_nozad_hershenson
      - nfx_currier_levy_weiss
      - floodgate_maples_miura_ko
      - bloomberg_beta_bahat
      - precursor_hudson
      - boost_draper
      - designer_fund_blumenrose_allen
      - 2048_iskold
      - k9_manu_kumar
      - naval_ravikant
      - jason_calacanis
      - sahil_lavingia
      - elad_gil
      - fabrice_grinda_fj_labs
    effect: Adds opt-in source-inspired POV reads; default empty prevents named-VC cosplay.
  substantive_weight_overrides:
    type: map[string, number]
    default: {}
    key_set: substantive_dimension_ids
    value_range: [0.0, 3.0]
    effect: Multiplies default substantive weights after frame modifiers.
  stylistic_weight_overrides:
    type: map[string, number]
    default: {}
    key_set: stylistic_dimension_ids
    value_range: [0.0, 3.0]
    effect: Multiplies default stylistic weights.
  register_override:
    type: string
    default: auto
    allowed: [auto, sharp_declarative, concrete_operator, earnest_founder, visionary_narrative, consultative_analytical]
    effect: Overrides voice/register auto-detection for style scoring.
  output_verbosity:
    type: string
    default: standard
    allowed: [terse, standard, deep]
    effect: Controls number of evidence quotes, depth of rationale, and action-list detail.
  include_action_list:
    type: boolean
    default: true
    effect: Toggles prioritized action list rendering.
  include_advisory_overall:
    type: boolean
    default: true
    effect: Toggles the optional overall composite while preserving separate substance/style/frame scores.
```

## 10. Override semantics

Weight overrides are multipliers, not replacements. Effective weight is:

```text
effective_weight = default_dimension_weight * frame_modifier * config_override
```

The evaluator should normalize final composite denominators after applying enabled-frame and override choices. A dimension override of `0` suppresses the dimension from composite math but should still allow the report to mention hard gates if the dimension contains a trust or stage-critical issue.

## 11. Verbosity semantics

| Verbosity | Required behavior |
|---|---|
| `terse` | Executive read, score snapshot, top 3 actions, only critical per-slide notes. |
| `standard` | Full frame scorecards, cross-frame synthesis, top 5 actions, concise per-slide annotations. |
| `deep` | Full evidence quotes, detailed rationale per dimension, expanded frame-switch notes, named POV details, and extended action list. |

## 12. Config safety examples

Invalid because it encodes a conclusion:

```yaml
founder_is_exceptional: true
market_is_large: true
```

Valid because it tunes the lens:

```yaml
substantive_weight_overrides:
  founder_market_fit_team_capacity: 1.25
  market_logic_venture_scale_path: 1.2
```
