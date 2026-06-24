from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.config import CHUNK_SIZE, CHUNK_OVERLAP
from src.ingestion.loader import load_all_documents


def chunk_documents(documents: list[Document]) -> list[Document]:
    """
    Split documents into smaller chunks for embedding.
    
    Args:
        documents: List of Document objects (typically full pages)
        
    Returns:
        List of Document objects, where each Document now represents
        a chunk of text rather than a full page. The metadata is preserved
        and enhanced with a 'chunk_id' field.
        
    Note:
        Even though the output is called 'chunks', they are still Document
        objects from langchain_core. The difference is their size.
    """

    #RecursiveCharacter derived from the TextSplitter Base Class from Langchain
    text_splitters=RecursiveCharacterTextSplitter(
          chunk_size=CHUNK_SIZE,
          chunk_overlap=CHUNK_OVERLAP,
          length_function=len,
          separators=["\n\n", "\r\n\r\n", "\n", "\r\n",
            ". ", ".\n", "? ", "?\n", "! ", "!\n",
            "; ", ": ", ", ", " ", ""]
    )

    #Creating the chunks

    chunks=text_splitters.split_documents(documents)


    #Enumerate to get the index and the element from the loop
    for i ,chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i

    print(f"Split {len(documents)} pages into {len(chunks)} chunks")
    print(f"Chunk size: {CHUNK_SIZE}, Overlap: {CHUNK_OVERLAP}")

    return chunks


if __name__=="__main__":

    docs = load_all_documents()
    chunks = chunk_documents(docs) 

    print(f"\nChunk 0 preview:")
    print(f"Metadata: {chunks[0].metadata}")
    print(f"Content: {chunks[0].page_content[:300]}...")
    print(f"\nChunk 1 preview:")
    print(f"Content: {chunks[1].page_content[:300]}...")



