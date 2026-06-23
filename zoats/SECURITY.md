# Security & Data Privacy

**Version:** 1.0  
**Last Updated:** 2025-10-26  
**Owner:** Vrijen Attawar / Careerspan

---

## Critical Privacy Principles

### 🔒 Core Rule: NEVER Commit Candidate PII

**What is PII in ZoATS context:**
- Resumes (any format: PDF, DOCX, MD, TXT)
- Candidate personal data (names, emails, phone numbers, addresses)
- Parsed candidate information
- Evaluation/scoring data
- Interview notes
- Any files containing real applicant information

**Why this matters:**
- Legal compliance (GDPR, CCPA, employment law)
- Candidate trust and professional ethics  
- Company liability and reputation  
- Prevents data breaches and identity theft

---

## Protected Directories

### ❌ NEVER Commit
- `jobs/*/candidates/` — All candidate data
- `jobs/*/inbox_drop/*.pdf` — Resume uploads
- `jobs/*/inbox_drop/*.docx` — Resume uploads
- Any file containing owner's name (vrijen, attawar)
- `**/parsed/` — Extracted candidate data
- `**/outputs/candidate.*` — Generated candidate profiles
- `**/outputs/dossier.*` — Candidate evaluations
- `**/outputs/scores.*` — Scoring data
- `**/*resume*.pdf` — Resume files anywhere
- `**/*cv*.pdf` — CV files anywhere

### ✅ Safe to Commit
- Job descriptions: `jobs/*/job_description.md`
- Rubrics: `jobs/*/rubric.json`
- System code: `workers/`, `lib/`, `scripts/`
- Configuration templates: `config/*.example.json`
- Documentation: `docs/`, `README.md`
- Test fixtures: `fixtures/` (synthetic data only)

---

## Protection Mechanisms

### 1. `.gitignore` (Comprehensive Patterns)
Blocks accidental staging of sensitive files. Covers:
- All candidate folders with recursive wildcards
- Resume files by extension and naming pattern
- Owner-specific PII patterns
- Parsed/generated data directories
- Test data that might contain PII

### 2. Pre-Commit Hook (Active Scanning)
Automatically runs before every commit:
- ✅ Scans for candidate data patterns
- ✅ Detects resume files
- ✅ Finds email addresses and phone numbers
- ✅ Blocks owner's name in any file
- ✅ Prevents committing parsed candidate data

**Hook location:** `.git/hooks/pre-commit`

**To bypass (NOT RECOMMENDED):**
```bash
git commit --no-verify
```

### 3. Repository Visibility
- **Status:** Private
- **Access:** Owner only (expand carefully)
- **Never make public** unless completely sanitized

---

## Safe Testing Practices

### Creating Test Data

**✅ DO:**
- Use obviously fake names: "Jane Doe", "Test Candidate", "Sample Applicant"
- Use fake emails: `test@example.com`, `jane.doe@example.invalid`
- Use fake phone: `(555) 123-4567`, `000-000-0000`
- Store in `fixtures/` directory with clear naming
- Mark test jobs clearly: `jobs/test-*`, `jobs/demo-*`, `jobs/smoke-test`

**❌ DON'T:**
- Use real candidate data "just for testing"
- Copy production resumes to test with
- Use your own resume or anyone else's real data
- Assume test data won't be committed

### Test Job Naming
```bash
jobs/
├── test-job/           # Clearly marked as test
├── demo/               # Demo data
├── smoke-test/         # Automated testing
└── {company}-{role}/   # Real jobs (never commit candidates!)
```

---

## Incident Response

### If You Accidentally Commit PII

**STOP. DO NOT PUSH.**

1. **Undo the commit:**
   ```bash
   git reset --soft HEAD~1
   ```

2. **Remove files from staging:**
   ```bash
   git reset HEAD <sensitive-file>
   ```

3. **Verify clean:**
   ```bash
   git status
   git diff --cached
   ```

4. **Commit safely:**
   Ensure pre-commit hook is enabled and retry.

### If PII Was Pushed to GitHub

**CRITICAL — Act immediately:**

1. **Make repository private:**
   ```bash
   gh repo edit owner/repo --visibility private
   ```

2. **Remove from history:**
   ```bash
   # List files to remove
   git log --all --name-only --pretty="" | grep "sensitive-pattern" > files.txt
   
   # Rewrite history
   git filter-repo --invert-paths --paths-from-file files.txt --force
   
   # Force push
   git remote add origin <url>
   git push --force origin main
   ```

3. **Notify affected parties** (candidates whose data was exposed)

4. **Document the incident:** Date, what was exposed, duration, remediation

---

## Verification Checklist

### Before Every Push

- [ ] Run: `git diff --cached --name-only | grep -E "candidates/|resume|inbox_drop"`
- [ ] Verify output is empty (no matches)
- [ ] Check: `git log --name-only -1` for accidental PII
- [ ] Confirm: pre-commit hook is enabled (`test -x .git/hooks/pre-commit`)

### Weekly Security Audit

- [ ] Check for untracked candidate files: `git status | grep candidates`
- [ ] Verify .gitignore coverage: `git check-ignore -v jobs/test-job/candidates/test.pdf`
- [ ] Review recent commits: `git log --name-only --since="1 week ago" | grep -i candidate`
- [ ] Scan for exposed emails: `git log -p --all | grep -E "[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}"`

---

## Team Guidelines

### Onboarding New Contributors

1. **Required reading:** This SECURITY.md document
2. **Verify setup:**
   ```bash
   # Check hook is installed
   test -x .git/hooks/pre-commit && echo "✅ Protected" || echo "❌ NOT PROTECTED"
   
   # Test the hook
   touch jobs/test/candidates/test.pdf
   git add jobs/test/candidates/test.pdf
   git commit -m "test"  # Should be BLOCKED
   ```

3. **Practice safe commits:** Start with non-sensitive files only

### Code Review Requirements

- **Reviewer must verify:** No PII in any changed files
- **Automated check:** CI/CD should scan for patterns
- **If uncertain:** Better to reject than to merge

---

## Compliance & Legal

### Regulations
- **GDPR** (EU): Right to erasure, data minimization
- **CCPA** (California): Consumer data protection rights
- **Employment Law:** Candidate data retention policies

### Data Retention
- **Active candidates:** Keep until hiring decision + 30 days
- **Rejected candidates:** Delete within 90 days (check local law)
- **Hired candidates:** Move to HR system, remove from ATS

### Audit Trail
- All candidate data access should be logged
- Regular reviews of who has repository access
- Annual security audit of all systems

---

## Questions?

**Non-urgent:** Open GitHub discussion or Slack #security  
**Urgent:** Email security@example.invalid or contact Vrijen directly

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-26 | Initial security documentation after PII breach remediation |

---

**Remember:** When in doubt, DON'T commit. It's easier to ask than to clean up exposed PII.
