"""PDF ingestion loader backed by PyMuPDF.

The loader converts text-bearing PDF pages into ``DocumentChunk`` objects
while preserving filename, one-indexed page number, and per-page chunk index
for auditability in downstream NLP, graph, and retrieval stages.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any, ClassVar

from nexusrcm.config import (
    DEFAULT_PDF_MAX_FILE_SIZE_BYTES,
    get_settings,
)
from nexusrcm.exceptions import LoaderError
from nexusrcm.ingestion._validation import (
    _ensure_path_source,
    _validate_existing_file,
    _validate_file_size,
    _validate_supported_extension,
)
from nexusrcm.interfaces import DocumentChunk, SourceRef

_PYMUPDF: Any
_FITZ_IMPORT_ERROR: ImportError | None

try:
    import fitz as _fitz_module  # type: ignore[import-untyped]
except ImportError as exc:  # pragma: no cover - exercised only without PyMuPDF.
    _PYMUPDF = None
    _FITZ_IMPORT_ERROR = exc
else:
    _PYMUPDF = _fitz_module
    _FITZ_IMPORT_ERROR = None

logger = logging.getLogger(__name__)

__all__ = ["PDFLoader"]


class PDFLoader:
    """Load textual PDF pages into normalized document chunks.

    Extension validation is case-insensitive, so ``.PDF`` and ``.Pdf`` are
    accepted in addition to ``.pdf``.
    """

    supported_extensions: ClassVar[frozenset[str]] = frozenset({".pdf"})
    max_file_size_bytes: int = DEFAULT_PDF_MAX_FILE_SIZE_BYTES

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        max_file_size_bytes: int | None = None,
    ) -> None:
        """Create a PDF loader.

        Args:
            chunk_size: Maximum whitespace-token count per chunk. Defaults to
                ``Settings.pdf_chunk_size_tokens``.
            chunk_overlap: Number of tokens repeated between adjacent chunks.
                Defaults to ``Settings.pdf_chunk_overlap_tokens``.
            max_file_size_bytes: Optional test or runtime override for the
                PDF size limit. Defaults to ``Settings.pdf_max_file_size_bytes``.

        Raises:
            ValueError: If chunk sizing cannot make forward progress.
        """

        settings = get_settings()
        self._chunk_size = (
            settings.pdf_chunk_size_tokens if chunk_size is None else chunk_size
        )
        self._chunk_overlap = (
            settings.pdf_chunk_overlap_tokens
            if chunk_overlap is None
            else chunk_overlap
        )
        self._min_text_chars_per_page = settings.pdf_min_text_chars_per_page
        self.max_file_size_bytes = (
            settings.pdf_max_file_size_bytes
            if max_file_size_bytes is None
            else max_file_size_bytes
        )

        if self._chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if self._chunk_overlap < 0:
            raise ValueError("chunk_overlap must be greater than or equal to zero")
        if self._chunk_overlap >= self._chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        if self.max_file_size_bytes <= 0:
            raise ValueError("max_file_size_bytes must be greater than zero")

    def load(self, source: Path) -> Iterator[DocumentChunk]:
        """Load a PDF source into normalized text chunks.

        Args:
            source: Path to a PDF file.

        Yields:
            Document chunks with auditable page and chunk references.

        Raises:
            LoaderError: If the source is invalid, unsupported, corrupted, or
                cannot be parsed safely.
        """

        _ensure_pymupdf_available()
        _ensure_path_source(source)
        _validate_existing_file(source)
        _validate_supported_extension(source, self.supported_extensions)
        file_size = _validate_file_size(source, self.max_file_size_bytes)

        logger.info(
            "pdf load started: %s (%s bytes)",
            source.name,
            file_size,
            extra={"source_filename": source.name, "file_size_bytes": file_size},
        )

        document: Any | None = None
        chunks_emitted = 0
        try:
            document = _PYMUPDF.open(source)
            total_pages = int(document.page_count)

            for page_index, page in enumerate(document):
                page_number = page_index + 1
                text = str(page.get_text("text")).strip()
                if len(text) < self._min_text_chars_per_page:
                    logger.warning(
                        "image-only page skipped",
                        extra={"source_filename": source.name, "page": page_number},
                    )
                    continue

                for local_chunk_index, chunk_text in enumerate(
                    self._chunk_page_text(text)
                ):
                    chunks_emitted += 1
                    yield DocumentChunk(
                        text=chunk_text,
                        source_ref=SourceRef(
                            filename=source.name,
                            page=page_number,
                            chunk_index=local_chunk_index,
                        ),
                        metadata={"loader": "pdf", "total_pages": total_pages},
                    )
        except (_PYMUPDF.FileDataError, RuntimeError) as exc:
            raise LoaderError(
                source,
                f"corrupted or encrypted pdf: {exc}",
            ) from exc
        else:
            logger.info(
                "pdf load finished: %s (%s chunks)",
                source.name,
                chunks_emitted,
                extra={
                    "source_filename": source.name,
                    "chunks_emitted": chunks_emitted,
                },
            )
        finally:
            if document is not None:
                document.close()

    def _chunk_page_text(self, text: str) -> Iterator[str]:
        """Split page text using a whitespace-token sliding window.

        This is an approximate tokenization strategy, not BPE or
        sentencepiece. It can be replaced once NLP extraction standardizes on
        a model tokenizer.
        """

        tokens = text.split()
        if not tokens:
            return

        step = self._chunk_size - self._chunk_overlap
        for start in range(0, len(tokens), step):
            chunk_tokens = tokens[start : start + self._chunk_size]
            if not chunk_tokens:
                continue
            yield " ".join(chunk_tokens)


def _ensure_pymupdf_available() -> None:
    """Raise a clear installation error if PyMuPDF is unavailable."""

    if _FITZ_IMPORT_ERROR is None:
        return

    message = (
        "PyMuPDF is required for PDFLoader. Install project dependencies from "
        "pyproject.toml, including 'PyMuPDF>=1.24,<2.0'."
    )
    raise LoaderError(Path("<PyMuPDF>"), message) from _FITZ_IMPORT_ERROR
