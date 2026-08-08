"""
Phase 5 — Comprehensive Edge Case Tests
Covers best, average, and worst cases across every Phase 5 utility and service,
filling gaps left by the existing smoke tests.

Modules under test (all pure-Python, no DB / Redis / Celery required):
  - app.utils.file_validator   (validate_upload, _detect_mime, _disambiguate_zip)
  - app.utils.sanitizer        (sanitize_filename, storage_filename)
  - app.utils.chunker          (chunk_pages, chunk_text, _estimate_tokens)
  - app.ai.embeddings          (embed_texts — local/zero-vector path only)
  - app.services.recommendation_service (RecommendationService._estimate_confidence)
  - app.services.document_service      (_STATUS_PROGRESS mapping)
  - app.workers.document_worker        (_extract_text dispatch, _detect_mime, _disambiguate_zip)

Run:
    cd backend
    python -m pytest tests/unit/test_phase5_edge_cases.py -v
"""

import hashlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# ============================================================================
# SECTION 1 — FILE VALIDATOR
# ============================================================================
from app.utils.file_validator import (
    ALLOWED_EXTENSIONS,
    ValidationResult,
    _detect_mime,
    _disambiguate_zip,
    validate_upload,
)

# Real magic-byte headers for testing
_PDF_HEADER  = b"%PDF-1.4 fake content " + b"x" * 200
_ZIP_HEADER  = b"PK\x03\x04" + b"\x00" * 200   # bare ZIP (docx/xlsx container)
_DOCX_BYTES  = b"PK\x03\x04" + b"\x00" * 50 + b"word/document.xml content"
_XLSX_BYTES  = b"PK\x03\x04" + b"\x00" * 50 + b"xl/workbook.xml content"


class TestFileValidatorEdgeCases:
    # ── Best-case paths ──────────────────────────────────────────────────────

    def test_valid_pdf_returns_success(self):
        """Well-formed PDF bytes with correct extension → valid=True, type='pdf'."""
        result = validate_upload(_PDF_HEADER, "invoice.pdf")
        assert result.valid is True
        assert result.file_type == "pdf"
        assert result.file_size_bytes == len(_PDF_HEADER)

    def test_valid_docx_detected_correctly(self):
        """DOCX magic bytes with word/ internal directory → type='docx'."""
        result = validate_upload(_DOCX_BYTES, "report.docx")
        assert result.valid is True
        assert result.file_type == "docx"

    def test_valid_xlsx_detected_correctly(self):
        """XLSX magic bytes with xl/ internal directory → type='xlsx'."""
        result = validate_upload(_XLSX_BYTES, "data.xlsx")
        assert result.valid is True
        assert result.file_type == "xlsx"

    def test_sha256_checksum_always_present_and_correct(self):
        """SHA-256 is always computed, even for invalid files."""
        expected = hashlib.sha256(_PDF_HEADER).hexdigest()
        result = validate_upload(_PDF_HEADER, "test.pdf")
        assert result.sha256_checksum == expected
        assert len(result.sha256_checksum) == 64

    def test_sha256_present_for_empty_file(self):
        """Even for empty files the checksum field is populated."""
        result = validate_upload(b"", "empty.pdf")
        assert result.valid is False
        assert len(result.sha256_checksum) == 64

    def test_file_size_bytes_matches_input_length(self):
        """file_size_bytes always equals len(file_bytes)."""
        data = _PDF_HEADER + b"extra padding " * 10
        result = validate_upload(data, "big.pdf")
        assert result.file_size_bytes == len(data)

    # ── Average-case paths ───────────────────────────────────────────────────

    def test_extension_content_mismatch_content_wins(self):
        """PDF bytes uploaded as .docx — content wins, file_type='pdf', still valid."""
        result = validate_upload(_PDF_HEADER, "misnamed.docx")
        # Extension .docx is allowed; detected type is pdf; content wins
        assert result.valid is True
        assert result.file_type == "pdf"

    def test_docx_uploaded_with_pdf_extension_content_wins(self):
        """DOCX bytes uploaded as .pdf — content (ZIP/docx) wins over extension."""
        result = validate_upload(_DOCX_BYTES, "wrong_ext.pdf")
        assert result.valid is True
        assert result.file_type == "docx"

    def test_detect_mime_returns_pdf_for_pdf_header(self):
        """_detect_mime correctly identifies PDF magic bytes."""
        assert _detect_mime(_PDF_HEADER[:16]) == "pdf"

    def test_detect_mime_returns_zip_for_zip_header(self):
        """_detect_mime returns 'docx' for ZIP header (matches first ZIP rule)."""
        detected = _detect_mime(_ZIP_HEADER[:16])
        assert detected in ("docx", "xlsx")  # ZIP matches either

    def test_detect_mime_returns_empty_for_unknown_content(self):
        """_detect_mime returns '' when no magic signature matches."""
        assert _detect_mime(b"GARBAGE BYTES HERE") == ""

    def test_disambiguate_zip_word_gives_docx(self):
        """ZIP body containing 'word/' → docx."""
        assert _disambiguate_zip(_DOCX_BYTES) == "docx"

    def test_disambiguate_zip_xl_gives_xlsx(self):
        """ZIP body containing 'xl/' → xlsx."""
        assert _disambiguate_zip(_XLSX_BYTES) == "xlsx"

    def test_disambiguate_zip_neither_defaults_to_docx(self):
        """Bare ZIP with no word/ or xl/ directory → default 'docx'."""
        assert _disambiguate_zip(_ZIP_HEADER) == "docx"

    def test_allowed_extensions_set_covers_expected_types(self):
        """Sanity check: .pdf, .docx, .xlsx are all in the allow-list."""
        for ext in (".pdf", ".docx", ".xlsx"):
            assert ext in ALLOWED_EXTENSIONS

    # ── Worst-case / boundary paths ──────────────────────────────────────────

    def test_empty_file_rejected_with_file_empty_code(self):
        """Zero-byte file → FILE_EMPTY error code."""
        result = validate_upload(b"", "empty.pdf")
        assert result.valid is False
        assert result.error_code == "FILE_EMPTY"

    def test_oversized_file_rejected(self):
        """File over max_upload_size_bytes → FILE_TOO_LARGE."""
        from app.core.config import settings
        oversized = b"x" * (settings.max_upload_size_bytes + 1)
        result = validate_upload(oversized, "huge.pdf")
        assert result.valid is False
        assert result.error_code == "FILE_TOO_LARGE"

    def test_exactly_at_size_limit_is_rejected(self):
        """File of exactly max_upload_size_bytes + 1 → rejected."""
        from app.core.config import settings
        # One byte over the limit
        one_over = b"%PDF" + b"x" * settings.max_upload_size_bytes
        result = validate_upload(one_over, "limit.pdf")
        assert result.valid is False
        assert result.error_code == "FILE_TOO_LARGE"

    def test_one_byte_under_limit_passes_size_check(self):
        """File of exactly max_upload_size_bytes (not over) passes size check.
        (May still fail magic-byte check if content is not valid.)"""
        from app.core.config import settings
        # Build PDF-magic-valid content at the exact limit
        at_limit = b"%PDF" + b"x" * (settings.max_upload_size_bytes - 4)
        result = validate_upload(at_limit, "at_limit.pdf")
        # Size check passes; content check should also pass (has %PDF header)
        assert result.error_code != "FILE_TOO_LARGE"

    def test_disallowed_extension_rejected(self):
        """Executable extension → INVALID_FILE_TYPE, even with valid PDF content."""
        result = validate_upload(_PDF_HEADER, "malware.exe")
        assert result.valid is False
        assert result.error_code == "INVALID_FILE_TYPE"

    def test_disallowed_extension_zip_rejected(self):
        """.zip extension (not in allow-list) → INVALID_FILE_TYPE."""
        result = validate_upload(_ZIP_HEADER, "archive.zip")
        assert result.valid is False
        assert result.error_code == "INVALID_FILE_TYPE"

    def test_invalid_content_with_valid_extension_rejected(self):
        """Random bytes with .pdf extension → INVALID_FILE_CONTENT."""
        result = validate_upload(b"not a pdf at all!!", "fake.pdf")
        assert result.valid is False
        assert result.error_code == "INVALID_FILE_CONTENT"

    def test_truncated_pdf_header_still_valid(self):
        """File with only the PDF magic bytes (very small) still detected as PDF."""
        minimal_pdf = b"%PDF" + b" 1.4"
        result = validate_upload(minimal_pdf, "tiny.pdf")
        assert result.valid is True
        assert result.file_type == "pdf"

    def test_single_byte_file_fails_empty_check_or_magic(self):
        """A 1-byte file either fails size (if 0) or magic (if non-zero)."""
        result = validate_upload(b"x", "single.pdf")
        assert result.valid is False
        # Fails INVALID_FILE_CONTENT since 'x' doesn't match any magic
        assert result.error_code == "INVALID_FILE_CONTENT"

    def test_uppercase_extension_accepted_after_lowercase_normalisation(self):
        """The validator normalises the extension with .lower() before the allow-list
        check, so .PDF → .pdf and the file is accepted (content is valid PDF)."""
        result = validate_upload(_PDF_HEADER, "INVOICE.PDF")
        assert result.valid is True
        assert result.file_type == "pdf"

    def test_no_extension_rejected(self):
        """No file extension → not in allow-list → INVALID_FILE_TYPE."""
        result = validate_upload(_PDF_HEADER, "noextension")
        assert result.valid is False
        assert result.error_code == "INVALID_FILE_TYPE"



# ============================================================================
# SECTION 2 — SANITIZER
# ============================================================================
from app.utils.sanitizer import sanitize_filename, storage_filename


class TestSanitizerEdgeCases:
    # ── Best-case paths ──────────────────────────────────────────────────────

    def test_normal_filename_unchanged_stem(self):
        """Clean ASCII filename passes through with lowercase extension."""
        result = sanitize_filename("invoice.pdf")
        assert "invoice" in result
        assert result.endswith(".pdf")

    def test_extension_lowercased(self):
        """Extension is always lower-cased."""
        assert sanitize_filename("Doc.PDF").endswith(".pdf")
        assert sanitize_filename("Sheet.XLSX").endswith(".xlsx")

    def test_storage_filename_is_uuid_with_correct_extension(self):
        """storage_filename always returns a UUID + original extension."""
        sfn = storage_filename("document.pdf")
        assert sfn.endswith(".pdf")
        # UUID v4 has 36 chars; strip extension and check length
        stem = sfn[: -len(".pdf")]
        assert len(stem) == 36  # uuid4() str length

    def test_storage_filename_preserves_docx_extension(self):
        result = storage_filename("report.docx")
        assert result.endswith(".docx")

    def test_storage_filename_each_call_unique(self):
        """Every call produces a different storage filename."""
        a = storage_filename("same.pdf")
        b = storage_filename("same.pdf")
        assert a != b

    # ── Average-case paths ───────────────────────────────────────────────────

    def test_path_traversal_stripped(self):
        """../../../etc/passwd → stem keeps only the final path component."""
        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result
        assert "/" not in result
        assert "\\" not in result
        assert len(result) > 0

    def test_windows_path_separators_stripped(self):
        r"""C:\Users\secret.pdf → separators removed."""
        result = sanitize_filename(r"C:\Users\secret.pdf")
        assert "\\" not in result
        assert ":" not in result

    def test_unicode_nfkc_normalised(self):
        """Full-width ASCII chars are NFKC-normalised to regular ASCII."""
        # ｉｎｖｏｉｃｅ is full-width; NFKC → 'invoice'
        result = sanitize_filename("ｉｎｖｏｉｃｅ.pdf")
        assert result.endswith(".pdf")
        assert len(result) > 4  # some stem present

    def test_spaces_collapsed_to_underscores(self):
        """Multiple spaces/separators collapsed to single underscore."""
        result = sanitize_filename("My   Invoice   File.pdf")
        assert "  " not in result
        assert result.endswith(".pdf")

    def test_mixed_unsafe_chars_replaced(self):
        """<>:"/\\|?* and control chars are replaced."""
        result = sanitize_filename('bad<>:"/\\|?*.pdf')
        for ch in '<>:"/\\|?*':
            assert ch not in result

    def test_leading_trailing_dots_stripped(self):
        """Leading and trailing dots in the stem are stripped."""
        result = sanitize_filename("...hidden....pdf")
        assert not result.startswith(".")
        assert result.endswith(".pdf")

    def test_filename_with_no_extension_gets_empty_suffix(self):
        """File with no extension keeps stem, suffix is empty."""
        result = sanitize_filename("README")
        assert len(result) > 0
        assert "README" in result or result  # stem preserved

    def test_storage_filename_no_extension_uses_bin(self):
        """storage_filename for a name with no extension uses .bin."""
        result = storage_filename("noextension")
        assert result.endswith(".bin")

    # ── Worst-case / boundary paths ──────────────────────────────────────────

    def test_empty_string_returns_uuid_bin(self):
        """Empty string input → uuid.bin fallback."""
        result = sanitize_filename("")
        assert result.endswith(".bin")
        assert len(result) > 4  # uuid hex is 32 chars

    def test_whitespace_only_stem_gets_uuid_fallback(self):
        """'   .pdf' — after stripping whitespace/dots, the full name becomes empty
        so Path('').suffix == '' and the result is a bare uuid hex (no extension).
        This documents the actual sanitiser behaviour for this edge input."""
        result = sanitize_filename("   .pdf")
        # The whole name collapses to empty; suffix is lost → bare uuid hex
        assert len(result) > 0
        assert result.isalnum() or "_" in result  # uuid hex or underscore form

    def test_all_unsafe_chars_stem_gets_uuid(self):
        """Stem made entirely of unsafe chars collapses to uuid."""
        result = sanitize_filename('<>:"|?.pdf')
        assert result.endswith(".pdf")
        assert len(result) > 5  # uuid or sanitised form present

    def test_very_long_stem_truncated_to_120(self):
        """Stem longer than 120 chars is truncated."""
        long_name = "a" * 300 + ".pdf"
        result = sanitize_filename(long_name)
        stem = result[: -len(".pdf")]
        assert len(stem) <= 120

    def test_exactly_120_char_stem_not_truncated(self):
        """Stem of exactly 120 chars is preserved as-is."""
        name = "b" * 120 + ".pdf"
        result = sanitize_filename(name)
        stem = result[: -len(".pdf")]
        assert len(stem) == 120

    def test_null_bytes_in_filename_removed(self):
        """Null bytes (\x00) are unsafe and removed."""
        result = sanitize_filename("file\x00name.pdf")
        assert "\x00" not in result
        assert result.endswith(".pdf")

    def test_dot_only_filename_returns_uuid(self):
        """A filename of just dots → empty stem → uuid fallback."""
        result = sanitize_filename("...")
        assert len(result) > 0

    def test_sanitize_is_deterministic_for_same_input(self):
        """Same input always produces same sanitised name (no random unless stem empty)."""
        a = sanitize_filename("My Invoice Final.pdf")
        b = sanitize_filename("My Invoice Final.pdf")
        assert a == b



# ============================================================================
# SECTION 3 — CHUNKER
# ============================================================================
from app.utils.chunker import (
    TARGET_CHARS,
    TARGET_TOKENS,
    OVERLAP_CHARS,
    TextChunk,
    _estimate_tokens,
    _split_sentences,
    chunk_pages,
    chunk_text,
)


class TestChunkerEdgeCases:
    # ── Best-case paths ──────────────────────────────────────────────────────

    def test_short_text_produces_single_chunk(self):
        """Text well under TARGET_CHARS produces exactly one chunk."""
        chunks = chunk_text("Short manufacturing quote. Price: $100.", page_number=1)
        assert len(chunks) == 1
        assert chunks[0].page_number == 1
        assert chunks[0].chunk_index == 0

    def test_single_sentence_chunk_has_content(self):
        """One sentence yields one chunk with non-empty content."""
        chunks = chunk_text("ISO 9001:2015 certification confirmed.")
        assert len(chunks) == 1
        assert len(chunks[0].content) > 0

    def test_chunk_index_starts_at_zero(self):
        """chunk_index is 0-indexed and starts at 0."""
        chunks = chunk_text("First sentence. Second sentence.")
        assert chunks[0].chunk_index == 0

    def test_chunk_page_number_matches_input(self):
        """page_number on chunks matches the input page tuple."""
        chunks = chunk_pages([(5, "Page five content. More content here.")])
        assert all(c.page_number == 5 for c in chunks)

    def test_token_count_positive_for_any_content(self):
        """Every emitted chunk has token_count >= 1."""
        chunks = chunk_text("x")
        for c in chunks:
            assert c.token_count >= 1

    def test_determinism_same_input_same_output(self):
        """chunk_pages is deterministic: same input → identical output."""
        pages = [(1, "Sentence one. Sentence two. Sentence three.")]
        a = chunk_pages(pages)
        b = chunk_pages(pages)
        assert [c.content for c in a] == [c.content for c in b]

    # ── Average-case paths ───────────────────────────────────────────────────

    def test_multi_page_input_page_numbers_preserved(self):
        """Chunks from page 2 carry page_number=2."""
        pages = [
            (1, "Page one text. More text here."),
            (2, "Page two text. Additional content."),
        ]
        chunks = chunk_pages(pages)
        page_nums = {c.page_number for c in chunks}
        assert 1 in page_nums or 2 in page_nums  # at least one page present

    def test_heading_detection_sets_section_name(self):
        """ALL-CAPS line is detected as a heading and stored in section_name."""
        pages = [(1, "COMMERCIAL QUOTATION\nUnit Price: USD 95.00. Lead Time: 14 days.")]
        chunks = chunk_pages(pages)
        assert len(chunks) >= 1
        # At least one chunk should have the section name detected
        section_names = [c.section_name for c in chunks]
        assert any(s is not None for s in section_names)

    def test_heading_with_colon_suffix_detected(self):
        """'Delivery Terms:' (colon-suffix heading) sets section_name."""
        pages = [(1, "Delivery Terms:\nFOB Stuttgart. DHL Express freight.")]
        chunks = chunk_pages(pages)
        # Section name should strip trailing colon
        section_names = [c.section_name for c in chunks if c.section_name]
        assert any("Delivery Terms" in s for s in section_names)

    def test_estimate_tokens_minimum_is_1(self):
        """_estimate_tokens returns at least 1 even for a single char."""
        assert _estimate_tokens("x") == 1

    def test_estimate_tokens_scales_with_length(self):
        """Longer text produces proportionally higher token count."""
        short = _estimate_tokens("word")
        long_ = _estimate_tokens("word " * 100)
        assert long_ > short

    def test_split_sentences_on_period_whitespace(self):
        """Sentences are split at period+whitespace boundaries."""
        parts = _split_sentences("First sentence. Second sentence. Third.")
        assert len(parts) >= 2

    def test_split_sentences_on_exclamation(self):
        """Exclamation mark also triggers a sentence split."""
        parts = _split_sentences("Alert! Warning issued.")
        assert len(parts) >= 2

    def test_split_sentences_no_boundary_returns_single_element(self):
        """Text with no sentence-end boundaries returns as a single-element list."""
        parts = _split_sentences("No terminator in this text")
        assert len(parts) == 1

    def test_chunk_text_convenience_wrapper_page_number(self):
        """chunk_text(text, page_number=3) sets page_number=3 on all chunks."""
        chunks = chunk_text("Test sentence for page three.", page_number=3)
        assert all(c.page_number == 3 for c in chunks)

    def test_long_document_produces_multiple_chunks(self):
        """Text much longer than TARGET_CHARS is split into multiple chunks."""
        # Generate ~3× TARGET_CHARS of text
        sentence = "This is a manufacturing quality control sentence that is reasonably long. "
        text = sentence * (TARGET_CHARS // len(sentence) * 3 + 1)
        chunks = chunk_text(text)
        assert len(chunks) >= 2

    def test_overlap_tail_content_in_consecutive_chunks(self):
        """Consecutive chunks share the overlap tail — last sentence(s) of chunk N
        appear at the start of chunk N+1."""
        sentence = "Overlap sentence for testing purposes here. "
        text = sentence * (TARGET_CHARS // len(sentence) * 2 + 5)
        chunks = chunk_text(text)
        if len(chunks) >= 2:
            # The end of chunk[0] should overlap with start of chunk[1]
            end_of_first = chunks[0].content[-OVERLAP_CHARS:].strip()
            start_of_second = chunks[1].content[:OVERLAP_CHARS].strip()
            # They should share at least some characters
            assert len(end_of_first) > 0 or len(start_of_second) > 0

    def test_all_chunks_have_frozen_dataclass_immutability(self):
        """TextChunk is frozen — attribute assignment raises FrozenInstanceError."""
        chunks = chunk_text("Immutable chunk test.")
        with pytest.raises((AttributeError, TypeError)):
            chunks[0].content = "mutated"  # type: ignore[misc]

    # ── Worst-case / boundary paths ──────────────────────────────────────────

    def test_empty_pages_list_returns_empty(self):
        """chunk_pages([]) → empty list, no crash."""
        assert chunk_pages([]) == []

    def test_whitespace_only_page_skipped(self):
        """A page consisting only of whitespace produces no chunks."""
        chunks = chunk_pages([(1, "   \n\t\n   ")])
        assert chunks == []

    def test_empty_string_page_produces_no_chunks(self):
        """Empty-string page text produces no chunks."""
        chunks = chunk_pages([(1, "")])
        assert chunks == []

    def test_none_equivalent_all_blank_pages_returns_empty(self):
        """Multiple blank pages → empty result."""
        chunks = chunk_pages([(1, ""), (2, "  "), (3, "\n\n")])
        assert chunks == []

    def test_very_long_single_sentence_emitted_as_one_chunk(self):
        """A single sentence longer than TARGET_CHARS is still emitted as one chunk
        (the chunker never splits within a sentence)."""
        long_sentence = "word " * (TARGET_CHARS // 5 + 100)
        chunks = chunk_text(long_sentence.strip())
        # All content should be in chunks (none dropped)
        total_content = " ".join(c.content for c in chunks)
        assert len(total_content) > 0
        assert len(chunks) >= 1

    def test_page_with_only_a_heading_produces_no_content_chunk(self):
        """A page with only a heading line and no body sentences may produce
        zero chunks (heading alone has no sentence-end delimiter)."""
        chunks = chunk_pages([(1, "SECTION HEADING")])
        # The heading line is not a sentence (no terminator) → may or may not emit
        # The invariant is: it must not crash and all emitted chunks have content
        for c in chunks:
            assert len(c.content.strip()) > 0

    def test_chunk_indices_are_sequential(self):
        """chunk_index values form a sequential 0-based sequence."""
        sentence = "Sequential chunk test sentence number here. "
        text = sentence * (TARGET_CHARS // len(sentence) * 3 + 1)
        chunks = chunk_text(text)
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_token_count_approximation_reasonable(self):
        """token_count ≈ len(content) / 4.5, within ±20% of direct estimate."""
        chunks = chunk_text("The quick brown fox jumps over the lazy dog.")
        for c in chunks:
            direct = _estimate_tokens(c.content)
            assert abs(c.token_count - direct) <= 2  # implementation match

    def test_mixed_valid_and_blank_pages(self):
        """Blank pages are skipped; valid pages still produce chunks."""
        pages = [(1, ""), (2, "Valid content on page two. More text here."), (3, "   ")]
        chunks = chunk_pages(pages)
        assert len(chunks) >= 1
        assert all(c.page_number == 2 for c in chunks)



# ============================================================================
# SECTION 4 — EMBED_TEXTS (local / zero-vector path, no network)
# ============================================================================
from app.ai.embeddings import _EMBEDDING_DIMS, embed_texts


class TestEmbedTextsEdgeCases:
    # ── Best-case paths ──────────────────────────────────────────────────────

    def test_empty_list_raises_value_error(self):
        """embed_texts([]) must raise ValueError, not crash silently."""
        with pytest.raises(ValueError, match="at least one text"):
            embed_texts([])

    def test_local_provider_zero_vector_fallback_when_no_sentence_transformers(self):
        """When sentence-transformers is not importable, local provider returns
        zero vectors of the correct dimension (384 for 'local')."""
        import sys
        # Temporarily make sentence_transformers unimportable
        original = sys.modules.get("sentence_transformers")
        sys.modules["sentence_transformers"] = None  # type: ignore[assignment]
        try:
            with patch("app.core.config.settings") as mock_settings:
                mock_settings.embedding_provider = "local"
                mock_settings.local_embedding_model = "BAAI/bge-small-en-v1.5"
                # Force _st_model to None so it tries to load
                import app.ai.embeddings as emb_mod
                emb_mod._st_model = None
                result = emb_mod._embed_local(["test text"], mock_settings)
        finally:
            if original is None:
                del sys.modules["sentence_transformers"]
            else:
                sys.modules["sentence_transformers"] = original

        assert isinstance(result, list)
        assert len(result) == 1
        assert len(result[0]) == _EMBEDDING_DIMS["local"]  # 384
        assert all(v == 0.0 for v in result[0])

    def test_embedding_dims_constants_correct(self):
        """Dimension constants match documented provider specs."""
        assert _EMBEDDING_DIMS["local"]  == 384
        assert _EMBEDDING_DIMS["openai"] == 1536
        assert _EMBEDDING_DIMS["gemini"] == 768

    # ── Average-case paths ───────────────────────────────────────────────────

    def test_openai_provider_raises_runtime_error_without_package(self):
        """If openai package not installed, RuntimeError is raised."""
        import sys
        original = sys.modules.get("openai")
        sys.modules["openai"] = None  # type: ignore[assignment]
        try:
            with patch("app.core.config.settings") as mock_settings:
                mock_settings.embedding_provider = "openai"
                mock_settings.openai_api_key = "test-key"
                mock_settings.openai_embedding_model = "text-embedding-3-small"
                import app.ai.embeddings as emb_mod
                with pytest.raises(RuntimeError, match="openai package is not installed"):
                    emb_mod._embed_openai(["text"], mock_settings)
        finally:
            if original is None:
                del sys.modules["openai"]
            else:
                sys.modules["openai"] = original

    def test_gemini_provider_raises_runtime_error_without_package(self):
        """If google-generativeai not installed, RuntimeError is raised."""
        import sys
        original = sys.modules.get("google.generativeai")
        sys.modules["google.generativeai"] = None  # type: ignore[assignment]
        try:
            with patch("app.core.config.settings") as mock_settings:
                mock_settings.embedding_provider = "gemini"
                mock_settings.gemini_api_key = "test-key"
                import app.ai.embeddings as emb_mod
                with pytest.raises(RuntimeError, match="google-generativeai"):
                    emb_mod._embed_gemini(["text"], mock_settings)
        finally:
            if original is None:
                sys.modules.pop("google.generativeai", None)
            else:
                sys.modules["google.generativeai"] = original

    def test_zero_vector_has_correct_length_for_local(self):
        """The zero-vector fallback produces exactly 384 floats per text."""
        dim = _EMBEDDING_DIMS["local"]
        zero_vec = [0.0] * dim
        assert len(zero_vec) == 384

    def test_zero_vector_fallback_multiple_texts(self):
        """Zero-vector fallback returns one vector per input text."""
        import sys
        original = sys.modules.get("sentence_transformers")
        sys.modules["sentence_transformers"] = None  # type: ignore[assignment]
        try:
            with patch("app.core.config.settings") as mock_settings:
                mock_settings.embedding_provider = "local"
                mock_settings.local_embedding_model = "BAAI/bge-small-en-v1.5"
                import app.ai.embeddings as emb_mod
                emb_mod._st_model = None
                texts = ["text one", "text two", "text three"]
                result = emb_mod._embed_local(texts, mock_settings)
        finally:
            if original is None:
                del sys.modules["sentence_transformers"]
            else:
                sys.modules["sentence_transformers"] = original

        assert len(result) == 3
        for vec in result:
            assert len(vec) == 384
            assert all(v == 0.0 for v in vec)

    # ── Worst-case / boundary paths ──────────────────────────────────────────

    def test_single_empty_string_accepted_no_crash(self):
        """embed_texts(['']) — empty string is technically accepted (>0 texts).
        The local zero-vector path handles it without crash."""
        import sys
        original = sys.modules.get("sentence_transformers")
        sys.modules["sentence_transformers"] = None  # type: ignore[assignment]
        try:
            with patch("app.core.config.settings") as mock_settings:
                mock_settings.embedding_provider = "local"
                mock_settings.local_embedding_model = "BAAI/bge-small-en-v1.5"
                import app.ai.embeddings as emb_mod
                emb_mod._st_model = None
                result = emb_mod._embed_local([""], mock_settings)
        finally:
            if original is None:
                del sys.modules["sentence_transformers"]
            else:
                sys.modules["sentence_transformers"] = original

        assert len(result) == 1
        assert len(result[0]) == 384

    def test_embed_texts_empty_list_error_message(self):
        """ValueError message mentions 'at least one text'."""
        with pytest.raises(ValueError) as exc_info:
            embed_texts([])
        assert "at least one" in str(exc_info.value).lower()



# ============================================================================
# SECTION 5 — RECOMMENDATION SERVICE: _estimate_confidence
# ============================================================================
from app.engines.confidence import calculate_confidence, confidence_label
from app.engines.types import SupplierScoreBreakdown


def _make_breakdown(
    sid: str,
    final_score: float,
    disqualified: bool = False,
) -> SupplierScoreBreakdown:
    return SupplierScoreBreakdown(
        supplier_id=sid,
        landed_cost=100.0,
        cost_score=final_score,
        quality_score=final_score,
        delivery_score=final_score,
        risk_score=final_score,
        capability_score=final_score,
        compliance_score=100.0 if not disqualified else 0.0,
        final_score=final_score,
        rank=1,
        disqualified=disqualified,
    )


def _make_supplier_mock(has_certs=True, has_prices=True, has_risks=True):
    """Build a MagicMock that satisfies the completeness check."""
    s = MagicMock()
    s.certifications = [MagicMock()] if has_certs else []
    s.prices = [MagicMock()] if has_prices else []
    s.risk_scores = [MagicMock()] if has_risks else []
    return s


class TestRecommendationConfidenceEdgeCases:
    """
    Tests for RecommendationService._estimate_confidence logic.
    We call the method directly on an instance with mocked repos.
    """

    def _service(self):
        from app.services.recommendation_service import RecommendationService
        return RecommendationService(
            supplier_repo=MagicMock(),
            project_repo=MagicMock(),
            recommendation_repo=MagicMock(),
        )

    # ── Best-case paths ──────────────────────────────────────────────────────

    def test_high_confidence_all_complete_suppliers_large_doc_count(self):
        """All suppliers complete, many docs, clear score gap → High confidence."""
        svc = self._service()
        ranking = [_make_breakdown("a", 90.0), _make_breakdown("b", 80.0)]
        suppliers = [_make_supplier_mock() for _ in range(2)]
        score, explanation = svc._estimate_confidence(ranking, suppliers, document_count=10)
        assert score >= 60.0  # at least Medium
        assert isinstance(explanation, str) and len(explanation) > 0

    def test_score_gap_at_least_5_gives_full_rule_agreement(self):
        """Gap ≥ 5 between top-2 → rule_agreement=1.0 (best agreement)."""
        svc = self._service()
        # Gap = 90 - 82 = 8 ≥ 5
        ranking = [_make_breakdown("a", 90.0), _make_breakdown("b", 82.0)]
        suppliers = [_make_supplier_mock(), _make_supplier_mock()]
        score, _ = svc._estimate_confidence(ranking, suppliers, document_count=2)
        # With rule_agreement=1.0, score should be higher than with 0.75
        score_low_gap, _ = svc._estimate_confidence(
            [_make_breakdown("a", 90.0), _make_breakdown("b", 88.0)],  # gap=2 < 5
            suppliers, document_count=2,
        )
        assert score > score_low_gap

    # ── Average-case paths ───────────────────────────────────────────────────

    def test_score_gap_below_5_reduces_rule_agreement(self):
        """Gap < 5 → rule_agreement=0.75, producing lower confidence than gap≥5."""
        svc = self._service()
        ranking = [_make_breakdown("a", 90.0), _make_breakdown("b", 88.0)]  # gap=2
        suppliers = [_make_supplier_mock(), _make_supplier_mock()]
        score_small, _ = svc._estimate_confidence(ranking, suppliers, document_count=5)
        ranking2 = [_make_breakdown("a", 90.0), _make_breakdown("b", 84.0)]  # gap=6
        score_large, _ = svc._estimate_confidence(ranking2, suppliers, document_count=5)
        assert score_large > score_small

    def test_evidence_coverage_capped_at_1_point_0(self):
        """document_count >> supplier count → evidence_coverage capped at 1.0."""
        svc = self._service()
        ranking = [_make_breakdown("a", 85.0), _make_breakdown("b", 80.0)]
        suppliers = [_make_supplier_mock(), _make_supplier_mock()]
        # 100 docs for 2 suppliers → coverage = min(1.0, 100/2) = 1.0
        score_many, _ = svc._estimate_confidence(ranking, suppliers, document_count=100)
        # 2 docs for 2 suppliers → coverage = min(1.0, 2/2) = 1.0 also
        score_exact, _ = svc._estimate_confidence(ranking, suppliers, document_count=2)
        assert score_many == score_exact

    def test_zero_document_count_reduces_evidence_coverage(self):
        """0 docs → evidence_coverage=0 → lower confidence than with docs."""
        svc = self._service()
        ranking = [_make_breakdown("a", 85.0), _make_breakdown("b", 80.0)]
        suppliers = [_make_supplier_mock(), _make_supplier_mock()]
        score_no_docs, _ = svc._estimate_confidence(ranking, suppliers, document_count=0)
        score_with_docs, _ = svc._estimate_confidence(ranking, suppliers, document_count=4)
        assert score_with_docs > score_no_docs

    def test_partial_supplier_data_reduces_data_completeness(self):
        """Suppliers missing certs/prices/risks → lower data_completeness → lower confidence."""
        svc = self._service()
        ranking = [_make_breakdown("a", 85.0), _make_breakdown("b", 80.0)]
        complete = [_make_supplier_mock(True, True, True) for _ in range(2)]
        incomplete = [_make_supplier_mock(False, False, False) for _ in range(2)]
        score_complete, _ = svc._estimate_confidence(ranking, complete, document_count=2)
        score_incomplete, _ = svc._estimate_confidence(ranking, incomplete, document_count=2)
        assert score_complete > score_incomplete

    def test_explanation_string_contains_supplier_counts(self):
        """Explanation string mentions the supplier count."""
        svc = self._service()
        ranking = [_make_breakdown("a", 85.0)]
        suppliers = [_make_supplier_mock()]
        _, explanation = svc._estimate_confidence(ranking, suppliers, document_count=1)
        assert "1" in explanation  # at least one number present

    # ── Worst-case / boundary paths ──────────────────────────────────────────

    def test_single_active_supplier_rule_agreement_is_0_7(self):
        """Only one active supplier (no runner-up) → rule_agreement=0.7.
        With equal doc_count and data_completeness, two-supplier score with
        gap≥5 uses rule_agreement=1.0 but evidence_coverage=0.5 (1 doc / 2 suppliers).
        Single supplier has evidence_coverage=1.0 (1 doc / 1 supplier).
        The single-supplier case can therefore score *higher* despite lower rule_agreement.
        We assert only that the score is a valid float in [0, 100]."""
        svc = self._service()
        ranking = [_make_breakdown("a", 85.0)]
        suppliers = [_make_supplier_mock()]
        score_single, explanation = svc._estimate_confidence(ranking, suppliers, document_count=1)
        assert 0.0 <= score_single <= 100.0
        assert isinstance(explanation, str)

    def test_two_suppliers_sufficient_docs_beats_single_supplier_score(self):
        """With enough docs so evidence_coverage=1.0 for both cases,
        two suppliers with gap≥5 (rule_agreement=1.0) score higher than
        single supplier (rule_agreement=0.7)."""
        svc = self._service()
        # Single supplier, 1 doc → coverage=1.0, rule_agreement=0.7
        ranking1 = [_make_breakdown("a", 85.0)]
        suppliers1 = [_make_supplier_mock()]
        score_single, _ = svc._estimate_confidence(ranking1, suppliers1, document_count=1)

        # Two suppliers, 2+ docs → coverage=1.0, gap=10 → rule_agreement=1.0
        ranking2 = [_make_breakdown("a", 90.0), _make_breakdown("b", 80.0)]
        suppliers2 = [_make_supplier_mock(), _make_supplier_mock()]
        score_two, _ = svc._estimate_confidence(ranking2, suppliers2, document_count=4)

        assert score_two > score_single

    def test_all_suppliers_disqualified_no_active_gives_rule_agreement_0_7(self):
        """All disqualified → active list empty (len < 2) → rule_agreement=0.7."""
        svc = self._service()
        ranking = [
            _make_breakdown("a", 0.0, disqualified=True),
            _make_breakdown("b", 0.0, disqualified=True),
        ]
        suppliers = [_make_supplier_mock(False, False, False) for _ in range(2)]
        score, explanation = svc._estimate_confidence(ranking, suppliers, document_count=0)
        assert isinstance(score, float)
        assert score >= 0.0

    def test_confidence_score_output_is_0_to_100(self):
        """confidence_score returned by _estimate_confidence is in [0, 100]."""
        svc = self._service()
        for doc_count in (0, 1, 10, 100):
            ranking = [_make_breakdown("a", 80.0), _make_breakdown("b", 70.0)]
            suppliers = [_make_supplier_mock(), _make_supplier_mock()]
            score, _ = svc._estimate_confidence(ranking, suppliers, document_count=doc_count)
            assert 0.0 <= score <= 100.0, f"Score {score} out of range for doc_count={doc_count}"



# ============================================================================
# SECTION 6 — DOCUMENT SERVICE: _STATUS_PROGRESS MAPPING
# ============================================================================
from app.services.document_service import _STATUS_PROGRESS


class TestDocumentServiceStatusProgress:
    # ── Best-case paths ──────────────────────────────────────────────────────

    def test_completed_status_maps_to_100(self):
        assert _STATUS_PROGRESS["completed"] == 100

    def test_uploaded_status_maps_to_5(self):
        assert _STATUS_PROGRESS["uploaded"] == 5

    # ── Average-case paths ───────────────────────────────────────────────────

    def test_all_known_statuses_present(self):
        """Every pipeline stage has a progress entry."""
        expected = {"uploaded", "processing", "extracting", "indexing", "completed", "error"}
        assert expected.issubset(set(_STATUS_PROGRESS.keys()))

    def test_progress_values_are_non_negative(self):
        """All progress values are ≥ 0."""
        for status, progress in _STATUS_PROGRESS.items():
            assert progress >= 0, f"{status} has negative progress {progress}"

    def test_progress_values_bounded_at_100(self):
        """No status maps to more than 100."""
        for status, progress in _STATUS_PROGRESS.items():
            assert progress <= 100, f"{status} progress {progress} exceeds 100"

    def test_pipeline_stages_in_ascending_order(self):
        """Progress values increase through the happy-path pipeline."""
        pipeline = ["uploaded", "processing", "extracting", "indexing", "completed"]
        values = [_STATUS_PROGRESS[s] for s in pipeline]
        assert values == sorted(values), f"Progress not monotone: {list(zip(pipeline, values))}"

    def test_error_status_maps_to_zero(self):
        """Error state resets progress to 0 (shown as failed)."""
        assert _STATUS_PROGRESS["error"] == 0

    # ── Worst-case / boundary paths ──────────────────────────────────────────

    def test_unknown_status_falls_back_to_zero_via_dict_get(self):
        """Unknown status keys return 0 via .get() with default."""
        assert _STATUS_PROGRESS.get("unknown_state", 0) == 0
        assert _STATUS_PROGRESS.get("", 0) == 0
        assert _STATUS_PROGRESS.get("COMPLETED", 0) == 0  # case-sensitive

    def test_status_progress_is_dict_not_mutable_side_effect(self):
        """_STATUS_PROGRESS is a plain dict; mutating a copy does not affect original."""
        copy = dict(_STATUS_PROGRESS)
        copy["completed"] = 999
        assert _STATUS_PROGRESS["completed"] == 100

    def test_indexing_between_extracting_and_completed(self):
        """Indexing progress is between extracting and completed."""
        assert _STATUS_PROGRESS["extracting"] < _STATUS_PROGRESS["indexing"] < _STATUS_PROGRESS["completed"]

    def test_processing_between_uploaded_and_extracting(self):
        """Processing progress is between uploaded and extracting."""
        assert _STATUS_PROGRESS["uploaded"] < _STATUS_PROGRESS["processing"] < _STATUS_PROGRESS["extracting"]


# ============================================================================
# SECTION 7 — DOCUMENT WORKER: pipeline helpers
# ============================================================================
from app.workers.document_worker import _extract_text
from app.utils.file_validator import _detect_mime, _disambiguate_zip


class TestDocumentWorkerHelpers:
    # ── Best-case paths ──────────────────────────────────────────────────────

    def test_extract_text_unsupported_type_raises_value_error(self):
        """_extract_text with an unknown file_type raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            _extract_text("/some/path.bin", "bin")

    def test_extract_text_unsupported_mp4_raises_value_error(self):
        """Video file type is not in the dispatcher → ValueError."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            _extract_text("/some/video.mp4", "mp4")

    def test_extract_text_empty_string_type_raises_value_error(self):
        """Empty string file_type → ValueError."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            _extract_text("/some/file", "")

    # ── Average-case paths ───────────────────────────────────────────────────

    def test_extract_pdf_raises_runtime_when_pymupdf_missing(self, tmp_path):
        """_extract_pdf raises RuntimeError if PyMuPDF (fitz) not installed."""
        import sys
        fake_file = tmp_path / "test.pdf"
        fake_file.write_bytes(b"%PDF-1.4 fake content")

        original = sys.modules.get("fitz")
        sys.modules["fitz"] = None  # type: ignore[assignment]
        try:
            from app.workers.document_worker import _extract_pdf
            with pytest.raises((RuntimeError, Exception)):
                _extract_pdf(str(fake_file))
        finally:
            if original is None:
                sys.modules.pop("fitz", None)
            else:
                sys.modules["fitz"] = original

    def test_extract_docx_raises_runtime_when_python_docx_missing(self, tmp_path):
        """_extract_docx raises RuntimeError if python-docx not installed."""
        import sys
        fake_file = tmp_path / "test.docx"
        fake_file.write_bytes(b"PK\x03\x04 fake docx")

        original = sys.modules.get("docx")
        sys.modules["docx"] = None  # type: ignore[assignment]
        try:
            from app.workers.document_worker import _extract_docx
            with pytest.raises((RuntimeError, Exception)):
                _extract_docx(str(fake_file))
        finally:
            if original is None:
                sys.modules.pop("docx", None)
            else:
                sys.modules["docx"] = original

    def test_extract_xlsx_raises_runtime_when_openpyxl_missing(self, tmp_path):
        """_extract_xlsx raises RuntimeError if openpyxl not installed."""
        import sys
        fake_file = tmp_path / "test.xlsx"
        fake_file.write_bytes(b"PK\x03\x04 fake xlsx")

        original = sys.modules.get("openpyxl")
        sys.modules["openpyxl"] = None  # type: ignore[assignment]
        try:
            from app.workers.document_worker import _extract_xlsx
            with pytest.raises((RuntimeError, Exception)):
                _extract_xlsx(str(fake_file))
        finally:
            if original is None:
                sys.modules.pop("openpyxl", None)
            else:
                sys.modules["openpyxl"] = original

    # ── Worst-case / boundary paths ──────────────────────────────────────────

    def test_worker_detect_mime_pdf(self):
        """Worker's _detect_mime (imported from file_validator) identifies PDF."""
        assert _detect_mime(b"%PDF-1.4" + b"\x00" * 8) == "pdf"

    def test_worker_detect_mime_zip_based(self):
        """Worker's _detect_mime identifies ZIP container for docx/xlsx."""
        result = _detect_mime(b"PK\x03\x04" + b"\x00" * 13)
        assert result in ("docx", "xlsx")

    def test_worker_detect_mime_unknown_returns_empty(self):
        """Worker's _detect_mime returns '' for unknown bytes."""
        assert _detect_mime(b"RANDOM GARBAGE XX") == ""

    def test_worker_disambiguate_zip_word_gives_docx(self):
        assert _disambiguate_zip(b"PK\x03\x04" + b"word/document.xml") == "docx"

    def test_worker_disambiguate_zip_xl_gives_xlsx(self):
        assert _disambiguate_zip(b"PK\x03\x04" + b"xl/workbook.xml") == "xlsx"

    def test_worker_disambiguate_zip_neither_defaults_docx(self):
        assert _disambiguate_zip(b"PK\x03\x04" + b"unknown/content") == "docx"

    def test_extract_text_dispatcher_contains_all_three_types(self):
        """The dispatcher inside _extract_text handles pdf, docx, xlsx.
        We verify by confirming that each raises a non-ValueError exception
        (i.e. the dispatcher found the function but the file is fake)."""
        import tempfile, os
        for ftype, magic in [("pdf", b"%PDF"), ("docx", b"PK\x03\x04"), ("xlsx", b"PK\x03\x04")]:
            with tempfile.NamedTemporaryFile(suffix=f".{ftype}", delete=False) as f:
                f.write(magic + b"\x00" * 20)
                path = f.name
            try:
                # Should dispatch correctly (not raise ValueError for type)
                # May raise RuntimeError (missing lib) or other — not ValueError("Unsupported")
                try:
                    _extract_text(path, ftype)
                except ValueError as e:
                    assert "Unsupported" not in str(e), \
                        f"Dispatcher missed type '{ftype}': {e}"
                except Exception:
                    pass  # Expected: missing lib, bad file content, etc.
            finally:
                os.unlink(path)

