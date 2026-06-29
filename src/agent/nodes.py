#Nodes.py file for the brain and muscles for the AI Agent to act on the current state of the states.py

# nodes.py
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage,SystemMessage
from src.retrieval.search import retrieve_vectordb
from src.generation.prompt_templates import format_context
from pydantic import BaseModel,Field
from src.config import LLM_MODEL, OPENAI_API_KEY
from src.generation.prompt_template import SYSTEM_PROMPT

llm = ChatOpenAI(model=LLM_MODEL,api_key=OPENAI_API_KEY, temperature=0)


# ==========================================
# 📋 STRUCTURED OUTPUT SCHEMAS (Pydantic)
# ==========================================

class GradeDocsField(BaseModel):
    """Schema for document relevance scoring."""
    score: float = Field(
        description="Relevance score for the documents. Return 1.0 if relevant, or 0.0 if completely irrelevant."
    )

class ValidateAnswerField(BaseModel):
    """Schema for answer hallucination/grounding validation."""
    grounded_score: bool = Field(
        description="True if the answer is strictly grounded in and supported by the context. False if it hallucinates outside info."
    )


#The Fetcher,look at the Vector DB and get back the documents related to the user's question
def retrieve_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Fetches documents from the vector database and formats the context string."""
    query = state["query"]
    results = retrieve_vectordb(query)
    context = format_context(results)
    return {
        "retrieved_docs": results,
        "context": context
    }
    
#The Quality Inspector
#This function basically looks at the fetched document and decides whether they actually help answer the user's question,
#or are they useless junk 
def grade_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Scores retrieved_docs against the query. Writes retrieval_score and needs_retry."""
    user_query = state["query"]
    docs = state["retrieved_docs"]

    # Fail-safe: If no documents were returned, flag for immediate retry
    if not docs:
        return {
            "retrieval_score": 0.0,
            "needs_retry": True
        }
    
    structured_llm_grader = llm.with_structured_output(GradeDocsField)

    system_prompt = (
        "You are an enterprise-grade auditor assessing the relevance of retrieved documents to a user query.\n"
        "If the documents contain any information or semantic context that helps answer the query, grade them as relevant (1.0).\n"
        "Otherwise, grade them as irrelevant (0.0)."
    )

    docs_content = state["context"]
    user_prompt = f"Retrieved Documents:\n{docs_content}\n\nUser Query: {user_query}"
    
    grade_result = structured_llm_grader.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])
    
    score = grade_result.score
    
    return {
        "retrieval_score": score,
        "needs_retry": True if score < 1.0 else False
    }

def reformulate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Rewrites the query for better retrieval on retry."""
    original_query = state["query"]
    retry_count = state.get("retry_count", 0)
    
    reformulation_prompt = f"""The following query did not retrieve relevant documents.
Rewrite it to be more specific and explicit.
Return ONLY the rewritten query.

Original query: {original_query}"""
    
    ai_message = llm.invoke([
        HumanMessage(content=reformulation_prompt)
    ])
    
    return {
        "query": ai_message.content.strip(),
        "reformulated_query": ai_message.content.strip(),
        "retry_count": retry_count + 1,
        "needs_retry": False
    }

#The Writer
#Write out a polished, professional response using only the approved documents.
def generate_node(state):
    """Generates the response using the formatted context. Writes answer."""
    user_query = state["query"]
    context_str = state["context"]
    user_prompt = f"Context:\n{context_str}\n\nQuestion: {user_query}\n\nAnswer:"
    
    ai_message = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt)
    ])
    
    return {
        "answer": ai_message.content
    }



#The Fact-Checker
#Double-check the writer's homework. Did the writer make up any fake facts (hallucinate), or is the answer strictly backed up by the official documents?
def validate_node(state):
    """Checks if the generated answer is strictly grounded in the context. Writes is_grounded."""
    context_str = state["context"]
    generated_answer = state["answer"]
    
    # If no answer was generated to test, it can't be grounded
    if not generated_answer:
       return {"is_grounded": False}
        
    structured_llm_validator = llm.with_structured_output(ValidateAnswerField)
    
    system_prompt = (
        "You are a strict compliance auditor checking an AI answer against official background context.\n"
        "Assess whether the generated answer is entirely grounded in and supported by the context.\n"
        "Return True if the answer is completely justified. Return False if it introduces outside assumptions or hallucinations."
    )
    user_prompt = f"Official Context:\n{context_str}\n\nGenerated AI Answer:\n{generated_answer}"
    
    validation_result = structured_llm_validator.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])
    
    return {
    "is_grounded": validation_result.grounded_score,
    "final_answer": state["answer"] if validation_result.grounded_score else "The answer could not be verified against the source documents."
    }