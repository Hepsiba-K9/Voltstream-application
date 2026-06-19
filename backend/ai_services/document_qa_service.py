from __future__ import annotations

from ai_services.ai_common import AIServiceError, FALLBACK_ANSWER, gemini_model
from ai_services.embedding_service import query_document


def retrieve_document_chunks(question: str, limit: int = 3) -> list[dict[str, str]]:
    """Return retrieved chunks from the shared VoltSenseBot PDF Q&A RAG index."""
    return query_document(question)[:limit]


def answer_from_document(question: str) -> tuple[str, list[dict[str, str]]]:
    chunks = retrieve_document_chunks(question)
    from agents.comments import ADVISOR_AGENT_NAME, record_tool_call

    record_tool_call(
        "RAG Retrieval",
        {"task": "answer_document_question", "question": question},
        {
            "agent": ADVISOR_AGENT_NAME,
            "retrieved_chunks": float(len(chunks)),
            "sources": ", ".join(chunk["source"] for chunk in chunks),
        },
    )

    if not chunks:
        return FALLBACK_ANSWER, []

    answer = generate_answer_from_chunks(question, chunks)
    return answer, chunks


def generate_answer_from_chunks(question: str, chunks: list[dict[str, str]]) -> str:
    from agents.comments import document_qa_prompt

    prompt = document_qa_prompt(question, chunks)
    try:
        response = gemini_model().generate_content(prompt, request_options={"timeout": 20})
    except Exception as exc:
        raise AIServiceError(str(exc)) from exc
    answer = getattr(response, "text", "").strip()
    return answer or FALLBACK_ANSWER
