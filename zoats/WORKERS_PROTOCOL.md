# Workers Protocol (ZoATS)

Standard: Each worker has its own focused file in `./workers/` so builders can stay scoped, avoid excess reading, and still share the same project context.

- Location: All worker docs live under `ZoATS/workers/` (same directory) and reference shared assets in `ZoATS/`.
- Scope: Each worker file includes purpose, I/O, interface, tonight milestones, DoD, risks, and a checklist.
- Commands: All workers MUST support `--dry-run` and verify outputs.
- Paths: Use the portable layout rooted at `ZoATS/`.
- Integration: Orchestrator links workers and runs the end-to-end pipeline.

Template (copy for new workers):

```
# <Worker Name> (Worker)
Status: Draft | Owner: <convo-id or person>

Purpose
Inputs
Outputs
Interface
Tonight Milestones
Definition of Done (Night 1)
Dependencies
Risks & Mitigations
Checklist (Night 1)
Paths
Integration Points
Notes
```