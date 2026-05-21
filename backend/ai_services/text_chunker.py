from __future__ import annotations


def chunk_text(text: str, max_words: int) -> list[str]:
    words = text.split()
    chunks = []
    for start in range(0, len(words), max_words):
        chunk = " ".join(words[start : start + max_words]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks
