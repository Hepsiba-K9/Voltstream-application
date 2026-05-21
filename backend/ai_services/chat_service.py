from __future__ import annotations

import re

from ai_services.ai_common import AIServiceError, gemini_model
from ai_services.document_loader import load_document_text_from_bytes, safe_document_name
from ai_services.text_chunker import chunk_text

CHAT_UPLOADED_DOCUMENT: dict[str, str] = {}


def generate_chat_response(message: str) -> str:
    message = normalize_general_energy_question(message)
    model = gemini_model()
    try:
        response = model.generate_content(
            [
                "You are VoltSenseBot, a helpful Gemini-powered assistant inside the VoltStream app. "
                "Answer the user's question directly and correctly on any topic. Be concise by default, "
                "and give practical energy guidance when the question is about energy, solar, devices, or billing.",
                message,
            ],
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

    question = normalize_uploaded_document_question(message, document_text)
    model = gemini_model()
    try:
        response = model.generate_content(
            [
                "You are VoltSenseBot, a practical energy assistant. Use the uploaded document text when the user's "
                "question is about that document, asks for a summary, asks for key topics, or asks for an example from it. "
                "If the uploaded document does not contain the answer, answer normally using your general energy knowledge. "
                "Do not answer as a search/software topic when the user likely means an energy term; for example, interpret "
                "'solr' as 'solar' in energy questions.",
                f"Uploaded document text:\n{document_text[:24000]}",
                f"Question: {question}",
            ],
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


def normalize_general_energy_question(message: str) -> str:
    if not is_energy_related_message(message):
        return message

    simple_corrections = {
        r"\bsolr\b": "solar",
        r"\bsolor\b": "solar",
        r"\bsloar\b": "solar",
        r"\bpanal\b": "panel",
        r"\bpanals\b": "panels",
        r"\benergry\b": "energy",
    }
    normalized = message
    for pattern, replacement in simple_corrections.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    if normalized == message:
        return message
    return f"{normalized}\n\nNote: The user question appears to contain a typo. Interpret it as: {normalized}"


def is_energy_related_message(message: str) -> bool:
    normalized = message.lower()
    energy_terms = {
        "appliance",
        "battery",
        "bill",
        "billing",
        "charger",
        "current",
        "device",
        "electric",
        "electricity",
        "energy",
        "grid",
        "inverter",
        "kwh",
        "load",
        "meter",
        "panel",
        "power",
        "solar",
        "tariff",
        "usage",
        "volt",
        "voltage",
        "watt",
    }
    words = set(re.findall(r"[a-zA-Z0-9]+", normalized))
    return bool(words & energy_terms)


def normalize_uploaded_document_question(message: str, document_text: str = "") -> str:
    normalized = " ".join(message.lower().split()).strip(" ?.!:")
    broad_followups = {
        "explain with an example",
        "explain this with an example",
        "explain with example",
        "make this more practical",
        "give me 3 quick steps",
        "give me three quick steps",
        "what is most important",
        "what should i ask next",
    }
    if normalized in broad_followups:
        return f"Based on the uploaded document, {message}."
    return correct_question_typos_from_document(message, document_text)


def correct_question_typos_from_document(message: str, document_text: str) -> str:
    if not document_text:
        return message

    document_words = {
        word
        for word in re.findall(r"[a-zA-Z]{4,}", document_text.lower())
        if word not in common_words()
    }
    if not document_words:
        return message

    corrected_words: list[str] = []
    changed = False
    for part in re.split(r"(\W+)", message):
        lowered = part.lower()
        if not lowered.isalpha() or len(lowered) < 4 or lowered in document_words or lowered in common_words():
            corrected_words.append(part)
            continue

        match = nearest_word(lowered, document_words)
        if match is None:
            corrected_words.append(part)
            continue

        corrected_words.append(match_case(part, match))
        changed = True

    corrected = "".join(corrected_words)
    if not changed:
        return message
    return f"{corrected}\n\nNote: The user question appears to contain a typo. Interpret it as: {corrected}"


def nearest_word(word: str, candidates: set[str]) -> str | None:
    best_word = None
    best_distance = 3
    for candidate in candidates:
        if abs(len(candidate) - len(word)) > 1:
            continue
        distance = edit_distance_at_most(word, candidate, best_distance)
        if distance < best_distance:
            best_distance = distance
            best_word = candidate
    return best_word


def edit_distance_at_most(left: str, right: str, limit: int) -> int:
    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        row_min = current[0]
        for right_index, right_char in enumerate(right, start=1):
            cost = 0 if left_char == right_char else 1
            current.append(
                min(
                    previous[right_index] + 1,
                    current[right_index - 1] + 1,
                    previous[right_index - 1] + cost,
                )
            )
            row_min = min(row_min, current[-1])
        if row_min >= limit:
            return limit
        previous = current
    return previous[-1]


def match_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement.capitalize()
    return replacement


def common_words() -> set[str]:
    return {
        "about",
        "answer",
        "document",
        "explain",
        "from",
        "give",
        "have",
        "information",
        "main",
        "that",
        "this",
        "what",
        "with",
    }
