---
created: 2026-06-21
last_edited: 2026-06-21
version: 1.0
provenance: con_dHhwJrMplpoKC0TW
---

# Research Engine — Product Diligence Mode

`product-diligence` is the canonical mode for researching a specific product, service, or product category and turning external evidence into a decision-ready buying/testing recommendation.

Use it when the owner asks questions like:

- "Find the best on-person AI recorder for meetings and walks."
- "Compare Plaud, Fieldy, Limitless, Granola, Otter, and similar products."
- "What product should I buy for <use case>?"
- "Which tools in this category are actually good, according to objective reviews?"

The mode works for both consumer and B2B products, but it is optimized for decisions where tradeoffs matter more than a generic ranked list.

## Invocation

Category-first invocation:

```bash
python3 Skills/research-engine/scripts/research_engine.py run \
  --query "Find the best on-person AI recorder / meeting transcription product for in-person meetings, walks, and voice notes" \
  --mode product-diligence \
  --depth standard \
  --topic ai-recorder-product-diligence
```

Specific product invocation:

```bash
python3 Skills/research-engine/scripts/research_engine.py run \
  --query "Diligence Plaud NotePin for in-person meeting capture and voice note workflows" \
  --mode product-diligence \
  --depth standard \
  --topic plaud-notepin-product-diligence
```

Fast, no-questions invocation:

```bash
python3 Skills/research-engine/scripts/research_engine.py run \
  --query "Quickly compare top AI voice recorder products for in-person capture" \
  --mode product-diligence \
  --depth one-shot \
  --topic ai-recorder-quick-compare
```

`one-shot` executes immediately, so it should include a preference-assumption section rather than pausing for dialogue. `quick`, `standard`, and `deep` should generate an initial scan and a Socratic preference interview before final ranking.

## Core job

Answer four questions:

1. What are the real product/category boundaries?
2. Which products are credible top candidates?
3. What does objective or semi-objective evidence say about each one?
4. Which product best fits the owner's actual preferences and tradeoffs?

The mode should not merely summarize marketing pages. It should make the decision structure visible.

## Two-stage workflow

### Stage 1 — Initial scan and Socratic preference discovery

Run a lightweight external scan first to identify:

- category boundaries and adjacent categories
- credible candidate products
- product types that may look similar but solve different jobs
- common failure modes and complaints
- objective review sources worth trusting
- the tradeoff axes that matter for this category

Then produce a short Socratic preference interview. The interview should be based on what the initial scan reveals, not generic consumer-product questions.

The interview should help clarify:

- primary job-to-be-done
- secondary jobs and nice-to-haves
- explicit non-goals
- must-not-fail constraints
- privacy/security constraints
- workflow/export needs
- form-factor tolerance
- price/subscription tolerance
- quality threshold and failure tolerance
- ecosystem/API/webhook needs
- contexts of use
- substitution tradeoffs against tools already owned

For an on-person AI recorder category, example questions include:

1. Are you optimizing mainly for in-person meetings, walks, voice notes, phone calls, or always-on memory?
2. What is the worst failure mode: missed recording, bad transcript, awkward form factor, privacy exposure, subscription lock-in, or poor export?
3. Is visible recording acceptable, or does the form factor need to be discreet?
4. Do you need raw audio export, transcript export, summary export, API/webhook sync, or all of these?
5. Is cloud transcription acceptable, or is local/private processing a hard constraint?
6. Would you rather have the best dedicated hardware, or a software workflow that uses devices you already carry?
7. Are phone calls a primary use case, or only a possible bonus?
8. How much subscription cost is acceptable if reliability and workflow quality are materially better?
9. Do you need recordings to move into Notion, Google Drive, a CRM, a knowledge base, or a custom webhook?
10. What kinds of environments matter most: conference rooms, coffee shops, outdoor walks, cars, or noisy events?

### Stage 2 — Evidence-led ranking and decision brief

After preferences are known, rank products by fit. The ranking must be based on explicit weighting, not vibe.

For every top candidate, capture:

- product name and category type
- primary use case fit
- pricing and subscription model
- recording hardware / capture method
- transcription and summarization capabilities
- export/API/webhook/workflow options
- privacy and data handling posture
- battery/storage constraints where applicable
- app ecosystem and platform support
- independent review signals
- recurring complaints
- objective or measurable evidence
- confidence level
- recommended disposition: `buy`, `trial`, `watch`, `avoid`, or `not-enough-evidence`

## Evidence source taxonomy

Prefer sources in roughly this order, while preserving source diversity:

1. Hands-on professional reviews with stated testing methods.
2. Customer reviews from retailer/app-store/SaaS marketplaces with volume and recency.
3. Forum/community reports with concrete failure details, especially Reddit, Hacker News, creator forums, productivity communities, and domain-specific forums.
4. Independent comparison articles that explain methodology.
5. Product documentation, support docs, API docs, pricing pages, privacy policies, and changelogs.
6. Founder/company announcements only for roadmap, availability, and policy claims.
7. Social discourse only as weak signal unless it contains concrete first-hand usage evidence.

Do not treat affiliate listicles as strong evidence unless their testing method is explicit. If affiliate or SEO content is used, label it as weak and corroborate elsewhere.

## Source policy

This mode is external-review-first. It can use ordinary web search, Exa, X/public discourse, product pages, support docs, API docs, reviews, app-store listings, marketplace reviews, and public forums.

Compared with `investor-diligence`, the source policy is intentionally less restrictive:

- Broad public product/category research is allowed.
- Internal workspace search is not used by default.
- Prior internal notes may be used only when the owner provides them explicitly via `--source` or authorizes local scan.
- Private app integrations are allowed only when directly relevant and explicitly authorized for the run.
- Outbound messages, purchases, signups, or account changes are never allowed without explicit owner approval.

## Ranking model

The final ranking should expose weights. Default criteria:

| Criterion | Default weight | Notes |
|---|---:|---|
| Reliability / capture success | 25% | Does it consistently capture the needed audio/event? |
| Output quality | 20% | Transcript accuracy, summary quality, speaker handling, searchability. |
| Workflow/export/API fit | 20% | Can the owner get data into the rest of their system? |
| Use-case fit / form factor | 15% | Does the product fit actual contexts of use? |
| Privacy/control | 10% | Cloud/local posture, retention, permissions, policy clarity. |
| Cost / lock-in | 10% | Hardware cost, subscription, cancellation/export friction. |

Change these weights when the Socratic interview reveals different priorities. State the final weights and why they changed.

## Recommended dossier structure

Recommended `standard` output:

1. Bottom line recommendation
2. Preference profile and assumptions
3. Socratic interview answers or unresolved questions
4. Category map and product archetypes
5. Candidate shortlist
6. Ranking criteria and weights
7. Ranked product table
8. Product deep dives
9. Objective review evidence and source quality notes
10. Common complaints / failure modes
11. Privacy, subscription, and lock-in analysis
12. Workflow/API/export analysis
13. Decision recommendation: buy / trial / watch / avoid
14. Next test plan
15. Source scope / tool provenance

## Persona-assisted explanation

The mode may use persona lenses for explanation, not for uncited claims.

Useful lenses:

- Teacher lens: explain unfamiliar product-category concepts and tradeoffs plainly.
- Builder lens: inspect API/export/workflow feasibility.
- Debugger lens: stress-test failure modes and reliability claims.
- Strategist lens: make the final decision recommendation and opportunity-cost tradeoffs.

When persona lenses are used, label them as interpretive help and keep factual claims tied to sources.

## Example preference profile — AI recorder category

For an in-person recorder run where the owner says they want meetings, walks, voice notes, and API/webhook export while avoiding always-on memory, encode the preference frame as:

- Primary job: reliable in-person capture for meetings and walks.
- Secondary job: voice notes that can move into other systems.
- Non-goal: always-on memory / lifelogging as the main category.
- Acceptable: visible recording, cloud transcription, subscription if cheap or clearly justified.
- Strong preference: raw audio/transcript export and API/webhook/workflow integration.
- Worst failure mode: missed recording.
- Next-worst failure mode: poor transcription accuracy.
- Call capture: interesting bonus, not worth compromising the core in-person capture use case.

This profile should change the ranking weights toward reliability, transcription quality, and workflow/export rather than novelty or always-on features.
