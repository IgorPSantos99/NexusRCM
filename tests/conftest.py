"""Shared pytest fixtures for NexusRCM tests."""

from __future__ import annotations

import base64
from collections.abc import Callable, Sequence
from pathlib import Path

import fitz  # type: ignore[import-untyped]
import pytest

_ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwM"
    "CAO+/p9sAAAAASUVORK5CYII="
)


@pytest.fixture
def tmp_pdf_factory(
    tmp_path: Path,
) -> Callable[[str, Sequence[str | None]], Path]:
    """Create small synthetic PDFs for loader tests.

    A page value of ``None`` creates an image-only page. An empty string
    creates a blank textless page.
    """

    def _create_pdf(filename: str, pages: Sequence[str | None]) -> Path:
        pdf_path = tmp_path / filename
        document = fitz.open()

        for page_content in pages:
            page = document.new_page()
            if page_content is None:
                page.insert_image(
                    fitz.Rect(72, 72, 144, 144),
                    stream=_ONE_PIXEL_PNG,
                )
                continue

            if page_content:
                page.insert_textbox(
                    fitz.Rect(72, 72, 540, 720),
                    page_content,
                    fontsize=11,
                )

        document.save(pdf_path)
        document.close()
        return pdf_path

    return _create_pdf


@pytest.fixture
def sample_pdf_path(
    tmp_pdf_factory: Callable[[str, Sequence[str | None]], Path],
) -> Path:
    """Create a three-page OEM-like maintenance manual sample."""

    return tmp_pdf_factory(
        "sample_manual.pdf",
        [
            "Pump P-101A shows elevated vibration and bearing wear.",
            "Inspect lubrication lines before replacing the bearing housing.",
            "After corrective action, verify alignment and trend vibration.",
        ],
    )
