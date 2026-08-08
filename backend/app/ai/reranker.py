"""
Reciprocal Rank Fusion (RRF) reranker.

Used by the hybrid retriever to merge vector-search and BM25 result lists
into a single ranked list.

Reference: Cormack, Clarke & Buettcher (2009).
Formula:   RRF(d) = Σ  1 / (k + rank_i(d))
           where k=60 (standard constant), rank_i is the 1-based position
           of document d in result list i.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RankedChunk:
    """A retrieved document chunk with its fused score and metadata."""

    chunk_id: str
    content: str
    score: float = 0.0
    metadata: dict = field(default_factory=dict)

    # Source scores for transparency / debugging
    vector_rank: int | None = None   # 1-based rank in vector results
    bm25_rank: int | None = None     # 1-based rank in BM25 results


def reciprocal_rank_fusion(
    vector_results: list[RankedChunk],
    bm25_results: list[RankedChunk],
    k: int = 60,
    top_k: int = 10,
) -> list[RankedChunk]:
    """
    Merge *vector_results* and *bm25_results* using Reciprocal Rank Fusion.

    Parameters
    ----------
    vector_results:
        Chunks ranked by cosine similarity (best first).
    bm25_results:
        Chunks ranked by BM25 score (best first).
    k:
        RRF constant (default 60, standard in literature).
    top_k:
        Number of results to return.

    Returns
    -------
    Merged list of up to *top_k* ``RankedChunk`` objects, ordered by
    descending RRF score.  Metadata and content are taken from whichever
    source list first provided the chunk.
    """
    # Build a lookup: chunk_id -> RankedChunk (from either list)
    chunk_map: dict[str, RankedChunk] = {}
    rrf_scores: dict[str, float] = {}

    for rank, chunk in enumerate(vector_results, start=1):
        chunk.vector_rank = rank
        chunk_map[chunk.chunk_id] = chunk
        rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0) + 1.0 / (k + rank)

    for rank, chunk in enumerate(bm25_results, start=1):
        chunk.bm25_rank = rank
        if chunk.chunk_id not in chunk_map:
            chunk_map[chunk.chunk_id] = chunk
        rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0) + 1.0 / (k + rank)

    # Attach final RRF score and sort
    results: list[RankedChunk] = []
    for chunk_id, score in rrf_scores.items():
        chunk = chunk_map[chunk_id]
        chunk.score = round(score, 6)
        results.append(chunk)

    results.sort(key=lambda c: c.score, reverse=True)
    return results[:top_k]
