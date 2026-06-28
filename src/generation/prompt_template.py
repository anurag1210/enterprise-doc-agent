from src.retrieval.retriever import retrieve_vectordb


# System prompt with your specific constraints
SYSTEM_PROMPT = """You are an enterprise document assistant. Follow these rules strictly:

1. Answer ONLY from the provided context. Do not use prior knowledge.
2. Cite your sources for every claim using the format: (Source: [filename], Page: [number]).
3. If the context does not contain enough information to answer, say: "The provided documents do not contain this information."
4. Be clear, precise, and structured in your responses.
"""

def get_user_content(context, query):
    return f"""<context>
    {context}
    </context>
    <question> 
    {query} 
    </question>"""


#Function to fetch the result from the retrieval and formats it 
def formatting_retrieval(query):
     results=retrieve_vectordb(query)
     return format_context(results)


def format_context(results):
    if not results:
        return ""
    lines = []
    seen = set()
    for doc, score in results:
        source_file = doc.metadata.get("source_file") or doc.metadata.get("source") or "Unknown"
        page = doc.metadata.get("page")
        chunk_id = doc.metadata.get("chunk_id")
        dedupe_key = (source_file, page, chunk_id, doc.page_content[:200])
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        lines.append(
            f"[Source: {source_file}, Page: {page}, Score: {score:.3f}] {doc.page_content}"
        )
    return "\n\n".join(lines)


#Main Block

if __name__=="__main__":
     print("This is the code for prompt template for a chat for a financial analyst")
     query=input("Input a Financial Query: ")
     context_results=formatting_retrieval(query)
     user_content = get_user_content(context_results, query)
     print(user_content)

