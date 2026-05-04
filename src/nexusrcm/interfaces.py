"""Central module contracts for NexusRCM.

This module defines the stable interfaces between the major layers of the
system. Concrete implementations may change over time, but downstream code
should depend only on these contracts.
"""

from __future__ import annotations

from collections.abc import Iterator
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar, Protocol, runtime_checkable
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from nexusrcm.exceptions import (
    ExtractionError,
    GraphStoreError,
    LoaderError,
    RetrievalError,
    VectorStoreError,
)

__contract_version__ = "0.1.0"


class SourceRef(BaseModel):
    """Traceable reference to the original evidence source."""

    filename: str
    page: int | None = Field(default=None, ge=1)
    chunk_index: int | None = Field(default=None, ge=0)


class DocumentChunk(BaseModel):
    """Normalized text unit produced by ingestion."""

    chunk_id: str = Field(default_factory=lambda: str(uuid4()))
    text: str = Field(min_length=1)
    source_ref: SourceRef
    metadata: dict[str, Any]

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        """Reject chunks without extractable text content."""
        if not value.strip():
            msg = "text must not be empty or whitespace"
            raise ValueError(msg)
        return value


class ExtractionResult(BaseModel):
    """Structured failure knowledge extracted from a document chunk."""

    equipment: list[str] = Field(default_factory=list)
    symptoms: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    root_causes: list[str] = Field(default_factory=list)
    corrective_actions: list[str] = Field(default_factory=list)
    source_ref: SourceRef
    metadata: dict[str, Any]


class GraphNode(BaseModel):
    """Graph node returned by graph store implementations."""

    node_id: str
    node_type: str
    attributes: dict[str, Any]


class GraphEdge(BaseModel):
    """Graph edge metadata returned by graph store implementations."""

    source: str
    target: str
    relationship_type: str
    attributes: dict[str, Any]


class GraphPath(BaseModel):
    """Structured graph path returned by graph traversal operations."""

    nodes: list[str]
    edges: list[GraphEdge]
    total_depth: int = Field(ge=0)


class RetrievalStrategy(StrEnum):
    """Retrieval strategy used to produce ranked evidence."""

    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    HYBRID = "hybrid"


class EvidenceRelevance(StrEnum):
    """Calibrated relevance label for diagnostic evidence."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvidenceRef(BaseModel):
    """Auditable reference to evidence used in a diagnostic response."""

    source: str = Field(min_length=1)
    relevance: EvidenceRelevance
    source_ref: SourceRef | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source")
    @classmethod
    def source_must_not_be_blank(cls, value: str) -> str:
        """Reject evidence that cannot be traced to a readable source."""
        if not value.strip():
            msg = "source must not be empty or whitespace"
            raise ValueError(msg)
        return value


class RetrievalResult(BaseModel):
    """Ranked retrieval result used by hybrid search and agent layers."""

    result_id: str
    content: str
    score: float
    source_ref: SourceRef
    metadata: dict[str, Any]
    strategy: RetrievalStrategy
    graph_path: GraphPath | None = None


class UsageMetrics(BaseModel):
    """Optional telemetry captured while producing a diagnostic response."""

    token_count: int | None = Field(default=None, ge=0)
    latency_ms: float | None = Field(default=None, ge=0.0)


class DiagnosticResponse(BaseModel):
    """Auditable response returned by the diagnostic agent."""

    failure_modes_identified: list[str]
    most_probable_root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[EvidenceRef]
    recommended_actions: list[str]
    related_equipment: list[str]
    graph_path: str
    usage_metrics: UsageMetrics | None = None

    @field_validator("failure_modes_identified", "recommended_actions")
    @classmethod
    def lists_must_not_be_empty(cls, value: list[str]) -> list[str]:
        """Reject diagnostic responses without findings or actions."""
        if not value:
            msg = "list must not be empty"
            raise ValueError(msg)
        return value


@runtime_checkable
class BaseLoader(Protocol):
    """Contract for document ingestion components.

    Loader implementations declare their accepted file extensions and maximum
    file size so orchestration code can validate inputs before doing expensive
    parsing work.
    """

    supported_extensions: ClassVar[frozenset[str]]
    max_file_size_bytes: ClassVar[int]

    def load(self, source: Path) -> Iterator[DocumentChunk]:
        """Load a source file into normalized document chunks.

        Returns an empty iterator when the source is valid but has no
        extractable text.

        Args:
            source: Path to the source document.

        Returns:
            Iterator of normalized document chunks with source metadata.

        Raises:
            LoaderError: If the source is missing, corrupted, unsupported, or
                cannot be parsed safely.
        """
        ...


@runtime_checkable
class BaseExtractor(Protocol):
    """Contract for NLP extraction components."""

    def extract(self, chunk: DocumentChunk) -> ExtractionResult:
        """Extract structured failure knowledge from a document chunk.

        Low-quality input, such as vague text or text without recognizable
        reliability entities, returns a valid ExtractionResult with empty lists.
        That absence of entities is normal data, not an exception.

        Repeated calls with the same chunk should be idempotent: they should
        produce equivalent extraction results when the extractor configuration
        and model versions are unchanged.

        Args:
            chunk: Normalized document chunk to analyze.

        Returns:
            Structured extraction result. The entity lists may be empty.

        Raises:
            ExtractionError: If extraction fails irrecoverably, for example
                because a model cannot be loaded or inference runs out of
                memory.
        """
        ...


@runtime_checkable
class GraphStore(Protocol):
    """Contract for graph persistence and traversal backends."""

    async def upsert_node(
        self,
        node_type: str,
        node_id: str,
        attributes: dict[str, Any],
    ) -> None:
        """Create or update a graph node using idempotent node_id semantics."""
        ...

    async def add_edge(
        self,
        source: str,
        target: str,
        relationship_type: str,
        attributes: dict[str, Any],
    ) -> None:
        """Insert or update a graph edge."""
        ...

    async def has_node(self, node_id: str) -> bool:
        """Return whether a node exists in the graph backend."""
        ...

    async def remove_node(self, node_id: str) -> None:
        """Remove a graph node and all connected edges as the node deletion API."""
        ...

    async def remove_edge(
        self,
        source: str,
        target: str,
        relationship_type: str,
    ) -> None:
        """Remove one relationship between two graph nodes."""
        ...

    async def get_neighbors(
        self,
        node_id: str,
        relationship_type: str | None = None,
    ) -> list[GraphNode]:
        """Return neighboring nodes for a given node."""
        ...

    async def query_path(
        self,
        start_node: str,
        end_node: str,
        max_depth: int = 3,
    ) -> list[GraphPath]:
        """Return matching graph paths between two nodes."""
        ...


@runtime_checkable
class BaseRetriever(Protocol):
    """Contract for retrieval strategies over text, graph, or both."""

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        """Return ranked evidence relevant to the user query."""
        ...


@runtime_checkable
class BaseVectorStore(Protocol):
    """Contract for pluggable vector database backends."""

    async def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Persist embeddings and their metadata using upsert semantics.

        If an id already exists, its embedding and metadata are overwritten.

        Raises:
            VectorStoreError: If ids, embeddings, and metadatas do not have
                matching lengths, or if the backend rejects the write.
        """
        ...

    async def query(
        self,
        embedding: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Search similar vectors using an embedding query.

        Results are returned ordered by score descending. The backend may
        return fewer than top_k results when the collection has fewer matching
        records than requested.
        """
        ...

    async def delete(self, ids: list[str]) -> None:
        """Delete embeddings by identifier."""
        ...


@runtime_checkable
class DiagnosticAgent(Protocol):
    """Contract for the orchestration layer that answers user questions."""

    async def answer(self, question: str, top_k: int = 5) -> DiagnosticResponse:
        """Generate an auditable diagnostic response for a user question.

        Args:
            question: Natural-language diagnostic question.
            top_k: Maximum number of retrieval results to use as evidence.

        Returns:
            Structured diagnostic response with evidence and recommended
            actions.

        Raises:
            RetrievalError: If retrieval completes but finds no relevant
                evidence for the question.
            ExtractionError: If the LLM fails to produce valid structured output
                after retries.
        """
        ...


__all__ = [
    "__contract_version__",
    "BaseExtractor",
    "BaseLoader",
    "BaseRetriever",
    "BaseVectorStore",
    "DiagnosticAgent",
    "DiagnosticResponse",
    "DocumentChunk",
    "EvidenceRef",
    "EvidenceRelevance",
    "ExtractionError",
    "ExtractionResult",
    "GraphEdge",
    "GraphNode",
    "GraphPath",
    "GraphStore",
    "GraphStoreError",
    "LoaderError",
    "RetrievalError",
    "RetrievalResult",
    "RetrievalStrategy",
    "SourceRef",
    "UsageMetrics",
    "VectorStoreError",
]
