# enterprise-doc-agent

An AI-powered agentic RAG system for enterprise document Q&A. Upload documents in multiple formats (PDF, TXT, CSV, Excel), ask natural language questions, and receive grounded, citation-backed answers — with an autonomous AI agent that retrieves, grades, reasons, and validates before responding.

Built as a capstone project for the Edureka Advanced Certification in Generative AI & Agentic AI Engineering.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER QUERY                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AGENT LAYER (LangGraph)                     │
│                                                                 │
│   ┌───────────┐    ┌───────────┐    ┌──────────────────┐        │
│   │ Retrieve  │───▶│   Grade   │───▶│   Reformulate    │        │
│   │   Node    │◀───│   Node    │    │   Node (retry)   │        │
│   └───────────┘    └─────┬─────┘    └──────────────────┘        │
│                          │ docs approved                        │
│                          ▼                                      │
│                    ┌───────────┐    ┌──────────────────┐        │
│                    │ Generate  │───▶│    Validate       │        │
│                    │   Node    │◀───│    Node           │        │
│                    └───────────┘    └──────────┬───────┘        │
│                                          grounded?              │
│                                               │                 │
└───────────────────────────────────────────────┼─────────────────┘
                                                ▼
                                        ┌──────────────┐
                                        │ Final Answer │
                                        │ (with cites) │
                                        └──────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION PIPELINE                          │
│                                                                 │
│   PDF ──┐                                                       │
│   TXT ──┼──▶ Loader ──▶ Chunker ──▶ Embedder ──▶ ChromaDB      │
│   CSV ──┤   (format-    (Recursive   (OpenAI      (vector       │
│   XLSX ─┘    aware)      splitting)   embed)       store)       │
│                                                                 │
│   * Tabular data (CSV/Excel) undergoes row-to-prose flattening  │
│     before chunking to preserve header context per row           │
└─────────────────────────────────────────────────────────────────┘
```

---

## What Makes This Agentic (Not Just RAG)

A standard RAG pipeline runs linearly: retrieve → generate → done. This system adds autonomous decision-making between steps:

- **Retrieval grading** — An LLM judge scores whether the retrieved documents are relevant to the query. If the score is below threshold, the agent reformulates the query and retries retrieval (up to 2 attempts).
- **Answer validation** — After generation, a separate LLM judge checks whether the answer is grounded in the retrieved context. If hallucination is detected, the agent regenerates.
- **Query reformulation** — When retrieval quality is poor, the agent autonomously rewrites the query to be more specific before retrying.

These decision points use Pydantic structured output for deterministic, typed responses from the grading and validation LLM calls.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent Orchestration | LangGraph | Stateful graph with conditional edges and retry loops |
| LLM | OpenAI GPT-4o-mini | Generation, grading, validation, query reformulation |
| Embeddings | OpenAI text-embedding-3-small | Document chunk embeddings |
| Vector Store | ChromaDB | Persistent vector storage and similarity search |
| Document Loading | pdfplumber, pandas | Multi-format ingestion (PDF, TXT, CSV, Excel) |
| Text Splitting | LangChain RecursiveCharacterTextSplitter | Chunk documents for embedding |
| Structured Output | Pydantic | Typed schemas for grading and validation LLM responses |
| Observability | LangSmith (optional) | Tracing agent runs end-to-end |
| Config Management | python-dotenv | Environment-based configuration |

---

## Project Structure

```
enterprise-doc-agent/
├── src/
│   ├── config.py                  # Central configuration (reads .env)
│   ├── ingestion/
│   │   ├── loader.py              # Multi-format document loader (PDF, TXT, CSV, Excel)
│   │   └── chunker.py             # Recursive text splitting with metadata preservation
│   ├── retrieval/
│   │   ├── vector_store.py        # ChromaDB singleton with OpenAI embeddings
│   │   ├── embedder.py            # Embed and store chunks
│   │   └── search.py              # Similarity search with score
│   ├── generation/
│   │   ├── prompt_template.py     # System prompt, context formatting, deduplication
│   │   └── generator.py           # LLM call with streaming, query reformulation
│   ├── agent/
│   │   ├── state.py               # AgentState TypedDict (shared graph state)
│   │   ├── nodes.py               # Graph nodes: retrieve, grade, reformulate, generate, validate
│   │   └── graph.py               # LangGraph StateGraph with conditional edges
│   ├── guardrails/                # Input validation and output safety controls
│   ├── evaluation/                # RAG evaluation metrics and results
│   └── api/                       # FastAPI endpoints
├── ui/                            # Streamlit front-end
├── data/
│   └── raw/                       # Upload enterprise documents here
├── docs/                          # Architecture documentation
├── evaluation_results/            # Evaluation run outputs
├── tests/                         # Unit and integration tests
├── .env.example                   # Required environment variables template
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.11+
- OpenAI API key

### Installation

```bash
git clone https://github.com/anurag1210/enterprise-doc-agent.git
cd enterprise-doc-agent

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

Required variables:
```
OPENAI_API_KEY=sk-proj-your-key-here
```

See `.env.example` for the full list of configurable parameters (chunk size, model selection, retrieval top-k, etc).

### Add Documents

Place your enterprise documents in `data/raw/`:
```bash
cp your-documents.pdf data/raw/
cp your-data.csv data/raw/
```

Supported formats: `.pdf`, `.txt`, `.md`, `.csv`, `.xlsx`, `.xls`

---

## Usage

### Test Individual Modules

```bash
# Test document loading
python -m src.ingestion.loader

# Test chunking
python -m src.ingestion.chunker

# Test embedding and storage
python -m src.retrieval.embedder

# Test retrieval search
python -m src.retrieval.search

# Test generation (standard RAG)
python -m src.generation.generator
```

### Run the Agentic RAG Pipeline

```bash
python -m src.agent.graph
```

This runs the full agent loop: retrieve → grade → (retry if needed) → generate → validate → final answer.

---

## Agentic RAG vs Standard RAG

| Aspect | Standard RAG | This System (Agentic RAG) |
|--------|-------------|--------------------------|
| Retrieval | Always runs once | Grades relevance; retries with reformulated query if poor |
| Generation | Always runs on whatever was retrieved | Only runs after retrieval is approved |
| Validation | None | LLM judge checks grounding; regenerates if hallucinated |
| Control flow | Linear pipeline | Conditional graph with loops and branching |
| Failure handling | Silent — bad retrieval produces bad answer | Explicit — agent detects and self-corrects |

---

## Design Decisions

**Why pdfplumber over PyPDFLoader?**
PyPDFLoader produced character corruption on certain PDFs. pdfplumber extracts text with higher fidelity — an autonomous decision validated through testing.

**Why row-to-prose flattening for tabular data?**
Naive chunking of CSV/Excel loses header context — row data gets separated from column names. Flattening each row into a labelled string (e.g. "Company: Apple | Revenue: 94.8B | Quarter: Q3") ensures every chunk is self-contained.

**Why LangGraph over CrewAI?**
This is a single-agent system with conditional routing, not a multi-agent delegation problem. LangGraph's StateGraph with conditional edges is the right abstraction. CrewAI adds unnecessary complexity for this use case.

**Why structured output (Pydantic) for grading/validation?**
Grading and validation require deterministic, typed responses (a float score, a boolean). Free-text LLM responses would need fragile parsing. Pydantic structured output guarantees the schema.

---

## Limitations

- **Single-user, local deployment** — no authentication, session management, or multi-tenancy
- **Tabular queries** — row-to-prose flattening works well for lookup queries but poorly for aggregate questions ("total revenue across all companies") since individual rows embed independently
- **No transitive dependency on document updates** — if a source document changes, the vector store must be manually re-indexed
- **Grading is binary** — documents are scored 1.0 (relevant) or 0.0 (irrelevant); partial relevance is not captured
- **Context window** — very large documents with many chunks may exceed the model's context window when formatted

---

## Future Improvements

- Hybrid search (BM25 + semantic) for improved retrieval precision
- RAGAS evaluation framework for systematic pipeline benchmarking
- Semantic caching for repeated or similar queries
- MCP server exposing the agent as a tool for external integrations
- GraphRAG for multi-hop reasoning over entity relationships
- Re-ranking with cross-encoder models before generation

---

## Licence

MIT