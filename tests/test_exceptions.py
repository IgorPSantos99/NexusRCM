"""Tests for NexusRCM domain exceptions."""

from __future__ import annotations

from pathlib import Path

import nexusrcm.exceptions as exceptions
import pytest
from nexusrcm.exceptions import (
    DiagnosticError,
    ExtractionError,
    GraphStoreError,
    IngestionError,
    LoaderError,
    NexusRCMError,
    RetrievalError,
    VectorStoreError,
)


def test_public_exceptions_are_exported() -> None:
    """All stable exception types should be part of the module public API."""

    assert set(exceptions.__all__) == {
        "NexusRCMError",
        "IngestionError",
        "DiagnosticError",
        "LoaderError",
        "ExtractionError",
        "GraphStoreError",
        "RetrievalError",
        "VectorStoreError",
    }


def test_exception_hierarchy_groups_domain_failures() -> None:
    """Specialized failures should share the common NexusRCM base type."""

    assert issubclass(RetrievalError, DiagnosticError)
    assert issubclass(LoaderError, IngestionError)
    assert issubclass(DiagnosticError, NexusRCMError)
    assert issubclass(IngestionError, NexusRCMError)
    assert issubclass(ExtractionError, NexusRCMError)
    assert issubclass(GraphStoreError, NexusRCMError)
    assert issubclass(RetrievalError, NexusRCMError)
    assert issubclass(VectorStoreError, NexusRCMError)


def test_nexus_rcm_error_stores_optional_reason() -> None:
    """The base exception should preserve a structured reason when provided."""

    error = NexusRCMError("Operation failed", reason="invalid contract state")

    assert str(error) == "Operation failed"
    assert error.reason == "invalid contract state"


@pytest.mark.parametrize(
    "error_type",
    [
        IngestionError,
        DiagnosticError,
        ExtractionError,
        GraphStoreError,
        RetrievalError,
        VectorStoreError,
    ],
)
def test_domain_errors_inherit_reason_support(
    error_type: type[NexusRCMError],
) -> None:
    """Concrete domain errors should share the base structured reason API."""

    error = error_type("Backend unavailable", reason="connection refused")

    assert str(error) == "Backend unavailable"
    assert error.reason == "connection refused"


def test_loader_error_stores_source_reason_and_message() -> None:
    """LoaderError should make file loading failures auditable."""

    source = Path("manuals/pump.pdf")
    error = LoaderError(source=source, reason="unsupported file type")

    assert error.source == source
    assert error.reason == "unsupported file type"
    assert str(error) == f"Failed to load '{source}': unsupported file type"
