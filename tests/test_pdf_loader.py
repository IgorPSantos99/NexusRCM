"""Unit tests for the PyMuPDF-backed PDF loader."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from pathlib import Path

import fitz  # type: ignore[import-untyped]
import pytest
from nexusrcm.exceptions import LoaderError
from nexusrcm.ingestion.pdf_loader import PDFLoader
from nexusrcm.interfaces import BaseLoader


def _write_corrupted_pdf(path: Path) -> Path:
    path.write_bytes(b"%PDF-1.7\ntruncated and invalid")
    return path


def test_supported_extensions_contains_pdf() -> None:
    """PDFLoader should declare the extension accepted by orchestration code."""

    assert PDFLoader.supported_extensions == frozenset({".pdf"})


def test_pdf_loader_satisfies_base_loader_protocol() -> None:
    """The concrete loader should satisfy the runtime-checkable protocol."""

    assert isinstance(PDFLoader(), BaseLoader)


def test_load_returns_iterator_not_list(sample_pdf_path: Path) -> None:
    """PDF loading should stream chunks instead of materializing a list."""

    result = PDFLoader().load(sample_pdf_path)

    assert isinstance(result, Iterator)
    assert not isinstance(result, list)


def test_load_rejects_str_source() -> None:
    """Passing a raw string instead of Path should fail before any I/O."""

    with pytest.raises(LoaderError):
        list(PDFLoader().load("some/path.pdf"))  # type: ignore[arg-type]


def test_load_happy_path_yields_chunks_with_source_ref(
    sample_pdf_path: Path,
) -> None:
    """Chunks should carry auditable source references and loader metadata."""

    chunks = list(PDFLoader(chunk_size=64, chunk_overlap=8).load(sample_pdf_path))

    assert chunks
    first_chunk = chunks[0]
    assert "Pump P-101A" in first_chunk.text
    assert first_chunk.source_ref.filename == "sample_manual.pdf"
    assert first_chunk.source_ref.page == 1
    assert first_chunk.source_ref.chunk_index == 0
    assert first_chunk.metadata["loader"] == "pdf"
    assert first_chunk.metadata["total_pages"] == 3


def test_load_preserves_page_numbering(
    sample_pdf_path: Path,
) -> None:
    """Page references should be one-indexed for humans and citations."""

    chunks = list(PDFLoader(chunk_size=64, chunk_overlap=8).load(sample_pdf_path))

    raw_pages = {chunk.source_ref.page for chunk in chunks}
    assert None not in raw_pages
    pages = {page for page in raw_pages if page is not None}
    assert pages == {1, 2, 3}
    assert all(page >= 1 for page in pages)


def test_load_chunk_index_resets_per_page(
    tmp_pdf_factory: Callable[[str, Sequence[str | None]], Path],
) -> None:
    """Each page should start chunk numbering at zero."""

    page_one = " ".join(f"page-one-token-{index}" for index in range(18))
    page_two = " ".join(f"page-two-token-{index}" for index in range(18))
    source = tmp_pdf_factory("multi_chunk.pdf", [page_one, page_two])

    chunks = list(PDFLoader(chunk_size=10, chunk_overlap=2).load(source))

    assert [
        (chunk.source_ref.page, chunk.source_ref.chunk_index) for chunk in chunks
    ] == [
        (1, 0),
        (1, 1),
        (1, 2),
        (2, 0),
        (2, 1),
        (2, 2),
    ]


@pytest.mark.parametrize(("chunk_size", "chunk_overlap"), [(12, 3), (8, 2)])
def test_load_respects_chunk_size_and_overlap(
    tmp_pdf_factory: Callable[[str, Sequence[str | None]], Path],
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    """Chunking should use a sliding token window with the configured overlap."""

    tokens = [f"token-{index}" for index in range(20)]
    source = tmp_pdf_factory("chunked.pdf", [" ".join(tokens)])

    chunks = list(
        PDFLoader(chunk_size=chunk_size, chunk_overlap=chunk_overlap).load(source)
    )

    assert all(len(chunk.text.split()) <= chunk_size for chunk in chunks)
    assert (
        chunks[1].text.split()[:chunk_overlap]
        == chunks[0].text.split()[-chunk_overlap:]
    )


def test_load_missing_file_raises_loader_error(tmp_path: Path) -> None:
    """Missing files should be converted to the domain LoaderError."""

    source = tmp_path / "missing.pdf"

    with pytest.raises(LoaderError) as exc_info:
        list(PDFLoader().load(source))

    assert exc_info.value.source == source
    assert exc_info.value.reason == "file not found"


def test_load_permission_denied(
    sample_pdf_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A PermissionError on stat should surface as LoaderError, not a raw OS error."""

    def raise_permission_error(self: Path) -> None:
        raise PermissionError("access denied")

    monkeypatch.setattr(Path, "stat", raise_permission_error)

    with pytest.raises(LoaderError) as exc_info:
        list(PDFLoader().load(sample_pdf_path))

    assert exc_info.value.source == sample_pdf_path
    assert exc_info.value.reason == "permission denied"


@pytest.mark.parametrize("filename", ["manual.txt", "manual.docx"])
def test_load_unsupported_extension_raises_loader_error(
    tmp_path: Path,
    filename: str,
) -> None:
    """Unsupported extensions should fail before PDF parsing starts."""

    source = tmp_path / filename
    source.write_text("not a pdf", encoding="utf-8")

    with pytest.raises(LoaderError) as exc_info:
        list(PDFLoader().load(source))

    assert exc_info.value.source == source
    assert exc_info.value.reason == f"unsupported extension '{source.suffix}'"


def test_load_oversized_file_raises_loader_error(
    tmp_pdf_factory: Callable[[str, Sequence[str | None]], Path],
) -> None:
    """Files larger than the configured limit should be rejected."""

    source = tmp_pdf_factory("small.pdf", ["Short text."])

    with pytest.raises(LoaderError) as exc_info:
        list(PDFLoader(max_file_size_bytes=1).load(source))

    assert exc_info.value.source == source
    assert exc_info.value.reason is not None
    assert "exceeds limit" in exc_info.value.reason


def test_load_corrupted_pdf_raises_loader_error(tmp_path: Path) -> None:
    """Corrupted PDF bytes should be reported as LoaderError."""

    source = _write_corrupted_pdf(tmp_path / "corrupted.pdf")

    with pytest.raises(LoaderError) as exc_info:
        list(PDFLoader().load(source))

    assert exc_info.value.source == source
    assert exc_info.value.reason is not None
    assert exc_info.value.reason.startswith("corrupted or encrypted pdf:")


def test_load_empty_pdf_returns_empty_iterator(
    tmp_pdf_factory: Callable[[str, Sequence[str | None]], Path],
) -> None:
    """A valid PDF with no extractable text should yield no chunks."""

    source = tmp_pdf_factory("empty.pdf", [""])

    assert list(PDFLoader().load(source)) == []


def test_load_image_only_page_logs_warning_and_skips(
    tmp_pdf_factory: Callable[[str, Sequence[str | None]], Path],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Image-only pages should be skipped with a warning, not an exception."""

    source = tmp_pdf_factory("image_only.pdf", [None])

    with caplog.at_level("WARNING"):
        chunks = list(PDFLoader().load(source))

    assert chunks == []
    assert "image-only page skipped" in caplog.text


def test_load_whitespace_only_page_treated_as_image_only(
    tmp_pdf_factory: Callable[[str, Sequence[str | None]], Path],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A page containing only whitespace should be skipped with a warning."""

    source = tmp_pdf_factory("whitespace_page.pdf", ["   \n\t  "])

    with caplog.at_level("WARNING"):
        chunks = list(PDFLoader().load(source))

    assert chunks == []
    assert "image-only page skipped" in caplog.text


def test_load_mixed_pages_only_text_pages_produce_chunks(
    tmp_pdf_factory: Callable[[str, Sequence[str | None]], Path],
) -> None:
    """Mixed PDFs should preserve text pages and skip image-only pages."""

    source = tmp_pdf_factory(
        "mixed_pages.pdf",
        [
            "Pump seal leak observed during inspection.",
            None,
            "Replace gasket and verify torque sequence.",
        ],
    )

    chunks = list(PDFLoader(chunk_size=64, chunk_overlap=8).load(source))

    assert [chunk.source_ref.page for chunk in chunks] == [1, 3]


@pytest.mark.parametrize(
    "fitz_error", [fitz.FileDataError("bad xref"), RuntimeError("boom")]
)
def test_load_does_not_leak_fitz_exceptions(
    sample_pdf_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fitz_error: Exception,
) -> None:
    """Raw PyMuPDF parsing failures should not escape the loader boundary."""

    def raise_fitz_error(_: Path) -> None:
        raise fitz_error

    monkeypatch.setattr(fitz, "open", raise_fitz_error)

    with pytest.raises(LoaderError) as exc_info:
        list(PDFLoader().load(sample_pdf_path))

    assert exc_info.value.source == sample_pdf_path
    assert exc_info.value.reason is not None
    assert exc_info.value.reason.startswith("corrupted or encrypted pdf:")


def test_load_is_lazy(sample_pdf_path: Path) -> None:
    """Calling load should return a generator that can be consumed incrementally."""

    result = PDFLoader(chunk_size=64, chunk_overlap=8).load(sample_pdf_path)

    first_chunk = next(result)

    assert first_chunk.source_ref.page == 1


@pytest.mark.parametrize("filename", ["manual.PDF", "manual.Pdf"])
def test_load_case_insensitive_extension(
    tmp_pdf_factory: Callable[[str, Sequence[str | None]], Path],
    tmp_path: Path,
    filename: str,
) -> None:
    """PDF extension validation should be case-insensitive."""

    source = tmp_pdf_factory("manual.pdf", ["Uppercase extension should work."])
    renamed_source = tmp_path / filename
    source.rename(renamed_source)

    assert list(PDFLoader().load(renamed_source))


def test_load_chunk_overlap_zero_no_token_repetition(
    tmp_pdf_factory: Callable[[str, Sequence[str | None]], Path],
) -> None:
    """With overlap=0 the sliding window should not repeat any token."""

    tokens = [f"token-{i}" for i in range(20)]
    source = tmp_pdf_factory("no_overlap.pdf", [" ".join(tokens)])

    chunks = list(PDFLoader(chunk_size=10, chunk_overlap=0).load(source))

    assert all(len(chunk.text.split()) <= 10 for chunk in chunks)
    all_tokens = [tok for chunk in chunks for tok in chunk.text.split()]
    assert all_tokens == tokens


def test_load_emits_info_logs_on_start_and_finish(
    sample_pdf_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The loader should emit INFO logs when it starts and when it finishes."""

    with caplog.at_level("INFO", logger="nexusrcm.ingestion.pdf_loader"):
        list(PDFLoader(chunk_size=64, chunk_overlap=8).load(sample_pdf_path))

    info_messages = [r.message for r in caplog.records if r.levelname == "INFO"]
    assert any("sample_manual.pdf" in msg for msg in info_messages)
    assert any("chunk" in msg for msg in info_messages)


def test_constructor_rejects_overlap_geq_chunk_size() -> None:
    """Invalid chunk windows should fail at construction time."""

    with pytest.raises(
        ValueError, match="chunk_overlap must be smaller than chunk_size"
    ):
        PDFLoader(chunk_size=32, chunk_overlap=32)
