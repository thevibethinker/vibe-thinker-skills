---
date: "2025-09-24T01:36:00Z"
last-tested: "2025-09-24T01:36:00Z"
generated_date: "2025-09-24T01:36:00Z"
checksum: jobs_scrape_v0_1_0
tags:
  - jobs
  - careers
  - scraping
  - automation
category: data-ingestion
priority: medium
related_files: 
anchors:
  - object Object
---
# `jobs-scrape`

Version: 0.1.0

Summary: Scrape open roles from given company list (TXT file)

Workflow: data

Tags: jobs, careers, scraping, batch-processing

## Inputs
- companies_file : file (required) — path/to/companies.txt (one per line)
- --roles : string (optional) — Filter by role keywords (e.g., "engineer", "product")
- --seniority : string (optional) — Filter by seniority (e.g., "senior", "staff", "manager")
- --location : string (optional) — Filter by location (e.g., "Remote", "San Francisco")
- --output : file (optional) — Output file path (default: Careerspan/Jobs/scraped_YYYYMMDD.jsonl)

## Outputs
- scraped_jobs : list — List of scraped jobs with metadata
- summary : text — Scraping summary (total jobs, by company, errors)

## Side Effects
- writes:file (Scraped jobs to JSONL file)
- external:api (Scrapes company career pages/job boards)

## Permissions Required
- external_api (for web scraping)
- file:write

## Process Flow
1. **Load Companies**: Read company list from file
2. **Discover Endpoints**: Find career pages for each company
3. **Scrape**: Extract job listings from each source
4. **Parse**: Extract structured data (title, location, salary, etc.)
5. **Filter**: Apply role/seniority/location filters
6. **Deduplicate**: Remove duplicate listings
7. **Save**: Write to JSONL file with metadata
8. **Report**: Generate scraping summary

## Examples
- Basic scrape: `python N5/scripts/jobs_scrape.py companies.txt`
- Filter by role: `python N5/scripts/jobs_scrape.py companies.txt --roles engineer`
- Multiple filters: `python N5/scripts/jobs_scrape.py companies.txt --roles "product manager" --seniority senior --location Remote`
- Custom output: `python N5/scripts/jobs_scrape.py companies.txt --output Careerspan/Jobs/custom_scrape.jsonl`

## Company File Format
```
Company Name
Another Company
Third Company Inc
```

One company name per line. The scraper will attempt to find career pages automatically.

## Data Sources
- Company career pages (primary)
- LinkedIn Jobs
- Indeed
- Glassdoor
- AngelList/Wellfound
- Built In

## Related Components

**Related Commands**: [`jobs-add`](../commands/jobs-add.md), [`jobs-review`](../commands/jobs-review.md), [`quick-add`](../commands/quick-add.md)

**Scripts**: `N5/scripts/jobs_scrape.py` (to be created), `N5/scripts/job_scrapers/` (scraper modules)

**Lists**: `Careerspan/Jobs/opportunities.jsonl`

**Examples**: See [Examples Library](../examples/) for usage patterns

## Implementation Notes
- Respects robots.txt and rate limits
- Caches company career page URLs
- Handles various job board formats
- Includes error handling for unreachable sites
- Logs failed scrapes for manual review

## Future Enhancements
- [ ] Integration with ATS APIs (Greenhouse, Lever, etc.)
- [ ] ML-based relevance scoring
- [ ] Automated application tracking
- [ ] Salary range estimation
- [ ] Company metadata enrichment
