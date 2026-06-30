import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.services.llm_service import LLMFactory

SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a telecom incident analyst. Summarize the following ticket concisely.\n"
        "Extract: issue type, affected service, impact scope, and urgency indicators.\n"
        "Respond in 2-3 sentences.",
    ),
    ("human", "Ticket:\nSubject: {subject}\nDescription: {description}\nCategory: {category}\nSeverity: {severity}"),
])

PRIORITY_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a telecom incident analyst. Assign a priority score (1-100) based on:\n"
        "  - Critical (81-100): Service outage, multiple customers affected\n"
        "  - High (61-80): Partial outage, performance degradation\n"
        "  - Medium (41-60): Single customer, non-urgent\n"
        "  - Low (1-40): Inquiry, informational\n"
        "Respond with a JSON object: {{\"score\": <int>, \"reason\": \"<brief reason>\"}}",
    ),
    ("human", "Category: {category}\nSeverity: {severity}\nDescription: {description}"),
])


def summarize_ticket(ticket: dict) -> str:
    llm = LLMFactory.get_llm(temperature=0.0, max_tokens=256)
    chain = SUMMARY_PROMPT | llm | StrOutputParser()
    return chain.invoke({
        "subject": ticket.get("subject", ""),
        "description": ticket.get("description", ""),
        "category": ticket.get("category", ""),
        "severity": ticket.get("severity", ""),
    })


def compute_priority(ticket: dict) -> dict:
    llm = LLMFactory.get_llm(temperature=0.0, max_tokens=128)
    chain = PRIORITY_PROMPT | llm | StrOutputParser()
    raw = chain.invoke({
        "category": ticket.get("category", ""),
        "severity": ticket.get("severity", ""),
        "description": ticket.get("description", ""),
    })
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"score": 50, "reason": "fallback - parse error"}
