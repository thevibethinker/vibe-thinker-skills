# Resume Parser - Usage Examples

## Real-World Test Cases

### Test Case 1: Markdown Resume (Jane Smith)
```bash
python workers/parser/main.py --job test-job --candidate test-001
```

**Input:** `jobs/test-job/candidates/test-001/raw/resume.md`
**Output:**
- Extracted: 859 characters
- Name: "# Jane Smith"
- Email: jane.smith@example.invalid
- Experience: 8 years

### Test Case 2: PDF Resume (Vrijen Attawar)
```bash
python workers/parser/main.py --job test-job --candidate vrijen-001
```

**Input:** `jobs/test-job/candidates/vrijen-001/raw/v_mostrecentresume-FCH.pdf`
**Output:**
- Extracted: 3603 characters
- Name: "VRIJEN S. ATTAWAR"
- Email: candidate@example.invalid
- Experience: 5 years

## Common Workflows

### Parse All Candidates for a Job

```bash
#!/bin/bash
JOB_ID="tech-role-2024"

for candidate_dir in jobs/$JOB_ID/candidates/*/; do
    candidate_id=$(basename "$candidate_dir")
    echo "Processing: $candidate_id"
    python workers/parser/main.py --job "$JOB_ID" --candidate "$candidate_id"
done
```

### Dry-Run Before Batch Processing

```bash
# Preview first
python workers/parser/main.py --job tech-role-2024 --candidate cand-001 --dry-run

# If satisfied, run for real
python workers/parser/main.py --job tech-role-2024 --candidate cand-001
```

### Validation Loop

```bash
# Parse and immediately validate
python workers/parser/main.py --job $JOB --candidate $CAND && \
    test -f jobs/$JOB/candidates/$CAND/parsed/text.md && \
    test -f jobs/$JOB/candidates/$CAND/parsed/fields.json && \
    echo "✓ Valid outputs"
```

## Error Handling Examples

### No Files Found
```bash
$ python workers/parser/main.py --job empty-job --candidate no-files
ERROR No resume files found in: jobs/empty-job/candidates/no-files/raw
Exit Code: 1
```

### Corrupted PDF
```bash
$ python workers/parser/main.py --job test --candidate bad-pdf
ERROR Failed to extract PDF: <error details>
WARNING Attempting fallback extraction...
# Will attempt basic text extraction or fail gracefully
```

## Integration Examples

### With Scoring Engine
```bash
# 1. Parse resume
python workers/parser/main.py --job j1 --candidate c1

# 2. Score parsed output
python workers/scorer/main.py --job j1 --candidate c1
# Reads: jobs/j1/candidates/c1/parsed/text.md
```

### With Email Intake
```bash
# Email intake creates raw files
python workers/intake/main.py --email candidate@example.invalid

# Then parse
python workers/parser/main.py --job auto-job --candidate auto-123
```

## Performance Notes

- **Markdown**: ~5ms per file
- **PDF**: ~200ms per file (pdfminer.six)
- **DOCX**: ~50ms per file (python-docx)

## Troubleshooting

### PDF Not Extracting Text
- Check if PDF is image-based (OCR needed - deferred to Night 2)
- Try opening PDF manually to verify it contains text
- Check logs for specific pdfminer.six errors

### Email Not Detected
- Verify email format is standard (name@example.invalid)
- Check if email is in an image (not extractable yet)
- Manual correction may be needed in fields.json

### Years of Experience Wrong
- Current heuristic is basic pattern matching
- Enhancement planned for Night 2 with LLM-assisted extraction
- Manual correction available in fields.json
