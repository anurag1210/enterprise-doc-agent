from typing import TypedDict, Optional


class AgentState(TypedDict):
    """State schema for the enterprise-doc-agent LangGraph."""
    
    # Input
    query: str
    
    # Retrieval
    retrieved_docs: list
    retrieval_score: Optional[float]
    
    # Decision
    retry_count: int
    needs_retry: bool
    reformulated_query: Optional[str]
    
    # Generation
    context: str
    answer: Optional[str]
    
    # Validation
    is_grounded: Optional[bool]
    
    # Final
    final_answer: str