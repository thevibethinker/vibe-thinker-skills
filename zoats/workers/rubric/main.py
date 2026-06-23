#!/usr/bin/env python3
"""
Rubric Generator Worker

Generates a scoring rubric from a job description (and optional founder notes).
Outputs rubric.json (machine), rubric.md (human), and deal_breakers.json.

Usage:
  python workers/rubric/main.py \
    --jd jobs/<job>/job-description.md \
    --out jobs/<job>/rubric.json \
    [--founder-notes path/to/notes.md] \
    [--interactive | --non-interactive] \
    [--dry-run]

Design:
- Deterministic heuristic extraction (no external APIs)
- Criteria buckets: Must-have, Should-have, Nice-to-have
- Weights normalized to sum to 100
- Deal breakers extracted from hard-requirement language

Quality:
- Logging, --dry-run, error handling, verification
"""
import argparse
import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MUST_PATTERNS = [
    r"\bmust\b", r"\brequired\b", r"\bmandatory\b", r"\bno exceptions\b",
    r"\bneed to\b", r"\bshall\b", r"\bnon[- ]negotiable\b",
    r"\b\d+\+?\s*(years|yrs)\b", r"\bdegree\b", r"\bmba\b", r"\bphd\b",
]
SHOULD_PATTERNS = [
    r"\bshould\b", r"\bstrong(ly)? (preferred|plus)\b", r"\bnice to have\b",
    r"\b(preferred|plus)\b",
]
NICE_PATTERNS = [
    r"\bnice\b", r"\bbonus\b", r"\bgood to have\b", r"\b(optional)\b",
]

DEAL_BREAKER_HINTS = [
    r"\b(us|work) authorization\b", r"\b(can work|eligible to work)\b",
    r"\bminimum (of )?\d+ (years|yrs)\b", r"\b\d+\+?\s*(years|yrs)\b", r"\bdegree (required|in)?\b",
    r"\b(on[- ]site|in[- ]office)\b", r"\bsecurity clearance\b",
]

SOFT_SKILL_HINTS = re.compile(r"problem[- ]?solv|logical|creative|communication|teamwork|collaborat|leadership|quantitative|initiative|ownership|drive|curious", re.I)

STOPWORDS = set("""
a an and are as at be but by for from how i if in into is it of on or our that the their them then there these they this to we with you your
""".split())

BULLET_PREFIX = re.compile(r"^\s*[-*•]\s+")

@dataclass
class Criterion:
    name: str
    weight: float  # percentage 0-100
    tier: str      # Must / Should / Nice
    description: str
    keywords: List[str]

@dataclass
class Rubric:
    job_id: str
    criteria: List[Criterion]
    bands: Dict[str, Dict[str, str]]  # e.g., {"Must": {"meets": "...", "below": "..."}, ...}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text(errors="ignore")


def extract_job_id(jd_path: Path) -> str:
    # Expect jobs/<job>/job-description.md
    parts = jd_path.parts
    if "jobs" in parts:
        idx = parts.index("jobs")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    # Fallback to parent directory name
    return jd_path.parent.name


def lines(text: str) -> List[str]:
    return [l.strip() for l in text.splitlines()]


def is_bullet(l: str) -> bool:
    return bool(re.match(r"^[-*•] ", l))


def sectionize(text: str) -> Dict[str, List[str]]:
    """Very light sectionization by common headings."""
    sections: Dict[str, List[str]] = {"requirements": [], "responsibilities": [], "about": [], "other": []}
    current = "other"
    for l in lines(text):
        lower = l.lower()
        if re.match(r"^(requirements|qualifications|your qualifications and skills|your qualifications)\b", lower):
            current = "requirements"; continue
        if re.match(r"^(responsibilities|what you\'ll do|role)\b", lower):
            current = "responsibilities"; continue
        if re.match(r"^(about (us|the role)|company)\b", lower):
            current = "about"; continue
        if re.match(r"^(industries|capabilities|your impact|your growth)\b", lower):
            current = "other"; continue
        sections.setdefault(current, []).append(l)
    return sections


def collect_bullets(section_lines: List[str]) -> List[str]:
    out: List[str] = []
    for i, l in enumerate(section_lines):
        if is_bullet(l):
            out.append(re.sub(r"^[-*•] ", "", l).strip())
    return out


def classify_tier(text: str) -> str:
    t = text.lower()
    if any(re.search(p, t) for p in MUST_PATTERNS):
        return "Must"
    if any(re.search(p, t) for p in SHOULD_PATTERNS):
        return "Should"
    if any(re.search(p, t) for p in NICE_PATTERNS):
        return "Nice"
    # Heuristic: requirements default to Must, responsibilities to Should
    return "Should"


def keywords_from_text(text: str, max_k: int = 6) -> List[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+/-]{2,}", text.lower())
    tokens = [t.strip("-+/ ") for t in tokens if t not in STOPWORDS]
    # de-dup preserve order
    seen = set()
    kws: List[str] = []
    for t in tokens:
        if t in seen:
            continue
        seen.add(t)
        kws.append(t)
        if len(kws) >= max_k:
            break
    return kws


def normalize_criteria(raw_items: List[Tuple[str, str]]) -> List[Criterion]:
    # raw_items: list of (text, tier)
    # Collapse duplicates by simple normalization
    normalized: Dict[Tuple[str, str], int] = {}
    cleaned: List[Tuple[str, str]] = []
    for txt, tier in raw_items:
        name = re.sub(r"[^a-z0-9 +/#()&]", "", txt.lower())
        name = re.sub(r"\s+", " ", name).strip()
        key = (name, tier)
        normalized[key] = normalized.get(key, 0) + 1
        cleaned.append((txt.strip(), tier))
    # Keep order, de-dup by seen keys
    seen: set = set()
    dedup: List[Tuple[str, str]] = []
    for txt, tier in cleaned:
        k = (re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 +/#()&]", "", txt.lower()).strip()), tier)
        if k in seen:
            continue
        seen.add(k)
        dedup.append((txt, tier))
    # Assign weights: Must heavier than Should than Nice
    must = [c for c in dedup if c[1] == "Must"]
    should = [c for c in dedup if c[1] == "Should"]
    nice = [c for c in dedup if c[1] == "Nice"]
    buckets = [(must, 0.65), (should, 0.25), (nice, 0.10)]  # total weight budget
    criteria: List[Criterion] = []
    for items, budget in buckets:
        if not items:
            continue
        w = (budget * 100.0) / len(items)
        for txt, tier in items:
            criteria.append(Criterion(name=shorten(txt), weight=round(w, 2), tier=tier, description=txt, keywords=keywords_from_text(txt)))
    # Re-normalize to sum to 100
    total = sum(c.weight for c in criteria)
    if total <= 0:
        return criteria
    factor = 100.0 / total
    for c in criteria:
        c.weight = round(c.weight * factor, 2)
    # Fix rounding drift on last item
    drift = round(100.0 - sum(c.weight for c in criteria), 2)
    if criteria and abs(drift) >= 0.01:
        criteria[-1].weight = round(criteria[-1].weight + drift, 2)
    return criteria


def shorten(text: str, max_len: int = 72) -> str:
    t = re.sub(r"\s+", " ", text.strip())
    return t if len(t) <= max_len else t[: max_len - 1] + "…"


def extract_criteria(jd_text: str, founder_text: Optional[str]) -> List[Criterion]:
    sections = sectionize(jd_text)
    req_bullets = collect_bullets(sections.get("requirements", []))
    resp_bullets = collect_bullets(sections.get("responsibilities", []))

    candidates: List[Tuple[str, str]] = []
    # Requirements
    for b in req_bullets:
        tier = classify_tier(b)
        # Default requirements to Must if no explicit tier words
        if tier in ("Should", "Nice"):
            tier = "Must"
        # demote soft-skill lines to Should unless they include must/degree/years
        if SOFT_SKILL_HINTS.search(b) and not re.search(r"\b(degree|\d+\+?\s*(years|yrs)|must|required)\b", b, re.I):
            tier = "Should"
        candidates.append((b, tier))
    # Responsibilities are often capability/skill → Should by default
    for b in resp_bullets:
        tier = classify_tier(b)
        if not SOFT_SKILL_HINTS.search(b):
            tier = "Should"
        else:
            tier = "Should"
        candidates.append((b, tier))

    # Founder notes can promote or demote certain criteria via hints
    if founder_text:
        lines_ = lines(founder_text)
        for l in lines_:
            m = re.match(r"^(must|should|nice)\s*:\s*(.+)$", l.strip(), re.I)
            if m:
                tier = m.group(1).capitalize()
                text = m.group(2).strip()
                candidates.append((text, tier))

    return normalize_criteria(candidates)


def extract_deal_breakers(jd_text: str, founder_text: Optional[str]) -> List[str]:
    items: List[str] = []
    for l in lines(jd_text):
        low = l.lower()
        if any(re.search(p, low) for p in MUST_PATTERNS + DEAL_BREAKER_HINTS):
            if is_bullet(l) or any(k in low for k in ["must", "required", "authorization", "clearance", "on-site", "in-office"]):
                items.append(re.sub(r"^[-*•] ", "", l).strip())
    if founder_text:
        for l in lines(founder_text):
            low = l.lower()
            if low.startswith("deal:") or low.startswith("dealbreaker:") or "deal breaker" in low:
                items.append(re.sub(r"^(deal:|dealbreaker:)\s*", "", l, flags=re.I).strip())
    # Deduplicate while preserving order
    seen = set()
    out: List[str] = []
    for it in items:
        key = re.sub(r"\s+", " ", it.lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def make_bands() -> Dict[str, Dict[str, str]]:
    return {
        "Must": {
            "meets": "Clearly present; candidate has direct, recent experience or verified qualification.",
            "below": "Missing or only superficial exposure; does not meet hard requirement.",
        },
        "Should": {
            "meets": "Demonstrated capability or strong evidence; can perform with minimal support.",
            "below": "Limited or no evidence; would require significant ramp-up.",
        },
        "Nice": {
            "meets": "Adds meaningful differentiation or accelerates ramp.",
            "below": "Not present (no penalty).",
        },
    }


def verify_outputs(rubric: Rubric, deal_breakers: List[str]) -> bool:
    if not rubric.criteria:
        logger.error("No criteria extracted")
        return False
    total_weight = round(sum(c.weight for c in rubric.criteria), 2)
    if abs(total_weight - 100.0) > 0.05:
        logger.error(f"Weights do not sum to 100 (got {total_weight})")
        return False
    names = [c.name for c in rubric.criteria]
    if len(names) != len(set(names)):
        logger.warning("Duplicate criterion names detected after normalization")
    # Deal breakers can be empty; warn only
    if not isinstance(deal_breakers, list):
        logger.error("deal_breakers is not a list")
        return False
    return True


def write_outputs(out_json: Path, rubric: Rubric, deal_breakers: List[str], dry_run: bool) -> Tuple[Optional[Path], Optional[Path]]:
    out_dir = out_json.parent
    md_path = out_dir / "rubric.md"
    deals_path = out_dir / "deal_breakers.json"

    rubric_json = {
        "job_id": rubric.job_id,
        "criteria": [asdict(c) for c in rubric.criteria],
        "bands": rubric.bands,
    }
    rubric_md = render_rubric_md(rubric)

    if dry_run:
        logger.info("[DRY RUN] Would write: %s", out_json)
        logger.info("[DRY RUN] Would write: %s", md_path)
        logger.info("[DRY RUN] Would write: %s", deals_path)
        return md_path, deals_path

    out_dir.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(rubric_json, indent=2), encoding="utf-8")
    md_path.write_text(rubric_md, encoding="utf-8")
    deals_path.write_text(json.dumps(deal_breakers, indent=2), encoding="utf-8")
    logger.info("Wrote rubric.json → %s", out_json)
    logger.info("Wrote rubric.md → %s", md_path)
    logger.info("Wrote deal_breakers.json → %s", deals_path)
    return md_path, deals_path


def render_rubric_md(rubric: Rubric) -> str:
    lines_md: List[str] = []
    lines_md.append(f"# Rubric — {rubric.job_id}")
    lines_md.append("")
    lines_md.append("## Criteria (sum to 100)")
    lines_md.append("")
    for c in rubric.criteria:
        lines_md.append(f"- {c.name} — {c.weight}% — {c.tier}")
        if c.description and c.description != c.name:
            lines_md.append(f"  - {c.description}")
    lines_md.append("")
    lines_md.append("## Bands")
    for tier, desc in rubric.bands.items():
        lines_md.append(f"- {tier}")
        lines_md.append(f"  - Meets: {desc['meets']}")
        lines_md.append(f"  - Below: {desc['below']}")
    lines_md.append("")
    return "\n".join(lines_md)


def run(jd_path: Path, out_path: Path, founder_notes: Optional[Path], interactive: bool, dry_run: bool) -> int:
    if not jd_path.exists():
        logger.error("JD not found: %s", jd_path)
        return 1
    if founder_notes and not founder_notes.exists():
        logger.error("Founder notes not found: %s", founder_notes)
        return 1

    jd_text = read_text(jd_path)
    founder_text = read_text(founder_notes) if founder_notes else None

    job_id = extract_job_id(jd_path)
    criteria = extract_criteria(jd_text, founder_text)
    bands = make_bands()
    rubric = Rubric(job_id=job_id, criteria=criteria, bands=bands)
    deal_breakers = extract_deal_breakers(jd_text, founder_text)

    if not verify_outputs(rubric, deal_breakers):
        return 1

    # Interactive mode (minimal, tonight): show summary and require confirmation
    if interactive:
        logger.info("Interactive preview:\n%s", render_rubric_md(rubric))
        try:
            resp = input("Accept rubric and write files? [y/N]: ").strip().lower()
        except Exception:
            resp = "n"
        if resp not in ("y", "yes"):
            logger.info("Declined. Exiting without writing.")
            return 0

    write_outputs(out_path, rubric, deal_breakers, dry_run)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="ZoATS Rubric Generator")
    parser.add_argument("--jd", required=True, help="Path to job-description.md")
    parser.add_argument("--out", required=True, help="Path to output rubric.json")
    parser.add_argument("--founder-notes", dest="founder_notes", help="Optional founder notes (md or txt)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--interactive", action="store_true")
    mode.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    interactive = bool(args.interactive and not args.non_interactive)

    try:
        return run(
            jd_path=Path(args.jd).resolve(),
            out_path=Path(args.out).resolve(),
            founder_notes=Path(args.founder_notes).resolve() if args.founder_notes else None,
            interactive=interactive,
            dry_run=bool(args.dry_run),
        )
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
