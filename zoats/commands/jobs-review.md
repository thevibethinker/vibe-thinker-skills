---
date: "2025-09-24T01:36:00Z"
last-tested: "2025-09-24T01:36:00Z"
generated_date: "2025-09-24T01:36:00Z"
checksum: jobs_review_v0_1_0
tags:
  - jobs
  - careers
  - review
  - tui
category: productivity
priority: medium
related_files:
anchors: [object Object]
---
# `jobs-review`

Version: 0.1.0

Summary: TUI to approve/reject PENDING jobs

Workflow: misc

Tags: jobs, careers, review, interactive

## Inputs
- --auto-fetch : flag (optional) — Automatically fetch pending jobs before review
- --filter : string (optional) — Filter jobs by criteria (e.g., "salary>100000")

## Outputs
- review_summary : text — Summary of approved/rejected/skipped jobs
- updated_list : file — Updated jobs list with new statuses

## Side Effects
- writes:file (Updates job statuses in Careerspan/Jobs/)
- modifies:file (Existing job entries)

## Process Flow
1. Load pending jobs from list
2. Display TUI with job details
3. User reviews each job (approve/reject/skip/flag)
4. Update job status in list
5. Generate review summary

## Examples
- Start review: `python N5/scripts/jobs_review.py`
- With auto-fetch: `python N5/scripts/jobs_review.py --auto-fetch`
- Filtered review: `python N5/scripts/jobs_review.py --filter "location:Remote"`

## TUI Controls
- `a` - Approve job
- `r` - Reject job
- `s` - Skip (review later)
- `f` - Flag for follow-up
- `↑/↓` - Navigate jobs
- `q` - Quit and save
- `?` - Show help

## Related Components

**Related Commands**: [`jobs-add`](../commands/jobs-add.md), [`jobs-scrape`](../commands/jobs-scrape.md), [`flow-run`](../commands/flow-run.md)

**Scripts**: `N5/scripts/jobs_review.py` (to be created)

**Lists**: `Careerspan/Jobs/opportunities.jsonl`

**Examples**: See [Examples Library](../examples/) for usage patterns
