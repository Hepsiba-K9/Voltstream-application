from __future__ import annotations

import logging
import hashlib
import json
import math
import os
import re
import sqlite3
from io import BytesIO
from collections.abc import Iterable
from pathlib import Path

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
logging.getLogger("chromadb.telemetry.product.posthog").disabled = True

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:  # pragma: no cover - handled at runtime for setup clarity
    chromadb = None
    Settings = None

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - handled at runtime for setup clarity
    genai = None

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - handled at runtime for setup clarity
    PdfReader = None


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "databases"
REFERENCE_DOCUMENTS = [
    DATA_DIR / "energy_efficiency_guide.txt",
    DATA_DIR / "energy_efficiency_report.txt",
    DATA_DIR / "detailed_energy_efficiency_report.txt",
]
CHROMA_DIR = DATABASE_DIR / "chroma_store"
INDEX_META_FILE = CHROMA_DIR / "index_meta.json"
COLLECTION_NAME = "energy_efficiency_guide"
FALLBACK_ANSWER = "I don't have that information."
EMBEDDING_DIMENSIONS = 384
EMBEDDING_EXPORT_TABLE = "rag_chunk_embeddings"
SUPPORTED_DOCUMENT_EXTENSIONS = {".pdf", ".txt"}
CHAT_UPLOADED_DOCUMENT: dict[str, str] = {}


class AIServiceError(RuntimeError):
    pass


def _configure_gemini() -> None:
    if genai is None:
        raise AIServiceError("google-generativeai is not installed. Run pip install -r backend/requirements.txt.")

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise AIServiceError("Set GEMINI_API_KEY in your environment or .env file.")

    genai.configure(api_key=api_key)


def generate_chat_response(message: str) -> str:
    message = _normalize_general_energy_question(message)
    _configure_gemini()
    model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
    model = genai.GenerativeModel(model_name)
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


def _normalize_general_energy_question(message: str) -> str:
    if not _is_energy_related_message(message):
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


def _is_energy_related_message(message: str) -> bool:
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


def _load_reference_text_for_typos() -> str:
    texts: list[str] = []
    for path in REFERENCE_DOCUMENTS:
        if path.exists() and path.suffix.lower() == ".txt":
            try:
                texts.append(path.read_text(encoding="utf-8"))
            except OSError:
                continue
    return "\n".join(texts)


def generate_chat_response_from_upload(message: str) -> str:
    document_text = CHAT_UPLOADED_DOCUMENT.get("text", "").strip()
    if not document_text:
        return generate_chat_response(message)

    question = _normalize_uploaded_document_question(message, document_text)
    _configure_gemini()
    model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
    model = genai.GenerativeModel(model_name)
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


def _normalize_uploaded_document_question(message: str, document_text: str = "") -> str:
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
    return _correct_question_typos_from_document(message, document_text)


def _correct_question_typos_from_document(message: str, document_text: str) -> str:
    if not document_text:
        return message

    document_words = {
        word
        for word in re.findall(r"[a-zA-Z]{4,}", document_text.lower())
        if word not in _common_words()
    }
    if not document_words:
        return message

    corrected_words: list[str] = []
    changed = False
    for part in re.split(r"(\W+)", message):
        lowered = part.lower()
        if not lowered.isalpha() or len(lowered) < 4 or lowered in document_words or lowered in _common_words():
            corrected_words.append(part)
            continue

        match = _nearest_word(lowered, document_words)
        if match is None:
            corrected_words.append(part)
            continue

        corrected_words.append(_match_case(part, match))
        changed = True

    corrected = "".join(corrected_words)
    if not changed:
        return message
    return f"{corrected}\n\nNote: The user question appears to contain a typo. Interpret it as: {corrected}"


def _nearest_word(word: str, candidates: set[str]) -> str | None:
    best_word = None
    best_distance = 3
    for candidate in candidates:
        if abs(len(candidate) - len(word)) > 1:
            continue
        distance = _edit_distance_at_most(word, candidate, best_distance)
        if distance < best_distance:
            best_distance = distance
            best_word = candidate
    return best_word


def _edit_distance_at_most(left: str, right: str, limit: int) -> int:
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


def _match_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement.capitalize()
    return replacement


def _common_words() -> set[str]:
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


def answer_from_document(question: str) -> tuple[str, list[dict[str, str]]]:
    chunks = _query_document(question)

    if not chunks:
        return FALLBACK_ANSWER, []

    answer = _extract_answer_from_chunks(question, chunks)
    return answer, chunks


def upload_chat_document_to_memory(filename: str, content: bytes) -> dict[str, str | int | bool]:
    safe_name = _safe_document_name(filename)
    if not safe_name:
        raise AIServiceError("Upload a PDF or text document.")

    document_text = _load_document_text_from_bytes(safe_name, content).strip()
    if not document_text:
        raise AIServiceError("No readable text was found in the uploaded document.")

    CHAT_UPLOADED_DOCUMENT.clear()
    CHAT_UPLOADED_DOCUMENT.update({"filename": safe_name, "text": document_text})
    return {
        "filename": safe_name,
        "chunk_count": len(_chunk_text(document_text, max_words=220)),
        "is_default": False,
    }


def chat_should_use_uploaded_document() -> bool:
    return bool(CHAT_UPLOADED_DOCUMENT.get("text", "").strip())


def _ensure_document_index() -> None:
    if chromadb is None:
        raise AIServiceError("chromadb is not installed. Run pip install -r backend/requirements.txt.")

    document_paths = _existing_reference_documents()
    collection = _get_collection()
    if collection.count() > 0 and _index_matches_documents(document_paths):
        if not _export_table_matches_collection(collection.count()):
            _export_collection_for_inspection(collection)
        return

    _reset_collection()
    collection = _get_collection()

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, str]] = []

    for document_path in document_paths:
        document_text = _load_document_text(document_path)
        chunks = _chunk_text(document_text, max_words=220)
        for index, chunk in enumerate(chunks, start=1):
            chunk_id = f"{document_path.stem}-chunk-{index}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({"source": document_path.name, "chunk_id": chunk_id})

    if not documents:
        raise AIServiceError("No text was found in the selected document.")

    embeddings = [_embed_text(chunk, task_type="retrieval_document") for chunk in documents]
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    _write_index_meta(document_paths, len(documents))
    _export_collection_for_inspection(collection)


def get_document_status() -> dict[str, str | int | bool]:
    document_paths = _existing_reference_documents()
    chunk_count = 0
    if document_paths and _index_matches_documents(document_paths):
        try:
            chunk_count = int(_read_index_meta().get("chunk_count", 0))
        except (TypeError, ValueError):
            chunk_count = 0

    return {
        "filename": ", ".join(path.name for path in document_paths),
        "chunk_count": chunk_count,
        "is_default": True,
    }


def _get_collection():
    if Settings is None:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    else:
        client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
    return client.get_or_create_collection(COLLECTION_NAME)


def _export_collection_for_inspection(collection) -> None:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    data = collection.get(include=["documents", "metadatas", "embeddings"])
    with sqlite3.connect(CHROMA_DIR / "chroma.sqlite3") as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {EMBEDDING_EXPORT_TABLE} (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                chunk_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                embedding_json TEXT NOT NULL,
                embedding_dimensions INTEGER NOT NULL
            )
            """
        )
        connection.execute(f"DELETE FROM {EMBEDDING_EXPORT_TABLE}")
        rows = []
        for index, chunk_id in enumerate(data.get("ids", []), start=1):
            metadata = data.get("metadatas", [])[index - 1] or {}
            embedding = data.get("embeddings", [])[index - 1]
            embedding_values = [float(value) for value in embedding]
            rows.append(
                (
                    chunk_id,
                    str(metadata.get("source", "reference-document")),
                    str(metadata.get("chunk_id", chunk_id)),
                    index,
                    data.get("documents", [])[index - 1],
                    json.dumps(embedding_values),
                    len(embedding_values),
                )
            )
        connection.executemany(
            f"""
            INSERT INTO {EMBEDDING_EXPORT_TABLE} (
                id, source, chunk_id, chunk_index, chunk_text,
                embedding_json, embedding_dimensions
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )


def _export_table_matches_collection(expected_count: int) -> bool:
    with sqlite3.connect(CHROMA_DIR / "chroma.sqlite3") as connection:
        table_exists = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
            """,
            (EMBEDDING_EXPORT_TABLE,),
        ).fetchone()
        if table_exists is None:
            return False

        stored_count = connection.execute(
            f"SELECT COUNT(*) FROM {EMBEDDING_EXPORT_TABLE}"
        ).fetchone()[0]
    return stored_count == expected_count


def _read_exported_chunks() -> list[dict[str, str]]:
    database_path = CHROMA_DIR / "chroma.sqlite3"
    if not database_path.exists():
        return []

    with sqlite3.connect(database_path) as connection:
        table_exists = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
            """,
            (EMBEDDING_EXPORT_TABLE,),
        ).fetchone()
        if table_exists is None:
            return []

        rows = connection.execute(
            f"""
            SELECT source, chunk_id, chunk_text
            FROM {EMBEDDING_EXPORT_TABLE}
            ORDER BY chunk_index
            """
        ).fetchall()

    return [
        {
            "source": str(source),
            "chunk_id": str(chunk_id),
            "text": str(chunk_text),
        }
        for source, chunk_id, chunk_text in rows
    ]


def _reset_collection() -> None:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    if Settings is None:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    else:
        client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    if INDEX_META_FILE.exists():
        INDEX_META_FILE.unlink()


def _query_document(question: str) -> list[dict[str, str]]:
    _ensure_document_index()
    collection = _get_collection()
    if _is_definition_question(question):
        return _stored_chunks(collection)

    result_count = min(collection.count(), 8 if _is_definition_question(question) else 3)
    if result_count == 0:
        return []

    results = collection.query(
        query_embeddings=[_embed_text(question, task_type="retrieval_query")],
        n_results=result_count,
    )
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    chunks: list[dict[str, str]] = []
    for index, text in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        chunks.append(
            {
                "source": str(metadata.get("source", "reference-document")),
                "chunk_id": str(metadata.get("chunk_id", f"chunk-{index + 1}")),
                "text": text,
            }
        )
    return chunks


def _stored_chunks(collection) -> list[dict[str, str]]:
    data = collection.get(include=["documents", "metadatas"])
    chunks: list[dict[str, str]] = []
    for index, text in enumerate(data.get("documents", [])):
        metadata = data.get("metadatas", [])[index] or {}
        chunk_id = data.get("ids", [])[index]
        chunks.append(
            {
                "source": str(metadata.get("source", "reference-document")),
                "chunk_id": str(metadata.get("chunk_id", chunk_id)),
                "text": text,
            }
        )
    return chunks


def _embed_text(text: str, task_type: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    for token in _keywords(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSIONS
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]


def _load_document_text(path: Path) -> str:
    if not path.exists():
        raise AIServiceError(f"Document not found: {path.name}")
    if path.suffix.lower() == ".pdf":
        if PdfReader is None:
            raise AIServiceError("pypdf is not installed. Run pip install -r backend/requirements.txt.")
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8")


def _load_document_text_from_bytes(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        if PdfReader is None:
            raise AIServiceError("pypdf is not installed. Run pip install -r backend/requirements.txt.")
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return content.decode("utf-8", errors="ignore")


def _chunk_text(text: str, max_words: int) -> list[str]:
    words = text.split()
    chunks = []
    for start in range(0, len(words), max_words):
        chunk = " ".join(words[start : start + max_words]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def _extract_answer_from_chunks(question: str, chunks: list[dict[str, str]]) -> str:
    keywords = _keywords(question)
    if not keywords:
        return FALLBACK_ANSWER

    scored_sentences: list[tuple[int, str]] = []
    definition_question = _is_definition_question(question)
    subject_keywords = _definition_subject_keywords(question) if definition_question else set()
    scoring_keywords = subject_keywords or keywords
    for chunk in chunks:
        for sentence in _split_sentences(chunk["text"]):
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


def _definition_subject_keywords(text: str) -> set[str]:
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
            return _keywords(match.group(1))
    return set()


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [_clean_sentence(sentence) for sentence in sentences if sentence.strip()]


def _clean_sentence(sentence: str) -> str:
    cleaned = " ".join(sentence.split()).strip()
    if ":" in cleaned:
        prefix, suffix = cleaned.rsplit(":", 1)
        suffix = suffix.strip()
        if re.search(r"\b(is|are|means|refers to)\b", suffix.lower()):
            return suffix
        if len(prefix.split()) <= 8 and suffix:
            return suffix
    return cleaned


def _keywords(text: str) -> set[str]:
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


def _is_definition_question(text: str) -> bool:
    normalized = text.lower().strip()
    return (
        normalized.startswith("what is ")
        or normalized.startswith("what are ")
        or normalized.startswith("explain ")
        or normalized.startswith("explain about ")
        or normalized.startswith("define ")
        or " meaning" in normalized
    )


def _looks_unsupported(answer: str) -> bool:
    normalized = answer.strip().lower().strip('"')
    return normalized in {
        FALLBACK_ANSWER.lower(),
        "i do not have that information.",
        "i don't have enough information.",
    }


def _existing_reference_documents() -> list[Path]:
    documents = _unique_paths(
        [
            *[path for path in REFERENCE_DOCUMENTS if path.exists()],
            *[
                path
                for path in sorted(DATA_DIR.iterdir())
                if path.is_file() and path.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS
            ],
        ]
    )
    if not documents:
        raise AIServiceError("No reference documents were found in backend/data.")
    return documents


def _unique_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def _safe_document_name(filename: str) -> str:
    original = Path(filename).name
    suffix = Path(original).suffix.lower()
    if suffix not in SUPPORTED_DOCUMENT_EXTENSIONS:
        return ""
    stem = re.sub(r"[^a-zA-Z0-9_-]+", "_", Path(original).stem).strip("_")
    if not stem:
        stem = "uploaded_document"
    return f"{stem}{suffix}"


def _document_signature(path: Path) -> dict[str, str | int]:
    stat = path.stat()
    return {
        "path": str(path.resolve()),
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
    }


def _read_index_meta() -> dict[str, str | int]:
    if not INDEX_META_FILE.exists():
        return {}
    try:
        return json.loads(INDEX_META_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_index_meta(paths: list[Path], chunk_count: int) -> None:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_META_FILE.write_text(
        json.dumps(
            {
                "documents": [_document_signature(path) for path in paths],
                "chunk_count": chunk_count,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _index_matches_documents(paths: list[Path]) -> bool:
    meta = _read_index_meta()
    return meta.get("documents") == [_document_signature(path) for path in paths]
