---
created: 2026-06-16
last_edited: 2026-06-18
version: 2.0
provenance: con_XbMMeD3u4MxlbvOE
---

# Research Engine — Investor Diligence Mode

`investor-diligence` is the canonical investor/VC prep mode for the owner's venture. It is a focused variation of generic `diligence`; keep generic `diligence` for non-investor vendor, partner, customer, candidate, competitor, and unknown-stakeholder DD.

All owner/venture identity in this mode — venture name, calendar accounts, email accounts, evergreen internal links, excluded calendars — is read from the profile (`config/profile.json`, falling back to `config/profile.default.json`). Nothing below is hardcoded; the venture is referred to generically as **the venture**. See `references/portability.md`.

## Invocation

Default named-entity invocation; no meeting required:

```bash
python3 Skills/research-engine/scripts/research_engine.py run \
  --query "Diligence <VC/Fund/Partner> for <venture> investor prep" \
  --mode investor-diligence \
  --depth standard \
  --topic <slug>
```

Brief size is optional and defaults to `standard`:

```bash
--brief-size skim
--brief-size standard
--brief-size full-dossier
```

Meeting-aware invocation is manual and optional. This must not become a scheduled automation by default.

## Calendar policy

When the owner asks to prepare for upcoming investor calls, inspect only the calendar accounts listed in the profile `allowed_calendar_accounts`, and never inspect any account in `excluded_calendar_accounts`. Prioritize calls in the next 72 hours; use a 14-day lookahead when scanning for candidate investor meetings.

If `allowed_calendar_accounts` is empty (e.g. a fresh import before remapping), do not scan calendars — ask the owner to populate the profile first.

## Private email policy

Use only the accounts in the profile `allowed_private_email_accounts`.

Email evidence in the dossier should be summary-only and traceable:

- short summary of relevant history
- subject line
- date
- counterparty / sender-recipient direction when useful
- source account

Do not dump full private email bodies into the dossier.

## Approved internal context

Always include venture context through approved sources only:

- the content library at the profile `content_library_root` (default `Knowledge/content-library/`), especially canonical positions and approved materials
- evergreen source links from the profile `evergreen_internal_sources`

Do not use accelerator/grant applications, any application-specific narrative, unrelated Research folders, or broad workspace search for the venture name. The workspace is generally not curated enough for broad search to be safe for this mode. Profile `exclusion_terms` lists path/term substrings to skip during content-library scan.

If the content library is absent or docs-only (common on a fresh import), the scan returns nothing and the run proceeds on external evidence only — clearly labeled as missing internal context.

## LinkedIn layer

Use connected LinkedIn tools where available to identify:

- fund/company profile signals
- key partners or decision makers
- people associated with the VC
- mutuals and plausible intro paths
- org/member signals that public web search misses

If connected LinkedIn tools do not expose a needed field, use web-visible LinkedIn evidence as fallback and label the limitation.

## X / public discourse layer

Use X/public discourse search to identify what the investor publicly supports, discusses, amplifies, or avoids, especially around the venture's domain (configurable via profile `focus_terms`) and founder-facing behavior and tone.

Cite posts/accounts or clearly mark unavailable evidence.

## Portfolio classification

Classify relevant portfolio companies with a rationale. Use these classes:

| Class | Meaning |
|---|---|
| `competitive` | Could conflict with or compete against the venture |
| `complementary` | Could partner with, buy from, or strengthen the venture |
| `channel` | Could open customers, hospitals, labs, buyers, or strategic distribution |
| `capital` | Signals fund capacity, follow-on behavior, syndicate quality, or relevant co-investors |
| `future-buyer` | Potential acquirer, strategic partner, or downstream buyer |
| `irrelevant` | No meaningful venture adjacency found |
| `unknown` | Insufficient evidence |

Every classification needs a brief explanation.

## Dossier structure

Recommended `standard` output:

1. Bottom line / recommended posture
2. Investor or fund snapshot
3. Partner / decision-maker map
4. Thesis and investment pattern
5. Domain fit (venture's space)
6. Portfolio classification table with rationales
7. Competitive or complementary portcos
8. LinkedIn mutuals and intro paths
9. X/public discourse signals
10. Relevant private history summary
11. Venture narrative hooks
12. Risks, conflicts, and red flags
13. Questions to ask live
14. Follow-up moves
15. Source scope / tool provenance

## Source provenance

The final dossier must distinguish ordinary web sources from Exa, LinkedIn, X, calendar/email, and internal workspace retrieval. Private app integrations must be labeled as private-source summaries, not public evidence.
