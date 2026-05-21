from __future__ import annotations

import logging
import os
from pathlib import Path

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
logging.getLogger("chromadb.telemetry.product.posthog").disabled = True

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - handled at runtime for setup clarity
    genai = None


BASE_DIR = Path(__file__).resolve().parent.parent
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


class AIServiceError(RuntimeError):
    pass


def configure_gemini() -> None:
    if genai is None:
        raise AIServiceError("google-generativeai is not installed. Run pip install -r backend/requirements.txt.")

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise AIServiceError("Set GEMINI_API_KEY in your environment or .env file.")

    genai.configure(api_key=api_key)


def gemini_model():
    configure_gemini()
    model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
    return genai.GenerativeModel(model_name)
