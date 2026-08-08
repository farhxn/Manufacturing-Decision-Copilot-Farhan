"""
Embedding generation module.

Provides a single public function — ``embed_texts()`` — that routes to the
correct provider based on ``settings.embedding_provider``.

Supported providers
-------------------
- ``"local"``  — sentence-transformers (BAAI/bge-small-en-v1.5, 384-dim).
                 Falls back to zero vectors when sentence-transformers is not
                 installed, so the worker never crashes in demo/CI mode.
- ``"openai"`` — OpenAI text-embedding-3-small (1536-dim).
- ``"gemini"`` — Google text-embedding-004 (768-dim).

The caller is responsible for batching.  This module does not enforce a
batch-size limit; document_worker.py sends slices of ≤100 texts.
"""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)

# Dimensions per provider — used for the zero-vector fallback
_EMBEDDING_DIMS: dict[str, int] = {
    "local":  384,
    "openai": 1536,
    "gemini": 768,
}

# Singleton sentence-transformer model so we don't reload it on every call
_st_model = None


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for *texts* using the configured provider.

    Parameters
    ----------
    texts:
        Non-empty list of strings to embed.  Empty strings are accepted
        but may produce degraded vectors.

    Returns
    -------
    List of float vectors, one per input text, in the same order.

    Raises
    ------
    RuntimeError
        If the provider is ``"openai"`` or ``"gemini"`` and the respective
        library is not installed.
    ValueError
        If *texts* is empty.
    """
    if not texts:
        raise ValueError("embed_texts requires at least one text.")

    from app.core.config import settings
    provider = settings.embedding_provider

    if provider == "openai":
        return _embed_openai(texts, settings)

    if provider == "gemini":
        return _embed_gemini(texts, settings)

    # Default: local sentence-transformers
    return _embed_local(texts, settings)


# ── Provider implementations ──────────────────────────────────────────────────

def _embed_openai(texts: list[str], settings) -> list[list[float]]:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai package is not installed. Run: pip install openai") from exc

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=texts,
    )
    vectors = [item.embedding for item in response.data]
    logger.debug("OpenAI embeddings generated", count=len(vectors))
    return vectors


def _embed_gemini(texts: list[str], settings) -> list[list[float]]:
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise RuntimeError(
            "google-generativeai package is not installed. "
            "Run: pip install google-generativeai"
        ) from exc

    genai.configure(api_key=settings.gemini_api_key)
    embeddings: list[list[float]] = []
    for text in texts:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
        )
        embeddings.append(result["embedding"])
    logger.debug("Gemini embeddings generated", count=len(embeddings))
    return embeddings


def _embed_local(texts: list[str], settings) -> list[list[float]]:
    global _st_model  # noqa: PLW0603

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.warning(
            "sentence-transformers not installed — using zero vectors (demo/CI mode). "
            "Install with: pip install sentence-transformers"
        )
        dim = _EMBEDDING_DIMS["local"]
        return [[0.0] * dim for _ in texts]

    if _st_model is None:
        _st_model = SentenceTransformer(settings.local_embedding_model)
        logger.info("SentenceTransformer model loaded", model=settings.local_embedding_model)

    vectors = _st_model.encode(texts, show_progress_bar=False)
    result = [v.tolist() for v in vectors]
    logger.debug("Local embeddings generated", count=len(result))
    return result
