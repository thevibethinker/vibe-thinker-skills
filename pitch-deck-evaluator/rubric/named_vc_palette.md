---
created: 2026-05-24
last_edited: 2026-05-24
version: 1.0
provenance: public-skill-export
---

# Named-VC POV Palette for Pre-seed Deck Evaluation

## Anti-cosplay disclaimer

This palette is a **simulation of publicly stated investor POVs**, not a claim to know how any named person would evaluate a specific deck, founder, or company. Real investors blend frames, change their mind with context, and make decisions through relationships, fund constraints, partner dynamics, timing, and portfolio construction. The skill should therefore render each named lens as: "Based on public writing/interviews, this lens would likely emphasize..." It must never say: "Investor X would invest/pass."

Named POVs are useful because they make evaluation less generic. A founder can ask, "Read this as if a warm founder-first pre-seed investor were skimming it," or "Read this as if a marketplace angel were doing two-call diligence." The value is contrast, not impersonation.

## Inclusion and confidence policy

Default palette entries must meet all three bars:

1. **Source bar:** at least 3 direct/primary or direct-profile sources from D1.1/D1.2.
2. **Confidence bar:** confidence `med` or `high` in the source artifact; all default entries below are `high` unless explicitly marked `med`.
3. **Distinctness bar:** opting into the lens should change the read. Near-duplicate "founder-first, sector-agnostic" POVs were excluded even when source quality was strong.

Low-confidence named lenses, if later added, should live behind an `experimental_opt_in` flag and be clearly labeled. No low-confidence lens is included in the default palette here.

## D2.2 frame mapping note

At D2.3 execution time, `synthesis/frame_matrix.md` and `deposits/D2.2.json` had not landed. Frame mappings below therefore use the D2.2 brief's frame definitions:

- **F1 — Warm Believer:** grants many assumptions because thesis, relationship, or exceptional founder signal pre-loads belief.
- **F2 — Curious Skeptic:** open to being convinced; grants that the market/problem may exist but interrogates insight and execution.
- **F3 — Cold Partner Read:** zero prior context; grants little; deck must earn attention quickly.
- **F4 — Hostile Diligence:** actively searches for reasons to pass; pounces on unsupported claims, weak proof, and hidden risks.

When D2.2 lands, orchestrator should reconcile labels if the final frame definitions materially differ.

## Palette overview

| # | Default lens | Confidence | Dominant frame | Primary stage / sector diversity | Why it is distinct |
|---:|---|---|---|---|---|
| 1 | Hustle Fund / Elizabeth Yin + Eric Bahn lens | high | F2 | Generalist pre-seed | Warm founder-first read with concrete deck mechanics and pre-seed traction nuance |
| 2 | Pear VC / Pejman Nozad + Mar Hershenson lens | high | F2 | Pre-seed/seed, company-building | Story iteration, customer knowledge, bottom-up market rigor |
| 3 | NFX / James Currier + Gigi Levy-Weiss lens | high | F2 | Network effects, marketplaces, software platforms | Timing, defensibility, one-sentence essence, proof ladder |
| 4 | Floodgate / Mike Maples Jr. + Ann Miura-Ko lens | high | F2 | Breakthrough seed, pattern-breakers | Breakthrough insight and superthinker/superbuilder posture |
| 5 | Bloomberg Beta / Roy Bahat lens | high | F3 | Future of work, AI, founder-as-customer | Demo-over-deck, open manual, concise proof of extraordinary potential |
| 6 | Precursor Ventures / Charles Hudson lens | high | F2 | Broad pre-seed, underrepresented/early founders | People-over-product plus retellable story discipline |
| 7 | Boost VC / Adam Draper lens | high | F1 | Frontier, sci-fi-to-reality | Grants weirdness; interrogates forcing function and cockroach founder resilience |
| 8 | Designer Fund / Ben Blumenrose + Enrique Allen lens | high | F2 | Design-led health, climate, prosperity | Design as durable advantage plus investor-return translation |
| 9 | 2048 Ventures / Alex Iskold lens | high | F3 | Vertical AI, Deep Tech, Health, Bio; NYC/Boston | Standardized pre-seed intake, founder-market fit, fast-track fit |
| 10 | K9 Ventures / Manu Kumar lens | high | F2 | Technical pre-seed, capital-efficient software/hardware | True pre-seed stage purity; no traction required if technical basis is real |
| 11 | Naval Ravikant lens | high | F1 | Angel, broad technology/networked systems | High-concept clarity and one exceptional dimension over deck completeness |
| 12 | Jason Calacanis lens | high | F3 | Angel, broad startups, product-in-market | Blunt traction/craft/founder-tenacity read with concise answers |
| 13 | Sahil Lavingia lens | high | F2 | Angel, creator economy/software/outside-SV | Technical taste, "teach me" outreach, VC-scale skepticism |
| 14 | Elad Gil lens | high | F3 | Angel/operator, broad high-growth technology | Fundraising-process quality and investor-fit discipline |
| 15 | Fabrice Grinda / FJ Labs lens | high | F4 | Marketplaces/network effects, global | Fast marketplace diligence, price discipline, unit economics |

---

## 1. Hustle Fund / Elizabeth Yin + Eric Bahn lens

**Source confidence:** high.

**Anti-cosplay reinforcement:** This lens simulates Hustle Fund's public founder guidance and partner-authored deck/traction content. It does not predict how Elizabeth Yin, Eric Bahn, or any Hustle Fund partner would decide on a live deal.

### What this POV grants

- True pre-seed companies may be pre-revenue, pre-customer, or pre-PMF; a prototype, MVP, or Figma can still support a serious read. [HF-1]
- A short deck can be enough: the canonical Hustle guidance reduces the pre-seed deck to team, problem, solution, market, and traction. [HF-1]
- The team slide can carry unusual weight when other proof is not yet available. [HF-1]
- Traction can mean customer discovery quality, pre-sales, waitlists with relationship depth, and experimentation velocity rather than only revenue. [HF-3]
- Warmth toward founders is compatible with practical specificity; the lens grants early chaos but not lazy communication. [HF-1][HF-2]

### What this POV interrogates

- Whether the founding team has relevant skills, problem-fit, and a credible prior working relationship. [HF-1]
- Whether the founder has actually talked to customers and learned something specific. [HF-3]
- Whether traction signals are meaningful or just vanity waitlist/landing-page numbers. [HF-3]
- Whether the market can plausibly support a 100x outcome, not merely a nice small business. [HF-1]
- Whether slide titles communicate claims in full sentences so a skimmer can understand 80% of the story. [HF-2]

### Signature heuristics

- **Five-slide pre-seed deck:** team, problem, solution, market, traction. [HF-1]
- **Full-sentence slide titles:** every title should make a claim, not label a section. [HF-2]
- **Pre-seed traction as operating behavior:** customer discovery and fast experiments count. [HF-3]
- **Founder grit with evidence:** not generic hustle rhetoric; proof of learning loops. [HF-3]

### Frame mapping

**Dominant posture: F2 — Curious Skeptic.** The lens wants to believe in early founders and grants pre-seed incompleteness, but it interrogates founder relevance, customer learning, and market logic with practical specificity. If the deck opens with concrete discovery and clear claim-titles, it can feel F1-warm; if it hides behind generic labels, it quickly becomes F3.

### Output style note

Warm, founder-friendly, and specific. Feedback should sound like a practical pre-seed coach: "You probably do not need 30 slides; show me the five claims that prove you are learning faster than others."

### Sources

[HF-1], [HF-2], [HF-3]

---

## 2. Pear VC / Pejman Nozad + Mar Hershenson lens

**Source confidence:** high.

**Anti-cosplay reinforcement:** This lens simulates Pear's public fundraising and market-sizing guidance plus partner-level founder-first posture. It is not a prediction of Pejman Nozad, Mar Hershenson, or Pear's investment decision.

### What this POV grants

- Early fundraising stories start rough and can improve through many iterations. [Pear-1][Pear-2]
- Pre-seed founders may need help shaping the narrative before institutional rounds. [Pear-2]
- Rough market estimates are acceptable if assumptions are visible and bottom-up. [Pear-3]
- Founder-first evaluation can give early teams room to learn if customer and market knowledge are deepening. [Pear-1][Pear-2]
- A deck can be treated as a company-building artifact, not only a transaction document. [Pear-2]

### What this POV interrogates

- Whether the founder knows the customer with enough specificity to anchor the story. [Pear-1]
- Whether market sizing is bottom-up and assumption-driven, not top-down TAM theater. [Pear-3]
- Whether the team is the right team to build this company now. [Pear-1]
- Whether the founder understands risks and can answer investor questions. [Pear-1][Pear-2]
- Whether the story is venture-scale and can survive repeated iteration. [Pear-2][Pear-3]

### Signature heuristics

- **Ultimate pitch deck questions:** customer knowledge, market knowledge, right team, getting things done, risk awareness. [Pear-1]
- **30+ story iterations:** PearX's fundraising support treats story refinement as a core pre-seed process. [Pear-2]
- **Bottom-up market sizing:** explicit unit assumptions beat broad industry numbers. [Pear-3]
- **Investor-question readiness:** anticipate objections before the meeting. [Pear-1][Pear-2]

### Frame mapping

**Dominant posture: F2 — Curious Skeptic.** Pear grants that a pre-seed story is not finished, but it tests the founder's ability to learn, size the market, and answer risk. A polished but assumption-thin TAM slide can flip this lens toward F4 skepticism on market quality.

### Output style note

Constructive and iterative, like a fundraising partner pushing the founder through another story draft. Feedback should name specific questions the deck must answer before a credible investor meeting.

### Sources

[Pear-1], [Pear-2], [Pear-3]

---

## 3. NFX / James Currier + Gigi Levy-Weiss lens

**Source confidence:** high.

**Anti-cosplay reinforcement:** This lens simulates NFX's public seed/pre-seed content, especially around pitch-deck structure, timing, defensibility, and network effects. It does not predict any NFX partner's live decision.

### What this POV grants

- An idea can be very early if the team, market, and timing are unusually compelling. [NFX-2][NFX-3]
- A founder can apply through lighter-weight artifacts such as deck, video, and brief answers in fast pre-seed contexts. [NFX-3]
- Business models may evolve as network effects and scale dynamics emerge. [NFX-1][NFX-4]
- Internal KPIs can matter more than generic traction metrics when they reveal network-effect formation. [NFX-1]
- A short one-sentence essence can carry a large amount of evaluative value. [NFX-1]

### What this POV interrogates

- Whether the company can be captured in one precise sentence. [NFX-1]
- Whether market timing explains why this can happen now, not someday. [NFX-1][NFX-4]
- Whether defensibility is real: network effects, proprietary tech/data, speed, or compounding advantages. [NFX-1][NFX-2]
- Whether traction is on a ladder of proof rather than a pile of unconnected metrics. [NFX-1]
- Whether the company fits NFX's seed/pre-seed platform and category logic. [NFX-2][NFX-3]

### Signature heuristics

- **One-sentence company essence:** compress the company without losing the wedge. [NFX-1]
- **Four slides every deck must have / six things VCs need:** a minimum evidence spine. [NFX-1]
- **Ladder of proof:** each proof point should advance conviction, not merely decorate. [NFX-1]
- **Network-effects defensibility:** evaluate how the product gets stronger as usage grows. [NFX-1][NFX-2]

### Frame mapping

**Dominant posture: F2 — Curious Skeptic.** NFX is thesis-friendly when the company fits network-effect/software-platform logic, but it interrogates timing, proof sequence, and defensibility. For non-network-effect companies, the same lens can become F3 quickly.

### Output style note

Strategic, compressed, and systems-oriented. Feedback should ask for the smallest sentence, proof ladder, and defensibility mechanism that make the company legible.

### Sources

[NFX-1], [NFX-2], [NFX-3], [NFX-4]

---

## 4. Floodgate / Mike Maples Jr. + Ann Miura-Ko lens

**Source confidence:** high.

**Anti-cosplay reinforcement:** This lens simulates Floodgate's public language around breakthrough founders, pattern-breakers, superthinkers, and superbuilders. It is not a claim to know how Mike Maples Jr., Ann Miura-Ko, or Floodgate would respond to a specific company.

### What this POV grants

- The product concept may evolve dramatically; the founder's breakthrough insight and builder quality can be more durable than the initial shape. [Floodgate-1]
- A founder can be a "prime mover" before the rest of the market recognizes the category. [Floodgate-2][Floodgate-3]
- Early uncertainty is acceptable if the founder is truth-seeking and fast-learning. [Floodgate-1]
- Pattern-breaking companies may not fit neat existing market maps. [Floodgate-3][Floodgate-4]
- A founding pair can be evaluated as a superthinker/superbuilder system rather than a résumé checklist. [Floodgate-1]

### What this POV interrogates

- Whether there is a real breakthrough insight, not just a clever feature. [Floodgate-1]
- Whether the founder can reframe the market and name the new pattern. [Floodgate-2][Floodgate-3]
- Whether the builder side can execute with velocity and joy. [Floodgate-1]
- Whether the team seeks contradictory evidence rather than defending sunk-cost prototypes. [Floodgate-1]
- Whether value accrues to this company if the insight proves true. [Floodgate-1][Floodgate-4]

### Signature heuristics

- **Breakthrough insight:** the non-obvious truth that makes the company possible. [Floodgate-1]
- **Superthinker + superbuilder:** complementary founder cognition and execution. [Floodgate-1]
- **Prime mover / pattern breaker:** founder as category reframer. [Floodgate-2][Floodgate-3]
- **First true believer:** the seed investor's role in underwriting an emergent category. [Floodgate-4]

### Frame mapping

**Dominant posture: F2 — Curious Skeptic.** Floodgate grants early category ambiguity, but the insight bar is high. A deck with a genuine "I had not thought of it this way" reframing can flip this lens toward F1; a conventional category story can fall to F3/F4.

### Output style note

High-conviction and pattern-seeking. Feedback should push for the breakthrough sentence: "What must be true that almost no one else yet believes?"

### Sources

[Floodgate-1], [Floodgate-2], [Floodgate-3], [Floodgate-4]

---

## 5. Bloomberg Beta / Roy Bahat lens

**Source confidence:** high.

**Anti-cosplay reinforcement:** This lens simulates Bloomberg Beta's open operating manual and Roy Bahat's public deck-evaluation posture. It does not predict Bloomberg Beta's actual investment decision.

### What this POV grants

- A deck is not always required; in a meaningful share of portfolio investments, Bloomberg Beta did not see a deck before investing. [BB-1][BB-4]
- A demo can be dramatically more useful than slides. [BB-1][BB-4]
- Day-zero milestones may be weak if they look more than a couple months out. [BB-2]
- The company can be early if there is one reason to believe it could become extraordinary. [BB-2]
- The founder's thinking, communication, and meeting-worthiness can matter more than template completeness. [BB-1][BB-2]

### What this POV interrogates

- What has been proven and what must be proven next. [BB-2]
- Who the first customers are and why they are the right ones. [BB-2]
- Whether the product is loved or meaningfully useful, not merely explained. [BB-2][BB-4]
- How quickly money will be spent and what will be true after half the round is spent. [BB-2]
- What harms could occur if the product succeeds. [BB-2]

### Signature heuristics

- **Demo is 50x more useful than slides:** show, don't just narrate. [BB-1][BB-4]
- **One reason to believe:** a single extraordinary proof point can matter more than many average ones. [BB-2]
- **What must be proven next:** milestones as near-term experiments. [BB-2]
- **Open manual discipline:** decision criteria are explicit enough to audit. [BB-1][BB-2]

### Frame mapping

**Dominant posture: F3 — Cold Partner Read.** The lens grants little to deck polish and quickly asks whether the artifact shows real product/customer truth. It is not hostile by default, but it has low patience for long, slide-heavy explanations without proof.

### Output style note

Transparent, concise, and almost checklist-like. Feedback should sound like an open operating manual: "Show the demo, the one metric, the first customers, and the next proof point."

### Sources

[BB-1], [BB-2], [BB-3], [BB-4]

---

## 6. Precursor Ventures / Charles Hudson lens

**Source confidence:** high.

**Anti-cosplay reinforcement:** This lens simulates Precursor's public people-over-product posture and Charles Hudson's public deck/story guidance. It does not predict Charles Hudson's actual response to a live pitch.

### What this POV grants

- Very early companies may lack product, market demand, or complete traction. [Precursor-1][Precursor-3]
- At the earliest stage, people can matter more than product. [Precursor-3][Precursor-4]
- Facts and data are necessary but not sufficient; the story can still be the core artifact. [Precursor-1]
- Consumer pitches can start from a new human-psychology insight. [Precursor-3]
- The founder's expertise in the problem can substitute for some absent company proof. [Precursor-1][Precursor-3]

### What this POV interrogates

- Whether the deck tells a coherent and exciting future story. [Precursor-1]
- Whether the story is simple enough for an investor to retell later. [Precursor-1]
- Why the founder has become expert in this problem. [Precursor-1][Precursor-3]
- Whether product and business model actually fit each other. [Precursor-3]
- Whether the founder is forcing a desired business model onto a product that wants to be something else. [Precursor-3]

### Signature heuristics

- **People over product:** underwrite founder quality before the product is complete. [Precursor-3][Precursor-4]
- **Retellability test:** can the investor explain the company a week later? [Precursor-1]
- **Consumer psychology insight:** for consumer, the founder needs a new behavioral truth. [Precursor-3]
- **Product/business-model fit:** the company is what the product can sustain, not what the deck wishes. [Precursor-3]

### Frame mapping

**Dominant posture: F2 — Curious Skeptic.** Precursor grants early uncertainty and founder primacy, but story coherence is non-negotiable. A deck with all facts but no retellable story fails this lens.

### Output style note

Direct but founder-respectful. Feedback should ask: "What is the simple future story, and why are you the person who sees it?"

### Sources

[Precursor-1], [Precursor-2], [Precursor-3], [Precursor-4]

---

## 7. Boost VC / Adam Draper lens

**Source confidence:** high.

**Anti-cosplay reinforcement:** This lens simulates Boost VC's public frontier/pre-seed thesis and Adam Draper's public "sci-fi to reality" language. It does not predict Boost VC's or Adam Draper's live investment behavior.

### What this POV grants

- Weird, frontier, and initially sci-fi-sounding ideas are in scope. [Boost-1][Boost-4]
- Technical, social, or regulatory changes can make a category suddenly plausible. [Boost-1][Boost-4]
- Early pre-seed companies can still be fundable with a huge vision and credible forcing function. [Boost-1][Boost-2]
- Founder authenticity, energy, and movement can matter before standard traction. [Boost-2]
- Resourceful "cockroach" founders can be attractive even when conditions are harsh. [Boost-3]

### What this POV interrogates

- Why this is the right team to make the future real. [Boost-1][Boost-2]
- Why now: what changed that moves the idea from impossible to inevitable. [Boost-1][Boost-4]
- Whether the vision is genuinely massive or merely odd. [Boost-1]
- Whether founders show resilience and ability to survive constraints. [Boost-2][Boost-3]
- Whether the founder has enough technical or movement-building credibility for the frontier category. [Boost-1][Boost-2]

### Signature heuristics

- **Make sci-fi a reality:** the idea should feel like a future category arriving early. [Boost-1][Boost-4]
- **Why now forcing function:** technical/social/regulatory pressure must be named. [Boost-1]
- **Cockroach founder:** survives, adapts, and keeps moving. [Boost-3]
- **Big vision with founder energy:** ambition must be embodied by the team. [Boost-2]

### Frame mapping

**Dominant posture: F1 — Warm Believer.** For thesis-fit frontier companies, this lens grants weirdness and early incompleteness more than most default rubrics. It becomes F4 only when the weirdness is cosmetic, the forcing function is missing, or the founder cannot credibly build.

### Output style note

Energetic, future-facing, and founder-momentum-oriented. Feedback should distinguish "weird because it reveals the future" from "weird because the deck lacks discipline."

### Sources

[Boost-1], [Boost-2], [Boost-3], [Boost-4]

---

## 8. Designer Fund / Ben Blumenrose + Enrique Allen lens

**Source confidence:** high.

**Anti-cosplay reinforcement:** This lens simulates Designer Fund's public pitch-deck and fundraising guidance. It does not predict how Ben Blumenrose, Enrique Allen, or Designer Fund would evaluate a specific company.

### What this POV grants

- Design can be a durable company-building advantage, not just surface polish. [DF-1][DF-2]
- Pre-seed decks do not need 30 pages or a full data room. [DF-3]
- Mission-driven founders can be compelling if mission translates into investor-return logic. [DF-1]
- A deck can center on 2-3 core strengths rather than treating every canonical slide equally. [DF-1]
- Health, climate, prosperity, and other mission-heavy categories can fit if the product is meaningfully better and venture-scale. [DF-2]

### What this POV interrogates

- Whether the problem is hair-on-fire, not a vitamin. [DF-1]
- Whether the product is 10x better and the user experience gap is real. [DF-2]
- Whether the founder translates mission into credible 50x-100x investor-return potential. [DF-1]
- Whether each slide has one idea and a strong headline. [DF-1]
- Whether predictable investor questions are anticipated in the core story or appendix. [DF-1][DF-3]

### Signature heuristics

- **Design as durable advantage:** superior product/user experience as strategy. [DF-2]
- **2-3 core strengths:** center the deck on what is actually strongest. [DF-1]
- **50x-100x return translation:** mission must map to fund math. [DF-1]
- **One idea per slide:** clarity and visual hierarchy are part of substance. [DF-1]

### Frame mapping

**Dominant posture: F2 — Curious Skeptic.** Designer Fund grants mission/design strength but scrutinizes venture-scale translation. A beautiful mission-only deck without fund-return logic can flip negative quickly.

### Output style note

Design-literate, constructive, and precise. Feedback should treat visual structure as strategic communication, not decoration.

### Sources

[DF-1], [DF-2], [DF-3]

---

## 9. 2048 Ventures / Alex Iskold lens

**Source confidence:** high.

**Anti-cosplay reinforcement:** This lens simulates 2048 Ventures' public pre-seed fast-track and cold-pitch intake guidance. It does not predict Alex Iskold's or 2048's live decision.

### What this POV grants

- Pre-seed companies can raise quickly when the company fits the fast-track stage and thesis. [2048-1]
- Solo founders may be considered if founder-market fit is strong, though complete teams are preferred. [2048-1]
- Founder talent and founder-market fit can precede mature traction. [2048-1]
- Standardized pitch inputs make fair comparison possible. [2048-2]
- Thesis-fit in Vertical AI, Deep Tech, Health, Bio, NYC/Boston, or related areas can increase initial receptivity. [2048-1][2048-3]

### What this POV interrogates

- Whether the company is actually in the fast-track stage: first round, target raise size, and capital need. [2048-1]
- Whether founder-market fit and vision/drive are clear. [2048-1]
- Whether the pitch package includes company description, vision, team LinkedIns, deck, founder video, and optional product video. [2048-2]
- Whether the founder has an irrational desire to do something difficult. [2048-1]
- Whether category fit is real rather than opportunistic keyword matching. [2048-1][2048-3]

### Signature heuristics

- **Pre-Seed Fast Track:** $250K-$750K check, $500K-$1.5M target round, quick decision when fit is clear. [2048-1]
- **Founder talent + founder-market fit:** earliest-stage standard. [2048-1]
- **Standardized cold-pitch packet:** deck plus founder/video context to compare consistently. [2048-2]
- **Irrational desire to do something impossible:** motivation as signal. [2048-1]

### Frame mapping

**Dominant posture: F3 — Cold Partner Read.** The lens is not hostile, but it standardizes inputs and grants little to incomplete packaging. A deck can earn F2 quickly if the founder-market fit and category thesis are obvious.

### Output style note

Structured, intake-oriented, and no-BS. Feedback should identify missing packet elements and whether the company fits the explicit fast-track aperture.

### Sources

[2048-1], [2048-2], [2048-3], [2048-4]

---

## 10. K9 Ventures / Manu Kumar lens

**Source confidence:** high.

**Anti-cosplay reinforcement:** This lens simulates Manu Kumar's public K9 Ventures investment criteria and pre-seed FAQ. It does not predict Manu Kumar's actual decision on a live deck.

### What this POV grants

- True pre-seed companies do not need traction. [K9-2]
- They also do not need a fully built product or unit economics at this stage. [K9-2]
- A prototype or well-fleshed-out deck can be sufficient evidence. [K9-2]
- Technical founders and new technology/new market can carry the early case. [K9-1]
- Capital efficiency and direct revenue orientation can matter before scale. [K9-1][K9-2]

### What this POV interrogates

- Whether founders are technical enough to build the core technology. [K9-1]
- Whether the company involves new technology or a new market rather than a me-too business. [K9-1]
- Whether direct customer revenue is plausible. [K9-1]
- Whether the company can be capital-efficient and avoid overcapitalization. [K9-1][K9-2]
- Whether core technology is outsourced or owned by the founding team. [K9-1]

### Signature heuristics

- **Necessary but not sufficient filters:** technical founder, technical product/new tech, direct revenue, capital efficiency. [K9-1]
- **No traction required at true pre-seed:** stage discipline as a guardrail. [K9-2]
- **Prototype or well-fleshed-out deck:** enough to begin evaluation. [K9-2]
- **Avoid overcapitalization:** raise enough to reach the next proof point. [K9-2][K9-3]

### Frame mapping

**Dominant posture: F2 — Curious Skeptic.** K9 is generous on missing traction but strict on technical founder/product criteria. It is especially useful when the default rubric risks asking pre-seed companies for seed/Series A proof.

### Output style note

Technical, stage-disciplined, and capital-efficient. Feedback should say when a deck is being unfairly penalized for missing later-stage metrics, while still demanding real technical/product substance.

### Sources

[K9-1], [K9-2], [K9-3]

---

## 11. Naval Ravikant lens

**Source confidence:** high.

**Anti-cosplay reinforcement:** This lens simulates Naval Ravikant's public Venture Hacks/AngelList/Spearhead style guidance around angel evaluation, high-concept pitches, prototypes, and exceptionality. It does not predict Naval's personal investment decision.

### What this POV grants

- A company can be incomplete if it is exceptional in one dimension: traction, team, product, social proof, or pitch. [Naval-2][Naval-3]
- A concise high-concept pitch can matter more than a complete business plan. [Naval-2]
- Imperfect decks are acceptable when a prototype, demo, or customer contact is available. [Naval-2][Naval-3]
- Angels can act as patrons/advisors rather than control-seeking institutions. [Naval-1]
- Fast noes are fairer than dragging founders through weeks of diligence. [Naval-1]

### What this POV interrogates

- Whether the company can be compressed into a spreadable high-concept sentence. [Naval-2]
- Whether the founder has made something when making something should be easy. [Naval-2][Naval-3]
- Whether the outcome can be large enough to attract downstream financing. [Naval-1][Naval-2]
- Whether the team/product/traction/social proof is exceptional rather than merely acceptable. [Naval-3][Naval-4]
- Whether the angel would want to work with the founder over time. [Naval-1]

### Signature heuristics

- **High-concept pitch:** easy-to-transmit compression. [Naval-2]
- **Exceptional in at least one regard:** one spike can beat average completeness. [Naval-3][Naval-4]
- **Best no is before the meeting:** fast filtering as founder-respecting behavior. [Naval-1]
- **Prototype before paperwork:** show making/customer contact when possible. [Naval-2][Naval-3]

### Frame mapping

**Dominant posture: F1 — Warm Believer with an exceptionality gate.** This lens grants incompleteness when one signal is unusually strong, but it quickly rejects average companies that require long explanation.

### Output style note

Parsimonious and sharp. Feedback should compress: "What is the high-concept sentence, and what one thing is undeniably exceptional?"

### Sources

[Naval-1], [Naval-2], [Naval-3], [Naval-4], [Naval-5]

---

## 12. Jason Calacanis lens

**Source confidence:** high.

**Anti-cosplay reinforcement:** This lens simulates Jason Calacanis's public Angel University, interview, and question-family guidance. It does not predict his personal investment decision.

### What this POV grants

- First-time founders can be investable if they have launched, learned, and show evidence of momentum. [Calacanis-2][Calacanis-3]
- Angels may want helpfulness/status as well as returns, so cap-table pull matters. [Calacanis-2][Calacanis-5]
- Small early syndicate checks can be rational before institutional rounds. [Calacanis-3][Calacanis-5]
- Product-in-market evidence can outweigh perfect fundraising theater. [Calacanis-3][Calacanis-4]
- Monthly investor updates can build trust before a check. [Calacanis-3]

### What this POV interrogates

- Whether the founder can build a team that builds a product users love. [Calacanis-1][Calacanis-2]
- Why now, why this business, why this founder, and what unfair advantage exists. [Calacanis-1]
- Whether customer knowledge and references are specific. [Calacanis-1][Calacanis-3]
- Whether growth charts or product usage show real market contact. [Calacanis-3][Calacanis-4]
- Whether answers are concise and tactical rather than evasive. [Calacanis-1]

### Signature heuristics

- **Goldilocks zone:** pre-Series-A startups with enough product/market signal for angel risk. [Calacanis-3][Calacanis-5]
- **Four question families:** founder/business, commitment, chance of succeeding, investor-return outcome. [Calacanis-1]
- **Monthly update discipline:** trust through repeated progress. [Calacanis-3]
- **Quick questions:** concise answers reveal founder command. [Calacanis-1]

### Frame mapping

**Dominant posture: F3 — Cold Partner Read.** The lens is not inherently hostile, but it is blunt and impatient with vague answers, side-hustle energy, and no product contact. Strong product/customer evidence can warm it to F2.

### Output style note

Blunt, tactical, and founder-accountability-heavy. Feedback should be direct: "Answer the question in one sentence; show the chart; stop hiding behind TAM."

### Sources

[Calacanis-1], [Calacanis-2], [Calacanis-3], [Calacanis-4], [Calacanis-5]

---

## 13. Sahil Lavingia lens

**Source confidence:** high.

**Anti-cosplay reinforcement:** This lens simulates Sahil Lavingia's public founder-investor posture around rolling funds, technical founders, direct-to-community capital, and outreach that teaches. It does not predict his personal investment decision.

### What this POV grants

- Pre-revenue versus post-revenue is not automatically gating. [Sahil-1][Sahil-2]
- Cold outreach can be taken seriously if it teaches something. [Sahil-1]
- Outside-Silicon-Valley founders can be credible first checks. [Sahil-1][Sahil-2]
- Good money can be benign and non-intrusive rather than high-control. [Sahil-2]
- Technical founders solving hard problems elegantly can overcome missing polish. [Sahil-1][Sahil-4]

### What this POV interrogates

- Whether the founder is technical or technically capable enough to build. [Sahil-1][Sahil-4]
- Whether the email/deck teaches why this problem matters. [Sahil-1]
- Why now, why you, and why the product has not already been built. [Sahil-1][Sahil-3]
- Whether the business is actually VC-scale or better suited to alternative funding. [Sahil-5]
- Whether the founder learned something rather than merely assembled a deck. [Sahil-1][Sahil-4]

### Signature heuristics

- **Teach me:** outreach should improve the investor's understanding. [Sahil-1]
- **Things I feel proud talking about:** personal conviction and taste as angel filter. [Sahil-2]
- **Founder empathy:** founders want founders on the cap table. [Sahil-2]
- **VC-scale skepticism:** do not force venture money onto non-venture businesses. [Sahil-5]

### Frame mapping

**Dominant posture: F2 — Curious Skeptic.** Sahil grants early and nontraditional founders but interrogates technical taste, founder learning, and scale/funding fit. It is especially useful as a counterweight to generic VC-scale theater.

### Output style note

Plainspoken, founder-to-founder, and taste-driven. Feedback should ask what the deck teaches and whether the company is trying to be VC-shaped for the wrong reasons.

### Sources

[Sahil-1], [Sahil-2], [Sahil-3], [Sahil-4], [Sahil-5]

---

## 14. Elad Gil lens

**Source confidence:** high.

**Anti-cosplay reinforcement:** This lens simulates Elad Gil's public seed-fundraising mechanics and operator-investor guidance. It does not predict his personal investment decision.

### What this POV grants

- Seed and angel rounds are fragmented and messy compared with later institutional rounds. [Elad-1]
- SAFEs and light-process angel rounds can be normal at seed. [Elad-1]
- Angels can be useful pitch-practice and advisor surfaces before top-priority investors. [Elad-2]
- A raise can reasonably take 2-3 months except for unusually hot outliers. [Elad-3]
- The right investor/partner can matter more than brand or valuation optimization. [Elad-1][Elad-2]

### What this POV interrogates

- Whether the fundraising process is deliberately compressed and sequenced. [Elad-2][Elad-3]
- Whether founders are targeting the right investors and partners. [Elad-1][Elad-2]
- Whether the pitch is improving through practice like a product. [Elad-2]
- Whether founders are over-optimizing headline valuation or brand. [Elad-1]
- Whether follow-up requests indicate real signal or weak investor interest. [Elad-2]

### Signature heuristics

- **Angel market is highly fragmented:** manage it differently from VC partnership processes. [Elad-1]
- **Fundraising takes about three months:** plan cadence and runway accordingly. [Elad-3]
- **Practice meetings:** iterate before priority investors. [Elad-2]
- **Pitch as product:** feedback loop, targeting, and sequencing matter. [Elad-2]

### Frame mapping

**Dominant posture: F3 — Cold Partner Read.** Elad's lens is less about deck slide taste and more about process readiness. It grants seed-stage messiness, but a sloppy or unfocused raise reads as a founder-process failure.

### Output style note

Operator-like, structured, and process-aware. Feedback should say not just "this slide is weak," but "this deck is not yet ready for your priority investor sequence."

### Sources

[Elad-1], [Elad-2], [Elad-3]

---

## 15. Fabrice Grinda / FJ Labs lens

**Source confidence:** high.

**Anti-cosplay reinforcement:** This lens simulates Fabrice Grinda's public marketplace and FJ Labs evaluation posture. It does not predict Fabrice Grinda's or FJ Labs' actual live decision.

### What this POV grants

- Marketplace investing can operate at high volume with imperfect information. [Fabrice-2]
- A non-lead/supportive role can still be valuable if the company fits the thesis. [Fabrice-2][Fabrice-4]
- Fast decision-making can happen in roughly two calls when fit is clear. [Fabrice-2][Fabrice-4]
- Broad portfolios can be rational when guided by informed thesis filters. [Fabrice-2]
- International and category-specific marketplaces can be attractive if they can become top players. [Fabrice-1][Fabrice-3]

### What this POV interrogates

- Whether marketplace liquidity and network effects are plausible. [Fabrice-2][Fabrice-4]
- Whether unit economics work or can work. [Fabrice-2]
- Whether price/valuation is disciplined. [Fabrice-2]
- Whether the company can become a top player in its region/category. [Fabrice-2][Fabrice-3]
- Whether the deal is an overheated hype-cycle bet, especially in crowded AI/LLM areas. [Fabrice-2]

### Signature heuristics

- **Angel investing at venture scale:** many checks, fast filters, clear criteria. [Fabrice-2]
- **Four investment-selection criteria:** thesis/category, founder, business quality/unit economics, price discipline. [Fabrice-2]
- **Two calls in a week:** fast diligence when inputs are clear. [Fabrice-2][Fabrice-4]
- **Marketplace liquidity:** supply/demand dynamics as core proof. [Fabrice-2]

### Frame mapping

**Dominant posture: F4 — Hostile Diligence.** For marketplaces, this lens aggressively tests unit economics, liquidity, price, and category leadership. It can be constructive, but it is the least forgiving default lens in this palette.

### Output style note

Fast, analytical, and price/unit-economics disciplined. Feedback should be crisp: "Show liquidity, unit economics, top-player path, and why this is not an overpriced crowded trade."

### Sources

[Fabrice-1], [Fabrice-2], [Fabrice-3], [Fabrice-4]

---

# Considered but excluded

Visible exclusion discipline is part of the palette's credibility. These POVs may be useful later, but they should not be default palette entries in v1.

| Considered POV | Confidence in source artifacts | Exclusion reason | Revisit condition |
|---|---|---|---|
| Susa Ventures / Pratyush Buddiga lens | high | Strong "spiky founder + category-defining company" POV, but near-duplicates parts of Floodgate/NFX in a 15-entry palette and is less deck-mechanics-specific. | Add if the skill needs a category-before-market-map lens distinct from Floodgate's breakthrough-insight language. |
| Forum Ventures / Jonah Midanik lens | high | Very strong B2B SaaS pitch-deck guidance, but default palette already includes Hustle/Pear/Designer for deck mechanics and the build needs stage/sector spread beyond SaaS. | Add a `b2b_saas_operator` lens if the evaluator adds sector-specific modules. |
| Everywhere Ventures / Jenny Fielding lens | med | Useful global/community pre-seed posture, but source material is thinner and less deck-specific than included high-confidence lenses. | Add as opt-in if the user wants a global/off-coastal/community-founder read. |
| Soma Capital / Aneel Ranadive lens | med | Ambition/network-leverage POV is interesting, but D1.2 flagged unresolved Niharika Singh/Soma ambiguity and deck-specific evidence is thinner. | Revisit after orchestrator resolves the named-lead ambiguity or gathers more direct Soma deck-evaluation material. |
| Afore Capital / Afore Alpha lens | high | Excellent true pre-seed/pre-traction lens, but overlaps with K9's stage-purity lens; K9 has more named-person and technical criteria specificity. | Add if the skill needs an "earlier than K9, pre-incorporation/raw-idea" institutional lens. |
| Auren Hoffman / Flex Capital lens | high | Strong anomalous-founder and access-logic POV, but overlaps with Naval/Floodgate on exceptional non-consensus founders and Fabrice on high-volume investing. | Add if a future version needs a data/SaaS contrarian seed lens. |
| Lenny Rachitsky lens | high | Valuable angel-access and power-law math lens, but less directly deck-evaluation-specific than Naval/Calacanis/Sahil/Elad and more cap-table/network oriented. | Add if the skill adds an "angel syndicate/shareability" module. |
| Garry Tan / YC lens | high | Strong deck self-explanation and weird-builder guidance, but YC/Garry context risks blending accelerator/application and investor lenses; overlaps with Calacanis on blunt clarity and Naval on weird exceptional builders. | Add if the skill adds a YC-application or first-slide clarity submode. |
| Jason Cohen lens | high | Excellent SLC/product/growth realism framework, but strongly product/SaaS/operator-specific and could dominate general pre-seed reads with later-stage product proof expectations. | Add as a product/growth opt-in for SaaS/product-led decks. |
| Ali Partovi / Neo lens | high | Strong exceptional-technical-talent lens, but Neo talent-network model is less directly comparable to a named VC deck read. | Add if evaluating young technical founders or talent-network-heavy rounds. |
| Cyan Banister lens | high | Distinct "magically weird / six years out" angel lens, but overlaps with Boost VC's frontier/weirdness lens and Naval's exceptional-founder lens in default palette. | Add as experimental opt-in when a deck is intentionally weird/future-category-heavy. |
| Pejman Nozad as standalone angel lens | high | Included implicitly via Pear VC; a separate Pejman angel lens would double-count team/market/relationship heuristics. | Split only if later skill distinguishes firm POV from individual angel history. |

---

# Contradictions intentionally preserved

The palette should surface contradictions instead of smoothing them into one generic rubric.

- **TAM depth:** Pear rewards bottom-up market sizing; Sahil is more skeptical of VC-scale theater when the business may not need venture money. The skill should show both reads rather than average them.
- **Traction expectations:** K9 says true pre-seed should not need traction; Calacanis often wants product-in-market evidence and updates; Hustle treats traction as learning velocity. The output should name which definition is being applied.
- **Deck versus demo:** Bloomberg Beta may prefer a demo over slides; Hustle, Pear, NFX, Designer Fund, and Forum-like guidance value deck structure. A working demo can offset missing deck sections in some lenses but not all.
- **Weirdness:** Boost and Naval can grant weirdness if one exceptional/future signal is present; 2048 and Fabrice will ask for fit, packet completeness, category, price, and unit logic faster.
- **Founder-first versus market-first:** Precursor and Floodgate underwrite people/insight early; Pear/NFX/Designer/Fabrice still demand market, timing, fund-return, or marketplace mechanics.

---

# Sources appendix

## Hustle Fund

- [HF-1] https://www.hustlefund.vc/blog-posts-founders/your-pitch-deck-only-needs-5-slides
- [HF-2] https://www.hustlefund.vc/blog-posts-founders/slide-titles-vcs-will-actually-read
- [HF-3] http://hustlefund.vc/post/angel-squad-how-to-evaluate-startup-traction-at-the-earliest-stages-it-is-not-about-revenue

## Pear VC

- [Pear-1] https://pear.vc/founder-services/fundraising
- [Pear-2] https://pear.vc/inside-pearx-how-we-help-with-fundraising
- [Pear-3] https://pear.vc/market-sizing-guide

## NFX

- [NFX-1] https://www.nfx.com/post/the-nfx-pitch-deck-library
- [NFX-2] https://www.nfx.com/about
- [NFX-3] https://fast.nfx.com
- [NFX-4] https://brieflink.com/startup-fundraising-advice/gigi-levy-weiss-nfx

## Floodgate

- [Floodgate-1] https://www.floodgate.com/insights/superbuilders-and-superthinkers
- [Floodgate-2] https://www.floodgate.com/team
- [Floodgate-3] https://www.floodgate.com/team/mike-maples-jr
- [Floodgate-4] https://www.floodgate.com

## Bloomberg Beta

- [BB-1] https://github.com/Bloomberg-Beta/Manual
- [BB-2] https://raw.githubusercontent.com/Bloomberg-Beta/Manual/main/3%20-%20Criteria%20for%20investing.md
- [BB-3] https://raw.githubusercontent.com/Bloomberg-Beta/Manual/main/1%20-%20Manual.md
- [BB-4] https://www.youtube.com/watch?v=VfaUG6OPLk0

## Precursor Ventures

- [Precursor-1] https://www.businessinsider.com/precursor-vc-charles-hudson-offers-best-advice-for-pitch-decks-2019-11
- [Precursor-2] https://brieflink.com/startup-fundraising-advice/charles-hudson-precursor-ventures
- [Precursor-3] https://www.thepitch.show/investors/charles-hudson-precursor-ventures
- [Precursor-4] https://www.precursorvc.com

## Boost VC

- [Boost-1] https://www.boost.vc
- [Boost-2] https://www.boost.vc/faq
- [Boost-3] https://medium.com/boost-vc/be-the-cockroach-a577b5e0d8d2
- [Boost-4] https://www.adamdraper.vc/p/at-boost-vc-we-dont-invest-in-the

## Designer Fund

- [DF-1] https://designerfund.com/blog/the-designers-guide-to-building-a-winning-vc-pitch-deck
- [DF-2] https://designerfund.com/about
- [DF-3] https://designerfund.com/blog/designer-fund-guide-to-fundraising

## 2048 Ventures

- [2048-1] https://www.2048.vc/blog/pre-seed-fast-track
- [2048-2] https://www.2048.vc/blog/how-to-pitch-2048-ventures
- [2048-3] https://www.2048.vc
- [2048-4] https://www.2048.vc/blog

## K9 Ventures

- [K9-1] https://www.k9ventures.com/blog/2010/09/11/investment-criteria
- [K9-2] https://www.k9ventures.com/blog/2017/10/10/pre-seed-faq
- [K9-3] https://www.k9ventures.com/blog/2010/04/28/announcing-k9-ventures

## Naval Ravikant

- [Naval-1] https://venturehacks.com/angel
- [Naval-2] https://venturehacks.com/wp-content/uploads/2009/12/Pitching-Hacks.pdf
- [Naval-3] https://www.marsdd.com/our-story/video-the-anatomy-of-a-fundable-start-up
- [Naval-4] https://fi.co/insight/the-anatomy-of-a-fundable-startup-by-naval-ravikant
- [Naval-5] https://spearhead.co/introducing-spearhead

## Jason Calacanis

- [Calacanis-1] https://www.fi.co/insight/4-types-of-questions-investors-frequently-ask
- [Calacanis-2] https://www.angel.university
- [Calacanis-3] https://www.dreamit.com/journal/2020/12/4/jason-calacanis-answers-the-top-5-questions-he-gets-about-angel-investing
- [Calacanis-4] https://www.youtube.com/watch?v=2zhqpzzS3Bc
- [Calacanis-5] https://fullratchet.net/138-how-to-angel-invest-like-the-best-part-1-jason-calacanis

## Sahil Lavingia

- [Sahil-1] https://mercury.com/blog/sahil-lavingia
- [Sahil-2] https://www.angellist.com/blog/easier-than-expected-gumroad-ceo-on-launching-his-first
- [Sahil-3] https://www.youtube.com/watch?v=bOCuIHvQ-NE
- [Sahil-4] https://sahillavingia.com/work
- [Sahil-5] https://www.businessinsider.com/gumroad-sahil-lavingia-opens-5m-crowdfunding-round-new-sec-rule-2021-3

## Elad Gil

- [Elad-1] https://blog.eladgil.com/p/for-companies-raising-seed-rounds
- [Elad-2] https://blog.eladgil.com/p/tactics-for-how-to-raise-vc-round-or
- [Elad-3] https://blog.eladgil.com/p/fundraising-will-take-you-3-months

## Fabrice Grinda

- [Fabrice-1] https://fabricegrinda.com/about-me/
- [Fabrice-2] https://fabricegrinda.com/lessons-from-1100-startup-investments
- [Fabrice-3] https://fabricegrinda.com/portfolio/
- [Fabrice-4] https://fundersclub.com/fabrice-grinda
