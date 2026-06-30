import os
import sys
import tempfile
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Streamlit runs this file from the `ui/` folder, so we add the project root
# to `sys.path` before importing anything from `src/`.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.graph import app as agent_app
from src.guardrails.input_validator import quick_check, validate_file
from src.guardrails.output_validator import check_output
from src.ingestion.chunker import chunk_documents
from src.ingestion.loader import load_file
from src.retrieval.embedder import embed_and_store_chunks


SUPPORTED_TYPES = ["pdf", "txt", "csv", "xlsx", "xls", "md"]


def save_uploaded_file(uploaded_file) -> str:
    """Write the Streamlit upload object to a temporary file path."""
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        return tmp.name


def ingest_uploaded_file(uploaded_file) -> tuple[bool, str]:
    """Validate, load, chunk, and embed one uploaded document."""
    temp_path = save_uploaded_file(uploaded_file)
    try:
        # 1) Block unsupported, empty, or oversized files.
        is_valid, message = validate_file(temp_path)
        if not is_valid:
            return False, message

        # 2) Build basic metadata so citations can point back to this file.
        metadata = {
            "source_file": uploaded_file.name,
            "document_name": Path(uploaded_file.name).stem.replace("_", " ").title(),
            "file_type": Path(uploaded_file.name).suffix.lower(),
        }

        # 3) Load raw content from the file.
        documents = load_file(temp_path, metadata)
        if not documents:
            return False, "No documents could be extracted from the uploaded file."

        # 4) Split the documents into smaller chunks for retrieval.
        chunks = chunk_documents(documents)
        if not chunks:
            return False, "No chunks were created from the uploaded file."

        # 5) Embed the chunks and store them in Chroma.
        embed_and_store_chunks(chunks)
        return True, f"Ingested {uploaded_file.name} successfully."
    finally:
        # Remove the temporary file regardless of success or failure.
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def format_citations(retrieved_docs: list) -> list[dict]:
    """Turn LangChain retrieval results into a compact citation structure."""
    citations = []
    seen = set()

    for item in retrieved_docs or []:
        # Retrieval results may come back as (Document, score) tuples.
        if isinstance(item, tuple) and len(item) == 2:
            doc, score = item
        else:
            doc, score = item, None

        metadata = getattr(doc, "metadata", {}) or {}
        source_file = metadata.get("source_file") or metadata.get("source") or "Unknown"
        page = metadata.get("page")
        chunk_id = metadata.get("chunk_id")
        dedupe_key = (source_file, page, chunk_id, getattr(doc, "page_content", "")[:120])

        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        citations.append(
            {
                "source": source_file,
                "page": page,
                "chunk_id": chunk_id,
                "score": score,
                "snippet": getattr(doc, "page_content", "")[:250].strip(),
            }
        )

    return citations





def render_citations(citations: list[dict]) -> None:
    """Render a small citation list under the answer."""
    if not citations:
        st.info("No citations returned for this answer.")
        return

    st.subheader("Citations")
    for citation in citations:
        parts = [citation["source"]]
        if citation.get("page") is not None:
            parts.append(f"Page {citation['page']}")
        if citation.get("chunk_id") is not None:
            parts.append(f"Chunk {citation['chunk_id']}")
        if citation.get("score") is not None:
            parts.append(f"Score {citation['score']:.3f}")

        st.markdown(f"- **{' | '.join(parts)}**")
        if citation.get("snippet"):
            st.caption(citation["snippet"])


def answer_query(query: str) -> tuple[str, list[dict], dict]:
    """Run the agent graph and return the answer plus retrieval citations."""
    result = agent_app.invoke(
        {
            "query": query,
            "retry_count": 0,
            "needs_retry": False,
        }
    )

    answer = result.get("final_answer") or result.get("answer") or ""
    citations = format_citations(result.get("retrieved_docs", []))
    return answer, citations, result


# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Enterprise Doc Agent", layout="centered")
st.title("Enterprise Doc Agent")
st.caption("Upload a document, ask a question, and review the grounded answer with citations.")

# Keep chat history in session state so it survives Streamlit reruns.
if "messages" not in st.session_state:
    st.session_state.messages = []


# -----------------------------
# Sidebar: file upload + ingest
# -----------------------------
with st.sidebar:
    st.header("Document Upload")
    uploaded_file = st.file_uploader(
        "Upload a source document",
        type=SUPPORTED_TYPES,
        accept_multiple_files=False,
    )

    # The upload only becomes part of the knowledge base after ingestion.
    if uploaded_file and st.button("Ingest file", type="primary"):
        with st.spinner("Validating and ingesting document..."):
            ok, message = ingest_uploaded_file(uploaded_file)
        if ok:
            st.success(message)
            st.session_state.last_ingested_file = uploaded_file.name
        else:
            st.error(message)

    if st.session_state.get("last_ingested_file"):
        st.caption(f"Last ingested file: {st.session_state.last_ingested_file}")


# -----------------------------
# Main chat history
# -----------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("citations"):
            with st.expander("Citations", expanded=False):
                render_citations(message["citations"])


# -----------------------------
# Query input + guarded answer flow
# -----------------------------
query = st.chat_input("Ask a question about the uploaded or indexed documents")

if query:
    # Basic empty-input check before any guardrail or model call.
    if not query.strip():
        st.error("Please enter a question.")
        st.stop()

    # Input guardrail: blocks prompt injection-like queries early.
    ok, message = quick_check(query)
    if not ok:
        st.error(message)
        st.stop()

    # Save and display the user's message first.
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    # Call the agent graph, which handles retrieval and answer generation.
# Call the agent graph
    with st.spinner("Generating answer..."):
        answer, citations, result = answer_query(query)

    # Output guardrail
    ok, message = check_output(answer)
    if not ok:
        st.error(message)
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "Response blocked by output guardrails.",
                "citations": [],
            }
        )
        st.stop()

    # Show the final answer, citations, and agent trace
    with st.chat_message("assistant"):
        st.markdown(answer)
        with st.expander("Citations", expanded=False):
            render_citations(citations)
        with st.expander("Agent Trace", expanded=False):
            st.write(f"Retrieval score: {result.get('retrieval_score')}")
            st.write(f"Grounded: {result.get('is_grounded')}")
            st.write(f"Retries: {result.get('retry_count')}")
            if result.get("reformulated_query"):
                st.write(f"Reformulated query: {result['reformulated_query']}")

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "citations": citations,
        }
    )