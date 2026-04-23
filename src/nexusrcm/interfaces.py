"""Central module contracts for NexusRCM.

This module defines the stable interfaces between the major layers of the
system. Concrete implementations may change over time, but downstream code
should depend only on these contracts.
"""

# QUESTION: Why we use __future__ imports in this module?
from __future__ import annotations

# QUESTION: How is the importance of every import below?
from pathlib import Path
from typing import Any, Protocol, TypedDict, runtime_checkable


class SourceRef(TypedDict):
    """Traceable reference to the original evidence source."""

    filename: str
    page: int | None
    chunk_index: int | None
# QUESTION: What is "chunk_index" used for in SourceRef?

class DocumentChunk(TypedDict):
    """Normalized text unit produced by ingestion."""

    chunk_id: str
    text: str
    source_ref: SourceRef
    metadata: dict[str, Any]
"""
QUESTION: "chunk_id" here, is the same as the "chunk_index" in SourceRef? 
if not what is the difference between them?
"""



class ExtractionResult(TypedDict):
    """Structured failure knowledge extracted from a document chunk."""

    equipment: list[str]
    symptoms: list[str]
    failure_modes: list[str]
    root_causes: list[str]
    corrective_actions: list[str]
    source_ref: SourceRef
    metadata: dict[str, Any]
"""
QUESTION: for this archive is a interface package, 
we should define only generic formats for the extractions results?
"""

# TODO: Search more to understand how this Graphs Classes are used in projects.
class GraphNode(TypedDict):
    """Graph node returned by graph store implementations."""

    node_id: str
    node_type: str
    attributes: dict[str, Any]


class GraphEdge(TypedDict):
    """Graph edge metadata returned by graph store implementations."""

    source: str
    target: str
    relationship_type: str
    attributes: dict[str, Any]


class RetrievalResult(TypedDict):
    """Ranked retrieval result used by hybrid search and agent layers."""

    result_id: str
    content: str
    score: float
    source_ref: SourceRef
    metadata: dict[str, Any]


class DiagnosticResponse(TypedDict):
    """Auditable response returned by the diagnostic agent."""

    failure_modes_identified: list[str]
    most_probable_root_cause: str
    confidence: float
    evidence: list[dict[str, Any]]
    recommended_actions: list[str]
    related_equipment: list[str]
    graph_path: str


@runtime_checkable
class BaseLoader(Protocol):
    """Contract for document ingestion components."""

    def load(self, source: Path) -> list[DocumentChunk]:
        """Load a source file into normalized document chunks."""


@runtime_checkable
class BaseExtractor(Protocol):
    """Contract for NLP extraction components."""

    def extract(self, chunk: DocumentChunk) -> ExtractionResult:
        """Extract structured failure knowledge from a document chunk."""


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

    def add_edge(
        self,
        source: str,
        target: str,
        relationship_type: str,
        attributes: dict[str, Any],
    ) -> None:
        """Insert or update a graph edge."""

    def get_neighbors(
        self,
        node_id: str,
        relationship_type: str | None = None,
    ) -> list[GraphNode]:
        """Return neighboring nodes for a given node."""

    def query_path(
        self,
        start_node: str,
        end_node: str,
        max_depth: int = 3,
    ) -> list[list[str]]:
        """Return matching graph paths between two nodes."""


@runtime_checkable
class BaseRetriever(Protocol):
    """Contract for retrieval strategies over text, graph, or both."""

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        """Return ranked evidence relevant to the user query."""


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

    def query(
        self,
        embedding: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Search similar vectors using an embedding query."""

    def delete(self, ids: list[str]) -> None:
        """Delete embeddings by identifier."""


@runtime_checkable
class DiagnosticAgent(Protocol):
    """Contract for the orchestration layer that answers user questions."""

    def answer(self, question: str, top_k: int = 5) -> DiagnosticResponse:
        """Generate an auditable diagnostic response for a user question."""


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
    "GraphStore",
    "RetrievalResult",
    "SourceRef",
]
