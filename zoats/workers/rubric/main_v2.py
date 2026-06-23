import sys as _sys
from pathlib import Path as _Path
_REPO_ROOT = _Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))
import sys
from pathlib import Path
from workers.rubric.llm_generator import generate_rubric_llm as generate_rubric_payload
#!/usr/bin/env python3
"""
Rubric Generator v2

Semantic extraction using LLM + role templates.
Generates comprehensive rubrics with 15-25 criteria (explicit + implicit).

Usage:
  python workers/rubric/main_v2.py \\
    --jd jobs/<job>/job-description.md \\
    --out jobs/<job>/rubric.json \\
    [--founder-notes path/to/notes.md] \\
    [--role-type management-consultant|software-engineer|product-manager] \\
    [--dry-run]

Design:
- Load role template (default criteria)
- LLM analyzes JD → customizes template
- Evidence-based weighting
- Evaluation guidance for 0-10 scoring
- Structured outputs (Pydantic)

Quality:
- Logging, --dry-run, error handling, verification
"""
import argparse
import json
import logging
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional, Literal
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Structured output models
@dataclass
class Criterion:
    id: str
    name: str
    description: str
    weight: float
    tier: Literal["must", "should", "nice"]
    evaluation_guidance: Dict[str, str]  # {"9-10": "...", "7-8": "...", ...}
    keywords: List[str]
    jd_evidence: Optional[str] = None  # Where in JD this came from

@dataclass
class Rubric:
    job_id: str
    job_title: str
    role_type: str
    criteria: List[Criterion]
    deal_breakers: List[str]
    meta_signals: Dict[str, str]
    created_at: str
    source: str = "rubric_v2"
    
    def validate(self) -> bool:
        """Verify rubric integrity"""
        total_weight = sum(c.weight for c in self.criteria)
        if abs(total_weight - 100.0) > 0.1:
            logger.error(f"Weights sum to {total_weight}, not 100")
            return False
        if not (15 <= len(self.criteria) <= 25):
            logger.warning(f"Criteria count {len(self.criteria)} outside recommended range (15-25)")
        return True


def load_role_template(role_type: str) -> Dict:
    """Load default criteria for role type"""
    template_path = Path(__file__).parent.parent.parent / "data" / "role_templates" / f"{role_type}.json"
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    with open(template_path) as f:
        return json.load(f)


def detect_role_type(jd_text: str) -> str:
    """Heuristic role detection from JD"""
    jd_lower = jd_text.lower()
    
    # Simple keyword matching (can be improved with LLM)
    if any(kw in jd_lower for kw in ["consultant", "consulting", "strategy", "advisory", "client"]):
        return "management-consultant"
    elif any(kw in jd_lower for kw in ["engineer", "software", "developer", "programming", "coding"]):
        return "software-engineer"
    elif any(kw in jd_lower for kw in ["product manager", "product lead", "pm", "product strategy"]):
        return "product-manager"
    
    # Default fallback
    logger.warning("Could not detect role type, defaulting to management-consultant")
    return "management-consultant"


def build_rubric_with_llm(jd_text: str, template: Dict, founder_notes: Optional[str] = None, jd_path: Optional[Path] = None) -> Rubric:
    """
    Use LLM to generate rubric from template + JD.
    
    This is where the magic happens:
    1. LLM reads JD + template
    2. Customizes criteria based on JD specifics
    3. Adds implicit requirements
    4. Assigns evidence-based weights
    5. Returns structured JSON
    """
    # Extract metadata
    job_lines = jd_text.split('\n')
    job_title = "Unknown"
    for line in job_lines[:20]:
        if line.strip() and not line.startswith('#') and not line.startswith('<!--'):
            job_title = line.strip()
            break
    
    # Derive job_id from path
    job_id = jd_path.parent.name if jd_path else "unknown"
    
    # Build prompt
    prompt = f"""You are an expert recruiter analyzing a job description to create a comprehensive scoring rubric.

# Role Template (Starting Point)
{json.dumps(template['default_criteria'], indent=2)}

# Job Description
{jd_text}

{f"# Founder Notes\\n{founder_notes}" if founder_notes else ""}

# Task
Generate a comprehensive rubric with 15-25 criteria that captures:
1. **Explicit requirements** from the JD (degrees, years of experience, skills)
2. **Implicit requirements** that aren't stated but are critical for this role
3. **Role-specific excellence indicators** (what separates good from great candidates)

For each criterion:
- Provide a unique id (snake_case)
- Clear name and description
- Weight (0-100, total must sum to 100)
- Tier: "must" (critical), "should" (important), "nice" (differentiator)
- Evaluation guidance for score bands: 9-10, 7-8, 5-6, 3-4, 0-2
- Keywords for resume matching
- JD evidence (quote the relevant JD text)

Weighting guidelines:
- "must" tier: 60-70% of total weight
- "should" tier: 20-30% of total weight
- "nice" tier: 5-15% of total weight

Also extract:
- Deal breakers (hard requirements that disqualify if missing)
- Meta signals to track (trajectory, achievement density, etc.)

Return valid JSON matching this schema:
{{
  "criteria": [
    {{
      "id": "criterion_id",
      "name": "Criterion Name",
      "description": "What this measures",
      "weight": 15.5,
      "tier": "must",
      "evaluation_guidance": {{
        "9-10": "Exceptional evidence",
        "7-8": "Strong evidence",
        "5-6": "Adequate evidence",
        "3-4": "Weak evidence",
        "0-2": "No evidence"
      }},
      "keywords": ["keyword1", "keyword2"],
      "jd_evidence": "Quote from JD"
    }}
  ],
  "deal_breakers": ["Must have X", "Must be authorized to work"],
  "meta_signals": {{
    "trajectory": "Description",
    "achievement_density": "Description"
  }}
}}

Be specific in evaluation guidance. Make it actionable for scoring.
"""

    # Call LLM (simulated here; replace with actual LLM call)
    # For now, we'll use a hybrid approach: template + JD heuristics
    logger.info("Generating rubric with LLM...")
    
    # TODO: Replace with actual LLM call
    # For MVP, we'll use the template with JD-specific adjustments
    rubric_data = generate_rubric_payload(jd_text, job_title)
    if not rubric_data or "criteria" not in rubric_data:
        rubric_data = _fallback_rubric_generation(jd_text, template, job_title)
    
    # Parse and validate
    criteria = [Criterion(**c) for c in rubric_data['criteria']]
    
    rubric = Rubric(
        job_id=job_id,
        job_title=job_title,
        role_type=template['role_type'],
        criteria=criteria,
        deal_breakers=rubric_data.get('deal_breakers', []),
        meta_signals=rubric_data.get('meta_signals', template.get('meta_signals', {})),
        created_at=datetime.utcnow().isoformat() + "Z"
    )
    
    if not rubric.validate():
        raise ValueError("Rubric validation failed")
    
    return rubric


def _fallback_rubric_generation(jd_text: str, template: Dict, job_title: str) -> Dict:
    """
    Fallback rubric generation using heuristics.
    This is a placeholder until we integrate actual LLM calls.
    """
    import re
    
    # Start with template criteria
    criteria = []
    for c in template['default_criteria']:
        # Check if JD mentions this criterion
        keywords = c.get('keywords', [])
        mentions = sum(1 for kw in keywords if re.search(rf'\b{re.escape(kw)}\b', jd_text, re.I))
        
        # Adjust weight based on JD emphasis
        base_weight = c['weight']
        if mentions > 0:
            # Find evidence in JD
            evidence_lines = []
            for line in jd_text.split('\n'):
                if any(kw.lower() in line.lower() for kw in keywords):
                    evidence_lines.append(line.strip())
                    if len(evidence_lines) >= 2:
                        break
            jd_evidence = " | ".join(evidence_lines[:2]) if evidence_lines else "Implicit requirement"
        else:
            jd_evidence = "Template criterion (adjust if not relevant)"
        
        criteria.append({
            'id': c.get('id', c['name'].lower().replace(' ', '_')),
            'name': c['name'],
            'description': c['description'],
            'weight': base_weight,
            'tier': c['tier'],
            'evaluation_guidance': c['evaluation_guidance'],
            'keywords': c.get('keywords', []),
            'jd_evidence': jd_evidence
        })
    
    # Normalize weights to sum to 100
    total = sum(c['weight'] for c in criteria)
    for c in criteria:
        c['weight'] = round((c['weight'] / total) * 100, 2)
    
    # Extract deal breakers
    deal_breaker_patterns = [
        r'must\s+(?:have|be)\s+(.+?)(?:\.|;|\n)',
        r'required:\s+(.+?)(?:\.|;|\n)',
        r'authorization\s+to\s+work',
        r'\d+\+?\s*years?\s+(?:of\s+)?(?:experience|exp)',
        r'(?:bachelor|master|phd|degree)\s+(?:required|in)',
    ]
    
    deal_breakers = []
    for pattern in deal_breaker_patterns:
        matches = re.findall(pattern, jd_text, re.I | re.M)
        deal_breakers.extend(matches[:3])  # Limit to prevent noise
    
    return {
        'criteria': criteria,
        'deal_breakers': deal_breakers[:5],  # Top 5
        'meta_signals': template.get('meta_signals', {})
    }


def write_outputs(rubric: Rubric, out_path: Path, dry_run: bool = False):
    """Write rubric.json, rubric.md, deal_breakers.json"""
    out_dir = out_path.parent
    stem = out_path.stem
    
    # rubric.json
    rubric_json_path = out_dir / f"{stem}.json"
    rubric_md_path = out_dir / f"{stem}.md"
    deal_breakers_path = out_dir / "deal_breakers.json"
    
    if dry_run:
        logger.info(f"[DRY RUN] Would write: {rubric_json_path}")
        logger.info(f"[DRY RUN] Would write: {rubric_md_path}")
        logger.info(f"[DRY RUN] Would write: {deal_breakers_path}")
        return
    
    # Write JSON
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(rubric_json_path, 'w') as f:
        json.dump(asdict(rubric), f, indent=2)
    logger.info(f"Wrote rubric.json → {rubric_json_path}")
    
    # Write Markdown
    md_content = f"""# Rubric — {rubric.job_title}

**Role Type:** {rubric.role_type}  
**Created:** {rubric.created_at}  
**Criteria Count:** {len(rubric.criteria)}

---

## Criteria (sum to {sum(c.weight for c in rubric.criteria):.1f})

"""
    
    for tier in ["must", "should", "nice"]:
        tier_criteria = [c for c in rubric.criteria if c.tier == tier]
        if not tier_criteria:
            continue
        
        md_content += f"\n### {tier.capitalize()} ({sum(c.weight for c in tier_criteria):.1f}%)\n\n"
        
        for c in tier_criteria:
            md_content += f"**{c.name}** — {c.weight:.1f}%\n"
            md_content += f"- {c.description}\n"
            md_content += f"- Evidence: {c.jd_evidence}\n"
            md_content += f"- Keywords: {', '.join(c.keywords)}\n"
            md_content += f"- Evaluation:\n"
            for band, guidance in c.evaluation_guidance.items():
                md_content += f"  - {band}: {guidance}\n"
            md_content += "\n"
    
    md_content += f"""---

## Deal Breakers

{chr(10).join(f"- {db}" for db in rubric.deal_breakers) if rubric.deal_breakers else "*None identified*"}

---

## Meta Signals

{chr(10).join(f"- **{k}**: {v}" for k, v in rubric.meta_signals.items())}
"""
    
    with open(rubric_md_path, 'w') as f:
        f.write(md_content)
    logger.info(f"Wrote rubric.md → {rubric_md_path}")
    
    # Write deal breakers
    with open(deal_breakers_path, 'w') as f:
        json.dump(rubric.deal_breakers, f, indent=2)
    logger.info(f"Wrote deal_breakers.json → {deal_breakers_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Rubric Generator v2")
    parser.add_argument("--jd", required=True, help="Path to job-description.md")
    parser.add_argument("--out", required=True, help="Path to output rubric.json")
    parser.add_argument("--founder-notes", dest="founder_notes", help="Optional founder notes")
    parser.add_argument("--role-type", dest="role_type", 
                       choices=["management-consultant", "software-engineer", "product-manager"],
                       help="Role type (auto-detected if not specified)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    try:
        # Load JD
        jd_path = Path(args.jd).resolve()
        if not jd_path.exists():
            raise FileNotFoundError(f"JD not found: {jd_path}")
        jd_text = jd_path.read_text()
        
        # Load founder notes
        founder_text = None
        if args.founder_notes:
            founder_path = Path(args.founder_notes).resolve()
            if founder_path.exists():
                founder_text = founder_path.read_text()
        
        # Detect or use specified role type
        role_type = args.role_type or detect_role_type(jd_text)
        logger.info(f"Role type: {role_type}")
        
        # Load template
        template = load_role_template(role_type)
        logger.info(f"Loaded template with {len(template['default_criteria'])} default criteria")
        
        # Generate rubric
        rubric = build_rubric_with_llm(jd_text, template, founder_text, jd_path=jd_path)
        logger.info(f"Generated rubric with {len(rubric.criteria)} criteria")
        
        # Write outputs
        write_outputs(rubric, Path(args.out).resolve(), dry_run=args.dry_run)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
