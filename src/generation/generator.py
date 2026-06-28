#Adding generator part to generate the output of the RAG
from langchain_openai import ChatOpenAI
from src.config import LLM_MODEL,OPENAI_API_KEY,MAX_TOKENS,LLM_TEMPERATURE
from src.generation.prompt_template import SYSTEM_PROMPT,formatting_retrieval,get_user_content


#Function to generate the output response from the LLM
def reform_query(query: str, chat_history: list, llm) -> str:
    if not chat_history:
        return query
    
    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" 
        for m in chat_history[-4:]  # last 2 exchanges only
    )
    
    reformation_prompt = f"""Given this conversation history:
{history_text}

Rewrite this follow-up query into a fully explicit standalone question.
If it's already explicit, return it unchanged.
Return ONLY the rewritten query, nothing else.

Follow-up query: {query}"""

    result = llm.invoke([("human", reformation_prompt)])
    return result.content.strip()

def generate_response_stream(query: str, chat_history: list = None):
    if chat_history is None:
         chat_history=[]

    llm = ChatOpenAI(
        model=LLM_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=LLM_TEMPERATURE,
        max_tokens=MAX_TOKENS,
        streaming=True,
    )

    reformed_query = reform_query(query, chat_history, llm)
    context = formatting_retrieval(reformed_query)
    user_content = get_user_content(context, reformed_query)

    messages = [
        ("system", SYSTEM_PROMPT),
        ("human", user_content),
    ]

    for chunk in llm.stream(messages):
        yield chunk.content


if __name__ == "__main__":
        query = input("Input your query: ")
        for chunk in generate_response_stream(query):
            print(chunk, end="", flush=True)
        print()#Adding a new line after the responses have been derived
