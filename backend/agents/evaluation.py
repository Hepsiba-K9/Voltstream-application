from typing import Any

from ai_services.ai_common import AIServiceError, gemini_model
from ai_services.document_qa_service import answer_from_document, retrieve_document_chunks
from agents.comments import general_chat_prompt


EVALUATION_QUESTIONS: list[str] = [
    "What is energy efficiency and why is it important for reducing costs and emissions?",
    "What are the recommended solar panel tilt angle and placement for maximum output?",
    "What are the fastest low-cost actions to reduce home energy use?",
    "Which appliances are good candidates for load shifting to solar production hours?",
    "Why should panels be kept clear of shade between 9 a.m. and 3 p.m.?",
    "What does a high grid draw during bright midday hours typically indicate?",
    "What are modern technologies used to improve energy efficiency?",
    "What does a sudden increase in night usage often point to?",
    "What are the main challenges limiting energy efficiency improvements?",
    "How do smart grids and energy management systems contribute to efficiency?",
]




def _create_evaluation_prompt(question: str, answer: str, context: str) -> str:
    """Create a prompt for LLM to evaluate answer faithfulness and relevance."""
    return f"""You are an expert evaluator. Evaluate the following answer based on TWO criteria:

QUESTION: {question}

ANSWER: {answer}

CONTEXT (from energy efficiency documents): {context}

Evaluate on a scale of 1-5:
1. FAITHFULNESS (is the answer grounded in the provided context/documents?):
   - Score 1-2: Answer contradicts or is not supported by context
   - Score 3: Answer partially supported by context
   - Score 4-5: Answer is well-grounded in context

2. RELEVANCE (does the answer directly address the question?):
   - Score 1-2: Answer doesn't address the question
   - Score 3: Answer partially addresses the question
   - Score 4-5: Answer directly and completely addresses the question

Respond ONLY with this format (no other text):
FAITHFULNESS: <score 1-5>
RELEVANCE: <score 1-5>
PASS: <YES or NO (YES if both scores >= 4, NO otherwise)>"""


def evaluate_answer_with_llm(question: str, answer: str) -> dict[str, Any]:
    """Use LLM to evaluate an answer for faithfulness and relevance.
    
    Returns:
        {
            "question": str,
            "answer": str,
            "faithfulness_score": int (1-5),
            "relevance_score": int (1-5),
            "pass": bool
        }
    """
    try:
        # Retrieve relevant document chunks
        chunks = retrieve_document_chunks(question, limit=3)
        context = "\n".join([chunk.get("text", "") for chunk in chunks])
        
        if not context.strip():
            context = "No relevant documents found."
        
        # Create evaluation prompt
        eval_prompt = _create_evaluation_prompt(question, answer, context)
        
        # Get LLM evaluation
        model = gemini_model()
        response = model.generate_content(
            general_chat_prompt(eval_prompt),
            request_options={"timeout": 60},
        )
        
        eval_text = (response.text or "").strip()
        
        # Parse evaluation response
        faithfulness_score = 3
        relevance_score = 3
        passed = False
        
        for line in eval_text.split("\n"):
            if "FAITHFULNESS:" in line:
                try:
                    faithfulness_score = int(line.split(":")[-1].strip().split()[0])
                except (ValueError, IndexError):
                    faithfulness_score = 3
            elif "RELEVANCE:" in line:
                try:
                    relevance_score = int(line.split(":")[-1].strip().split()[0])
                except (ValueError, IndexError):
                    relevance_score = 3
            elif "PASS:" in line:
                passed = "YES" in line.upper()
        
        return {
            "question": question,
            "answer": answer,
            "faithfulness_score": faithfulness_score,
            "relevance_score": relevance_score,
            "pass": passed or (faithfulness_score >= 4 and relevance_score >= 4),
        }
    
    except Exception as exc:
        raise AIServiceError(f"Answer evaluation failed: {exc}") from exc


def run_dynamic_evaluation() -> dict[str, Any]:
    """Run dynamic LLM-based evaluation on all questions.
    
    Returns evaluation summary with:
    - Individual answer scores
    - Pass/fail status per question
    - Overall pass/fail result
    """
    results = []
    passed_count = 0
    
    for question in EVALUATION_QUESTIONS:
        try:
            # Get answer from advisor agent's document QA
            answer, _ = answer_from_document(question)
            
            # Evaluate answer with LLM
            evaluation = evaluate_answer_with_llm(question, answer)
            results.append(evaluation)
            
            if evaluation["pass"]:
                passed_count += 1
        
        except Exception as exc:
            results.append({
                "question": question,
                "answer": f"Error: {str(exc)}",
                "faithfulness_score": 0,
                "relevance_score": 0,
                "pass": False,
            })
    
    total = len(EVALUATION_QUESTIONS)
    failed_count = total - passed_count
    final_result = "PASS" if passed_count >= 7 else "FAIL"
    
    return {
        "total_questions_tested": total,
        "passed": passed_count,
        "failed": failed_count,
        "final_result": final_result,
        "pass_condition": "At least 7 out of 10 answers should pass.",
        "results": results,
    }


def get_agent_evaluation_summary() -> dict[str, Any]:
    """Return evaluation metadata for API responses.
    
    Note: This returns static metadata, not actual evaluation results.
    Run run_dynamic_evaluation() for actual test results.
    """
    return {
        "total_questions_tested": len(EVALUATION_QUESTIONS),
        "pass_condition": "At least 7 out of 10 answers should pass.",
        "evaluation_type": "LLM-based (dynamic)",
    }


def format_local_evaluation() -> str:
    return "\n".join([
        "Agent Evaluation",
        "",
        f"Total Questions Tested: {len(EVALUATION_QUESTIONS)}",
        f"Pass Condition: At least 7 out of 10 answers should pass.",
        f"Evaluation Type: LLM-based (dynamic)",
        "",
        "Evaluation Questions:",
        *[f"{index}. {question}" for index, question in enumerate(EVALUATION_QUESTIONS, start=1)],
    ])


if __name__ == "__main__":
    import json
    import time
    
    print("=" * 80)
    print("🔄 Running Week 6 Dynamic LLM-Based Evaluation Report...")
    print("=" * 80)
    
    start = time.time()
    
    try:
        results = run_dynamic_evaluation()
        elapsed = time.time() - start
        
        # Print formatted summary
        print(f"\n📊 EVALUATION SUMMARY")
        print(f"   Total Questions: {results['total_questions_tested']}")
        print(f"   ✅ Passed: {results['passed']}/10")
        print(f"   ❌ Failed: {results['failed']}/10")
        print(f"   Final Result: {results['final_result']}")
        print(f"   Execution Time: {elapsed:.2f}s")
        print(f"   Pass Condition: {results['pass_condition']}")
        
        # Print detailed results
        print(f"\n📋 DETAILED RESULTS")
        print("-" * 80)
        for i, result in enumerate(results['results'], 1):
            status = "✅ PASS" if result['pass'] else "❌ FAIL"
            print(f"\n{i}. {status}")
            print(f"   Question: {result['question']}")
            print(f"   Faithfulness Score: {result['faithfulness_score']}/5")
            print(f"   Relevance Score: {result['relevance_score']}/5")
            answer_preview = result['answer'][:100].replace('\n', ' ')
            print(f"   Answer: {answer_preview}...")
        
        print("\n" + "=" * 80)
        print(f"✅ Evaluation completed in {elapsed:.2f}s")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error running evaluation: {str(e)}")
        print("=" * 80)
        raise
