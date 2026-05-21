from __future__ import annotations

import re


def extract_keywords(text: str) -> set[str]:
    stop_words = {
        "about",
        "after",
        "again",
        "also",
        "define",
        "explain",
        "from",
        "have",
        "into",
        "should",
        "that",
        "their",
        "there",
        "this",
        "what",
        "when",
        "where",
        "which",
        "with",
        "would",
        "your",
    }
    return {
        word
        for word in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if len(word) > 2 and word not in stop_words
    }


def is_definition_question(text: str) -> bool:
    normalized = text.lower().strip()
    return (
        normalized.startswith("what is ")
        or normalized.startswith("what are ")
        or normalized.startswith("explain ")
        or normalized.startswith("explain about ")
        or normalized.startswith("define ")
        or " meaning" in normalized
    )


def definition_subject_keywords(text: str) -> set[str]:
    normalized = text.lower().strip().rstrip("?.!")
    patterns = (
        r"^what\s+(?:is|are)\s+(.+)$",
        r"^explain\s+about\s+(.+)$",
        r"^explain\s+(.+)$",
        r"^define\s+(.+)$",
    )
    for pattern in patterns:
        match = re.match(pattern, normalized)
        if match:
            return extract_keywords(match.group(1))
    return set()
