# ATS-in-a-Box on Zo: Working Principles & Architecture

**Last Updated**: 2025-10-21 22:00 EST  
**Status**: Planning → Build starting tonight  
**Timeline**: MVP in one night, 2-week free trial window

---

## Core Thesis

*"Startup founders hiring employees 1-3 need to identify the **real person beneath the story** - not keyword-optimized resumes. What if your email inbox became an intelligent screening system powered by Zo that surfaces the 3-5 candidates you should actually talk to?"*

---

## Strategic Goals

### For Careerspan (Lead Magnet)
- Demonstrates deep recruiting + AI expertise
- Attracts founders at critical hiring moments (high intent)
- 2-week free trial → convert to paid Zo + Careerspan services
- Generates testimonials from successful hires

### For V + Zo (Product Validation)
- Stress-tests Zo's agentic capabilities
- Real product with revenue potential
- Proves "AI-native workflows beat legacy SaaS"

---

## Key Intelligence Features (What Makes This Different)

### 1. **Story Detection Over Keyword Matching**
- AI-generation likelihood scoring
- Pattern analysis across naive ChatGPT/Claude tailoring attempts
- Semantic reasoning vs. keyword optimization
- Cross-reference newsworthy claims (LinkedIn, news sources)
- **Goal**: Find the human beneath the polished application

### 2. **Uniqueness & Specificity Tracking**
- Compare all rationales for "why this company"
- Flag most unique/specific responses
- Identify ultra-signals:
  - Self-taught skills in new domains
  - Non-traditional backgrounds with exceptional achievement
  - Genuine passion indicators vs. generic enthusiasm

### 3. **Multi-Perspective Evaluation**
- Simulated panel interview with different personas
- More accurate scoring than single AI perspective
- Incorporates founder's embedded reflections on "who would thrive here"

### 4. **Bias Mitigation (Future)**
- Sanitized/anonymized resume versions for initial scoring
- Remove identifiable information before AI evaluation
- Ensure fair assessment

---

## System Architecture

### Email-First Interface
**Candidates:**
- Apply via `jobs@example.invalid` (or founder email + CC Zo)
- Receive AI-generated clarifying questions via email
- Async screening interview (core questions + personalized follow-ups)
- 48-hour response window

**Founders:**
- Receive digest: "Here are your 3 finalists, here's why, here's what to ask"
- No portal, no login, no configuration hell
- Bulk email drafting with BCC-ready candidate lists

### Data Model

```
ATS/
├── config/
│   ├── settings.json          # System configuration
│   └── email_templates.md     # Email templates
├── jobs/
│   ├── [job-slug]/
│   │   ├── job-description.md
│   │   ├── rubric.json        # Evaluation criteria
│   │   ├── candidates/
│   │   │   ├── [candidate-id].md
│   │   │   └── [candidate-id].json
│   │   ├── screening-questions.md
│   │   └── finalists.md
│   └── [another-job-slug]/
├── rubric-builder/
│   ├── voice-notes/           # Founder/team voice input
│   └── rubric-sessions.md     # Conversation history
└── roadmap.md                 # Feature tracking
```

**Note**: Start with markdown/JSON, plan migration path to database for high-volume jobs.

---

## Core Workflows

### 1. Rubric Building (Setup: ~30 min)
**Inputs:**
- Job description (paste or voice)
- Founder reflections (text or voice)
- Co-founder/team input (voice messages)
- "Who thrives here?" Socratic conversation

**Process:**
- Break down JD into: hard skills, soft skills, values, mindset, culture fit
- Identify must-haves, nice-to-haves, deal-breakers
- Generate structured rubric stored as JSON

**Output:**
- `rubric.json` with scoring criteria
- Deal-breaker thresholds for quick-test filter

### 2. Quick-Test Filter (First Pass)
**Triggered:** New candidate email arrives

**Analysis:**
- Resume parsing
- Deal-breaker check (hard skills, experience, red flags)
- AI-generation likelihood score
- Basic authenticity signals

**Routing:**
- **Pass**: → Deep screening
- **Fail**: → Polite rejection email
- **Borderline**: → Flag for manual review

### 3. Deep Screening (Second Pass)
**For candidates who pass quick-test:**

**Steps:**
1. Send personalized clarifying questions via email (2-3 questions)
2. Wait 48h for response
3. Cross-reference claims:
   - LinkedIn validation
   - News mentions if relevant
   - Public work samples
4. Semantic analysis of responses:
   - Specificity scoring
   - Uniqueness vs. other applicants
   - Authenticity signals
5. Simulated panel interview (multi-persona evaluation)
6. Final rubric scoring

**Output:**
- Updated `candidate-id.json` with:
  - Scores by rubric criteria
  - Authenticity assessment
  - Ultra-signal flags
  - Interview question recommendations

### 4. Finalist Selection & Digest
**Daily/Weekly:**
- Rank all candidates by total score
- Surface top 3-5 with rationale
- Generate founder digest email:
  - "Why these candidates"
  - "What to ask them"
  - "Red flags to probe"
  - "Ultra-signals to explore"

---

## Modularity & Customization Points

### Config Files (User-Customizable)
- `settings.json`: Scoring weights, thresholds, email frequency
- `email_templates.md`: Rejection, clarifying questions, finalist notifications
- `rubric.json`: Per-job evaluation criteria

### Pluggable Modules
- **Voice ingestion**: Whisper API → text for rubric building
- **Cross-reference engines**: LinkedIn scraper, news search
- **AI generation detector**: Swap models/methods as tech improves
- **Bias mitigation**: Anonymization pipeline (future)
- **Database migration**: When markdown lists → too large

### Out-of-the-Box Stack
- **Zo Computer**: Core runtime
- **N8N**: Workflow automation (email triggers, scheduling)
- **Python**: Screening logic, NLP analysis
- **Whisper**: Voice transcription
- **Claude/GPT**: Semantic analysis, panel simulation

---

## MVP Scope (Tonight → 2 Weeks)

### Night 1 (Core Loop)
- [ ] Email ingestion setup (Gmail integration)
- [ ] Resume parsing (PDF/DOCX → structured data)
- [ ] Quick-test filter (deal-breaker logic)
- [ ] Basic rubric builder (text input, simple Socratic flow)
- [ ] Candidate markdown file generation
- [ ] Manual finalist selection interface

### Week 1 (Intelligence Layer)
- [ ] AI-generation detection
- [ ] Uniqueness scoring across applicants
- [ ] Clarifying question generator
- [ ] Email response handling
- [ ] LinkedIn cross-reference (basic)
- [ ] Simulated panel interview scoring

### Week 2 (Polish & Distribution)
- [ ] Founder digest automation
- [ ] Bulk email drafting
- [ ] Voice note ingestion for rubric building
- [ ] Multi-job support
- [ ] Roadmap doc for future features
- [ ] Pricing setup (free 2 weeks, then $X/month via Zo)

---

## Expansion Path (Post-MVP)

### Phase 2: Advanced Intelligence
- [ ] Database migration for high-volume jobs
- [ ] News/GitHub cross-reference for technical roles
- [ ] Pattern library of AI-generated application styles
- [ ] Candidate portfolio analysis (not just resume)
- [ ] "Showcase different sides" prompts (unique interests, perspectives)

### Phase 3: Bias Mitigation
- [ ] Anonymized resume sanitization
- [ ] Blind screening mode
- [ ] Bias audit reports

### Phase 4: Team Collaboration
- [ ] Multi-stakeholder rubric building
- [ ] Collaborative candidate evaluation
- [ ] Interview scheduling integration
- [ ] Hiring pipeline dashboard

### Phase 5: Lead Magnet Optimization
- [ ] Testimonial collection automation
- [ ] Case study generation
- [ ] Careerspan service upsell workflows
- [ ] Referral incentives

---

## Key Success Metrics

### For MVP Validation
- **Time saved**: 5+ hours/week per founder
- **Quality**: AI surfaces hirable candidates (vs. false positives)
- **Miss rate**: <10% of founder-would-hire candidates filtered out
- **Speed**: Time-to-finalist <48 hours from application

### For Lead Magnet
- **Setup completion**: >70% finish 30-min rubric building
- **Engagement**: >50% actively use for hiring
- **Conversion**: 20% buy Careerspan services or extended Zo subscription
- **Testimonials**: 5+ "this changed our hiring" quotes

---

## Ultra-Signals to Surface

### Green Flags
- Self-taught skills in emerging domains
- Non-traditional background + exceptional achievement
- Specific, researched reasons for interest (not generic)
- Evidence of deep work vs. resume optimization
- Authentic enthusiasm (not performative)

### Red Flags
- AI-generation likelihood >70%
- Generic "why this company" rationale
- Keyword stuffing without substance
- Inconsistencies in LinkedIn vs. resume
- Response pattern matches naive ChatGPT output

---

## Technical Considerations

### Multi-Job Complexity
- One candidate may apply to multiple roles
- Separate candidate files per job (with cross-references)
- Shared candidate profile for LinkedIn/validation data
- Per-job rubric scoring

### Scalability Triggers
- **Markdown → Database**: When candidate list >100 per job
- **Email → API**: When volume >50 emails/day
- **Manual → Automated digest**: When jobs >3 concurrent

### Data Privacy
- All candidate data stored in founder's Zo workspace
- No external database (unless founder opts in)
- Audit trail of all AI decisions
- Candidate data deletion on request

---

## Roadmap Tracking

See `file 'ATS/roadmap.md'` (to be created) for:
- Feature backlog
- Prioritization rubric
- Dependency mapping
- Future capability alignment opportunities

---

## Cheap Test (Pre-Build)

Before full build, validate core intelligence:
1. Take 1 real job description
2. Take 10 real resumes (mix of strong/weak/AI-generated)
3. Run rubric builder + scoring manually
4. Show founder: "Here are your top 3, here's why"
5. **Decision**: If they say "whoa, this is different" → build. If not → pivot.

---

## Pricing Model

- **First 2 weeks**: Free (trial window for testimonials)
- **After trial**: $X/month via Zo subscription
- **Upsell**: Careerspan coaching for finalist interviews
- **Enterprise**: Custom pricing for high-volume hiring

---

## Next Steps (Tonight)

1. Set up email integration (Gmail API)
2. Build resume parser
3. Create rubric builder Socratic flow
4. Test quick-test filter logic
5. Generate first candidate markdown file

**Let's ship this thing.**
