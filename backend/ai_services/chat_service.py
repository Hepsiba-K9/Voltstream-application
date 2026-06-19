from __future__ import annotations

from ai_services.ai_common import AIServiceError, gemini_model
from ai_services.document_loader import load_document_text_from_bytes, safe_document_name
from ai_services.text_chunker import chunk_text
from agents.comments import general_chat_prompt, uploaded_document_chat_prompt

CHAT_UPLOADED_DOCUMENT: dict[str, str] = {}


def generate_chat_response(message: str) -> str:
    model = gemini_model()
    try:
        response = model.generate_content(
            general_chat_prompt(message),
            request_options={"timeout": 60},
        )
    except Exception as exc:  # pragma: no cover - depends on external API state
        raise AIServiceError(f"Gemini chat request failed: {exc}") from exc

    answer = (response.text or "").strip()
    if not answer:
        raise AIServiceError("Gemini returned an empty response.")
    return answer


def generate_chat_response_from_upload(message: str) -> str:
    document_text = CHAT_UPLOADED_DOCUMENT.get("text", "").strip()
    if not document_text:
        return generate_chat_response(message)

    model = gemini_model()
    try:
        response = model.generate_content(
            uploaded_document_chat_prompt(message, document_text),
            request_options={"timeout": 60},
        )
    except Exception as exc:  # pragma: no cover - depends on external API state
        raise AIServiceError(f"Gemini chat request failed: {exc}") from exc

    answer = (response.text or "").strip()
    if not answer:
        raise AIServiceError("Gemini returned an empty response.")
    return answer


def upload_chat_document_to_memory(filename: str, content: bytes) -> dict[str, str | int | bool]:
    safe_name = safe_document_name(filename)
    if not safe_name:
        raise AIServiceError("Upload a PDF or text document.")

    document_text = load_document_text_from_bytes(safe_name, content).strip()
    if not document_text:
        raise AIServiceError("No readable text was found in the uploaded document.")

    CHAT_UPLOADED_DOCUMENT.clear()
    CHAT_UPLOADED_DOCUMENT.update({"filename": safe_name, "text": document_text})
    return {
        "filename": safe_name,
        "chunk_count": len(chunk_text(document_text, max_words=220)),
        "is_default": False,
    }


def chat_should_use_uploaded_document() -> bool:
    return bool(CHAT_UPLOADED_DOCUMENT.get("text", "").strip())
