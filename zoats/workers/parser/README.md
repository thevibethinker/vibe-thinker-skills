# Resume Parser Worker

Extract text and basic fields from candidate resumes (PDF, DOCX, MD).

## Usage

```bash
# Basic usage
python workers/parser/main.py --job <job-id> --candidate <candidate-id>

# Dry run (preview without writing)
python workers/parser/main.py --job <job-id> --candidate <candidate-id> --dry-run

# Example
python workers/parser/main.py --job tech-role-2024 --candidate cand-001
```

## Inputs

Reads from: `jobs/<job>/candidates/<id>/raw/*.{pdf,docx,md}`

Supports:
- **PDF** - Extracted via pdfminer.six
- **DOCX** - Extracted via python-docx  
- **Markdown** - Direct passthrough

## Outputs

- `jobs/<job>/candidates/<id>/parsed/text.md` - Full extracted text
- `jobs/<job>/candidates/<id>/parsed/fields.json` - Structured fields

### fields.json Schema

```json
{
  "name": "string",           // Extracted name (first heading or name pattern)
  "email": "string | null",   // Email address if found
  "years_experience": "int | null"  // Years of experience (heuristic)
}
```

## Field Extraction Heuristics

### Name
1. First `# Heading` in markdown
2. Lines matching common name patterns (ALL CAPS, Title Case near top)
3. Fallback: "Unknown"

### Email
1. Standard email regex: `[\w\.-]+@[\w\.-]+\.\w+`
2. First match wins
3. Null if not found

### Years of Experience
1. Explicit phrases: "X years of experience", "X+ years experience"
2. Date range counting: (YYYY - YYYY) or (YYYY - Present)
3. Null if not detected

## Testing

```bash
# Run test suite
cd $ZOATS_HOME
python3 workers/parser/test_parser.py
```

## Dependencies

```bash
pip install pdfminer.six python-docx
```

## Exit Codes

- **0** - Success
- **1** - Error (no files found, parsing failed, validation failed)

## Logging

Logs to stderr with timestamps (UTC):
- INFO: Progress and extraction details
- ERROR: Failures with context

## Integration

Consumed by:
- Scoring Engine (reads parsed/text.md and parsed/fields.json)
- Dossier Builder (reads parsed outputs for candidate profiles)

## Status

✓ Complete - All Night 1 milestones achieved
- [x] PDF extraction
- [x] DOCX extraction
- [x] Markdown passthrough
- [x] Heuristic field extraction
- [x] Dry-run support
- [x] Output validation
- [x] Test suite
