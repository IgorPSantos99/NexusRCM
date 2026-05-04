"""Domain exceptions for NexusRCM operational failures."""

from __future__ import annotations

from pathlib import Path

__all__ = [
    "NexusRCMError",
    "IngestionError",
    "DiagnosticError",
    "LoaderError",
    "ExtractionError",
    "GraphStoreError",
    "RetrievalError",
    "VectorStoreError",
]


class NexusRCMError(Exception):
    """Base exception class for all domain failures."""

    def __init__(self, message: str, *, reason: str | None = None) -> None:
        super().__init__(message)
        self.reason = reason


class IngestionError(NexusRCMError):
    """Base exception for ingestion pipeline failures."""


class DiagnosticError(NexusRCMError):
    """Base exception for diagnostic failures."""


class LoaderError(IngestionError):
    """Raised when a source file cannot be loaded."""

    def __init__(self, source: Path, reason: str) -> None:
        self.source = source
        super().__init__(f"Failed to load '{source}': {reason}", reason=reason)


class ExtractionError(NexusRCMError):
    """Raised when NLP extraction fails irrecoverably."""


class GraphStoreError(NexusRCMError):
    """Raised when graph store operations fail."""


class RetrievalError(DiagnosticError):
    """Raised when retrieval cannot find relevant evidence."""


class VectorStoreError(NexusRCMError):
    """Raised when vector store operations fail."""
