from typing import TypedDict


class HumanDecision(TypedDict):
    decision: str  # "approved" | "rejected" | "edited"
    edited_resolution: str | None
    feedback: str | None


def format_for_human(state: dict) -> dict:
    return {
        "ticket_id": state.get("ticket", {}).get("ticket_id", "N/A"),
        "subject": state.get("ticket", {}).get("subject", ""),
        "category": state.get("category", ""),
        "confidence": state.get("classification_confidence", 0),
        "severity": state.get("severity", ""),
        "severity_score": state.get("severity_score", 0),
        "resolution": state.get("resolution", ""),
        "sources": state.get("resolution_sources", []),
    }


def process_human_decision(state: dict, decision: HumanDecision) -> dict:
    update = {
        "human_decision": decision["decision"],
        "human_feedback": decision.get("feedback"),
    }
    if decision["decision"] == "edited" and decision.get("edited_resolution"):
        update["human_edited_resolution"] = decision["edited_resolution"]
    return update
