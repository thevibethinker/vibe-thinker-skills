---
created: 2026-05-24
last_edited: 2026-05-24
version: 1.0
provenance: public-skill-export
drop_id: D3.1
title: Rubric v1
---

# Rubric v1 — Pitch Deck Evaluator

## Status
This hard-gate rubric is specification-only. Wave 4 must not begin until V approves this file plus `skill_design/SPEC.md`, `CONFIG_SCHEMA.md`, and `OUTPUT_FORMAT.md`.

## Source discipline
This file maps to all Wave-2 synthesis: D2.1 substantive dimensions, D2.2 frame matrix, D2.3 named-VC palette, D2.4 stage deltas, and D2.5 stylistic dimensions. Every evaluator finding must include deck evidence (`slide_ref`, excerpt, dimension, frame, confidence). Do not invent facts or named-investor predictions.

## Core output contract
The scorer emits four frame-distinct scorecards (F1 Warm Believer, F2 Curious Skeptic, F3 Cold Partner Read, F4 Hostile Diligence), one cross-frame synthesis, separate substantive and stylistic composites, optional advisory overall composite, optional named-POV reads, per-slide annotations, prioritized action list, and style/substance gap callout.

## Absence handling
| Absence type | Rule |
|---|---|
| Absence-by-stage | Missing later-stage proof granted at pre-seed; no penalty, emit `granted_at_pre_seed`. |
| Absence-by-omission | Missing pre-seed-native proof; penalize. |
| Absence-by-design | Equivalent evidence exists elsewhere; score evidence not slide canon. |
| Absence-by-format | Extraction cannot see the evidence; mark `requires_info`. |
| Absence-with-overclaim | Evidence absent but certainty claimed; penalize and possible trust flag. |

## Scoring model
Per dimension, score 0-5 using half-points. Compute a substantive composite and stylistic composite separately. Optional advisory overall default: `0.70 * substantive + 0.25 * stylistic + 0.05 * stage_adjustment`. Never average away frame divergence: a high F1/low F4 deck is a warm-believer deck with diligence risk, not a middling deck.

Hard gates escalate outside averages: intellectual dishonesty, fake scarcity, contradictory metrics, fake product/AI claims, evidence vacuum, no ICP/wedge, missing technical builder for a technical product, what-do-you-do opacity in the opening, and no clear ask/milestone map.

## Substantive dimensions
| ID | Dimension | Weight | Definition |
|---|---|---:|---|
| `founder_market_fit_team_capacity` | Founder-market fit + team capacity | 13 | credible right to understand, build, sell, recruit, and learn for this problem. |
| `non_obvious_insight_thesis_clarity` | Non-obvious insight + thesis clarity | 10 | the central risky-but-believable belief the deck asks an investor to underwrite. |
| `problem_urgency_icp_wedge` | Problem urgency + ICP/wedge | 9 | painful current problem for a narrow first customer/user and why that wedge starts. |
| `market_logic_venture_scale_path` | Market logic + venture-scale path | 8 | credible wedge-to-venture-scale reasoning without TAM theater. |
| `why_now_timing_pressure` | Why now + timing pressure | 8 | real inflection that makes the opportunity newly possible or urgent. |
| `evidence_demand_learning_velocity` | Evidence of demand + learning velocity | 10 | stage-appropriate proof that customers care and founders learn fast. |
| `solution_product_clarity_proof` | Solution/product clarity + proof | 7 | what exists/will exist, how it solves pain, and what product artifact proves it. |
| `defensibility_compounding_advantage` | Defensibility + compounding advantage | 7 | advantage that can compound through data, network, workflow, distribution, technical, category, brand, or regulation. |
| `competitive_landscape_differentiation` | Competitive landscape + differentiation | 6 | real alternatives and why customers switch/adopt. |
| `gtm_plausibility_first_distribution` | GTM plausibility + first distribution motion | 7 | specific first route to customers/users matched to buyer, product, price, and team. |
| `business_model_economic_logic` | Business model + economic logic | 5 | how value becomes revenue and why the model can work at stage. |
| `ask_milestones_next_round` | Ask + milestones to next round | 6 | round size/use/milestones mapped to risk reduction and next financing proof. |
| `risk_honesty_derisking_plan` | Risk honesty + de-risking plan | 4 | material risks and how this round/tests reduce them. |

### Founder-market fit + team capacity (`founder_market_fit_team_capacity`)
**Definition:** Evaluates credible right to understand, build, sell, recruit, and learn for this problem.

**Default weight:** 13/100 substantive.

**Strong signals:** founder spike; lived/domain access; builder/seller ownership; honest team gaps.

**Weak signals:** generic logos; no why-this-founder; missing technical owner; evasive claims.

**Prompt questions:**
1. What is the strongest claim the deck makes for this dimension?
2. Which slide/excerpt/metric/customer fact/product artifact supports it?
3. What must a skeptical reader infer because the deck does not state it?
4. Is missing evidence granted at this stage or a missing pre-seed substitute proof?
5. What is the highest-impact repair for this dimension?

**Frame sensitivity:**
| Frame | Modifier and note |
|---|---|
| F1 Warm Believer | 1.1x — underwrites person first; needs specific spike |
| F2 Curious Skeptic | 1.2x — asks why founder earned belief |
| F3 Cold Partner Read | 1.2x — needs why-this-team early |
| F4 Hostile Diligence | 1.2x — probes domain fit and execution ownership |

**Score anchors:**
| Score | Anchor for Founder-market fit + team capacity |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

**Stage constraint:** Apply D2.4 before scoring. Grant missing mature metrics; penalize missing pre-seed-native proof; flag false precision separately.

---

### Non-obvious insight + thesis clarity (`non_obvious_insight_thesis_clarity`)
**Definition:** Evaluates the central risky-but-believable belief the deck asks an investor to underwrite.

**Default weight:** 10/100 substantive.

**Strong signals:** repeatable thesis; grounded contrarian view; wedge/timing link.

**Weak signals:** buzzword thesis; empty checklist deck; facts without story.

**Prompt questions:**
1. What is the strongest claim the deck makes for this dimension?
2. Which slide/excerpt/metric/customer fact/product artifact supports it?
3. What must a skeptical reader infer because the deck does not state it?
4. Is missing evidence granted at this stage or a missing pre-seed substitute proof?
5. What is the highest-impact repair for this dimension?

**Frame sensitivity:**
| Frame | Modifier and note |
|---|---|
| F1 Warm Believer | 0.9x — may share thesis but needs retellable sentence |
| F2 Curious Skeptic | 1.2x — core question is what founder sees |
| F3 Cold Partner Read | 1.1x — earns cold attention |
| F4 Hostile Diligence | 1.5x — attacks borrowed memes and hype |

**Score anchors:**
| Score | Anchor for Non-obvious insight + thesis clarity |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

**Stage constraint:** Apply D2.4 before scoring. Grant missing mature metrics; penalize missing pre-seed-native proof; flag false precision separately.

---

### Problem urgency + ICP/wedge (`problem_urgency_icp_wedge`)
**Definition:** Evaluates painful current problem for a narrow first customer/user and why that wedge starts.

**Default weight:** 9/100 substantive.

**Strong signals:** specific ICP; urgent/frequent pain; sequenced expansion; discovery evidence.

**Weak signals:** everyone customer; unsequenced segments; technology before pain.

**Prompt questions:**
1. What is the strongest claim the deck makes for this dimension?
2. Which slide/excerpt/metric/customer fact/product artifact supports it?
3. What must a skeptical reader infer because the deck does not state it?
4. Is missing evidence granted at this stage or a missing pre-seed substitute proof?
5. What is the highest-impact repair for this dimension?

**Frame sensitivity:**
| Frame | Modifier and note |
|---|---|
| F1 Warm Believer | 0.8x — may infer pain from lived experience |
| F2 Curious Skeptic | 1.1x — checks current painful adoption |
| F3 Cold Partner Read | 1.2x — needs customer specificity fast |
| F4 Hostile Diligence | 1.3x — tests willingness-to-pay and substitutes |

**Score anchors:**
| Score | Anchor for Problem urgency + ICP/wedge |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

---

### Market logic + venture-scale path (`market_logic_venture_scale_path`)
**Definition:** Evaluates credible wedge-to-venture-scale reasoning without TAM theater.

**Default weight:** 8/100 substantive.

**Strong signals:** bottom-up assumptions; buyer budget; expansion path; venture-scale logic.

**Weak signals:** top-down TAM; no segmentation; report screenshots as proof.

**Prompt questions:**
1. What is the strongest claim the deck makes for this dimension?
2. Which slide/excerpt/metric/customer fact/product artifact supports it?
3. What must a skeptical reader infer because the deck does not state it?
4. Is missing evidence granted at this stage or a missing pre-seed substitute proof?
5. What is the highest-impact repair for this dimension?

**Frame sensitivity:**
| Frame | Modifier and note |
|---|---|
| F1 Warm Believer | 0.7x — tolerates rough math if wedge/founder strong |
| F2 Curious Skeptic | 1.1x — wants bottom-up assumptions |
| F3 Cold Partner Read | 1.2x — needs specific market/wedge |
| F4 Hostile Diligence | 1.3x — validates price, count, budget, capture |

**Score anchors:**
| Score | Anchor for Market logic + venture-scale path |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

---

### Why now + timing pressure (`why_now_timing_pressure`)
**Definition:** Evaluates real inflection that makes the opportunity newly possible or urgent.

**Default weight:** 8/100 substantive.

**Strong signals:** tech/regulatory/behavior/cost/distribution shift tied to wedge.

**Weak signals:** trend label only; no forcing function; timing mismatch.

**Prompt questions:**
1. What is the strongest claim the deck makes for this dimension?
2. Which slide/excerpt/metric/customer fact/product artifact supports it?
3. What must a skeptical reader infer because the deck does not state it?
4. Is missing evidence granted at this stage or a missing pre-seed substitute proof?
5. What is the highest-impact repair for this dimension?

**Frame sensitivity:**
| Frame | Modifier and note |
|---|---|
| F1 Warm Believer | 0.8x — may grant category timing intuition |
| F2 Curious Skeptic | 1.1x — needs concrete inflection |
| F3 Cold Partner Read | 1.1x — creates cold urgency |
| F4 Hostile Diligence | 1.4x — challenges fundraising slogans |

**Score anchors:**
| Score | Anchor for Why now + timing pressure |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

---

### Evidence of demand + learning velocity (`evidence_demand_learning_velocity`)
**Definition:** Evaluates stage-appropriate proof that customers care and founders learn fast.

**Default weight:** 10/100 substantive.

**Strong signals:** interviews; design partners; LOIs; usage; prototype; iteration loop.

**Weak signals:** evidence vacuum; vanity metrics; fake hockey stick; skipped traction because early.

**Prompt questions:**
1. What is the strongest claim the deck makes for this dimension?
2. Which slide/excerpt/metric/customer fact/product artifact supports it?
3. What must a skeptical reader infer because the deck does not state it?
4. Is missing evidence granted at this stage or a missing pre-seed substitute proof?
5. What is the highest-impact repair for this dimension?

**Frame sensitivity:**
| Frame | Modifier and note |
|---|---|
| F1 Warm Believer | 0.9x — can fund before mature proof but needs motion |
| F2 Curious Skeptic | 1.2x — separates revenue absence from evidence absence |
| F3 Cold Partner Read | 1.2x — needs proof beyond cold scan |
| F4 Hostile Diligence | 1.4x — hunts vanity/fake traction |

**Score anchors:**
| Score | Anchor for Evidence of demand + learning velocity |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

**Stage constraint:** Apply D2.4 before scoring. Grant missing mature metrics; penalize missing pre-seed-native proof; flag false precision separately.

---

### Solution/product clarity + proof (`solution_product_clarity_proof`)
**Definition:** Evaluates what exists/will exist, how it solves pain, and what product artifact proves it.

**Default weight:** 7/100 substantive.

**Strong signals:** demo/mock/prototype/screenshot; fast product/customer/value clarity.

**Weak signals:** no product visual; feature tour; technical weeds before value.

**Prompt questions:**
1. What is the strongest claim the deck makes for this dimension?
2. Which slide/excerpt/metric/customer fact/product artifact supports it?
3. What must a skeptical reader infer because the deck does not state it?
4. Is missing evidence granted at this stage or a missing pre-seed substitute proof?
5. What is the highest-impact repair for this dimension?

**Frame sensitivity:**
| Frame | Modifier and note |
|---|---|
| F1 Warm Believer | 0.8x — accepts concept if builder credible |
| F2 Curious Skeptic | 1.0x — wants product proof linking pain/execution |
| F3 Cold Partner Read | 1.2x — needs visual/clear explanation |
| F4 Hostile Diligence | 1.3x — checks real/differentiated/not vapor |

**Score anchors:**
| Score | Anchor for Solution/product clarity + proof |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

---

### Defensibility + compounding advantage (`defensibility_compounding_advantage`)
**Definition:** Evaluates advantage that can compound through data, network, workflow, distribution, technical, category, brand, or regulation.

**Default weight:** 7/100 substantive.

**Strong signals:** specific compounding path tied to wedge and milestone.

**Weak signals:** generic moat; first-mover/platform claims; easy-copy idea.

**Prompt questions:**
1. What is the strongest claim the deck makes for this dimension?
2. Which slide/excerpt/metric/customer fact/product artifact supports it?
3. What must a skeptical reader infer because the deck does not state it?
4. Is missing evidence granted at this stage or a missing pre-seed substitute proof?
5. What is the highest-impact repair for this dimension?

**Frame sensitivity:**
| Frame | Modifier and note |
|---|---|
| F1 Warm Believer | 0.8x — grants early path if founder/inflection strong |
| F2 Curious Skeptic | 1.1x — wants moat hypothesis and substitutes |
| F3 Cold Partner Read | 1.0x — wants homework honesty |
| F4 Hostile Diligence | 1.5x — pressure-tests copyability/incumbents |

**Score anchors:**
| Score | Anchor for Defensibility + compounding advantage |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

---

### Competitive landscape + differentiation (`competitive_landscape_differentiation`)
**Definition:** Evaluates real alternatives and why customers switch/adopt.

**Default weight:** 6/100 substantive.

**Strong signals:** direct/indirect/status quo alternatives; switching trigger; humble nuance.

**Weak signals:** no competition; strawman incumbents; checkbox theater.

**Prompt questions:**
1. What is the strongest claim the deck makes for this dimension?
2. Which slide/excerpt/metric/customer fact/product artifact supports it?
3. What must a skeptical reader infer because the deck does not state it?
4. Is missing evidence granted at this stage or a missing pre-seed substitute proof?
5. What is the highest-impact repair for this dimension?

**Frame sensitivity:**
| Frame | Modifier and note |
|---|---|
| F1 Warm Believer | 0.8x — may follow up but no-competition hurts |
| F2 Curious Skeptic | 1.1x — tests market understanding |
| F3 Cold Partner Read | 1.0x — needs honest alternatives |
| F4 Hostile Diligence | 1.5x — treats no-competition as judgment failure |

**Score anchors:**
| Score | Anchor for Competitive landscape + differentiation |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

---

### GTM plausibility + first distribution motion (`gtm_plausibility_first_distribution`)
**Definition:** Evaluates specific first route to customers/users matched to buyer, product, price, and team.

**Default weight:** 7/100 substantive.

**Strong signals:** founder-led/design-partner/community/partner path; sequenced buyer/channel.

**Weak signals:** channel spray; generic paid ads; distribution assumed.

**Prompt questions:**
1. What is the strongest claim the deck makes for this dimension?
2. Which slide/excerpt/metric/customer fact/product artifact supports it?
3. What must a skeptical reader infer because the deck does not state it?
4. Is missing evidence granted at this stage or a missing pre-seed substitute proof?
5. What is the highest-impact repair for this dimension?

**Frame sensitivity:**
| Frame | Modifier and note |
|---|---|
| F1 Warm Believer | 0.8x — may grant access/community pull |
| F2 Curious Skeptic | 1.1x — wants ICP/buyer/channel sequence |
| F3 Cold Partner Read | 1.2x — rejects broad customer language |
| F4 Hostile Diligence | 1.4x — tests distribution logic |

**Score anchors:**
| Score | Anchor for GTM plausibility + first distribution motion |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

**Stage constraint:** Apply D2.4 before scoring. Grant missing mature metrics; penalize missing pre-seed-native proof; flag false precision separately.

---

### Business model + economic logic (`business_model_economic_logic`)
**Definition:** Evaluates how value becomes revenue and why the model can work at stage.

**Default weight:** 5/100 substantive.

**Strong signals:** who pays; why pay; pricing hypothesis; value-capture milestone.

**Weak signals:** fantasy projections; premature CAC/LTV; product-model mismatch.

**Prompt questions:**
1. What is the strongest claim the deck makes for this dimension?
2. Which slide/excerpt/metric/customer fact/product artifact supports it?
3. What must a skeptical reader infer because the deck does not state it?
4. Is missing evidence granted at this stage or a missing pre-seed substitute proof?
5. What is the highest-impact repair for this dimension?

**Frame sensitivity:**
| Frame | Modifier and note |
|---|---|
| F1 Warm Believer | 0.6x — underweights mature economics |
| F2 Curious Skeptic | 0.8x — wants credible value capture |
| F3 Cold Partner Read | 0.8x — needs enough model clarity |
| F4 Hostile Diligence | 1.2x — challenges projections/CAC/LTV/pricing |

**Score anchors:**
| Score | Anchor for Business model + economic logic |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

**Stage constraint:** Apply D2.4 before scoring. Grant missing mature metrics; penalize missing pre-seed-native proof; flag false precision separately.

---

### Ask + milestones to next round (`ask_milestones_next_round`)
**Definition:** Evaluates round size/use/milestones mapped to risk reduction and next financing proof.

**Default weight:** 6/100 substantive.

**Strong signals:** amount, runway, build/customer/revenue/key-hire milestones.

**Weak signals:** no ask; headcount/runway only; fake urgency; valuation detached.

**Prompt questions:**
1. What is the strongest claim the deck makes for this dimension?
2. Which slide/excerpt/metric/customer fact/product artifact supports it?
3. What must a skeptical reader infer because the deck does not state it?
4. Is missing evidence granted at this stage or a missing pre-seed substitute proof?
5. What is the highest-impact repair for this dimension?

**Frame sensitivity:**
| Frame | Modifier and note |
|---|---|
| F1 Warm Believer | 0.8x — can ask directly but needs closeable round |
| F2 Curious Skeptic | 1.05x — maps to fund fit and proof |
| F3 Cold Partner Read | 1.05x — needs visible action requested |
| F4 Hostile Diligence | 1.3x — rejects headcount-only/fake urgency |

**Score anchors:**
| Score | Anchor for Ask + milestones to next round |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

**Stage constraint:** Apply D2.4 before scoring. Grant missing mature metrics; penalize missing pre-seed-native proof; flag false precision separately.

---

### Risk honesty + de-risking plan (`risk_honesty_derisking_plan`)
**Definition:** Evaluates material risks and how this round/tests reduce them.

**Default weight:** 4/100 substantive.

**Strong signals:** risks named/bounded; facts vs hypotheses; experiments tied to risks.

**Weak signals:** obvious risks hidden; NDA/SWOT-first; milestones dodge real risks.

**Prompt questions:**
1. What is the strongest claim the deck makes for this dimension?
2. Which slide/excerpt/metric/customer fact/product artifact supports it?
3. What must a skeptical reader infer because the deck does not state it?
4. Is missing evidence granted at this stage or a missing pre-seed substitute proof?
5. What is the highest-impact repair for this dimension?

**Frame sensitivity:**
| Frame | Modifier and note |
|---|---|
| F1 Warm Believer | 0.7x — expects awareness not risk-first deck |
| F2 Curious Skeptic | 1.0x — rewards de-risking sequence |
| F3 Cold Partner Read | 0.9x — enough risk awareness to trust |
| F4 Hostile Diligence | 1.5x — built around risk interrogation |

**Score anchors:**
| Score | Anchor for Risk honesty + de-risking plan |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

**Stage constraint:** Apply D2.4 before scoring. Grant missing mature metrics; penalize missing pre-seed-native proof; flag false precision separately.

---

## Stylistic dimensions
Style asks whether claims are legible, memorable, and appropriately forceful. It does not judge whether claims are true or fundable. Style and substance are scored independently.

| ID | Dimension | Weight | Definition | Detection heuristics |
|---|---|---:|---|---|
| `punch_density` | Punch / Density | 16 | high signal per word/slide; minimal throat-clearing. | word count, label headlines, throat-clearing phrases, multi-claim slides. |
| `specificity_quantification` | Specificity / Quantification | 16 | numbers, concrete nouns, examples, user-visible facts. | number density, adjective-proof ratio, customer-scope flags. |
| `voice_register_fit` | Voice + Register Fit | 14 | coherent voice matched to evidence, investor context, category. | register consistency, confidence/hedging fit, voice-mode features. |
| `claim_hygiene` | Claim Hygiene | 16 | claims are proven, sourced, framed as belief, or marked as assumption. | claim/proof adjacency, unsupported superlatives, contradiction scan. |
| `hierarchy_scannability` | Hierarchy + Scannability | 14 | headlines/copy expose the argument in fast-read order. | headline-as-claim rate, opening path, buried lede. |
| `anti_buzzword_discipline` | Anti-Buzzword Discipline | 12 | avoids inflated startup language and jargon camouflage. | buzzword density, acronym soup, abstraction stacks. |
| `narrative_cohesion` | Narrative Cohesion | 12 | slides form one through-line rather than a pile of points. | through-line continuity, causal links, orphan slides. |

### Style/substance gap labels
| Label | Condition | Required note |
|---|---:|---|
| Strong style, weak substance | style ≥75 and substance <55 | Polish may mask missing proof; diligence will expose it. |
| Strong substance, weak style | substance ≥75 and style <55 | Fundable substance is hard to parse; rewrite for comprehension. |
| Over-polished thinness | style ≥70, claim hygiene <50, substance <50 | Copy carries unsupported claims. |
| Rough but real | substance ≥70 and punch/scannability <50 | Evidence exists but is buried. |

### Voice modes
V1 sharp-declarative, V2 concrete/operator, V3 earnest-founder, V4 visionary narrative, V5 consultative/analytical. Auto-detect by default; config may override. Reward register fit; penalize unsupported swagger, diary sequencing, abstract frameworks, or vision without wedge.

#### Punch / Density
| Score | Anchor for Punch / Density |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

#### Specificity / Quantification
| Score | Anchor for Specificity / Quantification |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

#### Voice + Register Fit
| Score | Anchor for Voice + Register Fit |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

#### Claim Hygiene
| Score | Anchor for Claim Hygiene |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

#### Hierarchy + Scannability
| Score | Anchor for Hierarchy + Scannability |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

#### Anti-Buzzword Discipline
| Score | Anchor for Anti-Buzzword Discipline |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

#### Narrative Cohesion
| Score | Anchor for Narrative Cohesion |
|---:|---|
| 0 | Missing or actively harmful; no usable evidence or credibility damage. |
| 1 | Severe weakness; a reader must infer almost everything and may pass. |
| 2 | Weak/incomplete; some evidence exists but is vague, unsupported, buried, or unsequenced. |
| 3 | Adequate; stage-aware and scorable, with gaps a meeting can clarify. |
| 4 | Strong; specific, evidence-backed, and memo-ready with normal pre-seed uncertainty. |
| 5 | Exceptional; creates positive conviction and is likely to be quoted in a partner memo. |

## Frame matrix
| Frame | Summary | Grants | Demands |
|---|---|---|---|
| F1 Warm Believer | Relationship/thesis-aligned reader wanting a reason to say yes. | incompleteness, founder promise, weirdness with logic | no trust breaks; one exceptional signal; milestone logic |
| F2 Curious Skeptic | Open institutional read. | market may exist; revenue may be absent | why this team, why now, proof, sequence |
| F3 Cold Partner Read | No-context scan. | only a brief scan | product/customer/problem by slide 1-3 |
| F4 Hostile Diligence | Adversarial pressure test. | only clean weirdness | source quality, contradictions, market mechanics |

| Dimension | F1 | F2 | F3 | F4 |
|---|---|---|---|---|
| Founder-market fit + team capacity | 1.1x — underwrites person first; needs specific spike | 1.2x — asks why founder earned belief | 1.2x — needs why-this-team early | 1.2x — probes domain fit and execution ownership |
| Non-obvious insight + thesis clarity | 0.9x — may share thesis but needs retellable sentence | 1.2x — core question is what founder sees | 1.1x — earns cold attention | 1.5x — attacks borrowed memes and hype |
| Problem urgency + ICP/wedge | 0.8x — may infer pain from lived experience | 1.1x — checks current painful adoption | 1.2x — needs customer specificity fast | 1.3x — tests willingness-to-pay and substitutes |
| Market logic + venture-scale path | 0.7x — tolerates rough math if wedge/founder strong | 1.1x — wants bottom-up assumptions | 1.2x — needs specific market/wedge | 1.3x — validates price, count, budget, capture |
| Why now + timing pressure | 0.8x — may grant category timing intuition | 1.1x — needs concrete inflection | 1.1x — creates cold urgency | 1.4x — challenges fundraising slogans |
| Evidence of demand + learning velocity | 0.9x — can fund before mature proof but needs motion | 1.2x — separates revenue absence from evidence absence | 1.2x — needs proof beyond cold scan | 1.4x — hunts vanity/fake traction |
| Solution/product clarity + proof | 0.8x — accepts concept if builder credible | 1.0x — wants product proof linking pain/execution | 1.2x — needs visual/clear explanation | 1.3x — checks real/differentiated/not vapor |
| Defensibility + compounding advantage | 0.8x — grants early path if founder/inflection strong | 1.1x — wants moat hypothesis and substitutes | 1.0x — wants homework honesty | 1.5x — pressure-tests copyability/incumbents |
| Competitive landscape + differentiation | 0.8x — may follow up but no-competition hurts | 1.1x — tests market understanding | 1.0x — needs honest alternatives | 1.5x — treats no-competition as judgment failure |
| GTM plausibility + first distribution motion | 0.8x — may grant access/community pull | 1.1x — wants ICP/buyer/channel sequence | 1.2x — rejects broad customer language | 1.4x — tests distribution logic |
| Business model + economic logic | 0.6x — underweights mature economics | 0.8x — wants credible value capture | 0.8x — needs enough model clarity | 1.2x — challenges projections/CAC/LTV/pricing |
| Ask + milestones to next round | 0.8x — can ask directly but needs closeable round | 1.05x — maps to fund fit and proof | 1.05x — needs visible action requested | 1.3x — rejects headcount-only/fake urgency |
| Risk honesty + de-risking plan | 0.7x — expects awareness not risk-first deck | 1.0x — rewards de-risking sequence | 0.9x — enough risk awareness to trust | 1.5x — built around risk interrogation |

## Stage-discipline rules
Classify every weakness before scoring: `granted_at_pre_seed`, `stage_appropriate_evidence`, `missing_pre_seed_proof`, `false_precision`, `inverse_trap`, or `credibility_risk`.

Dimension constraints: no revenue alone has max penalty 0 at pre-seed; no validation substitute caps demand evidence at 2. Missing PMF is granted; missing PMF-search evidence is not. Missing exec layer is granted; missing builder control for technical products is not. No why-this-founder caps founder dimension at 2 unless supplied elsewhere. Thin traction plus missing insight caps thesis at 2. Rough market estimates are granted; top-down TAM theater caps market at 2.5. Lack of repeatable GTM is granted; lack of first buyer/channel/test is not. Missing CAC/LTV is granted; missing who-pays/why-pay is weak. Mature moat absence is granted; no compounding path or no-competition claim is weak. Pre-MVP is granted if product clarity/proof exists. Vague/no ask is never stage-granted. No formal risk slide is fine; no risk/milestone logic is not.

## Named-VC palette
Default is empty. Optional source-inspired lenses: `hustle_fund_yin_bahn`, `pear_nozad_hershenson`, `nfx_currier_levy_weiss`, `floodgate_maples_miura_ko`, `bloomberg_beta_bahat`, `precursor_hudson`, `boost_draper`, `designer_fund_blumenrose_allen`, `2048_iskold`, `k9_manu_kumar`, `naval_ravikant`, `jason_calacanis`, `sahil_lavingia`, `elad_gil`, `fabrice_grinda_fj_labs`. They render separate POV reads and must not say “Investor X will pass.”

## Machine-readable output fields
`deck_metadata`, `frame_scorecards[]`, `substantive_dimensions[]`, `stylistic_dimensions[]`, `composites`, `hard_gates[]`, `likely_frame_switches[]`, `cross_frame_synthesis`, `named_pov_reads[]`, `per_slide_annotations[]`, `prioritized_action_list[]`, and `style_substance_gap`.
