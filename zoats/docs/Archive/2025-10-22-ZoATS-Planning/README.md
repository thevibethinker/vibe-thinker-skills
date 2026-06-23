# ZoATS (ATS-in-a-Box) — Initial Planning Session

**Date**: 2025-10-22  
**Conversation**: con_E5iuQnmFOeZcOUDX  
**Type**: Planning  
**Status**: Completed

---

## Overview

Initial architecture and planning session for ZoATS (ATS-in-a-Box) — an intelligent hiring system built on Zo Computer for startup founders hiring employees 1-3.

**Core Innovation**: Find "the real person beneath the story" through AI-powered intelligence features rather than keyword matching.

**Strategic Purpose**:
- Lead magnet for Careerspan
- Proof-of-concept for Zo's agentic capabilities
- Real product that demonstrates deep AI + recruiting expertise

---

## Accomplishments

### Architecture Defined
- **Email-first interface**: No portals, candidates apply and interact via email
- **Intelligence features**: AI-generation detection, story authenticity scoring, cross-referencing, multi-perspective evaluation
- **Portable design**: Entire system lives in user's Zo workspace, readable/auditable markdown + JSON
- **Modular overlays**: Company/job-specific configs that can be swapped in/out

### Project Structure Created
Location: `file 'ZoATS/'`

```
ZoATS/
├── docs/           # Planning, specs, guides
├── configs/        # Core defaults (immutable)
├── overlays/       # Per-company/job substitutions
├── profiles/       # Reusable rubrics
│   ├── lib/        # Atomic criteria library
│   └── examples/   # Role-specific rubrics
├── voices/         # Voice memo inputs (NEW files only)
├── templates/      # Email & rubric templates
├── scripts/        # Generators, evaluators
├── schemas/        # Data models
└── data/          # Runtime (candidates, jobs)
```

### Key Deliverables
- file 'ZoATS/docs/working-principles.md' - Complete architecture
- file 'ZoATS/roadmap.md' - Feature roadmap & timeline
- file 'ZoATS/configs/core.defaults.json' - Base configuration
- file 'ZoATS/profiles/examples/*.rubric.json' - Example rubrics (Engineer, Designer, PM)
- file 'ZoATS/scripts/evaluator.py' - Scoring engine scaffold

### Worker Spawned
- **Assignment**: file 'Records/Temporary/WORKER_ASSIGNMENT_20251022_090235_OUDX.md'
- **Scope**: Rubric system development (schemas, criteria library, scoring, evaluation pipeline)
- **Priority roles**: Founding Engineer, Designer, PM
- **Constraints**: Voices folder (create new files only, don't move existing)

---

## Technical Decisions

### Data Architecture
- **Candidates**: Markdown profiles + JSON metadata
- **Rubrics**: JSON with must-haves, nice-to-haves, story signals, deal-breakers
- **Scoring**: Weighted components (must_have: 0.5, nice_to_have: 0.15, story_authenticity: 0.2, crossref: 0.15)
- **Thresholds**: Quick-pass: 0.62, Borderline: 0.48

### Intelligence Signals
Core verification/validation concerns:
- AI-generation likelihood
- Story uniqueness/depth
- Cross-reference validation (LinkedIn, news, GitHub)
- Multi-perspective evaluation (panel simulation)
- Temporal consistency (career trajectory coherence)
- Contact verification

### Portability Strategy
- **Overlays**: Substitutable config packages (company + job + voice + rubric)
- **Generators**: Scripts to create new overlays from base templates
- **Localized state**: All company-specific data in overlay, core system stays clean
- **Flash & go**: Drop overlay into new Zo system → works immediately

---

## Timeline & Go-to-Market

### MVP Build (Tonight → 2 weeks)
- **Night 1**: Email integration, resume parsing, rubric builder
- **Week 1**: Intelligence features (AI detection, cross-ref, scoring)
- **Week 2**: Multi-job support, digest emails, polish

### Launch
- **Free trial**: 2 weeks (time to surface testimonials)
- **Pricing**: $X/month via Zo subscription
- **Target**: 10-15 early-stage founders

### Success Metrics
- 5+ hours saved per founder per week
- <10% miss rate (filtered candidates who shouldn't have been)
- 20% conversion to Careerspan services
- 5+ strong testimonials

---

## Next Actions

1. **Open worker assignment** in new conversation (rubric system development)
2. **Email integration**: Gmail API setup, label watching
3. **Resume parser**: PDF/DOCX → structured JSON
4. **Rubric builder**: Socratic conversation flow (voice-enabled)
5. **Test with real client** (parallel to current process)

---

## Related Files

### Planning Documents
- file 'Documents/Archive/2025-10-22-ZoATS-Planning/ats-in-a-box-principles.md' - Full architecture
- file 'Documents/Archive/2025-10-22-ZoATS-Planning/SESSION_STATE.md' - Session tracking

### Active Project
- file 'ZoATS/' - Full project directory

### Worker Assignment
- file 'Records/Temporary/WORKER_ASSIGNMENT_20251022_090235_OUDX.md'

---

## Key Insights

1. **Lead magnet mechanics**: Free trial long enough (2 weeks) to generate testimonials, but short enough to create urgency
2. **Founder pain**: Not lack of applicants, but drowning in volume with no good filter
3. **Differentiation**: Intelligence (authenticity, verification) not automation (speed)
4. **Portability wins**: Entire system readable, auditable, modifiable → trustworthy
5. **CRM-lite**: Track candidate state but keep distinct from general CRM
6. **Bulk operations**: Draft emails, BCC lists, batch actions matter at scale

---

## Lessons for Future

- **Voices folder protocol**: Create new files only, never move existing (prevents data loss)
- **Worker spawn protocol**: Use file 'N5/scripts/spawn_worker.py' with proper context handoff
- **Overlay pattern**: Powerful for multi-tenant or multi-config scenarios
- **Rubric evolution**: Expect rubrics to evolve with voice feedback → version them

---

*Archive created: 2025-10-22 05:35 ET*  
*Closed by: conversation-end protocol v2.0.0*
