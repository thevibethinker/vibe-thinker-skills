#!/usr/bin/env python3
"""
ZoATS Rejection Email Composer (Drafts Only)
- Generates professional decline emails for candidates with decision == "REJECT" (or PASS)
- Drafts only; do not send. For human review/approval before deployment.

Usage:
  python workers/rejection_email/main.py --job <job-id> --candidate <candidate-id> [--dry-run]
"""
import argparse, json, logging, re
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
CFG_PATH = ROOT / "workers" / "rejection_email" / "config.json"

ALLOWED_REASON_CODES = {
    "ROLE_ALIGNMENT": "Another candidate aligned more closely with the role's current priorities.",
    "EXPERIENCE_DEPTH": "Selected candidates showed comparatively greater depth or recency with specific tools or problems central to this role.",
    "SCOPE_SCALE": "Selected candidates had more recent experience at the scope/scale we need right now.",
    "DOMAIN_EXPOSURE": "Domain exposure was less direct relative to those selected for this role.",
    "TIMING_COMPETITION": "This cycle had exceptionally strong competition and a limited number of interview slots."
}

BANNED_DEFAULTS = [
    "age", "gender", "sex", "sexual orientation", "race", "ethnicity", "color", "religion", "creed", "national origin",
    "citizenship", "immigration", "disability", "handicap", "medical", "pregnan", "marital", "family", "parental",
    "veteran", "military", "union", "genetic", "culture fit", "personality", "young", "old", "overqualified", "underqualified"
]


def read_json(p: Path) -> dict:
    if not p.exists():
        raise FileNotFoundError(f"Missing required file: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def load_cfg() -> dict:
    if CFG_PATH.exists():
        try:
            return json.loads(CFG_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Config unreadable, using defaults: {e}")
    # Defaults mirror the shipped config.json
    return {
        "employer_promo": {
            "enabled": True,
            "position": "footer",
            "cta_text": (
                "This recruiting process is supported by ZoATS. If helpful, their free tools can assist with refining "
                "professional storytelling, strengthening resume and interview narratives, and improving odds in future searches: "
                "https://example.com"
            ),
        },
        "feedback": {
            "enabled": False,
            "mode": "per_candidate",
            "include_positive_signals": True,
            "allowed_reason_codes": list(ALLOWED_REASON_CODES.keys()),
            "disclaimer_text": (
                "Feedback reflects comparative fit against current role needs and is not a legal determination or guarantee of future outcomes."
            ),
        },
        "legal_filter": {
            "banned_terms": BANNED_DEFAULTS,
            "style": "neutralize",
        },
    }


def neutralize(text: str, banned_terms: list[str]) -> str:
    out = text
    for term in banned_terms:
        # case-insensitive, partial (e.g., "pregnan" catches pregnancy/pregnant)
        out = re.sub(fr"{re.escape(term)}", "comparative fit", out, flags=re.IGNORECASE)
    return out


def extract_feedback(ge: dict, cfg: dict) -> dict:
    """Derive a compact, legally-safe feedback structure from gestalt_evaluation.json."""
    banned = cfg.get("legal_filter", {}).get("banned_terms", BANNED_DEFAULTS)
    allowed = set(cfg.get("feedback", {}).get("allowed_reason_codes", []))
    positives = []
    if cfg.get("feedback", {}).get("include_positive_signals", True):
        for s in (ge.get("key_strengths") or [])[:2]:
            cat = s.get("category") or "Strength"
            rel = s.get("relevance") or "Positive signal"
            item = neutralize(f"{cat}: {rel}", banned)
            positives.append(item)
    # naive mapping from concerns text → reason code
    raw_concerns = [c.get("issue", "") for c in (ge.get("concerns") or [])]
    mapped_codes: list[str] = []
    for issue in raw_concerns:
        t = issue.lower()
        if any(k in t for k in ["experience", "recency", "recent"]):
            mapped_codes.append("EXPERIENCE_DEPTH")
        elif any(k in t for k in ["domain", "industry", "consulting"]):
            mapped_codes.append("DOMAIN_EXPOSURE")
        elif any(k in t for k in ["scope", "scale", "complexity"]):
            mapped_codes.append("SCOPE_SCALE")
        else:
            mapped_codes.append("ROLE_ALIGNMENT")
    # filter to allowed + unique, cap 2
    mapped_codes = [c for c in mapped_codes if c in allowed]
    seen = set()
    uniq_codes = []
    for c in mapped_codes:
        if c not in seen:
            uniq_codes.append(c)
            seen.add(c)
        if len(uniq_codes) >= 2:
            break
    negatives = [ALLOWED_REASON_CODES[c] for c in uniq_codes]
    # generic fallback if nothing safe/specific
    if not positives and not negatives:
        negatives = [
            "In this cycle, selected candidates showed a closer match to the role's current priorities.",
            "Continuing to make outcomes legible and role-aligned examples sharper can strengthen future applications.",
        ]
    disclaimer = cfg.get("feedback", {}).get("disclaimer_text", "")
    return {
        "positives": positives,
        "focus": [neutralize(n, banned) for n in negatives],
        "disclaimer": disclaimer,
    }


def compose_email(candidate_name: str, job_title: str, company_name: str, cfg: dict, feedback_block: str | None) -> str:
    date_str = datetime.utcnow().strftime("%B %d, %Y")
    body = [
        f"Subject: Update on your application — {job_title}",
        "",
        f"Dear {candidate_name},",
        "",
        f"Thank you for your interest in the {job_title} role at {company_name} and for the time you invested in your application.",
        "",
        "After careful consideration, we've decided not to move forward with your candidacy at this time. We recognize the effort that goes into applying, and we're grateful for the opportunity to learn more about your background.",
    ]
    if feedback_block:
        body.extend(["", feedback_block])
    promo = None
    if cfg.get("employer_promo", {}).get("enabled", True):
        cta = cfg.get("employer_promo", {}).get("cta_text", "")
        if cta:
            promo = f"*{cta}*"
    # promo right before sign-off
    if promo:
        body.extend(["", promo])
    body.extend([
        "",
        f"We appreciate your interest in {company_name} and wish you every success in your job search.",
        "",
        "Sincerely,",
        "The Hiring Team",
        f"{company_name}",
    ])
    return "\n".join(body)


def main(job_id: str, candidate_id: str, dry_run: bool = False) -> int:
    job_dir = ROOT / "jobs" / job_id
    cand_dir = job_dir / "candidates" / candidate_id
    ge_p = cand_dir / "outputs" / "gestalt_evaluation.json"
    fields = cand_dir / "parsed" / "fields.json"

    data = read_json(ge_p)
    decision = (data.get("decision", "") or "").upper()
    if decision not in {"REJECT", "PASS"}:
        logger.info(f"Skipping: Decision is {decision}, not REJECT/PASS")
        return 0

    info = read_json(fields)
    candidate_name = (info.get("name") or "Candidate").title()

    # job meta (fallbacks)
    job_title = job_id.replace("-", " ").title()
    company_name = (job_dir / "company.txt").read_text(encoding="utf-8").strip() if (job_dir / "company.txt").exists() else "Hiring Team"

    cfg = load_cfg()

    # feedback: always collect/save JSON; include in email iff enabled
    fb = extract_feedback(data, cfg)
    feedback_json_path = cand_dir / "outputs" / "feedback.json"
    feedback_json_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        feedback_json_path.write_text(json.dumps(fb, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not write feedback.json: {e}")

    feedback_block = None
    if cfg.get("feedback", {}).get("enabled", False):
        # render compact block with bullets and disclaimer; cap total lines
        lines = []
        if fb.get("positives"):
            lines.append("What stood out:")
            for s in fb["positives"][:2]:
                lines.append(f"- {s}")
        if fb.get("focus"):
            lines.append("Where to strengthen (relative to this role's current priorities):")
            for s in fb["focus"][:2]:
                lines.append(f"- {s}")
        if fb.get("disclaimer"):
            lines.append("")
            lines.append(f"_{fb['disclaimer']}_")
        feedback_block = "\n".join(lines)

    email = compose_email(candidate_name, job_title, company_name, cfg, feedback_block)

    out_dir = cand_dir / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "rejection_email.md"

    if dry_run:
        logger.info("[DRY RUN] Preview:\n" + email)
    else:
        out_path.write_text(email, encoding="utf-8")
        logger.info(f"✓ Draft saved: {out_path}")

    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Generate a rejection email draft (REJECT/PASS)")
    p.add_argument("--job", required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    raise SystemExit(main(args.job, args.candidate, args.dry_run))
