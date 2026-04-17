# NexusRCM — Industrial Failure Knowledge Engine

## Project Summary

NexusRCM is an end-to-end knowledge engineering system for industrial reliability. It ingests heterogeneous maintenance documentation (technical manuals, work orders, inspection reports, RCA documents), extracts structured failure knowledge via NLP, builds a domain-specific knowledge graph, and exposes a GraphRAG query interface that answers diagnostic questions in auditable, structured JSON. The system is datasource-agnostic by design and deployable via Docker Compose.

---

## Problem Statement

Industrial failure knowledge exists in three disconnected silos:
1. **Technical documentation** — OEM manuals, FMEAs, maintenance procedures (PDFs, Word)
2. **Operational history** — SAP PM work orders, inspection records, failure reports (CSV, structured data)
3. **Tacit knowledge** — expertise held by senior technicians, never formally captured

When a reliability engineer or field technician faces an uncommon failure, they spend hours querying these silos manually or make decisions with incomplete information. The knowledge evaporates when senior technicians retire. NexusRCM solves this by consolidating all three sources into a queryable, structured knowledge graph with semantic search.

**Target users:** Reliability engineers, maintenance planners, field technicians, plant managers.
**Target companies:** TRACTIAN, ThermoFisher Scientific, industrial startups, SIs/consultancies.

---

## Core Capabilities

- Ingest PDFs (OEM manuals, RCA reports), CSVs (work orders), and plain text (inspection notes)
- Extract failure entities via NLP: equipment, symptom, failure mode, root cause, corrective action
- Populate a domain-specific knowledge graph with reliability ontology
- Perform hybrid retrieval: semantic search (Vector DB) + structural traversal (Graph DB)
- Return auditable, structured diagnostic responses with traceable evidence sources
- Expose REST API endpoints for ingestion and query

---

## Domain Ontology

The knowledge graph uses a reliability-specific schema:

**Node types:**
- `Equipment` — asset identifier, type, manufacturer, criticality
- `FailureMode` — ISO 14224 / OREDA-aligned mode labels
- `Symptom` — observable indicators (vibration, temperature, noise, pressure drop)
- `RootCause` — underlying physical or process cause
- `CorrectiveAction` — recommended intervention
- `CriticalComponent` — subcomponent associated with the failure path

**Relationship types:**
- `(Equipment)-[EXHIBITS]->(Symptom)`
- `(Symptom)-[INDICATES]->(FailureMode)`
- `(FailureMode)-[HAS_ROOT_CAUSE]->(RootCause)`
- `(RootCause)-[RESOLVED_BY]->(CorrectiveAction)`
- `(FailureMode)-[AFFECTS]->(CriticalComponent)`
- `(Equipment)-[SIMILAR_TO]->(Equipment)`

**Example graph query:**
> "All failure modes linked to axial vibration symptoms in centrifugal compressors operating above 80% load, ordered by occurrence frequency."

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        INGESTION LAYER                      │
│  PDF (PyMuPDF/Docling) │ CSV (Pandas) │ Plain Text          │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                        NLP PIPELINE                         │
│  NER (HuggingFace) → Zero-Shot Classification → JSON output │
│  Schema: {equipment, symptoms, failure_mode,                │
│           root_cause, corrective_action, source_ref}        │
└────────────────┬────────────────────────────────────────────┘
                 │
       ┌─────────┴─────────┐
       │                   │
┌──────▼──────┐    ┌───────▼───────┐
│  VECTOR DB  │    │  GRAPH DB     │
│  ChromaDB / │    │  NetworkX →   │
│  Qdrant     │    │  Neo4j        │
│             │    │               │
│  Semantic   │    │  Structural   │
│  search     │    │  traversal    │
│  (chunks)   │    │  (relations)  │
└──────┬──────┘    └───────┬───────┘
       │                   │
       └─────────┬─────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                     GraphRAG AGENT                          │
│  LlamaIndex orchestration                                   │
│  Query routing: semantic | structural | hybrid              │
│  Structured output enforced via JSON Schema                 │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                      FASTAPI LAYER                          │
│  POST /ingest  │  POST /query                               │
│  Swagger docs auto-generated                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Query Response Schema

All diagnostic responses follow a strict JSON schema for auditability:

```json
{
  "failure_modes_identified": ["bearing wear", "misalignment"],
  "most_probable_root_cause": "inadequate lubrication interval under high ambient temperature",
  "confidence": 0.87,
  "evidence": [
    {"source": "SKF Bearing Manual p.34", "relevance": "high"},
    {"source": "Work Order #4521", "relevance": "medium"}
  ],
  "recommended_actions": [
    "Reduce lubrication interval from 720h to 480h in summer months",
    "Inspect bearing housing for thermal deformation"
  ],
  "related_equipment": ["P-101A", "P-101B"],
  "graph_path": "axial_vibration → bearing_wear → inadequate_lubrication → lubrication_interval_adjustment"
}
```

This schema is auditable and traceable — every recommendation links to a source document or work order entry.

---

## Data Sources Strategy

The system is designed to work without proprietary data. Public sources used for development and demonstration:

| Source | Type | Content |
|---|---|---|
| SKF, Emerson, Siemens OEM manuals | PDF | Troubleshooting guides, failure descriptions |
| NASA Reliability reports | PDF | RCA case studies, failure event databases |
| OREDA offshore database (public subset) | Structured | Failure rates, failure modes by equipment type |
| ANP accident reports (Brazil) | PDF | Public industrial incident RCAs |
| Synthetic SAP PM work orders | CSV | LLM-generated, parametrized with real failure taxonomy |

The synthetic work order generation process is documented transparently in the README as a deliberate design decision, with the generation script versioned in the repository.

---

## Technology Stack

| Layer | Technology | Role |
|---|---|---|
| Document parsing | PyMuPDF, Docling | PDF and document ingestion |
| NLP / Entity extraction | HuggingFace Transformers | NER, zero-shot classification |
| Embeddings | HuggingFace sentence-transformers | Semantic vector generation |
| Vector DB (phase 1) | ChromaDB | Local semantic search |
| Vector DB (phase 2) | Qdrant | Production-grade vector store |
| Graph DB (phase 1) | NetworkX | In-memory graph, rapid prototyping |
| Graph DB (phase 2) | Neo4j | Persistent graph, Cypher queries, Graph Data Science |
| RAG orchestration | LlamaIndex | GraphRAG pipeline, query routing, structured output |
| LLM | OpenAI API / Ollama (local) | Reasoning and structured response generation |
| API | FastAPI | REST endpoints, Swagger auto-docs |
| Testing | Pytest | TDD — unit and integration tests |
| Containerization | Docker, Docker Compose | Full stack: API + ChromaDB + Neo4j |
| CI/CD | GitHub Actions | Automated test runs on every push |

---

## Architectural Decision Records (ADRs)

All major architectural decisions are documented in `docs/adr/`:

| ADR | Decision | Rationale |
|---|---|---|
| `001-networkx-vs-neo4j.md` | Start with NetworkX, migrate to Neo4j at scale threshold | Reduce operational overhead in phase 1; define migration triggers explicitly |
| `002-llamaindex-vs-langchain.md` | LlamaIndex for RAG orchestration | Native GraphRAG support, cleaner document pipeline abstractions |
| `003-local-vs-cloud-llm.md` | Ollama for dev, OpenAI API for demo | Cost control during development; no vendor lock-in |
| `004-synthetic-data-rationale.md` | LLM-generated SAP PM records | Eliminates data privacy risk while preserving schema realism |

---

## Development Roadmap

### Month 1 — Data Ingestion and NLP Extraction

**Week 1-2: Data pipeline**
- Build PDF ingestion with PyMuPDF and Docling
- Ingest public OEM manuals and RCA reports
- Generate synthetic SAP PM work orders (Python script, versioned)
- Output: raw document corpus, ~2,000–5,000 text chunks

**Week 3-4: NLP extraction pipeline**
- HuggingFace NER for entity extraction
- Zero-shot classification for failure category labeling
- Structured JSON output per document chunk
- Pytest suite: empty text, corrupted PDF, mixed pt/en text, oversized chunks

### Month 2 — Knowledge Graph and Hybrid Search

**Week 5-6: Graph construction (NetworkX)**
- Build reliability ontology schema
- Populate graph from NLP extraction output
- Implement structural queries: failure path traversal, symptom-to-action chains, equipment clustering
- Write ADR 001

**Week 7-8: Vector DB and hybrid retrieval**
- Generate embeddings for all document chunks
- Store in ChromaDB
- Implement hybrid retrieval function: semantic score + graph path combined ranking
- Benchmark retrieval quality on 20 manually labeled test queries

### Month 3 — GraphRAG Agent, API, and Deployment

**Week 9-10: LlamaIndex GraphRAG pipeline**
- Implement query router: semantic | structural | hybrid decision logic
- Enforce structured JSON output schema via LlamaIndex output parsers
- Test with 10 realistic diagnostic queries against the full corpus

**Week 11: FastAPI layer**
- `POST /ingest` — accepts PDF, CSV, or plain text; runs full pipeline
- `POST /query` — accepts natural language question; returns structured JSON
- Error handling, input validation, Swagger documentation

**Week 12: DevOps and finalization**
- Dockerfile for API service
- `docker-compose.yml` spinning up: API, ChromaDB, Neo4j
- GitHub Actions: lint + Pytest on every push
- Architecture diagram (draw.io) in README
- README written business-first: problem statement before stack

---

## Future Extensions (Documented, Not Implemented)

These are explicitly documented as next-phase roadmap items in the repository:

| Extension | Technology | Value |
|---|---|---|
| Real-time failure event ingestion | Apache Kafka | Replaces batch ingest with streaming |
| Scheduled pipeline orchestration | Apache Airflow | DAG-based ingestion automation |
| Cloud infrastructure | Terraform + AWS S3 + SageMaker | Production deployment IaC |
| Multi-agent diagnostic reasoning | LangGraph / CrewAI / Agno | Specialized agents per retrieval strategy |
| Vibration signal layer | FFT + CWRU dataset | Physical signal integration for TRACTIAN use case |
| Model fine-tuning on failure vocabulary | LoRA / QLoRA | Domain-adapted LLM for reliability terminology |
| Tool exposure for external LLMs | MCP (Model Context Protocol) | Graph as a tool callable by any LLM agent |
| Failure severity classifier | CatBoost / Gradient Boosting | AUC/KS/Gini-evaluated severity prediction layer |
| Visual inspection ingestion | VLM (Vision Language Model) | Ingest equipment damage photos and inspection images |
| Kubernetes orchestration | Kubernetes / Kubeflow | Container scaling for production load |

---

## Portfolio Positioning

**What differentiates this project from standard ML portfolios:**

1. **GraphRAG, not plain RAG** — the combination of semantic search and structural graph traversal is rare in junior portfolios and directly addresses limitations of vector-only retrieval
2. **Domain ontology** — the reliability schema (`Equipment → Symptom → FailureMode → RootCause → CorrectiveAction`) signals genuine industrial domain knowledge, not generic AI application
3. **Auditable structured output** — every recommendation is traceable to a source document; this is a product-maturity signal most ML projects lack
4. **ADR documentation** — architectural decisions are treated as engineering artifacts, not afterthoughts
5. **Datasource-agnostic** — any company with SAP PM history and OEM manuals can immediately see themselves as a user
6. **Real problem, not a Kaggle dataset** — the problem (fragmented failure knowledge) is universally recognized by anyone who has worked in industrial maintenance

**Elevator pitch per target audience:**

- **TRACTIAN:** "When a sensor detects an anomaly, NexusRCM queries the historical failure knowledge base and returns the most probable diagnosis with documentary evidence — reducing field technician diagnostic time."
- **ThermoFisher:** "The same engine applies to lab equipment: chromatographs, spectrometers, centrifuges. The ontology changes; the architecture is identical."
- **Industrial startups / SIs:** "Every company with a SAP PM history and a pile of OEM manuals can deploy this. The cost of not having it is the knowledge that walks out the door when the senior technician retires."

---

## Repository Structure

```
nexusrcm/
├── README.md                          # Business-first description + architecture diagram
├── docker-compose.yml
├── Dockerfile
├── .github/
│   └── workflows/
│       └── ci.yml                     # GitHub Actions: lint + pytest
├── docs/
│   └── adr/
│       ├── 001-networkx-vs-neo4j.md
│       ├── 002-llamaindex-vs-langchain.md
│       ├── 003-local-vs-cloud-llm.md
│       └── 004-synthetic-data-rationale.md
├── data/
│   ├── raw/                           # Ingested documents (gitignored if large)
│   ├── processed/                     # NLP extraction output JSONs
│   └── synthetic/
│       └── generate_work_orders.py    # Synthetic SAP PM generator script
├── src/
│   ├── ingestion/
│   │   ├── pdf_loader.py
│   │   └── csv_loader.py
│   ├── nlp/
│   │   ├── entity_extractor.py        # HuggingFace NER
│   │   └── classifier.py             # Zero-shot classification
│   ├── graph/
│   │   ├── ontology.py               # Node/edge schema definitions
│   │   ├── builder.py                # Graph population from NLP output
│   │   └── queries.py                # Structural query functions
│   ├── retrieval/
│   │   ├── vector_store.py           # ChromaDB interface
│   │   ├── embeddings.py             # Embedding generation
│   │   └── hybrid_retriever.py       # GraphRAG combined retrieval
│   ├── agent/
│   │   └── diagnostic_agent.py       # LlamaIndex GraphRAG pipeline
│   └── api/
│       ├── main.py                   # FastAPI app
│       ├── routes.py                 # /ingest and /query endpoints
│       └── schemas.py                # Pydantic models
└── tests/
    ├── test_ingestion.py
    ├── test_nlp.py
    ├── test_graph.py
    ├── test_retrieval.py
    └── test_api.py
```

---

*NexusRCM — transforming fragmented industrial maintenance knowledge into queryable, auditable, structured intelligence.