from __future__ import annotations

import re
import os
from collections.abc import Iterable
from io import BytesIO
from pathlib import Path

from ai_services.ai_common import AIServiceError, DATA_DIR, REFERENCE_DOCUMENTS, SUPPORTED_DOCUMENT_EXTENSIONS

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - handled at runtime for setup clarity
    PdfReader = None


def existing_reference_documents() -> list[Path]:
    configured_documents = [path for path in REFERENCE_DOCUMENTS if path.exists()]
    index_all_documents = os.getenv("VOLTSTREAM_INDEX_ALL_DOCUMENTS", "").strip().lower() in {"1", "true", "yes"}
    if configured_documents and not index_all_documents:
        documents = unique_paths(configured_documents)
    else:
        documents = unique_paths(
            [
                *configured_documents,
                *[
                    path
                    for path in sorted(DATA_DIR.iterdir())
                    if is_indexable_reference_document(path)
                ],
            ]
        )
    if not documents:
        raise AIServiceError("No reference documents were found in backend/data.")
    return documents


def is_indexable_reference_document(path: Path) -> bool:
    if not path.is_file() or path.suffix.lower() not in SUPPORTED_DOCUMENT_EXTENSIONS:
        return False
    if path.suffix.lower() == ".pdf" and path.with_suffix(".txt").exists():
        return False
    return True


def unique_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def safe_document_name(filename: str) -> str:
    original = Path(filename).name
    suffix = Path(original).suffix.lower()
    if suffix not in SUPPORTED_DOCUMENT_EXTENSIONS:
        return ""
    stem = re.sub(r"[^a-zA-Z0-9_-]+", "_", Path(original).stem).strip("_")
    if not stem:
        stem = "uploaded_document"
    return f"{stem}{suffix}"


def load_document_text(path: Path) -> str:
    if not path.exists():
        raise AIServiceError(f"Document not found: {path.name}")
    if path.suffix.lower() == ".pdf":
        if PdfReader is None:
            raise AIServiceError("pypdf is not installed. Run pip install -r backend/requirements.txt.")
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8")


def load_document_text_from_bytes(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        if PdfReader is None:
            raise AIServiceError("pypdf is not installed. Run pip install -r backend/requirements.txt.")
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return content.decode("utf-8", errors="ignore")
