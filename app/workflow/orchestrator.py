from typing import TypedDict, Literal
from typing_extensions import Annotated
import operator

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.classification_agent import classify_ticket
from app.agents.severity_agent import detect_severity
from app.agents.resolution_agent import suggest_resolution


class AgentState(TypedDict):
    ticket: dict
    category: str | None
    classification_confidence: float
    classification_reasoning: str
    severity: str | None
    severity_score: int
    severity_reasoning: str
    resolution: str | None
    resolution_eta: str | None
    resolution_sources: list[str]
    route: str | None
    human_decision: str | None
    human_edited_resolution: str | None
    human_feedback: str | None
    error: str | None


def classification_node(state: AgentState) -> dict:
    ticket = state["ticket"]
    result = classify_ticket(ticket)
    return {
        "category": result["category"],
        "classification_confidence": result.get("confidence", 0),
        "classification_reasoning": result.get("reasoning", ""),
    }


def severity_node(state: AgentState) -> dict:
    ticket = state["ticket"]
    category = state["category"]
    result = detect_severity(ticket, category or "")
    return {
        "severity": result["severity"],
        "severity_score": result.get("score", 50),
        "severity_reasoning": result.get("reasoning", ""),
    }


def resolution_node(state: AgentState) -> dict:
    ticket = state["ticket"]
    category = state["category"] or ""
    severity = state["severity"] or ""
    result = suggest_resolution(ticket, category, severity)
    return {
        "resolution": result.get("resolution", ""),
        "resolution_eta": result.get("estimated_time", ""),
        "resolution_sources": result.get("references", []),
    }


def auto_resolve_node(state: AgentState) -> dict:
    return {
        "resolution": "Auto-resolved: Low-severity billing ticket processed automatically. "
                       "Credit applied to customer account. No further action needed.",
        "resolution_eta": "5 minutes",
        "resolution_sources": ["auto-billing-rule"],
    }


def route_ticket(state: AgentState) -> Literal["resolution", "auto_resolve", "__end__"]:
    severity = (state.get("severity") or "").lower()
    category = (state.get("category") or "").lower()
    if severity == "low" and category == "billing":
        return "auto_resolve"
    return "resolution"


def build_workflow() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("classify", classification_node)
    builder.add_node("severity", severity_node)
    builder.add_node("resolution", resolution_node)
    builder.add_node("auto_resolve", auto_resolve_node)

    builder.add_edge(START, "classify")
    builder.add_edge("classify", "severity")
    builder.add_conditional_edges("severity", route_ticket)
    builder.add_edge("resolution", END)
    builder.add_edge("auto_resolve", END)

    return builder


def compile_workflow():
    graph = build_workflow()
    return graph.compile(checkpointer=MemorySaver())


def run_workflow(ticket: dict, thread_id: str = "default") -> AgentState:
    app = compile_workflow()
    config = {"configurable": {"thread_id": thread_id}}
    initial_state: AgentState = {
        "ticket": ticket,
        "category": None,
        "classification_confidence": 0.0,
        "classification_reasoning": "",
        "severity": None,
        "severity_score": 0,
        "severity_reasoning": "",
        "resolution": None,
        "resolution_eta": None,
        "resolution_sources": [],
        "route": None,
        "human_decision": None,
        "human_edited_resolution": None,
        "human_feedback": None,
        "error": None,
    }
    result = app.invoke(initial_state, config)
    return result
