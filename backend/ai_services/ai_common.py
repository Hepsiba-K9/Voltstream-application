from __future__ import annotations

import logging
import os
from pathlib import Path

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
logging.getLogger("chromadb.telemetry.product.posthog").disabled = True

try:
    from google import genai
except ImportError:  # pragma: no cover - handled at runtime for setup clarity
    genai = None


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = Path(
    os.getenv(
        "VOLTSTREAM_RUNTIME_DATA_DIR",
        "/tmp/voltstream_databases" if os.getenv("K_SERVICE") else str(BASE_DIR / "databases"),
    )
)
REFERENCE_DOCUMENTS = [
    DATA_DIR / "energy_efficiency_guide.txt",
    DATA_DIR / "energy_efficiency_report.txt",
    DATA_DIR / "detailed_energy_efficiency_report.txt",
]
CHROMA_DIR = DATABASE_DIR / "chroma_store"
INDEX_META_FILE = CHROMA_DIR / "index_meta.json"
COLLECTION_NAME = "energy_efficiency_guide"
FALLBACK_ANSWER = "I don't have that information."
EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
EMBEDDING_EXPORT_TABLE = "rag_chunk_embeddings"
SUPPORTED_DOCUMENT_EXTENSIONS = {".pdf", ".txt"}


class AIServiceError(RuntimeError):
    pass


class GeminiModel:
    def __init__(self, client, model_name: str) -> None:
        self.client = client
        self.model_name = model_name

    def generate_content(self, contents, request_options: dict[str, int] | None = None):
        _ = request_options
        return self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
        )


def use_vertex_ai() -> bool:
    return os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").strip().lower() in {"1", "true", "yes"}


def configure_google_ai_client():
    if genai is None:
        raise AIServiceError("google-genai is not installed. Run pip install -r backend/requirements.txt.")

    if use_vertex_ai():
        project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_PROJECT_ID")
        location = os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("GOOGLE_CLOUD_REGION") or "us-central1"
        if not project:
            raise AIServiceError("Set GOOGLE_CLOUD_PROJECT in your environment or .env file.")
        return genai.Client(vertexai=True, project=project, location=location)

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise AIServiceError(
            "Set GOOGLE_GENAI_USE_VERTEXAI=true with GOOGLE_CLOUD_PROJECT, or set GEMINI_API_KEY."
        )
    return genai.Client(api_key=api_key)


def gemini_model():
    client = configure_google_ai_client()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    return GeminiModel(client, model_name)
