# Ethics & Principles (ZoATS)

Status: Draft (governs system behavior; referenced by all workers)

## Core Principles
- Fairness and respect for candidates; transparency in evaluation
- Minimize harm: avoid deceptive prompts or hidden tests
- Pay for time when asking for substantial work products (recommendation)
- Data stewardship: collect minimum necessary, secure storage, retention limits
- Accountability: decision traces and rationale captured
- Founder responsibilities vs system responsibilities clearly delineated

## Policy Hooks (enforced by code where feasible)
- Deal-breakers and thresholds must be declared, not implicit
- Every automated score must include rationale text or trace
- Redaction utilities available before sharing candidate data
- Opt-out path for candidates upon request (operational guidance)

## Implementation Notes
- Workers reference this file in README and outputs where relevant
- Add governance checks to scoring/test harness in later versions

## Changelog
- 2025-10-22: Initial draft created by orchestrator
