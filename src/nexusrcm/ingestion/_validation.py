"""Internal file validation helpers for ingestion loaders."""

from __future__ import annotations

import stat
from os import stat_result as StatResult
from pathlib import Path

from nexusrcm.exceptions import LoaderError

__all__: list[str] = []


def _ensure_path_source(source: object) -> None:
    """Ensure the loader source is a pathlib Path instance."""

    if not isinstance(source, Path):
        raise LoaderError(Path(str(source)), "source must be a pathlib.Path")


def _validate_existing_file(source: Path) -> None:
    """Validate that source exists, is accessible, and is a regular file."""

    source_stat = _stat_source(source)
    if not stat.S_ISREG(source_stat.st_mode):
        raise LoaderError(source, "not a regular file")


def _validate_supported_extension(
    source: Path,
    supported_extensions: frozenset[str],
) -> None:
    """Validate that the source suffix is accepted by the loader."""

    extension = source.suffix
    normalized_extensions = frozenset(ext.lower() for ext in supported_extensions)
    if extension.lower() not in normalized_extensions:
        raise LoaderError(source, f"unsupported extension '{extension}'")


def _validate_file_size(source: Path, max_file_size_bytes: int) -> int:
    """Validate source size and return the actual byte size."""

    source_stat = _stat_source(source)
    file_size = source_stat.st_size
    if file_size > max_file_size_bytes:
        reason = f"file size {file_size} bytes exceeds limit {max_file_size_bytes}"
        raise LoaderError(source, reason)
    return file_size


def _stat_source(source: Path) -> StatResult:
    """Return source stat metadata, converting OS failures to LoaderError."""

    try:
        return source.stat()
    except FileNotFoundError as exc:
        raise LoaderError(source, "file not found") from exc
    except PermissionError as exc:
        raise LoaderError(source, "permission denied") from exc
    except OSError as exc:
        raise LoaderError(source, f"cannot access file: {exc}") from exc
