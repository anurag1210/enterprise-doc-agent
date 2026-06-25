#Importing the necessary packages
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from src.config import OPENAI_API_KEY,CHROMA_PERSIST_DIR,COLLECTION_NAME,EMBEDDING_MODEL
import sys

# Optional override for macOS environments that need pysqlite3

try:
    __import__("pysqlite3")
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ModuleNotFoundError:
    pass


_vector_store = None



def get_vector_store():
    global _vector_store
    if _vector_store is None:
        print("Initializing the vector DB ")
        embedding_model=OpenAIEmbeddings(
            api_key=OPENAI_API_KEY,
            model=EMBEDDING_MODEL
        )

        _vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embedding_model,
            persist_directory=CHROMA_PERSIST_DIR
        )
    return _vector_store
    