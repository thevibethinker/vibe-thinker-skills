# Candidate Intake Processor

CLI to process candidate application bundles from `inbox_drop/` into `jobs/<job>/candidates/<id>/` and initialize `interactions.md`.

## Usage

```
python workers/candidate_intake/main.py --job <job> [--dry-run]
```

- If only one job exists under `jobs/`, `--job` can be omitted.
- With multiple jobs, `--job` is required.
- `--dry-run` previews actions without writing.

## Behavior
- Groups files by temporal proximity (<= 2 min) and filename stem similarity
- Requires at least one resume-like file (.pdf, .docx, .md, .txt)
- Moves (not copies) files into `raw/`
- Creates `interactions.md` with intake event entry
- Leaves non-qualifying bundles in `inbox_drop/`

## Candidate ID Format
`<roleCode>-<nameSlug>-<yyyymmdd>-<shortid>`

- roleCode: `--job` value or metadata.role_code
- nameSlug: derived from metadata.name or resume filename
- yyyymmdd: metadata.applied_date or file mtime
- shortid: 6-char random suffix

## Future Integration
- Gmail API Intake (poll Gmail, write files into `inbox_drop/`)
- LLM-assisted bundle validation and name extraction
