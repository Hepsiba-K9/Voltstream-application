#!/usr/bin/env python
"""Week 6 RAG Evaluation Report Runner"""

import json
import time
from pathlib import Path

from dotenv import load_dotenv
from agents.evaluation import run_dynamic_evaluation

# Load environment variables from .env file
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

if __name__ == "__main__":
    print("=" * 80)
    print("🔄 Running Week 6 Dynamic LLM-Based Evaluation Report...")
    print("=" * 80)
    
    start = time.time()
    
    try:
        results = run_dynamic_evaluation()
        elapsed = time.time() - start
        
        # Print formatted summary
        print(f"\n EVALUATION SUMMARY")
        print(f"   Total Questions: {results['total_questions_tested']}")
        print(f"    Passed: {results['passed']}/10")
        print(f"    Failed: {results['failed']}/10")
        print(f"   Final Result: {results['final_result']}")
        print(f"   Execution Time: {elapsed:.2f}s")
        print(f"   Pass Condition: {results['pass_condition']}")
        
        # Print detailed results
        print(f"\n DETAILED RESULTS")
        print("-" * 80)
        for i, result in enumerate(results['results'], 1):
            status = "PASS" if result['pass'] else " FAIL"
            print(f"\n{i}. {status}")
            print(f"   Question: {result['question']}")
            print(f"   Faithfulness Score: {result['faithfulness_score']}/5")
            print(f"   Relevance Score: {result['relevance_score']}/5")
            answer_preview = result['answer'][:100].replace('\n', ' ')
            print(f"   Answer: {answer_preview}...")
        
        # Save full report to JSON
        print("\n" + "=" * 80)
        with open("evaluation_report.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"Full report saved to: evaluation_report.json")
        print(f" Evaluation completed successfully in {elapsed:.2f}s")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n Error running evaluation: {str(e)}")
        print("=" * 80)
        raise
