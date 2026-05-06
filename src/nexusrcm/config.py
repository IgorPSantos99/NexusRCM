"""Runtime configuration for NexusRCM.

Settings centralize environment-driven values used by infrastructure
components. This keeps operational limits visible and validated before they
affect ingestion behavior.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_PDF_CHUNK_SIZE_TOKENS = 512
DEFAULT_PDF_CHUNK_OVERLAP_TOKENS = 64
DEFAULT_PDF_MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024
DEFAULT_PDF_MIN_TEXT_CHARS_PER_PAGE = 10

__all__ = [
    "DEFAULT_PDF_CHUNK_OVERLAP_TOKENS",
    "DEFAULT_PDF_CHUNK_SIZE_TOKENS",
    "DEFAULT_PDF_MAX_FILE_SIZE_BYTES",
    "DEFAULT_PDF_MIN_TEXT_CHARS_PER_PAGE",
    "Settings",
    "get_settings",
]


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Environment variables use the ``NEXUSRCM_`` prefix. For example,
    ``NEXUSRCM_PDF_CHUNK_SIZE_TOKENS=256`` overrides the PDF chunk size.
    """

    model_config = SettingsConfigDict(env_prefix="NEXUSRCM_", env_file=".env")

    pdf_chunk_size_tokens: int = Field(default=DEFAULT_PDF_CHUNK_SIZE_TOKENS, gt=0)
    pdf_chunk_overlap_tokens: int = Field(
        default=DEFAULT_PDF_CHUNK_OVERLAP_TOKENS,
        ge=0,
    )
    pdf_max_file_size_bytes: int = Field(
        default=DEFAULT_PDF_MAX_FILE_SIZE_BYTES,
        gt=0,
    )
    pdf_min_text_chars_per_page: int = Field(
        default=DEFAULT_PDF_MIN_TEXT_CHARS_PER_PAGE,
        ge=0,
    )

    @field_validator("pdf_chunk_overlap_tokens")
    @classmethod
    def overlap_must_be_smaller_than_chunk_size(
        cls,
        value: int,
        info: ValidationInfo,
    ) -> int:
        """Reject chunk overlap values that cannot make forward progress."""

        chunk_size = info.data.get("pdf_chunk_size_tokens")
        if isinstance(chunk_size, int) and value >= chunk_size:
            msg = "pdf_chunk_overlap_tokens must be smaller than pdf_chunk_size_tokens"
            raise ValueError(msg)
        return value


@lru_cache
def get_settings() -> Settings:
    """Return cached runtime settings."""

    return Settings()
