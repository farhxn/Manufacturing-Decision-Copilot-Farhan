"""
Semantic text chunker.

Splits extracted document text into overlapping chunks suitable for
embedding and retrieval.  Operates on per-page text produced by the
document extractor, so page numbers are tracked precisely.

Strategy
--------
- Split on paragraph / sentence boundaries (NOT fixed character count).
- Target ~600 tokens per chunk (≈ 800–900 words at 1.3 chars/token avg).
- 50-token overlap between consecutive chunks to preserve context.
- Never split a sentence across a chunk boundary.
- Emit a section_name based on heading heuristics where detectable.

No external NLP library required — pure Python regex + heuristics.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ── Config ────────────────────────────────────────────────────────────────────

TARGET_TOKENS = 600
OVERLAP_TOKENS = 50
# Rough chars-per-token estimate for English manufacturing text
CHARS_PER_TOKEN = 4.5

TARGET_CHARS = int(TARGET_TOKENS * CHARS_PER_TOKEN)    # ≈ 2 700
OVERLAP_CHARS = int(OVERLAP_TOKENS * CHARS_PER_TOKEN)  # ≈ 225

# Sentence boundary: end of sentence followed by whitespace
_SENTENCE_END = re.compile(r'(?<=[.!?])\s+')
# Heading heuristics: ALL-CAPS line, or line ending with colon, ≤ 80 chars
_HEADING = re.compile(r'^([A-Z][A-Z\s\d.:-]{2,79}[A-Z\d]|[\w].*?:)\s*$', re.MULTILINE)


# ── Output type ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TextChunk:
    content: str
    page_number: int         # 1-indexed page where the chunk starts
    chunk_index: int         # 0-indexed position within the document
    section_name: str | None # Nearest preceding heading, if detected
    token_count: int         # Estimated token count


# ── Internal helpers ──────────────────────────────────────────────────────────

def _estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / CHARS_PER_TOKEN))


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, keeping the delimiter attached."""
    parts = _SENTENCE_END.split(text)
    return [p.strip() for p in parts if p.strip()]


def _detect_section(line: str) -> str | None:
    """Return a section name if *line* looks like a heading, else None."""
    line = line.strip()
    if not line or len(line) > 100:
        return None
    if _HEADING.match(line):
        return line.rstrip(":")
    return None


# ── Public API ────────────────────────────────────────────────────────────────

def chunk_pages(pages: list[tuple[int, str]]) -> list[TextChunk]:
    """
    Chunk a document that has been extracted as a list of (page_number, text)
    tuples.

    Parameters
    ----------
    pages:
        List of ``(1-indexed page number, page text)`` pairs, as produced by
        the document extractor.

    Returns
    -------
    List of TextChunk objects in document order.
    """
    chunks: list[TextChunk] = []
    current_sentences: list[str] = []
    current_chars: int = 0
    current_page: int = 1
    current_section: str | None = None
    chunk_index: int = 0
    overlap_tail: list[str] = []   # sentences carried from previous chunk

    def _emit() -> None:
        nonlocal chunk_index, current_chars, current_sentences, overlap_tail
        if not current_sentences:
            return
        content = " ".join(current_sentences).strip()
        if not content:
            return
        chunks.append(
            TextChunk(
                content=content,
                page_number=current_page,
                chunk_index=chunk_index,
                section_name=current_section,
                token_count=_estimate_tokens(content),
            )
        )
        chunk_index += 1
        # Build overlap tail: last N chars worth of sentences
        tail: list[str] = []
        tail_chars = 0
        for sent in reversed(current_sentences):
            if tail_chars + len(sent) > OVERLAP_CHARS:
                break
            tail.insert(0, sent)
            tail_chars += len(sent)
        overlap_tail = tail
        current_sentences = list(tail)
        current_chars = tail_chars

    for page_num, page_text in pages:
        if not page_text or not page_text.strip():
            continue

        lines = page_text.splitlines()
        for line in lines:
            # Detect headings and update section context
            maybe_section = _detect_section(line)
            if maybe_section:
                current_section = maybe_section

        sentences = _split_sentences(page_text)
        for sent in sentences:
            sent_chars = len(sent)
            if current_chars + sent_chars > TARGET_CHARS and current_sentences:
                _emit()
                # page of the new chunk is the current page
            current_page = page_num
            current_sentences.append(sent)
            current_chars += sent_chars

    # Emit any remaining content
    _emit()

    return chunks


def chunk_text(text: str, page_number: int = 1) -> list[TextChunk]:
    """
    Convenience wrapper for single-page or pre-concatenated text.
    """
    return chunk_pages([(page_number, text)])
