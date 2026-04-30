"""Tests for the central NexusRCM module contracts."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
from nexusrcm.interfaces import (
    BaseExtractor,
    BaseLoader,
    BaseRetriever,
    BaseVectorStore,
    DiagnosticAgent,
    DiagnosticResponse,
    DocumentChunk,
    ExtractionResult,
    GraphEdge,
    GraphNode,
    GraphPath,
    GraphStore,
    RetrievalResult,
    RetrievalStrategy,
    SourceRef,
)
from pydantic import ValidationError


def build_source_ref() -> SourceRef:
    """Create a reusable source reference fixture."""

    return SourceRef(filename="manual.pdf", page=1, chunk_index=0)


class DummyLoader:
    """Minimal loader implementation for protocol validation."""

    def load(self, source: Path) -> list[DocumentChunk]:
        return [
            DocumentChunk(
                chunk_id=source.stem,
                text="bearing wear detected",
                source_ref=build_source_ref(),
                metadata={"loader": "dummy"},
            )
        ]


class DummyExtractor:
    """Minimal extractor implementation for protocol validation."""

    def extract(self, chunk: DocumentChunk) -> ExtractionResult:
        return ExtractionResult(
            equipment=["pump"],
            symptoms=["vibration"],
            failure_modes=["bearing wear"],
            root_causes=["poor lubrication"],
            corrective_actions=["inspect bearing housing"],
            source_ref=chunk.source_ref,
            metadata={"extractor": "dummy"},
        )


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
            GraphNode(
                node_id=node_id,
                node_type=relationship_type or "Symptom",
                attributes={"weight": 1.0},
            )
        ]

    def query_path(
        self,
        start_node: str,
        end_node: str,
        max_depth: int = 3,
    ) -> list[GraphPath]:
        edge = GraphEdge(
            source=start_node,
            target=end_node,
            relationship_type="related_to",
            attributes={"max_depth": max_depth},
        )
        return [
            GraphPath(
                nodes=[start_node, end_node],
                edges=[edge],
                total_depth=1,
            )
        ]


class DummyRetriever:
    """Minimal retriever implementation for protocol validation."""

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        return [
            RetrievalResult(
                result_id=f"result-{top_k}",
                content=query,
                score=0.9,
                source_ref=build_source_ref(),
                metadata={"strategy": "dummy"},
                strategy=RetrievalStrategy.SEMANTIC,
            )
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
            RetrievalResult(
                result_id="vector-1",
                content=str(embedding),
                score=0.8,
                source_ref=build_source_ref(),
                metadata=filters or {},
                strategy=RetrievalStrategy.SEMANTIC,
            )
        ]

    def delete(self, ids: list[str]) -> None:
        self._deleted = ids


class DummyDiagnosticAgent:
    """Minimal agent implementation for protocol validation."""

    def answer(self, question: str, top_k: int = 5) -> DiagnosticResponse:
        return DiagnosticResponse(
            failure_modes_identified=["bearing wear"],
            most_probable_root_cause=question,
            confidence=0.91,
            evidence=[{"source": "manual.pdf", "relevance": "high"}],
            recommended_actions=["inspect bearing housing"],
            related_equipment=["P-101A"],
            graph_path=f"symptom -> failure_mode -> cause ({top_k})",
        )


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


def test_document_chunk_generates_default_chunk_id() -> None:
    """Document chunks should get a UUID identifier when none is provided."""

    chunk = DocumentChunk(
        text="bearing wear detected",
        source_ref=build_source_ref(),
        metadata={"loader": "dummy"},
    )

    assert UUID(chunk.chunk_id)


def test_document_chunk_rejects_blank_text() -> None:
    """Document chunks should reject empty or whitespace-only text."""

    with pytest.raises(ValidationError):
        DocumentChunk(
            text="   ",
            source_ref=build_source_ref(),
            metadata={"loader": "dummy"},
        )


def test_extraction_result_defaults_to_empty_lists() -> None:
    """An empty extraction result should be valid and use independent lists."""

    result = ExtractionResult(source_ref=build_source_ref(), metadata={})
    other_result = ExtractionResult(source_ref=build_source_ref(), metadata={})

    assert result.equipment == []
    assert result.symptoms == []
    assert result.failure_modes == []
    assert result.root_causes == []
    assert result.corrective_actions == []

    result.equipment.append("pump")

    assert other_result.equipment == []


def test_retrieval_strategy_values_are_json_friendly() -> None:
    """RetrievalStrategy should expose stable string values."""

    assert RetrievalStrategy.SEMANTIC.value == "semantic"
    assert RetrievalStrategy.STRUCTURAL.value == "structural"
    assert RetrievalStrategy.HYBRID.value == "hybrid"


def test_graph_path_preserves_nodes_edges_and_depth() -> None:
    """GraphPath should represent a structured traversal result."""

    edge = GraphEdge(
        source="symptom:vibration",
        target="failure_mode:bearing_wear",
        relationship_type="indicates",
        attributes={"weight": 0.9},
    )
    path = GraphPath(
        nodes=["symptom:vibration", "failure_mode:bearing_wear"],
        edges=[edge],
        total_depth=1,
    )

    assert path.nodes == ["symptom:vibration", "failure_mode:bearing_wear"]
    assert path.edges == [edge]
    assert path.total_depth == 1


def test_retrieval_result_supports_semantic_strategy_without_graph_path() -> None:
    """Semantic retrieval results should not require a graph path."""

    result = RetrievalResult(
        result_id="semantic-1",
        content="bearing wear detected",
        score=0.93,
        source_ref=build_source_ref(),
        metadata={"source": "vector"},
        strategy=RetrievalStrategy.SEMANTIC,
    )

    assert result.strategy is RetrievalStrategy.SEMANTIC
    assert result.graph_path is None
    assert result.model_dump(mode="json")["strategy"] == "semantic"


def test_retrieval_result_supports_structural_graph_path() -> None:
    """Structural retrieval results should carry the graph path when available."""

    graph_path = GraphPath(
        nodes=["symptom:vibration", "failure_mode:bearing_wear"],
        edges=[
            GraphEdge(
                source="symptom:vibration",
                target="failure_mode:bearing_wear",
                relationship_type="indicates",
                attributes={},
            )
        ],
        total_depth=1,
    )
    result = RetrievalResult(
        result_id="structural-1",
        content="vibration indicates bearing wear",
        score=0.88,
        source_ref=build_source_ref(),
        metadata={"source": "graph"},
        strategy=RetrievalStrategy.STRUCTURAL,
        graph_path=graph_path,
    )

    assert result.strategy is RetrievalStrategy.STRUCTURAL
    assert result.graph_path == graph_path


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_diagnostic_response_rejects_confidence_outside_unit_interval(
    confidence: float,
) -> None:
    """Diagnostic confidence should be constrained to the [0.0, 1.0] interval."""

    with pytest.raises(ValidationError):
        DiagnosticResponse(
            failure_modes_identified=["bearing wear"],
            most_probable_root_cause="poor lubrication",
            confidence=confidence,
            evidence=[{"source": "manual.pdf"}],
            recommended_actions=["inspect bearing housing"],
            related_equipment=["P-101A"],
            graph_path="symptom -> failure_mode -> cause",
        )


@pytest.mark.parametrize(
    ("failure_modes_identified", "recommended_actions"),
    [
        ([], ["inspect bearing housing"]),
        (["bearing wear"], []),
    ],
)
def test_diagnostic_response_rejects_empty_findings_or_actions(
    failure_modes_identified: list[str],
    recommended_actions: list[str],
) -> None:
    """Diagnostic responses should include findings and recommended actions."""

    with pytest.raises(ValidationError):
        DiagnosticResponse(
            failure_modes_identified=failure_modes_identified,
            most_probable_root_cause="poor lubrication",
            confidence=0.8,
            evidence=[{"source": "manual.pdf"}],
            recommended_actions=recommended_actions,
            related_equipment=["P-101A"],
            graph_path="symptom -> failure_mode -> cause",
        )
