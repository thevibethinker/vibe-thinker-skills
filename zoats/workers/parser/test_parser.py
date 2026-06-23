#!/usr/bin/env python3
"""Test suite for resume parser worker."""

import json
import subprocess
import sys
from pathlib import Path
from lib.paths import ZOATS_HOME

def run_test(job_id: str, candidate_id: str) -> bool:
    """Run parser on a candidate and validate outputs."""
    print(f"\n{'='*60}")
    print(f"Testing: job={job_id}, candidate={candidate_id}")
    print('='*60)
    
    # Run parser
    result = subprocess.run(
        ["python3", "workers/parser/main.py", "--job", job_id, "--candidate", candidate_id],
        cwd=str(ZOATS_HOME),
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Parser failed with return code {result.returncode}")
        print(f"STDERR: {result.stderr}")
        return False
    
    print(f"✓ Parser executed successfully")
    print(f"Output:\n{result.stderr}")
    
    # Validate outputs
    base_path = ZOATS_HOME / f"jobs/{job_id}/candidates/{candidate_id}/parsed"
    text_file = base_path / "text.md"
    fields_file = base_path / "fields.json"
    
    # Check text.md exists and is non-empty
    if not text_file.exists():
        print(f"❌ text.md not found at {text_file}")
        return False
    
    text_content = text_file.read_text()
    if len(text_content) == 0:
        print(f"❌ text.md is empty")
        return False
    
    print(f"✓ text.md exists ({len(text_content)} chars)")
    
    # Check fields.json exists and has required fields
    if not fields_file.exists():
        print(f"❌ fields.json not found at {fields_file}")
        return False
    
    try:
        fields = json.loads(fields_file.read_text())
    except json.JSONDecodeError as e:
        print(f"❌ fields.json is invalid JSON: {e}")
        return False
    
    print(f"✓ fields.json exists and is valid JSON")
    
    # Validate required fields
    required = ["name", "email", "years_experience"]
    missing = [f for f in required if f not in fields]
    
    if missing:
        print(f"❌ Missing required fields: {missing}")
        return False
    
    print(f"✓ All required fields present: {fields}")
    
    # Validate field types
    if not isinstance(fields["name"], str):
        print(f"❌ 'name' is not a string")
        return False
    
    if fields["email"] is not None and not isinstance(fields["email"], str):
        print(f"❌ 'email' is not a string or null")
        return False
    
    if fields["years_experience"] is not None and not isinstance(fields["years_experience"], int):
        print(f"❌ 'years_experience' is not an integer or null")
        return False
    
    print(f"✓ Field types are correct")
    print(f"\n✓✓✓ Test PASSED for {job_id}/{candidate_id}")
    
    return True

def main():
    """Run all tests."""
    print("Resume Parser Test Suite")
    print("="*60)
    
    tests = [
        ("test-job", "test-001"),  # Markdown
        ("test-job", "vrijen-001"),  # PDF
    ]
    
    results = []
    for job_id, candidate_id in tests:
        try:
            passed = run_test(job_id, candidate_id)
            results.append((job_id, candidate_id, passed))
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append((job_id, candidate_id, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    for job_id, candidate_id, passed in results:
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status}: {job_id}/{candidate_id}")
    
    passed_count = sum(1 for _, _, p in results if p)
    total_count = len(results)
    
    print(f"\nPassed: {passed_count}/{total_count}")
    
    if passed_count == total_count:
        print("✓✓✓ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
