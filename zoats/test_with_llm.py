#!/usr/bin/env python3
"""
Test ZoATS Pipeline with LLM Access

This script tests the full pipeline with real LLM extraction.
Designed to run in Zo environment where ANTHROPIC_API_KEY is available.
"""
import subprocess
import sys
import json
from pathlib import Path
from lib.paths import ZOATS_HOME

def main():
    print("=== Testing ZoATS Pipeline with LLM Extraction ===\n")
    
    # Run pipeline
    result = subprocess.run(
        [sys.executable, "pipeline/run.py", "--job", "test-fixture"],
        cwd=str(ZOATS_HOME),
        capture_output=True,
        text=True
    )
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)
    
    # Parse results
    try:
        output = json.loads(result.stdout)
        summary = output.get("summary", {})
        breakdown = summary.get("decision_breakdown", {})
        
        print("\n=== RESULTS ===")
        print(f"Total candidates: {summary.get('total', 0)}")
        print(f"Decision breakdown:")
        for decision, count in breakdown.items():
            print(f"  {decision}: {count}")
        
        # Check each candidate
        print("\n=== CANDIDATE DETAILS ===")
        for cand_result in output.get("candidates", []):
            cand_id = cand_result.get("candidate_id", "unknown")
            decision = cand_result.get("decision", "UNKNOWN")
            print(f"{cand_id}: {decision}")
            
            # Read full evaluation
            eval_path = ZOATS_HOME / f"jobs/test-fixture/candidates/{cand_id}/outputs/gestalt_evaluation.json"
            if eval_path.exists():
                eval_data = json.loads(eval_path.read_text())
                print(f"  Confidence: {eval_data.get('confidence')}")
                print(f"  Narrative: {eval_data.get('overall_narrative')}")
                print(f"  Strengths: {len(eval_data.get('key_strengths', []))}")
                print(f"  Concerns: {len(eval_data.get('concerns', []))}")
                print()
        
        return 0
        
    except Exception as e:
        print(f"\nError parsing results: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
