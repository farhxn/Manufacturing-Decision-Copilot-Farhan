from __future__ import annotations
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_chroma_client: Any = None


def get_chroma_client() -> chromadb.PersistentClient:
    """Returns a singleton ChromaDB persistent client."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        logger.info(
            "ChromaDB client initialized",
            persist_dir=settings.chroma_persist_dir,
        )
    return _chroma_client


def get_document_chunks_collection() -> chromadb.Collection:
    """Returns (or creates) the document_chunks collection."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def check_chroma_health() -> bool:
    """Returns True if ChromaDB is accessible."""
    try:
        client = get_chroma_client()
        client.heartbeat()
        return True
    except Exception as exc:
        logger.error("ChromaDB health check failed", error=str(exc))
        return False
