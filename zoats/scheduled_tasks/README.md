# ZoATS Scheduled Task Specs (Do not auto-register on this instance)

This directory contains specifications for scheduled tasks intended for deployment during ZoATS bootstrap on new Zo computers. These specs are NOT automatically registered or run on this instance.

How to use (for future bootstrap)
- Read each task spec `.md` file
- Confirm config and dry-run settings
- Register the task using your platform’s scheduler (e.g., tool create_scheduled_task) with the included RRULE and instruction
- Start with dry-run where indicated, validate outputs, then toggle off dry-run

Conventions
- One task per file
- Include: id, label, purpose, RRULE, instruction, dry-run guidance, success criteria, error handling, references

Tasks
- rejection_drafts_5min.md — Generate at most one rejection draft every 5 minutes (drafts only, approvals queue)
