#!/usr/bin/env python3
"""
ZoATS Gestalt System Smoke Test
Fixture-driven validation for test-fixture
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict

import jsonschema
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.paths import ZOATS_HOME

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)sZ %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

JOB_ID = "test-fixture"
CANDIDATES = ["candidate-alpha", "candidate-beta"]
VALID_DECISIONS = ["STRONG_INTERVIEW", "INTERVIEW", "MAYBE", "PASS", "BACKUP_LIST", "UNKNOWN"]
BASE_PATH = ZOATS_HOME / "jobs"


class TestFailure(Exception):
    """Test failure exception"""
    pass


def verify_file_exists(path: Path, description: str) -> bool:
    """Verify file exists and is non-empty"""
    if not path.exists():
        raise TestFailure(f"Missing: {description} at {path}")
    
    if path.is_file() and path.stat().st_size == 0:
        raise TestFailure(f"Empty file: {description} at {path}")
    
    if path.is_dir():
        logger.info(f"✓ {description} exists (dir)")
    else:
        logger.info(f"✓ {description} exists ({path.stat().st_size} bytes)")
    return True


def load_schema(path: Path) -> Dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise TestFailure(f"Failed to load schema at {path}: {e}")


def validate_json_against_schema(data: Dict, schema: Dict, desc: str) -> None:
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        raise TestFailure(f"Schema validation failed for {desc}: {e.message}")


def verify_gestalt_evaluation(path: Path, candidate: str) -> Dict:
    """Verify gestalt_evaluation.json is valid and complete"""
    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise TestFailure(f"Invalid JSON in {candidate} gestalt_evaluation: {e}")
    
    # Validate decision
    decision = data.get("decision")
    if decision not in VALID_DECISIONS:
        raise TestFailure(
            f"{candidate}: Invalid decision '{decision}'. "
            f"Expected one of {VALID_DECISIONS}"
        )
    
    confidence = data.get("confidence")
    if confidence is not None and confidence not in ["high", "medium", "low"]:
        raise TestFailure(
            f"{candidate}: Invalid confidence '{confidence}'. Expected high/medium/low"
        )
    
    logger.info(f"✓ {candidate}: Valid gestalt ({decision})")
    return data


def verify_dossier(path: Path, candidate: str) -> None:
    """Verify dossier.md exists and has content"""
    content = path.read_text()
    
    # Check for key sections
    required_sections = [
        "# Candidate Dossier",
        "## Executive Summary",
        "## Key Strengths",
        "## Concerns"
    ]
    
    missing_sections = [s for s in required_sections if s not in content]
    if missing_sections:
        logger.warning(
            f"{candidate}: Dossier missing sections: {missing_sections}"
        )
    
    if len(content) < 500:
        logger.warning(
            f"{candidate}: Dossier seems short ({len(content)} chars)"
        )
    
    logger.info(f"✓ {candidate}: Valid dossier ({len(content)} chars)")


def collect_decision_distribution(evaluations: Dict[str, Dict]) -> Dict[str, int]:
    """Collect decision distribution across candidates"""
    distribution = {d: 0 for d in VALID_DECISIONS}
    
    for candidate, data in evaluations.items():
        decision = data.get("decision")
        if decision:
            distribution[decision] += 1
    
    return distribution


def main() -> int:
    """Run smoke test"""
    logger.info(f"Starting smoke test for job {JOB_ID}")
    logger.info(f"Testing {len(CANDIDATES)} candidates: {', '.join(CANDIDATES)}")
    
    job_path = BASE_PATH / JOB_ID
    if not job_path.exists():
        logger.error(f"Job directory not found: {job_path}")
        return 1
    
    # Validate job contract files + schema
    failures = []
    try:
        verify_file_exists(job_path / "job-description.md", "job-description.md")
        verify_file_exists(job_path / "rubric.json", "rubric.json")
        verify_file_exists(job_path / "deal_breakers.json", "deal_breakers.json")
        verify_file_exists(job_path / "metadata.json", "metadata.json")

        job_schema = load_schema(ZOATS_HOME / "schemas" / "job.schema.json")
        job_meta = json.loads((job_path / "metadata.json").read_text(encoding="utf-8"))
        validate_json_against_schema(job_meta, job_schema, "job metadata.json")
        logger.info("✓ job metadata.json validates against job.schema.json")
    except TestFailure as e:
        logger.error(f"✗ job contract/schema: {e}")
        failures.append(("job", str(e)))
    except Exception as e:
        logger.error(f"✗ job contract/schema: Unexpected error: {e}", exc_info=True)
        failures.append(("job", f"Unexpected error: {e}"))
    
    evaluations = {}
    
    # Test each candidate
    for candidate in CANDIDATES:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing candidate: {candidate}")
        logger.info(f"{'='*60}")
        
        candidate_path = job_path / "candidates" / candidate
        
        try:
            # Check directory exists
            if not candidate_path.exists():
                raise TestFailure(f"Candidate directory not found: {candidate_path}")
            
            # Check raw resume
            raw_resume = candidate_path / "raw" / "resume.txt"
            verify_file_exists(raw_resume, f"{candidate} raw resume.txt")
            
            logger.info(f"✓ {candidate}: ALL CHECKS PASSED")
            
        except TestFailure as e:
            logger.error(f"✗ {candidate}: {e}")
            failures.append((candidate, str(e)))
        except Exception as e:
            logger.error(f"✗ {candidate}: Unexpected error: {e}", exc_info=True)
            failures.append((candidate, f"Unexpected error: {e}"))
    
    # Validate pipeline_run.json if present (written only on non-dry-run); for dry-run, pipeline prints JSON
    pipeline_run = job_path / "pipeline_run.json"
    if pipeline_run.exists():
        try:
            data = json.loads(pipeline_run.read_text(encoding="utf-8"))
            if data.get("job") != JOB_ID:
                raise TestFailure(f"pipeline_run.json job mismatch: {data.get('job')}")
            if "candidate_results" not in data or not isinstance(data["candidate_results"], list):
                raise TestFailure("pipeline_run.json missing candidate_results list")
            if "summary" not in data or not isinstance(data["summary"], dict):
                raise TestFailure("pipeline_run.json missing summary object")
            logger.info("✓ pipeline_run.json structure looks valid")
        except TestFailure as e:
            logger.error(f"✗ pipeline_run.json: {e}")
            failures.append(("pipeline_run.json", str(e)))
        except Exception as e:
            logger.error(f"✗ pipeline_run.json: Unexpected error: {e}", exc_info=True)
            failures.append(("pipeline_run.json", f"Unexpected error: {e}"))
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("SUMMARY")
    logger.info(f"{'='*60}")
    
    passed = len(CANDIDATES) - len(failures)
    logger.info(f"Candidates tested: {len(CANDIDATES)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {len(failures)}")
    
    if failures:
        logger.error("\nFAILURES:")
        for candidate, error in failures:
            logger.error(f"  {candidate}: {error}")
        return 1
    
    logger.info("\n✓ ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    exit(main())
