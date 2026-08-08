"""
File validation utilities.

Validates uploaded files by size, extension, and MIME type (magic-bytes).
Never trusts the Content-Type header or file extension alone.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Allowed types ─────────────────────────────────────────────────────────────

# Canonical extension → human label
ALLOWED_EXTENSIONS: dict[str, str] = {
    ".pdf": "PDF",
    ".docx": "Word Document",
    ".xlsx": "Excel Spreadsheet",
}

# Magic-byte signatures for each MIME type.
# Tuples of (offset, bytes) — ALL must match for the entry to fire.
_MAGIC: list[tuple[str, list[tuple[int, bytes]]]] = [
    ("pdf",  [(0, b"%PDF")]),
    ("docx", [(0, b"PK\x03\x04")]),   # ZIP-based Office Open XML
    ("xlsx", [(0, b"PK\x03\x04")]),   # same container as docx
]


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    file_type: str          # "pdf" | "docx" | "xlsx" | ""
    file_size_bytes: int
    sha256_checksum: str
    error_code: str = ""    # e.g. "FILE_TOO_LARGE"
    error_message: str = ""


# ── Internal helpers ──────────────────────────────────────────────────────────

def _detect_mime(header: bytes) -> str:
    """
    Return the detected file type from the first 16 bytes.
    Returns "" if no signature matches.
    """
    for file_type, signatures in _MAGIC:
        if all(
            len(header) > offset and header[offset : offset + len(magic)] == magic
            for offset, magic in signatures
        ):
            return file_type
    return ""


def _disambiguate_zip(file_bytes: bytes) -> str:
    """
    Both .docx and .xlsx are ZIP containers.  Distinguish by checking
    the internal directory listing for Office-specific entry names.
    """
    if b"word/" in file_bytes:
        return "docx"
    if b"xl/" in file_bytes:
        return "xlsx"
    return "docx"   # default to docx if ambiguous


# ── Public API ────────────────────────────────────────────────────────────────

def validate_upload(file_bytes: bytes, original_filename: str) -> ValidationResult:
    """
    Validate *file_bytes* against size, extension, and magic-byte rules.

    Parameters
    ----------
    file_bytes:
        Complete file content read into memory (FastAPI UploadFile.read()).
    original_filename:
        The filename provided by the client (used only for extension check).

    Returns
    -------
    ValidationResult with ``valid=True`` on success, or an error code/message
    on failure.
    """
    size = len(file_bytes)
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    ext = Path(original_filename).suffix.lower()

    # 1. Size limit
    if size == 0:
        return ValidationResult(
            valid=False,
            file_type="",
            file_size_bytes=size,
            sha256_checksum=sha256,
            error_code="FILE_EMPTY",
            error_message="Uploaded file is empty.",
        )

    if size > settings.max_upload_size_bytes:
        limit_mb = settings.max_upload_size_mb
        return ValidationResult(
            valid=False,
            file_type="",
            file_size_bytes=size,
            sha256_checksum=sha256,
            error_code="FILE_TOO_LARGE",
            error_message=f"File exceeds the {limit_mb} MB upload limit.",
        )

    # 2. Extension allow-list
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(ALLOWED_EXTENSIONS.keys())
        return ValidationResult(
            valid=False,
            file_type="",
            file_size_bytes=size,
            sha256_checksum=sha256,
            error_code="INVALID_FILE_TYPE",
            error_message=f"File type '{ext}' is not allowed. Accepted: {allowed}.",
        )

    # 3. Magic-byte check (server-side MIME validation)
    header = file_bytes[:16]
    detected = _detect_mime(header)

    if not detected:
        return ValidationResult(
            valid=False,
            file_type="",
            file_size_bytes=size,
            sha256_checksum=sha256,
            error_code="INVALID_FILE_CONTENT",
            error_message="File content does not match a supported document format.",
        )

    # 4. Disambiguate ZIP-based formats
    if detected in ("docx", "xlsx"):
        detected = _disambiguate_zip(file_bytes)

    # 5. Extension / content agreement
    expected_ext = f".{detected}"
    if ext != expected_ext:
        logger.warning(
            "Extension/content mismatch",
            ext=ext,
            detected=detected,
            filename=original_filename,
        )
        # Accept but use the detected type (content wins over extension)

    logger.info(
        "File validated",
        filename=original_filename,
        size_bytes=size,
        file_type=detected,
    )

    return ValidationResult(
        valid=True,
        file_type=detected,
        file_size_bytes=size,
        sha256_checksum=sha256,
    )
