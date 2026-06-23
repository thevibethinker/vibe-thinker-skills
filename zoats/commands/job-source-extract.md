---
date: '2025-10-13T01:53:00Z'
last-tested: '2025-10-13T01:53:00Z'
generated_date: '2025-10-13T01:53:00Z'
checksum: job_source_extract_v1_0_0
tags: [jobs, sourcing, google-drive, extraction]
category: data-ingestion
priority: high
related_files: []
anchors:
  input: null
  output: /home/workspace/N5/commands/job-source-extract.md
---
# `job-source-extract`

Version: 1.0.0

Summary: Extract job posting from URL and add to Google Drive sourced jobs sheet with verification

Workflow: automation

Tags: jobs, sourcing, extraction, google-drive

## Inputs
- url : string (required) — URL of job posting to extract

## Outputs
- job_data : dict — Extracted job information (title, location, description, etc.)
- verification_status : string — Confirmation that extraction is 100% accurate
- sheet_update_status : string — Confirmation of Google Drive sheet update

## Side Effects
- reads:webpage (Job posting URL)
- writes:google-drive (sourced jobs Google Sheet)
- creates:file (Temporary extraction files in conversation workspace)

## Verification Process
1. Extract job description using view_webpage (JavaScript-rendered content)
2. Re-read the extracted content
3. Character-by-character verification against source
4. Confirmation of 100% accuracy before proceeding

## Examples
- Extract from Notion: `python N5/scripts/n5_job_source_extract.py "https://tatosolutions.notion.site/chief-of-staff"`
- Extract from Greenhouse: `python N5/scripts/n5_job_source_extract.py "https://boards.greenhouse.io/company/jobs/123456"`
- Extract from Lever: `python N5/scripts/n5_job_source_extract.py "https://jobs.lever.co/company/job-id"`

## Related Components

**Related Commands**: [`jobs-add`](../commands/jobs-add.md), [`jobs-scrape`](../commands/jobs-scrape.md)

**Scripts**: `N5/scripts/n5_job_source_extract.py`

**Google Drive**: `sourced jobs.csv` (or Google Sheet equivalent)

**Examples**: See [Examples Library](../examples/) for usage patterns

## Notes
- Uses view_webpage for JavaScript-rendered content (e.g., Notion pages)
- Implements double-verification to ensure 100% accuracy
- Automatically updates Google Drive sheet
- Preserves exact formatting and content from source
