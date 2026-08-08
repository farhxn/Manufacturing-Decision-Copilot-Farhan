"""
Filename sanitization utilities.

Prevents path traversal attacks and normalises uploaded filenames to
safe, predictable values before writing to disk.
"""

import re
import unicodedata
import uuid
from pathlib import Path


# Characters that are unsafe in filenames on any OS
_UNSAFE_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
# Collapse multiple whitespace / dots / dashes
_COLLAPSE_RE = re.compile(r'[\s._-]+')


def sanitize_filename(original: str) -> str:
    """
    Return a safe filename derived from *original*.

    Rules applied (in order):
    1. Unicode NFKC normalisation (e.g. full-width chars → ASCII equivalents).
    2. Strip leading/trailing whitespace and dots.
    3. Remove characters that are illegal on Windows, Linux, or macOS.
    4. Collapse consecutive separators to a single underscore.
    5. Preserve the file extension (lower-cased).
    6. Truncate stem to 120 chars so the full name fits in 255 chars.
    7. If the result is empty after sanitisation, generate a random UUID name.

    Examples
    --------
    >>> sanitize_filename("../../../etc/passwd")
    'etcpasswd'
    >>> sanitize_filename("My Invoice (2026) — Final.PDF")
    'My_Invoice_2026_Final.pdf'
    """
    if not original:
        return f"{uuid.uuid4().hex}.bin"

    # 1. Unicode normalisation
    name = unicodedata.normalize("NFKC", original)

    # 2. Strip surrounding whitespace/dots
    name = name.strip(" .")

    path = Path(name)
    stem = path.stem.strip(" .")
    suffix = path.suffix.lower()  # e.g. ".pdf"

    # 3. Remove unsafe characters
    stem = _UNSAFE_RE.sub("_", stem)

    # 4. Collapse separators
    stem = _COLLAPSE_RE.sub("_", stem).strip("_")

    # 5. Truncate
    stem = stem[:120]

    # 6. Fallback if stem is now empty
    if not stem:
        stem = uuid.uuid4().hex

    return f"{stem}{suffix}"


def storage_filename(original: str) -> str:
    """
    Return a UUID-based storage filename that preserves the original extension.

    This is the name written to disk — never user-controlled.

    Examples
    --------
    >>> storage_filename("../../secret.pdf")
    'a1b2c3d4-...-xxxx.pdf'
    """
    suffix = Path(original).suffix.lower() or ".bin"
    return f"{uuid.uuid4()}{suffix}"
