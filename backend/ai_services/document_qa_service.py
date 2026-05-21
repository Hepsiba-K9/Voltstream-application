from __future__ import annotations

import re

from ai_services.ai_common import FALLBACK_ANSWER
from ai_services.embedding_service import query_document
from ai_services.text_analysis import definition_subject_keywords, extract_keywords, is_definition_question


def answer_from_document(question: str) -> tuple[str, list[dict[str, str]]]:
    chunks = query_document(question)

    if not chunks:
        return FALLBACK_ANSWER, []

    answer = extract_answer_from_chunks(question, chunks)
    return answer, chunks


def extract_answer_from_chunks(question: str, chunks: list[dict[str, str]]) -> str:
    keywords = extract_keywords(question)
    if not keywords:
        return FALLBACK_ANSWER

    scored_sentences: list[tuple[int, str]] = []
    definition_question = is_definition_question(question)
    subject_keywords = definition_subject_keywords(question) if definition_question else set()
    scoring_keywords = subject_keywords or keywords
    for chunk in chunks:
        for sentence in split_sentences(chunk["text"]):
            lowered = sentence.lower()
            score = sum(1 for keyword in scoring_keywords if keyword in lowered)
            if definition_question and score:
                has_definition_phrase = (
                    " is " in lowered
                    or " are " in lowered
                    or " means " in lowered
                    or " refers to " in lowered
                )
                if has_definition_phrase:
                    score += 8
                if any(lowered.startswith(keyword) for keyword in scoring_keywords):
                    score += 3
                if "using" in lowered or "during" in lowered or "placement" in lowered:
                    score -= 1
            if score:
                scored_sentences.append((score, sentence))

    if not scored_sentences:
        return FALLBACK_ANSWER

    scored_sentences.sort(key=lambda item: item[0], reverse=True)
    best_score = scored_sentences[0][0]
    if best_score < 2 and len(keywords) > 2:
        return FALLBACK_ANSWER

    if definition_question:
        definition_sentences = [
            (score, sentence)
            for score, sentence in scored_sentences
            if re.search(r"\b(is|are|means|refers to)\b", sentence.lower())
        ]
        if definition_sentences:
            scored_sentences = definition_sentences

    selected: list[str] = []
    for _, sentence in scored_sentences:
        if sentence not in selected:
            selected.append(sentence)
        if len(selected) == (2 if definition_question else 3):
            break

    return " ".join(selected)


def split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [clean_sentence(sentence) for sentence in sentences if sentence.strip()]


def clean_sentence(sentence: str) -> str:
    cleaned = " ".join(sentence.split()).strip()
    if ":" in cleaned:
        prefix, suffix = cleaned.rsplit(":", 1)
        suffix = suffix.strip()
        if re.search(r"\b(is|are|means|refers to)\b", suffix.lower()):
            return suffix
        if len(prefix.split()) <= 8 and suffix:
            return suffix
    return cleaned
