#Code to Retrieve thevector DB embeddings from the user query
from src.retrieval.vector_store import get_vector_store
from src.config import TOP_K

#Method to retrieve the embeddings from the vector db

def retrieve_vectordb(user_query,filter=None):
    vector_store=get_vector_store()
    if filter:
        results = vector_store.similarity_search_with_score(user_query, k=TOP_K, filter=filter)
    else:
        results = vector_store.similarity_search_with_score(user_query, k=TOP_K)    
    
    return results


#Main Block
if __name__=="__main__":
    print('The search for the correct embedding starts here')
    user_query=input('Input the User Query :')
    results=retrieve_vectordb(user_query)

    if results:
            for res, score in results:
                print(f"Match: {res.page_content[:200]}... (Score: {score:.3f})")
    else:
                print("No matching documents found.")