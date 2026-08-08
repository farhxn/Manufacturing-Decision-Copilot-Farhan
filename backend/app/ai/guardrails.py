"""
Guardrails for AI inputs and outputs.

Two responsibilities:
1. Strip prompt-injection patterns from document text before it is sent
   to any LLM.  Treats all document content as untrusted.
2. Validate AI output schemas — reject and raise if invalid.

Security note (from roadmap §16):
  "Prompt injection via documents → Strip patterns + system prompt guardrail"
  "LLM output trust → Validate all outputs against Pydantic schema"
"""

from __future__ import annotations

import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

# ── Injection pattern catalogue ───────────────────────────────────────────────
# Patterns that attackers embed in uploaded documents to hijack the LLM.
# Each entry is (description, compiled_pattern, replacement).

_INJECTION_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    (
        "ignore_previous",
        re.compile(
            r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|context)",
            re.IGNORECASE,
        ),
        "[REDACTED]",
    ),
    (
        "you_are_now",
        re.compile(
            r"you\s+are\s+now\s+(a\s+|an\s+)?(?!Manufacturing|MDC|Copilot)",
            re.IGNORECASE,
        ),
        "[REDACTED]",
    ),
    (
        "new_instructions",
        re.compile(
            r"(new|updated|revised|following)\s+instructions?:",
            re.IGNORECASE,
        ),
        "[REDACTED]:",
    ),
    (
        "system_prompt_leak",
        re.compile(
            r"(print|reveal|show|output|repeat|display)\s+(your\s+)?(system\s+)?(prompt|instructions?|rules?)",
            re.IGNORECASE,
        ),
        "[REDACTED]",
    ),
    (
        "role_injection",
        re.compile(
            r"<\s*(system|user|assistant|human|ai|bot)\s*>",
            re.IGNORECASE,
        ),
        "[TAG]",
    ),
    (
        "act_as",
        re.compile(
            r"\bact\s+as\s+(a\s+|an\s+)?\w+",
            re.IGNORECASE,
        ),
        "[REDACTED]",
    ),
    (
        "jailbreak_dan",
        re.compile(
            r"\bDAN\b|\bjailbreak\b|\bunfiltered\b|\bunrestricted\b",
            re.IGNORECASE,
        ),
        "[REDACTED]",
    ),
]

# Maximum length of a single text chunk sent to LLM (chars).
# Prevents context-window flooding via oversized documents.
_MAX_CHUNK_CHARS = 4_000


def sanitize_for_llm(text: str) -> str:
    """
    Strip prompt-injection patterns from *text* before sending to any LLM.

    Parameters
    ----------
    text:
        Raw document chunk text (untrusted).

    Returns
    -------
    Sanitised text, truncated to ``_MAX_CHUNK_CHARS`` characters.
    """
    if not text:
        return ""

    result = text
    for name, pattern, replacement in _INJECTION_PATTERNS:
        before = result
        result = pattern.sub(replacement, result)
        if result != before:
            logger.warning(
                "Injection pattern detected and stripped",
                pattern=name,
                chars_removed=len(before) - len(result),
            )

    # Truncate oversized chunks
    if len(result) > _MAX_CHUNK_CHARS:
        result = result[:_MAX_CHUNK_CHARS] + " [TRUNCATED]"

    return result


def sanitize_chunks(chunks: list[str]) -> list[str]:
    """Apply ``sanitize_for_llm`` to a list of chunk texts."""
    return [sanitize_for_llm(c) for c in chunks]


# ── Output validation ─────────────────────────────────────────────────────────

def validate_output(schema_cls: type[T], raw: dict) -> T:
    """
    Validate a raw dict against a Pydantic schema.

    Parameters
    ----------
    schema_cls:
        The expected output schema class (e.g. ``RecommendationOutput``).
    raw:
        The dict returned by the LLM (already JSON-parsed).

    Returns
    -------
    A validated instance of *schema_cls*.

    Raises
    ------
    ValueError
        If validation fails.  The caller should handle this by falling back
        to a cached or deterministic result.
    """
    try:
        return schema_cls.model_validate(raw)
    except ValidationError as exc:
        logger.error(
            "AI output failed schema validation",
            schema=schema_cls.__name__,
            errors=exc.errors(),
        )
        raise ValueError(
            f"AI output does not conform to {schema_cls.__name__}: {exc}"
        ) from exc


def filter_evidence_ids(
    evidence_ids: list[str],
    allowed_ids: set[str],
) -> list[str]:
    """
    Remove any evidence_id from the LLM output that was not in the
    provided retrieval set.

    The LLM must only cite chunks it was actually given.  This prevents
    hallucinated chunk references from reaching the database.
    """
    valid = [eid for eid in evidence_ids if eid in allowed_ids]
    hallucinated = len(evidence_ids) - len(valid)
    if hallucinated:
        logger.warning(
            "Hallucinated evidence IDs removed from AI output",
            count=hallucinated,
        )
    return valid
