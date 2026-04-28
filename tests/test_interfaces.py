"""Tests for the central NexusRCM module contracts."""

from __future__ import annotations

from pathlib import Path

from nexusrcm.interfaces import (
    BaseExtractor,
    BaseLoader,
    BaseRetriever,
    BaseVectorStore,
    DiagnosticAgent,
    DiagnosticResponse,
    DocumentChunk,
    ExtractionResult,
    GraphNode,
    GraphStore,
    RetrievalResult,
    SourceRef,
)


def build_source_ref() -> SourceRef:
    """Create a reusable source reference fixture."""

    return {
        "filename": "manual.pdf",
        "page": 1,
        "chunk_index": 0,
    }


class DummyLoader:
    """Minimal loader implementation for protocol validation."""

    def load(self, source: Path) -> list[DocumentChunk]:
        return [
            {
                "chunk_id": source.stem,
                "text": "bearing wear detected",
                "source_ref": build_source_ref(),
                "metadata": {"loader": "dummy"},
            }
        ]


class DummyExtractor:
    """Minimal extractor implementation for protocol validation."""

    def extract(self, chunk: DocumentChunk) -> ExtractionResult:
        return {
            "equipment": ["pump"],
            "symptoms": ["vibration"],
            "failure_modes": ["bearing wear"],
            "root_causes": ["poor lubrication"],
            "corrective_actions": ["inspect bearing housing"],
            "source_ref": chunk["source_ref"],
            "metadata": {"extractor": "dummy"},
        }


class DummyGraphStore:
    """Minimal graph store implementation for protocol validation."""

    def add_node(
        self,
        node_type: str,
        node_id: str,
        attributes: dict[str, object],
    ) -> None:
        self._last_node = (node_type, node_id, attributes)

    def add_edge(
        self,
        source: str,
        target: str,
        relationship_type: str,
        attributes: dict[str, object],
    ) -> None:
        self._last_edge = (source, target, relationship_type, attributes)

    def get_neighbors(
        self,
        node_id: str,
        relationship_type: str | None = None,
    ) -> list[GraphNode]:
        return [
            {
                "node_id": node_id,
                "node_type": relationship_type or "Symptom",
                "attributes": {"weight": 1.0},
            }
        ]

    def query_path(
        self,
        start_node: str,
        end_node: str,
        max_depth: int = 3,
    ) -> list[list[str]]:
        return [[start_node, "bearing_wear", end_node][: max_depth + 1]]


class DummyRetriever:
    """Minimal retriever implementation for protocol validation."""

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        return [
            {
                "result_id": f"result-{top_k}",
                "content": query,
                "score": 0.9,
                "source_ref": build_source_ref(),
                "metadata": {"strategy": "dummy"},
            }
        ]


class DummyVectorStore:
    """Minimal vector store implementation for protocol validation."""

    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, object]],
    ) -> None:
        self._items = list(zip(ids, embeddings, metadatas, strict=False))

    def query(
        self,
        embedding: list[float],
        top_k: int,
        filters: dict[str, object] | None = None,
    ) -> list[RetrievalResult]:
        return [
            {
                "result_id": "vector-1",
                "content": str(embedding),
                "score": 0.8,
                "source_ref": build_source_ref(),
                "metadata": filters or {},
            }
        ]

    def delete(self, ids: list[str]) -> None:
        self._deleted = ids


class DummyDiagnosticAgent:
    """Minimal agent implementation for protocol validation."""

    def answer(self, question: str, top_k: int = 5) -> DiagnosticResponse:
        return {
            "failure_modes_identified": ["bearing wear"],
            "most_probable_root_cause": question,
            "confidence": 0.91,
            "evidence": [{"source": "manual.pdf", "relevance": "high"}],
            "recommended_actions": ["inspect bearing housing"],
            "related_equipment": ["P-101A"],
            "graph_path": f"symptom -> failure_mode -> cause ({top_k})",
        }


class IncompleteLoader:
    """Implementation missing the required loader contract."""

    def read(self, source: Path) -> list[DocumentChunk]:
        return []


def test_loader_contract_is_runtime_checkable() -> None:
    """A loader implementation should satisfy the BaseLoader protocol."""

    assert isinstance(DummyLoader(), BaseLoader)


def test_extractor_contract_is_runtime_checkable() -> None:
    """An extractor implementation should satisfy the BaseExtractor protocol."""

    assert isinstance(DummyExtractor(), BaseExtractor)


def test_graph_store_contract_is_runtime_checkable() -> None:
    """A graph backend should satisfy the GraphStore protocol."""

    assert isinstance(DummyGraphStore(), GraphStore)


def test_retriever_contract_is_runtime_checkable() -> None:
    """A retrieval strategy should satisfy the BaseRetriever protocol."""

    assert isinstance(DummyRetriever(), BaseRetriever)


def test_vector_store_contract_is_runtime_checkable() -> None:
    """A vector backend should satisfy the BaseVectorStore protocol."""

    assert isinstance(DummyVectorStore(), BaseVectorStore)


def test_agent_contract_is_runtime_checkable() -> None:
    """An orchestration layer should satisfy the DiagnosticAgent protocol."""

    assert isinstance(DummyDiagnosticAgent(), DiagnosticAgent)


def test_incomplete_loader_does_not_satisfy_protocol() -> None:
    """A loader without the expected method should fail the contract."""

    assert not isinstance(IncompleteLoader(), BaseLoader)
