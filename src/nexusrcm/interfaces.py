"""Central module contracts for NexusRCM.

This module defines the stable interfaces between the major layers of the
system. Concrete implementations may change over time, but downstream code
should depend only on these contracts.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class SourceRef(BaseModel):
    """Traceable reference to the original evidence source."""

    filename: str
    page: int | None = None
    chunk_index: int | None = None


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
    total_depth: int


class RetrievalStrategy(StrEnum):
    """Retrieval strategy used to produce ranked evidence."""

    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    HYBRID = "hybrid"


class RetrievalResult(BaseModel):
    """Ranked retrieval result used by hybrid search and agent layers."""

    result_id: str
    content: str
    score: float
    source_ref: SourceRef
    metadata: dict[str, Any]
    strategy: RetrievalStrategy
    graph_path: GraphPath | None = None


class DiagnosticResponse(BaseModel):
    """Auditable response returned by the diagnostic agent."""

    failure_modes_identified: list[str]
    most_probable_root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[dict[str, Any]]
    recommended_actions: list[str]
    related_equipment: list[str]
    graph_path: str

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
    """Contract for document ingestion components."""

    def load(self, source: Path) -> list[DocumentChunk]:
        """Load a source file into normalized document chunks."""
        ...

@runtime_checkable
class BaseExtractor(Protocol):
    """Contract for NLP extraction components."""

    def extract(self, chunk: DocumentChunk) -> ExtractionResult:
        """Extract structured failure knowledge from a document chunk."""
        ...

@runtime_checkable
class GraphStore(Protocol):
    """Contract for graph persistence and traversal backends."""

    def add_node(
        self,
        node_type: str,
        node_id: str,
        attributes: dict[str, Any],
    ) -> None:
        """Insert or update a graph node."""
        ...

    def add_edge(
        self,
        source: str,
        target: str,
        relationship_type: str,
        attributes: dict[str, Any],
    ) -> None:
        """Insert or update a graph edge."""
        ...

    def get_neighbors(
        self,
        node_id: str,
        relationship_type: str | None = None,
    ) -> list[GraphNode]:
        """Return neighboring nodes for a given node."""
        ...

    def query_path(
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

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        """Return ranked evidence relevant to the user query."""
        ...

@runtime_checkable
class BaseVectorStore(Protocol):
    """Contract for pluggable vector database backends."""

    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Persist embeddings and their metadata."""
        ...

    def query(
        self,
        embedding: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Search similar vectors using an embedding query."""
        ...

    def delete(self, ids: list[str]) -> None:
        """Delete embeddings by identifier."""
        ...

@runtime_checkable
class DiagnosticAgent(Protocol):
    """Contract for the orchestration layer that answers user questions."""

    def answer(self, question: str, top_k: int = 5) -> DiagnosticResponse:
        """Generate an auditable diagnostic response for a user question."""
        ...

__all__ = [
    "BaseExtractor",
    "BaseLoader",
    "BaseRetriever",
    "BaseVectorStore",
    "DiagnosticAgent",
    "DiagnosticResponse",
    "DocumentChunk",
    "ExtractionResult",
    "GraphEdge",
    "GraphNode",
    "GraphPath",
    "GraphStore",
    "RetrievalResult",
    "RetrievalStrategy",
    "SourceRef",
]
