from langgraph.graph import StateGraph, START, END
from src.agent.state import AgentState
from src.agent.nodes import (
    retrieve_node,
    grade_node,
    reformulate_node,
    generate_node,
    validate_node
)

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Conditional routing logic
def route_after_grading(state: AgentState) -> str:
    if state["needs_retry"]:
        return "retry"
    return "generate"

def route_after_validation(state: AgentState) -> str:
    if state["is_grounded"]:
        return "approved"
    if state.get("retry_count", 0) >= 2:
        return "approved"
    return "regenerate"

# Build graph
workflow = StateGraph(AgentState)

workflow.add_node("retrieve", retrieve_node)
workflow.add_node("grade", grade_node)
workflow.add_node("reformulate", reformulate_node)
workflow.add_node("generate", generate_node)
workflow.add_node("validate", validate_node)

workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "grade")
workflow.add_edge("generate", "validate")
workflow.add_edge("reformulate", "retrieve")

workflow.add_conditional_edges(
    "grade",
    route_after_grading,
    {
        "generate": "generate",
        "retry": "reformulate"
    }
)

workflow.add_conditional_edges(
    "validate",
    route_after_validation,
    {
        "approved": END,
        "regenerate": "generate"
    }
)

app = workflow.compile()

if __name__ == "__main__":
    result = app.invoke({
        "query": "What was Apple's revenue in 2025?",
        "retry_count": 0,
        "needs_retry": False
    })
    print(result["final_answer"])