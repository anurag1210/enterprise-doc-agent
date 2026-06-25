from src.config import COLLECTION_NAME
from src.retrieval.vector_store import get_vector_store
from src.ingestion.loader import load_all_documents
from src.ingestion.chunker import chunk_documents


def embed_and_store_chunks(chunks):
    """Take the chunks and embed and store into the vector database."""
    if not chunks:
        print("No chunks provided")
        return
    
    vector_store = get_vector_store()
    vector_store.add_documents(documents=chunks)
    print(f"Successfully stored {len(chunks)} chunks in {COLLECTION_NAME}.")



if __name__ == "__main__":
    
    print("Loading documents...")
    docs = load_all_documents()
    
    print("Chunking documents...")
    chunks = chunk_documents(docs)
    
    print("Embedding and storing...")
    embed_and_store_chunks(chunks)