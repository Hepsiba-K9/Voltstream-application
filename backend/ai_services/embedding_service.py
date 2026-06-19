from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ai_services.ai_common import (
    AIServiceError,
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    EMBEDDING_EXPORT_TABLE,
    INDEX_META_FILE,
    configure_google_ai_client,
)
from ai_services.document_loader import existing_reference_documents, load_document_text
from ai_services.text_chunker import chunk_text

EMBEDDING_BATCH_SIZE = 50

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:  # pragma: no cover - handled at runtime for setup clarity
    chromadb = None
    Settings = None


def ensure_document_index() -> None:
    if chromadb is None:
        raise AIServiceError("chromadb is not installed. Run pip install -r backend/requirements.txt.")

    document_paths = existing_reference_documents()
    collection = get_collection()
    if collection.count() > 0 and index_matches_documents(document_paths):
        if not export_table_matches_collection(collection.count()):
            export_collection_for_inspection(collection)
        return

    reset_collection()
    collection = get_collection()

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, str]] = []

    for document_path in document_paths:
        document_text = load_document_text(document_path)
        chunks = chunk_text(document_text, max_words=220)
        for index, chunk in enumerate(chunks, start=1):
            chunk_id = f"{document_path.stem}-chunk-{index}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({"source": document_path.name, "chunk_id": chunk_id})

    if not documents:
        raise AIServiceError("No text was found in the selected document.")

    embeddings = embed_texts(documents, task_type="RETRIEVAL_DOCUMENT")
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    write_index_meta(document_paths, len(documents))
    export_collection_for_inspection(collection)


def get_document_status() -> dict[str, str | int | bool]:
    document_paths = existing_reference_documents()
    chunk_count = 0
    if document_paths and index_matches_documents(document_paths):
        try:
            chunk_count = int(read_index_meta().get("chunk_count", 0))
        except (TypeError, ValueError):
            chunk_count = 0

    return {
        "filename": ", ".join(path.name for path in document_paths),
        "chunk_count": chunk_count,
        "is_default": True,
    }


def query_document(question: str) -> list[dict[str, str]]:
    ensure_document_index()
    collection = get_collection()

    requested_count = 3
    result_count = min(collection.count(), 30)
    if result_count == 0:
        return []

    results = collection.query(
        query_embeddings=[embed_text(question, task_type="RETRIEVAL_QUERY")],
        n_results=requested_count,
        include=["documents", "metadatas", "distances"],
    )
    documents = list(results.get("documents", [[]])[0])
    metadatas = list(results.get("metadatas", [[]])[0])
    distances = list(results.get("distances", [[]])[0])

    chunks: list[dict[str, str]] = []
    for index, text in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        chunk_id = str(metadata.get("chunk_id", f"chunk-{index + 1}"))
        chunks.append({
            "source": str(metadata.get("source", "reference-document")),
            "chunk_id": chunk_id,
            "score": format_similarity_score(distances[index] if index < len(distances) else None),
            "text": text,
        })
    return chunks


def format_similarity_score(distance: float | None) -> str:
    if distance is None:
        return ""
    similarity = 1 / (1 + max(float(distance), 0.0))
    return f"{similarity:.3f}"


def get_collection():
    if Settings is None:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    else:
        client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
    return client.get_or_create_collection(COLLECTION_NAME)


def export_collection_for_inspection(collection) -> None:
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


def export_table_matches_collection(expected_count: int) -> bool:
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


def reset_collection() -> None:
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


def stored_chunks(collection) -> list[dict[str, str]]:
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


def embed_text(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    return embed_texts([text], task_type=task_type)[0]


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    if not texts:
        return []

    try:
        from google.genai import types
    except ImportError as exc:  # pragma: no cover - handled at runtime for setup clarity
        raise AIServiceError("google-genai is not installed. Run pip install -r backend/requirements.txt.") from exc

    client = configure_google_ai_client()
    vectors: list[list[float]] = []
    try:
        for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[start:start + EMBEDDING_BATCH_SIZE]
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
                config=types.EmbedContentConfig(taskType=task_type),
            )
            embeddings = getattr(response, "embeddings", None) or []
            vectors.extend(list(embedding.values or []) for embedding in embeddings)
    except Exception as exc:
        raise AIServiceError(str(exc)) from exc

    if len(vectors) != len(texts) or any(not vector for vector in vectors):
        raise AIServiceError("Gemini embedding request returned an invalid response.")
    return vectors


def document_signature(path: Path) -> dict[str, str | int]:
    stat = path.stat()
    return {
        "path": str(path.resolve()),
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
    }


def read_index_meta() -> dict[str, str | int]:
    if not INDEX_META_FILE.exists():
        return {}
    try:
        return json.loads(INDEX_META_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_index_meta(paths: list[Path], chunk_count: int) -> None:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_META_FILE.write_text(
        json.dumps(
            {
                "documents": [document_signature(path) for path in paths],
                "chunk_count": chunk_count,
                "embedding_model": EMBEDDING_MODEL,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def index_matches_documents(paths: list[Path]) -> bool:
    meta = read_index_meta()
    return (
        meta.get("documents") == [document_signature(path) for path in paths]
        and meta.get("embedding_model") == EMBEDDING_MODEL
    )
